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

# import custom application models
from django.conf import settings
for app in settings.INSTALLED_APPS:
    if app.startswith("openPLM") and app != 'openPLM.apps.pdfgen':
        __import__("%s.models" % app, globals(), locals(), [], -1)

import openPLM.plmapp.search_indexes

from openPLM.plmapp.tests.filehandlers import *
from openPLM.plmapp.tests.controllers import *
from openPLM.plmapp.tests.lifecycle import *
from openPLM.plmapp.tests.views import *
from openPLM.plmapp.tests.ajax import *
from openPLM.plmapp.tests.api import *
from openPLM.plmapp.tests.csvimport import *
from openPLM.plmapp.tests.archive import *
from openPLM.plmapp.tests.pcle import *
from openPLM.plmapp.tests.gestion_document_native import *
from openPLM.plmapp.tests.navigate import *
from openPLM.plmapp.tests.reference import *
from openPLM.plmapp.tests.restricted import *
from openPLM.plmapp.tests.filters import *

import openPLM.plmapp.models
from openPLM.plmapp.lifecycle import LifecycleList
def get_doctest(module_name):
    test_dict={}
    module = __import__(module_name,{},{},module_name.split('.')[-1])
    for obj_name,obj in module.__dict__.items():
        if '__module__' in dir(obj) and obj.__module__ == module_name:
            if obj.__doc__:
                test_dict[obj_name] = obj
                return test_dict

__test__ = get_doctest("openPLM.plmapp.utils")
__test__.update(get_doctest("openPLM.plmapp.controllers.plmobject"))
__test__.update(get_doctest("openPLM.plmapp.lifecycle"))

