import os
import string
import random
import glob

from django.utils.encoding import iri_to_uri
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

from openPLM.opOp import models
from openPLM.plmapp.base_views import init_ctx, get_obj, get_obj_by_id, handle_errors, get_generic_data
import openPLM.plmapp.forms as forms
from openPLM.plmapp.views.main import r2r

def rand():
    r = ""
    for i in xrange(7):
        r += random.choice(string.ascii_lowercase + string.digits)
    return r


def get_content_url(url,doc_id, dest_dir = "/tmp"):
    dir_name = dest_dir+"/"+str(doc_id)
    if os.path.exists(dir_name):
        dir_name = dir_name+"_"+rand()
    cmd_gt = "httrack -g "+url+" -%O "+dir_name
    os.system(cmd_gt)
    return dir_name
    
def get_doc_from_url(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if request.method == "GET" :
        pass
    return HttpResponseRedirect(obj.plmobject_url+"documentation/")


def display_URLDoc(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    ctx.update({'current_page':'content', 
               })
    return r2r('content.html', ctx, request)
