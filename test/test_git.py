
import os
import shutil
from subprocess import CalledProcessError, check_output
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

def test_not_bare():
    repo = assert_clone('not_bare')
    is_bare = repo.is_bare()
    assert not is_bare, "Repo should not invalidly claim to be bare"

def test_bare():
    repo_path = os.path.join(work_path, 'bare')
    os.mkdir(repo_path)
    check_output('git init --bare', shell=True, cwd=repo_path)
    repo = GitRepository(repo_path)
    is_bare = repo.is_bare()
    assert is_bare, "Should be bare when created as such"

def test_files_added():
    repo_path = os.path.join(work_path, 'files_added')
    os.mkdir(repo_path)

    def run(cmd):
        check_output(cmd, shell=True, cwd=repo_path)

    def open_(name, *args):
        return open(os.path.join(repo_path, name), *args)

    def touch(name):
        open_(name, 'w').close()

    def edit(name):
        with open_(name, 'w') as f:
            f.write("bacon\n")

    def rm(name):
        os.remove(os.path.join(repo_path, name))

    def commit_all(msg):
        run('git add -A . && git commit -m "{0}"'.format(msg))

    run('git init')

    baseline = 'baseline'
    touch(baseline)

    commit_all('Initial')

    foo = 'foo'
    bar = 'bar'
    touch(foo)
    touch(bar)

    commit_all('Second')

    rm(foo)
    edit(bar)
    another = 'another'
    touch(another)

    commit_all('Third')

    repo = GitRepository(repo_path)

    added = repo.files_added('HEAD')
    assert [another] == added

    added = repo.files_added('HEAD^')
    # don't care about ordering
    assert set([foo, bar]) == set(added)
