
from fritter.template_lister import TemplateLister

class FakeRepo(object):
    def __init__(self, files_added):
        self._files = files_added
        self.revision = None

    def files_added(self, rev):
        self.revision = rev
        return self._files

def test_pattern():
    all_files = ['a/b.c', 'a/b/c/d', 'a/c/b/z.e', 'z/b.c']
    def helper(pattern, expected):
        repo = FakeRepo(all_files)
        tl = TemplateLister(repo, pattern)

        actual = tl.get_files('rev')

        actual_rev = repo.revision
        assert 'rev' == actual_rev, "Passed the wrong revision to the repo"

        assert expected == actual, "Filtered incorrectly"

    yield helper, 'a*', ['a/b.c', 'a/b/c/d', 'a/c/b/z.e']
    yield helper, '*.c', ['a/b.c', 'z/b.c']
    yield helper, 'a*.c', ['a/b.c']
