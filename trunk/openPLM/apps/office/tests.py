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

"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

"""

from django.core.files.base import File

from openPLM.apps.office.models import OfficeDocumentController
from openPLM.plmapp.tests.controllers.document import DocumentControllerTest


class OfficeTest(DocumentControllerTest):
    TYPE = "OfficeDocument"
    CONTROLLER = OfficeDocumentController
    DATA = {}

    def test_add_odt(self):
        # format a4, 3 pages
        f = file("datatests/office_a4_3p.odt", "rb")
        my_file = File(f)
        self.controller.add_file(my_file)
        self.assertEquals(self.controller.nb_pages, 3)
        self.assertEquals(self.controller.format, "A4")
        f2 = self.controller.files.all()[0]
        self.assertTrue(f2.file.path.endswith(".odt"))
        self.controller.delete_file(f2)

    def test_add_odt2(self):
        # fake odt
        # No exceptions should be raised
        self.controller.add_file(self.get_file("plop.odt"))
        f2 = self.controller.files.all()[0]
        self.controller.delete_file(f2)

    def test_add_odt3(self):
        # do not update fields
        f = file("datatests/office_a4_3p.odt", "rb")
        my_file = File(f)
        self.controller.add_file(my_file, False)
        self.assertEquals(self.controller.nb_pages, None)
        f2 = self.controller.files.all()[0]
        self.controller.delete_file(f2)


