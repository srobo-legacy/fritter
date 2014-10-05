
from __future__ import print_function

from contextlib import contextmanager
import logging

try:
    # python 2
    from StringIO import StringIO
except ImportError:
    # python 3
    from io import StringIO

from .gerrit_ssh import PatchSet
from .repo_template_loader import RepoTemplateLoader

@contextmanager
def close_on_exit(item):
    yield item
    item.close()

class FritterService(object):
    "Main service runner"
    @staticmethod
    def create_patchset(event):
        return PatchSet(event['change']['project'], event['patchSet']['revision'])

    def __init__(self, project_name, repo, previewer, feedback_handler):
        self._project = project_name
        self._repo = repo
        self._previewer = previewer
        self._feedback = feedback_handler
        self._logger = logging.getLogger('fritter.fritter_service')
        self._handlers = {
            'patchset-created': self.patchset_created,
            'change-merged': self.change_merged,
        }

    def event_handler(self, event):
        patchset = self.create_patchset(event)
        if patchset.project != self._project:
            return

        kind = event['type']
        handler = self._handlers.get(kind, None)
        if handler is None:
            return

        try:
            handler(patchset)
        except:
            self._logger.exception("Error handling '%s' event for %s.",
                                   kind, patchset)

    def patchset_created(self, patchset):
        added_files = self._repo.files_added(patchset.revision)
        added_templates = [f for f in added_files if f.endswith('.txt')]
        if not added_templates:
            return

        preview = None
        with close_on_exit(StringIO()) as preview_buffer:
            errors_map = self._write_preview(patchset.revision, added_templates, preview_buffer)
            preview = preview_buffer.getvalue()

        verified = 1
        if errors_map:
            verified = -1

        self._feedback.set_review(patchset, preview, verified)

    def _write_preview(self, revision, files, writer):
        errors_map = {}

        for file_path in files:
            print('-' * 10, file_path, '-' * 10, file = writer)
            print(file = writer)
            template_name = RepoTemplateLoader.template_name(file_path, revision)
            errors = self._previewer.preview(template_name, writer)
            if errors:
                errors_map[file_path] = errors

        return errors_map


    def change_merged(self, patchset):
        pass
