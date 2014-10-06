
import fnmatch

class TemplateLister(object):
    "A filter around the files added within a given revision"
    def __init__(self, repo, pattern):
        """Create a new template lister.

        Parameters
        ----------
        repo : GitRepository
            The repo to lookup the revision within.
        pattern : str
            The pattern to filter the files down to.
        """
        self._repo = repo
        self._pattern = pattern

    def get_files(self, revision):
        added_files = self._repo.files_added(revision)
        return fnmatch.filter(added_files, self._pattern)
