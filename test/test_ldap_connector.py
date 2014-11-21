
import mock

from fritter.libfritter.libfritter.recipient_checker import InvalidRecipient
from fritter.ldap_connector import LDAPGroupConnector, UnknownGroup, User

def get_mock_srusers():
    return mock.patch('fritter.ldap_connector.srusers')

def get_mock_group_ctor(in_db, desc = None, members = []):
    mock_group = mock.Mock()
    mock_group.in_db = in_db
    mock_group.desc = desc
    mock_group.members = members
    mock_group_ctor = mock.Mock(return_value = mock_group)
    return mock_group_ctor

def get_mock_user_ctor(first, last, email):
    mock_user = mock.Mock()
    mock_user.cname = first
    mock_user.sname = last
    mock_user.email = email
    mock_user_ctor = mock.Mock(return_value = mock_user)
    return mock_user_ctor

def test_valid_group_missing():
    with get_mock_srusers() as mock_srusers:
        mock_srusers.group = get_mock_group_ctor(in_db = False)

        threw = False
        group_name = 'my-missing-group'
        try:
            LDAPGroupConnector([group_name])
        except UnknownGroup as ug:
            msg = ug.message
            assert group_name in msg, "Should include the group name in the message"
            threw = True

        assert threw, "Should have errored about the missing group"

def test_valid_group():
    with get_mock_srusers() as mock_srusers:
        mock_srusers.group = get_mock_group_ctor(in_db = True)

        LDAPGroupConnector(['found'])

def test_describe_invalid_group():
    with get_mock_srusers() as mock_srusers:
        mock_srusers.group = get_mock_group_ctor(in_db = True)

        c = LDAPGroupConnector(['valid'])

        threw = False
        group_name = 'other'
        try:
            c.describe(group_name)
        except InvalidRecipient as ig:
            msg = ig.message
            assert group_name in msg, "Should include the group name in the message"
            threw = True

        assert threw, "Should have errored about the invalid group"

def test_describe_valid_group():
    with get_mock_srusers() as mock_srusers:
        desc = 'bacon'
        mock_srusers.group = get_mock_group_ctor(in_db = True, desc = desc)

        name = 'valid'
        c = LDAPGroupConnector([name])

        actual = c.describe(name)
        assert desc == actual, "Wrong description returned"

def test_describe_valid_group_no_description():
    with get_mock_srusers() as mock_srusers:
        mock_srusers.group = get_mock_group_ctor(in_db = True)

        name = 'valid'
        c = LDAPGroupConnector([name])

        actual = c.describe(name)
        assert name == actual, "Should fall back to the name if the description is empty"

def test_get_users_empty_group():
    with get_mock_srusers() as mock_srusers:
        mock_srusers.group = get_mock_group_ctor(in_db = True)

        name = 'valid'
        c = LDAPGroupConnector([name])

        actual = c.get_users(name)
        assert [] == actual, "Should return empty list for empty group"

def test_get_users():
    with get_mock_srusers() as mock_srusers:
        member_name = 'my-member-uid'
        mock_srusers.group = get_mock_group_ctor(in_db = True, members = [member_name])
        first, last = 'fff', 'lll'
        email = 'tim@example.com'
        mock_srusers.user = get_mock_user_ctor(first, last, email)

        name = 'valid'
        c = LDAPGroupConnector([name])

        actual = c.get_users(name)
        expected = [User(first, last, email)]
        assert expected == actual, "Should return a list of emails"
        mock_srusers.user.assert_called_once_with(member_name)

def test_user_no_email():
    with get_mock_srusers() as mock_srusers:
        member_name = 'my-member-uid'
        mock_srusers.group = get_mock_group_ctor(in_db = True, members = [member_name])
        first, last = 'fff', 'lll'
        email = None
        mock_srusers.user = get_mock_user_ctor(first, last, email)

        name = 'valid'
        c = LDAPGroupConnector([name])

        actual = c.get_users(name)
        expected = []
        assert expected == actual, "Should return a list of valid emails"
        mock_srusers.user.assert_called_once_with(member_name)
