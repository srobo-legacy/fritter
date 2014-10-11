
import os.path
from subprocess import CalledProcessError, check_output, STDOUT

from tests_helpers import root, test_data

def get_preview(revision):
    script = os.path.join(root(), 'preview')
    repo_path = test_data('testing-repo.git')

    cmd_args = [script, repo_path, revision]
    preview = None
    try:
        preview = check_output(cmd_args, stderr=STDOUT).decode('utf-8')
    except CalledProcessError as cpe:
        print(cpe.output)
        raise

    return preview

def test_valid_submission():
    preview = get_preview('c994ec517e4f809c8acf3b0c7f4d9f466b8069b1')

    assert 'error' not in preview.lower(), "Should not have errored"
    assert 'Body' in preview, "Should have output the body"

def test_invalid_submission():
    preview = get_preview('53cac75793444bd9e450f3d223644075f84f01c9')

    assert 'Error' in preview, "Should have output an error"
    assert 'Invalid placeholder(s)' in preview, "Should have output a description of the errors"
