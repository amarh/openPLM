from django.shortcuts import render_to_response, get_object_or_404
import plmapp.views as pviews


def freecad(request, type_value, reference_value, revision_value):
    """ Manage html page for attributes """
    obj = pviews.get_obj(type_value, reference_value, revision_value, request.user)
    class_for_div="NavigateBox4Doc"
    menu_list = obj.menu_items
    attributes_list = []
    for attr in obj.attributes:
        item = obj._meta.get_field(attr).verbose_name
        attributes_list.append((item, getattr(obj, attr)))
    context_dict = pviews.init_context_dict(type_value, reference_value, revision_value)
    context_dict.update({'current_page':'freecad', 'class4div': class_for_div, 'object_menu': menu_list, 'object_attributes': attributes_list})
    var_dict, request_dict = pviews.display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObject.htm', context_dict)

