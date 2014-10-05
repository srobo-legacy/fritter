
class GroupMailer(object):
    """Sends templated emails to all members of the groups listed in the
    "To:" field within the template.
    """
    def __init__(self, mailer, group_expander, template_factory):
        """Create a new group mailer

        Parameters
        ----------
        mailer : callable(toaddr : str, template_name : str, template_vars : dict)
            A function which actually sends the emails.
        group_expander : callable(group_name)
            A function which returns an iterable of ``User`` instances for
            each member of the group name given.
        template_factory : callable(template_name)
            A function which returns an ``EmailTemplate`` instance for the
            given name.
        """
        self._mailer = mailer
        self._group_expander = group_expander
        self._template_factory = template_factory

    def send_template(self, template_name):
        et = self._template_factory(template_name)
        for group_name in et.to:
            for user in self._group_expander(group_name):
                values = user._asdict()
                self._mailer(user.email, template_name, values)
