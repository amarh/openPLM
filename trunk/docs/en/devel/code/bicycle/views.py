from openPLM.plmapp.base_views import get_generic_data
from openPLM.plmapp.utils import r2r


def attributes(request, obj_ref, obj_revi):
    """Custom attributes page """
    obj_type = "Bicycle"
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    object_attributes = []
    for attr in obj.attributes:
        item = obj.get_verbose_name(attr) + ":" # <- this is our small modification
        object_attributes.append((item, getattr(obj, attr)))
    ctx.update({'current_page':'attributes',
                'object_attributes': object_attributes})
    return r2r('attributes.html', ctx, request)

