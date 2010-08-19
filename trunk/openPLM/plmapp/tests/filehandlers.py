"""
This module contains test for filehandlers stuff.
"""

import os.path
from django.test import TestCase

from openPLM.plmapp.filehandlers import *

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
        self.failUnless(myfile.is_valid())
        self.assertEquals(tuple(myfile.attributes), ("nb_pages", "format"))
        self.assertEqual("A4", myfile.format)
        self.assertEqual(3, myfile.nb_pages)

    def test_get_all_supported_types(self):
        handlers = sorted(HandlersManager.get_all_supported_types())
        self.assertEquals(handlers, [".odt", ".pdf"])

