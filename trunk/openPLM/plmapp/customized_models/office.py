import os

from django.db import models
from django.contrib import admin

from openPLM.plmapp.filehandlers import HandlersManager
from openPLM.plmapp.models import Document
from openPLM.plmapp.controllers import DocumentController
from openPLM.plmapp.utils import CFORMATS

def register(cls):
    try:
        admin.site.register(cls)
    except admin.sites.AlreadyRegistered:
        pass

class OfficeDocument(Document):

    class Meta:
        app_label = "plmapp"

    nb_pages = models.PositiveIntegerField("Number of pages", blank=True, null=True)
    format = models.CharField(max_length=10, choices=CFORMATS, default=lambda: "A4")

    @property
    def attributes(self):
        attrs = list(super(OfficeDocument, self).attributes)
        attrs.extend(["nb_pages", "format"])
        return attrs

class OfficeDocumentController(DocumentController):

    def handle_added_file(self, doc_file):
        if os.path.splitext(doc_file.file.path)[1].lower() == ".odt":
            handler_cls = HandlersManager.get_best_handler(".odt")
            handler = handler_cls(doc_file.file.path, doc_file.filename)
            if handler.is_valid():
                self.nb_pages = handler.nb_pages
                self.format = handler.format
        self.save()

register(OfficeDocument)

