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
This module contains test for filehandlers stuff.
"""

import os.path
from django.test import TestCase

from openPLM.plmapp.filehandlers import HandlersManager, ODFHandler

class FileHandlerTest(TestCase):
    FILE_TYPE = ".odt"
    FILE = "datatests/office_a4_3p.odt"
    
    def test_get_handler(self):
        handler = HandlersManager.get_best_handler(".odt")
        self.assertEquals(handler, ODFHandler)
    
    def test_get_handler_error(self):
        self.assertRaises(KeyError, HandlersManager.get_best_handler, ".___")
    
    def test_get_all_handler(self):
        handlers = HandlersManager.get_all_handlers(".odt")
        self.assertEquals(handlers, [ODFHandler])
    
    def test_parse(self):
        handler = HandlersManager.get_best_handler(".odt")
        myfile = handler(self.FILE, os.path.basename(self.FILE))
        self.assertTrue(myfile.is_valid())
        self.assertEquals(tuple(myfile.attributes), ("nb_pages", "format"))
        self.assertEqual("A4", myfile.format)
        self.assertEqual(3, myfile.nb_pages)

    def test_get_all_supported_types(self):
        handlers = sorted(HandlersManager.get_all_supported_types())
        self.assertEquals(handlers, [".odt", ".pdf"])

