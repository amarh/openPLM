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
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

from django.shortcuts import render_to_response
from django.template import RequestContext

import openPLM.plmapp.views as pviews


def freecad(request, obj_ref, obj_revi):
    """ Manage html page for attributes """
    obj_type = "FreeCAD"
    obj, ctx = pviews.get_generic_data(request, obj_type, obj_ref, obj_revi)
    object_attributes_list = []
    for attr in obj.attributes:
        item = obj.get_verbose_name(attr) + ":"
        object_attributes_list.append((item, getattr(obj, attr)))
    ctx.update({'current_page':'attributes', 
        'object_attributes': object_attributes_list})
    return render_to_response('DisplayObject.htm', ctx,
                              context_instance=RequestContext(request))

