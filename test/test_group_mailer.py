
import mock

from fritter.group_mailer import GroupMailer
from fritter.ldap_connector import User

class FakeEmailTemplate(object):
    def __init__(self, to):
        self.to = to

def test_send_template():

    expected_group = 'to-group'
    fake_loader = mock.Mock(return_value = FakeEmailTemplate([expected_group]))

    user_to_return = User('fff', 'lll', 'fl@example.com')
    fake_connector = mock.Mock(return_value = [user_to_return])

    fake_mailer = mock.Mock()

    mailer = GroupMailer(fake_mailer, fake_connector, fake_loader)

    expected_template = 'exp-tpl'
    mailer.send_template(expected_template)

    fake_loader.assert_called_with(expected_template)
    fake_connector.assert_called_with(expected_group)
    fake_mailer.assert_called_with(user_to_return.email, expected_template, user_to_return._asdict())
