
from __future__ import print_function

from contextlib import contextmanager
from functools import partial
import logging
import sqlite3

try:
    # python 2
    from StringIO import StringIO
except ImportError:
    # python 3
    from io import StringIO

from .libfritter.libfritter.mailer import Mailer
from .libfritter.libfritter.previewer import Previewer
from .git import GitRepository
from .gerrit_ssh import GerritSSH, PatchSet
from .group_mailer import GroupMailer
from .ldap_connector import LDAPGroupConnector
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

    @classmethod
    def create(cls, config):
        "Create a new instance of the service around the given config."

        valid_groups = [g.strip() for g in config.get('ldap', 'valid-groups').split(',')]
        ldap_connector = LDAPGroupConnector(valid_groups)

        target_project = config.get('fritter', 'project_name')
        repo = GitRepository(config.get('fritter', 'project_path'))
        loader = RepoTemplateLoader(repo)
        previewer = Previewer(loader.load, ldap_connector.describe, None)

        feedback = GerritSSH(config)

        db_connector = partial(sqlite3.connect, config.get('fritter', 'sqlite_db'))

        mailer_config = dict(config.items('mailer'))
        mailer = Mailer(mailer_config, db_connector, loader.load)

        group_mailer = GroupMailer(mailer, ldap_connector, loader.load)

        service = cls(target_project, repo, previewer, feedback, group_mailer)

        return service

    def __init__(self, project_name, repo, previewer, feedback_handler, mailer):
        self._project = project_name
        self._repo = repo
        self._previewer = previewer
        self._feedback = feedback_handler
        self._mailer = mailer
        self._logger = logging.getLogger('fritter.fritter_service')
        self._handlers = {
            'patchset-created': self.patchset_created,
            'change-merged': self.change_merged,
        }

    def event_handler(self, event):
        kind = event['type']
        handler = self._handlers.get(kind, None)
        if handler is None:
            self._logger.debug("Ignoring %s event without handler.", kind)
            return

        patchset = self.create_patchset(event)
        if patchset.project != self._project:
            self._logger.debug("Ignoring %s event on unrelated project: %s.",
                               kind, patchset)
            return

        try:
            self._logger.info("About to handle %s event for %s",
                              kind, patchset)
            handler(patchset)
        except:
            self._logger.exception("Error handling '%s' event for %s.",
                                   kind, patchset)

    def _get_added_templates(self, patchset):
        added_files = self._repo.files_added(patchset.revision)
        added_templates = [f for f in added_files if f.endswith('.txt')]
        return added_templates

    def patchset_created(self, patchset):
        added_templates = self._get_added_templates(patchset)
        if not added_templates:
            return

        preview = None
        with close_on_exit(StringIO()) as preview_buffer:
            errors_map = self._write_preview(patchset.revision, added_templates, preview_buffer)
            preview = preview_buffer.getvalue()

        verified = 1
        if errors_map:
            verified = -1

        self._logger.debug("Review of %s: %d", patchset, verified)

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
        added_templates = self._get_added_templates(patchset)
        if not added_templates:
            return

        errors_map = None
        with close_on_exit(StringIO()) as preview_buffer:
            errors_map = self._write_preview(patchset.revision, added_templates, preview_buffer)

        format_section = self._previewer.format_section

        if errors_map:
            message_lines = ["Errors in templates. Unable to send the following:", ""]
            for f, err in errors_map.items():
                message_lines.append(format_section(f, err))

            message = "\n".join(message_lines)
            self._feedback.set_review(patchset, message, 0)

        valid_templates = set(added_templates) - set(errors_map.keys())

        for template_path in valid_templates:
            template_name = RepoTemplateLoader.template_name(template_path, patchset.revision)
            self._logger.info("Sending %s.", template_name)
            self._mailer.send_template(template_name)

        success_heading = "Success - sent the following templates"
        templates_str = "\n".join(valid_templates)
        success_message = format_section(success_heading, templates_str)
        self._feedback.set_review(patchset, success_message, 0)
