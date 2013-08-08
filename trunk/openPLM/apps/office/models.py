############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
#
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

import os

from django.db import models
from django.contrib import admin

from django.utils.translation import ugettext_lazy as _

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

    nb_pages = models.PositiveIntegerField(_("Number of pages"), blank=True, null=True)
    format = models.CharField(verbose_name=_("format"), max_length=10, choices=CFORMATS, default=lambda: "A4")

    @property
    def attributes(self):
        attrs = list(super(OfficeDocument, self).attributes)
        attrs.extend(["nb_pages", "format"])
        return attrs

    @classmethod
    def excluded_creation_fields(cls):
        return Document.excluded_creation_fields() + ["nb_pages", "format"]


    @classmethod
    def get_creation_score(cls, files):
        office_ext = (".odt", ".ods", ".odp", ".doc", ".xls", ".ppt", ".docx", ".xlsx", ".pptx")
        if any(f.filename.lower().endswith(office_ext) for f in files):
            return 40
        return super(OfficeDocument, cls).get_creation_score(files)


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

