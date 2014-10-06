
try:
    # python 2
    import ConfigParser as configparser
except ImportError:
    # python 3
    import configparser

from contextlib import contextmanager
import json
import mock
from nose import with_setup
import os.path
import shutil
import tempfile

from fritter.fritter_service import FritterService

from test_ldap_connector import get_mock_srusers, get_mock_group_ctor, \
                                get_mock_user_ctor
from tests_helpers import test_root, test_data

from fritter.libfritter.test.tests_helpers import delete_db, ensure_db, \
                                                  last_email as last_email_

TEST_DB = os.path.join(test_root(), 'test.db')

work_path = None

def clear_db():
    delete_db(TEST_DB)

def get_last_email():
    return last_email_(TEST_DB)

def setup():
    # don't use `test_data` here as that asserts the file exists,
    # which it validly might not
    global work_path
    work_path = tempfile.mkdtemp()
    print("work_path:", work_path)
    shutil.copytree(test_data('testing-repo.git'), os.path.join(work_path, 'testing-repo.git'))
    ensure_db(TEST_DB)

def teardown():
    global work_path
    shutil.rmtree(work_path)

def load_event(file_name):
    file_path = test_data(file_name)
    with open(file_path, 'r') as f:
        return json.load(f)

def load_config():
    global work_path
    defaults = {'test_root': test_root(), 'work_path': work_path}
    config = configparser.SafeConfigParser(defaults)
    ini_path = test_data('test.ini')
    read = config.read(ini_path)
    assert ini_path in read, "Failed to read test config file."
    return config

@contextmanager
def mock_ssh(mock_exec_command):
    mock_connection = mock.Mock()
    mock_connection.exec_command = mock_exec_command
    mock_connection_mgr = mock.MagicMock(spec = file)
    mock_connection_mgr.__enter__ = mock.Mock(return_value = mock_connection)
    mock_connector = mock.Mock(return_value = mock_connection_mgr)
    with mock.patch('fritter.gerrit_ssh.ssh_connection', mock_connector):
        yield mock_connector

    mock_connector.assert_called_with('test-host', 29418, 'fritter',
                                      key_filename = 'test-priv-key',
                                      timeout = 5)

def do_submit(event_file):
    config = load_config()
    with get_mock_srusers() as mock_srusers:
        mock_srusers.group = get_mock_group_ctor(in_db = True)
        service = FritterService.create(config)

        event = load_event(event_file)
        patchset = FritterService.create_patchset(event)

        mock_out = mock.Mock()
        mock_err = mock.Mock()
        mock_exec_command = mock.Mock(return_value = (None, mock_out, mock_err))
        with mock_ssh(mock_exec_command):

            service.patchset_created(patchset)

    assert mock_exec_command.called, "Should have emitted a review at Gerrit"
    command = mock_exec_command.call_args[0][0]
    return command

def test_submit():
    command = do_submit('submit.json')
    assert command.startswith('gerrit review'), "Wrong command ran against Gerrit"
    assert 'testing-repo' in command, "Doesn't mention right project"
    assert 'nice-ship.txt' in command, "Doesn't mention right file"
    assert 'An example template' in command, "Doesn't contain the subject"
    assert 'We like your ship' in command, "Doesn't contain the body"

def test_submit_bad():
    command = do_submit('submit-bad-fields.json')
    assert command.startswith('gerrit review'), "Wrong command ran against Gerrit"
    assert '$INVALID_BACON' in command, "Doesn't mention the bad placeholder"
    assert 'Error' in command, "Doesn't indicate an error"
    assert 'testing-repo' in command, "Doesn't mention right project"
    assert 'bad-fields.txt' in command, "Doesn't mention right file"
    assert 'Bad fields' in command, "Doesn't contain the subject"

@with_setup(clear_db)
def test_merged():
    config = load_config()
    first, last, addr = 'Jim', 'Kirk', 'jtk@example.com'
    with get_mock_srusers() as mock_srusers:
        mock_srusers.group = get_mock_group_ctor(in_db = True, members = 'jtk')
        mock_srusers.user = get_mock_user_ctor(first, last, addr)
        service = FritterService.create(config)

        event = load_event('merged.json')
        patchset = FritterService.create_patchset(event)

        mock_out = mock.Mock()
        mock_err = mock.Mock()
        mock_exec_command = mock.Mock(return_value = (None, mock_out, mock_err))
        with mock_ssh(mock_exec_command):

            service.change_merged(patchset)

    assert mock_exec_command.called, "Should have emitted a review at Gerrit"
    command = mock_exec_command.call_args[0][0]
    assert command.startswith('gerrit review'), "Wrong command ran against Gerrit"
    assert 'testing-repo' in command, "Doesn't mention right project"
    assert 'nice-ship.txt' in command, "Doesn't mention right file"

    last_email = get_last_email()

    toaddr        = last_email.toaddr
    template_name = last_email.template_name
    template_vars = last_email.template_vars

    assert addr == toaddr, "Sent to wrong person"
    assert 'nice-ship.txt@c994ec517e4f809c8acf3b0c7f4d9f466b8069b1' == \
           template_name, "Sent wrong template"

    expected_vars = {
        'first_name': first,
        'last_name': last,
        'email': addr,
    }
    assert expected_vars == template_vars, "Wrong template vars"
