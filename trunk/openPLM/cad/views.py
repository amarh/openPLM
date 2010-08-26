from django.shortcuts import render_to_response
from django.template import RequestContext

import openPLM.plmapp.views as pviews


def freecad(request, obj_ref, obj_revi):
    """ Manage html page for attributes """
    obj_type = "FreeCAD"
    obj, context_dict, request_dict = pviews.display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    object_attributes_list = []
    for attr in obj.attributes:
        item = obj.get_verbose_name(attr) + ":"
        object_attributes_list.append((item, getattr(obj, attr)))
    context_dict.update({'current_page':'attributes', 'object_menu': menu_list, 'object_attributes': object_attributes_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObject.htm', context_dict,
                              context_instance=RequestContext(request))

