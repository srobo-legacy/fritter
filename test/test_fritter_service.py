
from fritter.fritter_service import FritterService
from fritter.gerrit_ssh import PatchSet
from fritter.repo_template_loader import RepoTemplateLoader

class FakeRepo(object):
    def __init__(self, files_added):
        self._files_added = files_added
        self.revision = None

    def files_added(self, revision):
        self.revision = revision
        return self._files_added

class FakeFeedback(object):
    def __init__(self):
        self.review = None

    def set_review(self, patchset, message, verified):
        self.review = (patchset, message, verified)

class FakePreviewer(object):
    def __init__(self, preview):
        self._preview = preview
        self.template_name = None

    def format_section(self, h, c):
        return "{0}{1}".format(h, c)

    def preview(self, template_name, target):
        self.template_name = template_name
        target.write(self._preview)

class FakeMailer(object):
    def __init__(self):
        self.template_name = None

    def send_template(self, template_name):
        self.template_name = template_name

def get_service(project, files_added = [], preview = ''):
    repo = FakeRepo(files_added)
    previewer = FakePreviewer(preview)
    feedback = FakeFeedback()
    mailer = FakeMailer()
    service = FritterService(project, repo, previewer, feedback, mailer)
    return service, repo, previewer, feedback, mailer

def get_event(project, revision, type_):
    # Equivalent to what Gerrit outputs
    return {
        'change': { 'project': project },
        'patchSet': { 'revision': revision },
        'type': type_,
    }

def test_create_patchset():
    proj = 'the-project'
    rev  = 'the-revision'

    event = get_event(proj, rev, None)
    ps = FritterService.create_patchset(event)
    expected = PatchSet(proj, rev)

    assert expected == ps, "Created bad patch set"

def test_other_event():
    service, _, _, _, _ = get_service('')
    service.event_handler({'type':'other'})

def test_good_template():
    tpl = 'tpl.txt'
    preview = 'my-preview'
    project = 'test-project'
    service, repo, previewer, feedback, _ = get_service(project, [tpl], preview)

    revision = '02d8cb070835fa80543e48f2699e5d37110359c1'
    event = get_event(project, revision, 'patchset-created')

    service.event_handler(event)

    queried_rev = repo.revision
    assert revision == queried_rev, "Asked the repo for the wrong revisison"

    expected_template = RepoTemplateLoader.template_name(tpl, revision)
    actual_template = previewer.template_name
    assert expected_template == actual_template, "Wrong template name previewed"

    patchset, message, verified = feedback.review
    pp = patchset.project
    assert project == pp, "Gave feedback on the wrong project"
    pr = patchset.revision
    assert revision == pr, "Gave feedback on the wrong revision"

    assert tpl in message, "Should mention the file name in the message"
    assert preview in message, "Should include the preview in the message"

    assert 1 == verified, "Should verify the result"

def test_merge_good_template():
    tpl = 'tpl.txt'
    preview = 'my-preview'
    project = 'test-project'
    service, repo, previewer, feedback, mailer = get_service(project, [tpl], preview)

    revision = '02d8cb070835fa80543e48f2699e5d37110359c1'
    event = get_event(project, revision, 'change-merged')

    service.event_handler(event)

    queried_rev = repo.revision
    assert revision == queried_rev, "Asked the repo for the wrong revisison"

    expected_template = RepoTemplateLoader.template_name(tpl, revision)
    actual_template = previewer.template_name
    assert expected_template == actual_template, "Wrong template name previewed"

    patchset, message, verified = feedback.review
    pp = patchset.project
    assert project == pp, "Gave feedback on the wrong project"
    pr = patchset.revision
    assert revision == pr, "Gave feedback on the wrong revision"

    assert tpl in message, "Should mention the file name in the message"
    assert preview not in message, "Should not include the preview in the message"

    assert 0 == verified, "Verification value should be 0 as it is ignored once the patchset has been merged"

    mailer_template = mailer.template_name
    assert expected_template == mailer_template, "Gave the wrong template to the mailer"
