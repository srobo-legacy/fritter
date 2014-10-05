
from collections import namedtuple

from . import srusers

class UnknownGroup(Exception):
    """An exception to raise when we are asked about a group that isn't
    in the database.
    """
    def __init__(self, group_name):
        super(UnknownGroup, self).__init__(
            "Unknown group '{0}'.".format(group_name)
        )

class InvalidGroup(Exception):
    """An exception to raise when we are asked about a group that isn't
    in the list of valid groups.
    """
    def __init__(self, group_name):
        super(InvalidGroup, self).__init__(
            "Group '{0}' is not allowed.".format(group_name)
        )

User = namedtuple('User', ['first_name', 'last_name', 'email'])

class LDAPGroupConnector(object):
    def __init__(self, valid_groups):
        """Create a new connector.

        Parameters
        ----------
        valid_groups : list of str
            A list of names which are valid for this instance to lookup
            information about. Will raise ``UnknownGroup`` for any which
            don't exist in the underlying database.
        """
        map(self._get_group, valid_groups)
        self._valid_groups = valid_groups

    def _get_group(self, group_name):
        g = srusers.group(group_name)
        if not g.in_db:
            raise UnknownGroup(group_name)
        return g

    def _check_valid(self, group_name):
        if not group_name in self._valid_groups:
            raise InvalidGroup(group_name)

    def describe(self, group_name):
        self._check_valid(group_name)
        g = self._get_group(group_name)
        return g.desc or group_name

    def get_users(self, group_name):
        self._check_valid(group_name)
        g = self._get_group(group_name)
        users = []
        for uid in g.members:
            u = srusers.user(uid)
            user = User(u.cname, u.sname, u.email)
            users.append(user)
        return users
