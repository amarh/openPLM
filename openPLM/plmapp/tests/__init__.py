from openPLM.plmapp.tests.filehandlers import *
from openPLM.plmapp.tests.controllers import *
from openPLM.plmapp.tests.lifecycle import *
from openPLM.plmapp.tests.views import *
#from openPLM.plmapp.tests.closure import *

def get_doctest(module_name):
    test_dict={}
    module = __import__(module_name,{},{},module_name.split('.')[-1])
    for obj_name,obj in module.__dict__.items():
        if '__module__' in dir(obj) and obj.__module__ == module_name:
            if obj.__doc__:
                test_dict[obj_name] = obj.__doc__
                return test_dict

__test__ = get_doctest("plmapp.utils")
__test__.update(get_doctest("plmapp.controllers"))
__test__.update(get_doctest("plmapp.lifecycle"))

