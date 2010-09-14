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

