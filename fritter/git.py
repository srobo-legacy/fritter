
import logging
from subprocess import Popen, PIPE, CalledProcessError

def _git(cwd, args):
    args.insert(0, 'git')
    proc = Popen(args, cwd=cwd, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    if proc.returncode:
        cmd = "'{0}'".format("' '".join(args))
        tpl = "Call to '%s' in '%s' failed (returned %d):\nSTDOUT:\n%s\nSTDERR:\n%s"
        logging.error(tpl, cmd, cwd, proc.returncode, out, err)
        raise CalledProcessError(proc.returncode, cmd, out)

    return out.decode('utf-8')

class GitRepository(object):

    @classmethod
    def clone(cls, source, dest):
        _git(None, ['clone', source, dest])
        return cls(dest)

    def __init__(self, path):
        self._path = path

    def _git(self, *args):
        return _git(self._path, list(args))

    def is_bare(self):
        out = self._git('config', '--get', '--bool', 'core.bare')
        return out.strip().lower() == 'true'

    def files_added(self, ref):
        out = self._git('diff', '--name-status', ref + '^', ref)
        lines = out.splitlines()
        added = []
        for line in lines:
            kind, path = line.split()
            if kind == 'A':
                added.append(path)

        return added

    def file_content(self, file_path, ref):
        content = self._git('show', "{0}:{1}".format(ref, file_path))
        return content
