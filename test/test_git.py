# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import shutil
from subprocess import CalledProcessError, check_output
import sys
import tempfile

from tests_helpers import root

from fritter.git import GitRepository

BACON_PONY_LINE = "bacon-♘\n"

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
    repo = build_repo('files_added')

    added = repo.files_added('HEAD')
    assert ['another'] == added

    added = repo.files_added('HEAD^')
    # don't care about ordering
    assert set(['foo', 'bar']) == set(added)

def test_file_content():
    repo = build_repo('file_content')

    def helper(name, ref, expected):
        actual = repo.file_content(name, ref)
        assert expected == actual, "Wrong content in '{0}'.".format(name)

    yield helper, 'bar', 'HEAD', BACON_PONY_LINE
    yield helper, 'bar', 'HEAD^', ''

def test_file_not_present():
    repo = build_repo('file_not_present')

    threw = False
    try:
        repo.file_content('nope', 'HEAD')
    except:
        threw = True

    assert threw, "Should have raised an exception about the file not existing"

def build_repo(name):
    repo_path = os.path.join(work_path, name)
    os.mkdir(repo_path)

    def run(cmd):
        check_output(cmd, shell=True, cwd=repo_path)

    def open_(name, *args):
        if sys.version_info[0] < 3:
            import codecs
            open_ = codecs.open
        else:
            open_ = open
        return open_(os.path.join(repo_path, name), *args, encoding='utf-8')

    def touch(name):
        open_(name, 'w').close()

    def edit(name):
        with open_(name, 'w') as f:
            f.write(BACON_PONY_LINE)

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
    return repo
