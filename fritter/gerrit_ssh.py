
from collections import namedtuple
from contextlib import contextmanager
import logging
import paramiko
import pipes

PatchSet = namedtuple('PatchSet', ['project', 'branch', 'change_id', 'revision'])

CONFIG_SECTION = 'GerritServer'

@contextmanager
def ssh_connection(*args, **kwargs):
    client = paramiko.client.SSHClient()
    client.load_system_host_keys()
    client.connect(*args, **kwargs)
    yield client
    client.close()

class GerritSSH(object):
    def __init__(self, config):
        """Create a new wrapper around a Gerrit instance's SSH API.

        Parameters
        ----------
        config : ConfigParser
            configuration object containing connection details
        """
        self._config = config
        self._logger = logging.getLogger('fritter.gerrit_ssh')

    def _cmd(self, *args):
        host = self._config.get(CONFIG_SECTION, 'host')
        user = self._config.get(CONFIG_SECTION, 'user')
        port = self._config.get(CONFIG_SECTION, 'port')
        privkey = self._config.get(CONFIG_SECTION, 'privkey')

        with ssh_connection(host, int(port), user, key_filename = privkey, timeout = 5) as client:
            str_args = map(str, iter(args))
            # Yes pipes.quote is deprecated, but shlex.quote doesn't exist until Python 3.3
            command = " ".join(map(pipes.quote, str_args))

            _, stdout, stderr = client.exec_command("gerrit " + command)

            errors = stderr.read()
            if errors:
                self._logger.error("Error running \"%s\": \"%s\".", command, errors)

            return stdout.read()

    def set_review(self, patch_set, message, verified):
        """Add a review to the given patch set.

        Parameters
        ----------
        patch_set : PatchSet
            A ``PatchSet`` instance describing the patch set to review.
        message : str
            The main body of the review.
        verified : {0, -1, 1}
        """

        valid_verified = (0, -1, 1)
        assert verified in valid_verified, "Bad value for 'verified', expecting one of {}.".format(valid_verified)

        args = [
            'review',
            '--project', patch_set.project,
            '--message', message,
            '--verified', verified,
            patch_set.revision,
        ]
        self._cmd(*args)
