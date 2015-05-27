
from collections import namedtuple
import logging

from . import srusers
from .libfritter.libfritter.previewer import BadRecipient
from .libfritter.libfritter.recipient_checker import RestrictedRecipientsChecker

class UnknownGroup(BadRecipient):
    """An exception to raise when we are asked about a group that isn't
    in the database.
    """
    def __init__(self, group_name):
        super(UnknownGroup, self).__init__(group_name, "Unknown group '{0}'.")

User = namedtuple('User', ['first_name', 'last_name', 'email'])

class LDAPGroupConnector(RestrictedRecipientsChecker):
    def __init__(self, valid_groups):
        """Create a new connector.

        Parameters
        ----------
        valid_groups : list of str
            A list of names which are valid for this instance to lookup
            information about. Will raise ``UnknownGroup`` for any which
            don't exist in the underlying database.
        """
        self._logger = logging.getLogger('fritter.ldap_connector')
        map(self._get_group, valid_groups)
        super(LDAPGroupConnector, self).__init__(valid_groups)

    def _get_group(self, group_name):
        self._logger.debug("Getting group '%s'.", group_name)
        g = srusers.group(group_name)
        if not g.in_db:
            raise UnknownGroup(group_name)
        return g

    def describe(self, group_name):
        self.check_valid(group_name)
        g = self._get_group(group_name)
        return g.desc or group_name

    def get_users(self, group_name):
        self.check_valid(group_name)
        g = self._get_group(group_name)
        users = []
        for uid in g.members:
            u = srusers.user(uid)
            if not u.email:
                self._logger.warn("Skipping user '%s' due to missing email", uid)
                continue
            user = User(u.cname, u.sname, u.email)
            users.append(user)
        self._logger.debug("Got %d useable members of group '%s'.", len(users), group_name)
        return users
