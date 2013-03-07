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

Replace these with more appropriate tests for your application.

"""

from openPLM.apps.computer.models import SinglePartController
from openPLM.plmapp.tests.views import ViewTest
from openPLM.plmapp.tests.controllers.part import PartControllerTest

class HardDiskViewTest(ViewTest):
    TYPE = "HardDisk"
    DATA = {"capacity_in_go" : 500,
            "supplier" : "ASupplier"}

    def test_display_attributes2(self):
        response = self.get(self.base_url + "attributes/")
        self.assertTrue(response.context["object_attributes"])
        attributes = dict((x.lower(), y) for (x,y, _) in
                          response.context["object_attributes"])
        self.assertEqual(attributes["capacity in go"], self.DATA["capacity_in_go"])
        self.assertEqual(attributes["supplier"], self.DATA["supplier"])
        self.assertEqual(attributes["tech details"], "")

class HardDiskControllerTest(PartControllerTest):
    TYPE = "HardDisk"
    CONTROLLER = SinglePartController
    DATA = {"capacity_in_go" : 500}

    def test_create_reference(self):
        c = self.CONTROLLER.create("PART_00256", self.TYPE, "a", self.user, self.DATA)
        self.assertEqual(256, c.reference_number)


