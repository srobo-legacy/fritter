
import logging
from subprocess import Popen, PIPE, CalledProcessError

def _git(cwd, args):
    args.insert(0, 'git')
    proc = Popen(args, cwd=cwd, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    if proc.returncode:
        cmd = "'{0}'".format("' '".join(args))
        tpl = "Call to '%s' failed (returned %d):\nSTDOUT:\n%s\nSTDERR:\n%s"
        logging.error(tpl, cmd, proc.returncode, out, err)
        raise CalledProcessError(proc.returncode, cmd, out)

    return out

class GitRepository(object):

    @classmethod
    def clone(cls, source, dest):
        _git(None, ['clone', source, dest])
        return cls(dest)

    def __init__(self, path):
        self._path = path

    def _git(self, args):
        _git(self._path, args)

    def fetch(source, ref = None):
        args = ['fetch', source]
        if ref is not None:
            args.append(ref)
        _git(args)

    def checkout(ref):
        _git(['checkout', ref])

    def files_added(commit):
        out = _git(['diff', '--name-status'])
