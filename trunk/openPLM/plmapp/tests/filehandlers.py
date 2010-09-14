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
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Ce fichier fait parti d' openPLM.
#
#    Ce programme est un logiciel libre ; vous pouvez le redistribuer ou le
#    modifier suivant les termes de la “GNU General Public License” telle que
#    publiée par la Free Software Foundation : soit la version 3 de cette
#    licence, soit (à votre gré) toute version ultérieure.
#
#    Ce programme est distribué dans l’espoir qu’il vous sera utile, mais SANS
#    AUCUNE GARANTIE : sans même la garantie implicite de COMMERCIALISABILITÉ
#    ni d’ADÉQUATION À UN OBJECTIF PARTICULIER. Consultez la Licence Générale
#    Publique GNU pour plus de détails.
#
#    Vous devriez avoir reçu une copie de la Licence Générale Publique GNU avec
#    ce programme ; si ce n’est pas le cas, consultez :
#    <http://www.gnu.org/licenses/>.
#    
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

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

