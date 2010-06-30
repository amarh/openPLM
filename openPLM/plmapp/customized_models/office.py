import os

from django.db import models
from django.contrib import admin

# see odfpy (sudo easy_install odfpy)
from odf.opendocument import load
from odf.meta import DocumentStatistic
from odf.style import PageLayoutProperties

from openPLM.plmapp.models import Document
from openPLM.plmapp.controllers import DocumentController
from openPLM.plmapp.utils import size_to_format, UNITS

def register(cls):
    try:
        admin.site.register(cls)
    except admin.sites.AlreadyRegistered:
        pass

class OfficeDocument(Document):

    class Meta:
        app_label = "plmapp"

    FORMATS = zip(UNITS.itervalues(), UNITS.itervalues()) 
    nb_pages = models.PositiveIntegerField("Number of pages", blank=True, null=True)
    format = models.CharField(max_length=10, choices=FORMATS, default=lambda: "A4")

    @property
    def attributes(self):
        attrs = list(super(OfficeDocument, self).attributes)
        attrs.extend(["nb_pages", "format"])
        return attrs

class OfficeDocumentController(DocumentController):

    def handle_added_file(self, doc_file):
        if os.path.splitext(doc_file.file.path)[1].lower() == ".odt":
            try:
                doc = load(doc_file.file.path)
                stat = doc.getElementsByType(DocumentStatistic)[0]
                page = doc.getElementsByType(PageLayoutProperties)[0]
                self.nb_pages = int(stat.attributes["meta:page-count"])
                w = page.attribute['fo:page-width']
                h = page.attribute['fo:page-height']
                self.format = size_to_format(w, h)
            except Exception:
                # load may raise several exceptions...
                pass
        self.save()

register(OfficeDocument)

