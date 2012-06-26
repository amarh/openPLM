
from openPLM.plmapp.base_views import get_generic_data
from openPLM.plmapp.views.main import r2r

def display_URLDoc(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    ctx.update({'current_page':'content', 
               })
    return r2r('content.html', ctx, request)
