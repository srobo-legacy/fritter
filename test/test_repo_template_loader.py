
from fritter.repo_template_loader import RepoTemplateLoader

class FakeRepo(object):
    subject = "Fake subject line"

    @staticmethod
    def fake_body_for(name, ref):
        return "Fake content for '{0}' @ '{1}'.".format(name, ref)

    def file_content(self, name, ref):
        return "Subject: {0}\n{1}".format(self.subject, self.fake_body_for(name, ref))

def test_loader():
    r = FakeRepo()
    l = RepoTemplateLoader(r)

    name = 'bacon'
    et = l.load('bacon@HEAD')

    expected_subject = r.subject
    subject = et.subject
    assert expected_subject == subject, "Wrong subject line"

    expected_body = r.fake_body_for(name, 'HEAD')
    body = et.raw_body
    assert expected_body == body, "Wrong body line"
