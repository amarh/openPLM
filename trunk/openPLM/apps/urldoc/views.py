
from openPLM.plmapp.views.base import get_generic_data, handle_errors
from openPLM.plmapp.utils import r2r

@handle_errors
def display_URLDoc(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    ctx.update({'current_page':'content', 
               })
    return r2r('content.html', ctx, request)
