import openPLM.plmapp.views as pviews


def attributes(request, obj_ref, obj_revi):
    """ Manage html page for attributes """
    obj_type = "Bicycle"
    obj, ctx = pviews.get_generic_data(request, obj_type, obj_ref, obj_revi)
    object_attributes = []
    for attr in obj.attributes:
        item = obj.get_verbose_name(attr) + ":" # <- this is our small modification
        object_attributes.append((item, getattr(obj, attr)))
    ctx.update({'current_page':'attributes', 
                'object_attributes': object_attributes})
    return pviews.r2r('attributes.html', ctx, request)

