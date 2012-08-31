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

class Design(Document):

    pass

register(Design)

class Drawing(Design):
    
    nb_pages = models.PositiveIntegerField(_("Number of pages"), blank=True, null=True)
    format = models.CharField(verbose_name=_("format"), max_length=10, choices=CFORMATS, default=lambda: "A4")

    @property
    def attributes(self):
        attrs = list(super(Drawing, self).attributes)
        attrs.extend(["nb_pages", "format"])
        return attrs

class DrawingController(DocumentController):

    def handle_added_file(self, doc_file):
        ext = os.path.splitext(doc_file.file.path)[1].lower() 
        if os.path.splitext(doc_file.file.path)[1].lower() == ".pdf":
            handler_cls = HandlersManager.get_best_handler(".pdf")
            handler = handler_cls(doc_file.file.path, doc_file.filename)
            if handler.is_valid():
                self.nb_pages = handler.nb_pages
                self.name = handler.title
        self.save()

register(Drawing)

class CustomerDrawing(Drawing):

    customer = models.CharField(verbose_name=_("customer"), max_length=50, blank=True)
    
    @property
    def attributes(self):
        attrs = list(super(CustomerDrawing, self).attributes)
        attrs.extend(["customer"])
        return attrs

register(CustomerDrawing)

class SupplierDrawing(Drawing):

    supplier = models.CharField(verbose_name=_("supplier"), max_length=50, blank=True)
    
    @property
    def attributes(self):
        attrs = list(super(SupplierDrawing, self).attributes)
        attrs.extend(["supplier"])
        return attrs

register(SupplierDrawing)


class FMEA(Design):

    pass

register(FMEA)


class Sketch(Design):

    pass

register(Sketch)


class FreeCAD(Design):
    pass

register(FreeCAD)


class Patent(Design):

    expiration_date = models.DateField(verbose_name=_("expiration date"), null=True, blank=True)
    inventor = models.CharField(verbose_name=_("inventor"), max_length=50, blank=True)

register(Patent)

