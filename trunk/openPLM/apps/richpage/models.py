from django.db import models
from django.contrib import admin

import openPLM.plmapp.exceptions as exc
from openPLM.plmapp.models import Document
from openPLM.plmapp.controllers import DocumentController

class Page(Document):

    ACCEPT_FILES = False

    page_content = models.TextField(default="Edit me")
    page_content.richtext = True

    @classmethod
    def get_creation_fields(cls):
        return Document.get_creation_fields() + ["page_content",]

    def is_promotable(self):
        # a Page has no files, so we do not checks
        # if it has a locked file
        return self._is_promotable()

admin.site.register(Page)


class PageController(DocumentController):

    def lock(self, doc_file):
        raise exc.LockError()

    def unlock(self, doc_file):
        raise exc.UnlockErrot()

    def add_file(self, f, update_attributes=True):
        raise exc.AddFileError()

    def delete_file(self, doc_file):
        raise exc.DeleteFileError()

    def edit_content(self, new_content):
        self.check_edit_files()
        self.page_content = new_content
        self.save()


