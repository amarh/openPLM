from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_noop, ugettext_lazy as _

from openPLM.plmapp.models import Document
from openPLM.plmapp.controllers import DocumentController

class Page(Document):

    page_content = models.TextField(default="Edit me")
    page_content.richtext = True

    @classmethod
    def get_creation_fields(cls):
        return Document.get_creation_fields() + ["page_content",]

    @property
    def menu_items(self):
        menu = super(Page, self).menu_items
        menu.insert(0, ugettext_noop("page"))
        return menu

    def is_promotable(self):
        # if a Page has no files, it is still promotable
        if not self._is_promotable():
            return False
        if self.files.filter(locked=True).exists():
            self._promotion_errors.append(_("Some files are locked."))
            return False
        return True

    @property
    def published_attributes(self):
        return super(Page, self).published_attributes + ["page_content"]

admin.site.register(Page)


class PageController(DocumentController):

    def edit_content(self, new_content):
        self.check_edit_files()
        self.page_content = new_content
        self.save()


