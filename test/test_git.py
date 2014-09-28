
import os.path
import shutil
from subprocess import CalledProcessError
import tempfile

from tests_helpers import root

from fritter.git import GitRepository

work_path = None

def setUp():
    global work_path
    work_path = tempfile.mkdtemp()

def tearDown():
    global work_path
    shutil.rmtree(work_path)

def assert_clone(target):
    repo_root = root()
    clone_path = os.path.join(work_path, target)

    repo = GitRepository.clone(repo_root, clone_path)
    assert os.path.exists(clone_path), "Failed to create folder during clone of '{0}'.".format(target)
    assert repo is not None, "Failed to create repo from clone of '{0}'.".format(target)
    return repo

def test_clone():
    assert_clone('clone')

def test_clone_fail():
    clone_path = os.path.join(work_path, 'clone_fail')

    threw = False
    try:
        repo = GitRepository.clone(work_path, clone_path)
    except CalledProcessError:
        threw = True

    assert threw, "Should have raised an exception for git's error"

def test_bare():
    repo = assert_clone('bare')
    is_bare = repo.is_bare()
    assert not is_bare, "Repo should not invalidly claim to be bare"
