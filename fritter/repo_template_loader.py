
from .libfritter.libfritter.email_template import EmailTemplate

class RepoTemplateLoader(object):
    @staticmethod
    def template_name(file_path, ref):
        return "{0}@{1}".format(file_path, ref)

    def __init__(self, repo):
        self._repo = repo

    def load(self, name):
        file_path, ref = name.split('@')
        content = self._repo.file_content(file_path, ref)
        et = EmailTemplate(content)
        return et
