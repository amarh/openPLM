import traceback
import sys

from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson
from django.core.mail import mail_admins
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, QueryDict, HttpResponse

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController, get_controller, DocumentController
import openPLM.plmapp.forms as forms
from openPLM.plmapp.utils import get_next_revision


def json_view(func):
    def wrap(request, *a, **kw):
        response = None
        try:
            response = dict(func(request, *a, **kw))
            if 'result' not in response:
                response['result'] = 'ok'
        except KeyboardInterrupt:
            # Allow keyboard interrupts through for debugging.
            raise
        except Exception, e:
            print e
            #Mail the admins with the error
            exc_info = sys.exc_info()
            subject = 'JSON view error: %s' % request.path
            try:
                request_repr = repr(request)
            except:
                request_repr = 'Request repr() unavailable'
            message = 'Traceback:\n%s\n\nRequest:\n%s' % (
                '\n'.join(traceback.format_exception(*exc_info)),
                request_repr,
                )
            mail_admins(subject, message, fail_silently=True)

            #Come what may, we're returning JSON.
            msg = _('Internal error')+': '+str(e)
            response = {'result': 'error',
                        'text': msg}

        json = simplejson.dumps(response)
        return HttpResponse(json, mimetype='application/json')
    return wrap

def replace_white_spaces(Chain):
    """ Replace all whitespace characteres by %20 in order to be compatible with an URL"""
    return Chain.replace(" ","%20")


def get_obj(object_type_value, object_reference_value, object_revision_value):
    """ Get Type, Reference and Revision and return an object """
    obj = get_object_or_404(models.PLMObject, type=object_type_value,
                            reference=object_reference_value,
                            revision=object_revision_value)
    # guess what kind of PLMObject (Part, Document) obj is
    cls = models.PLMObject
    find = True
    while find:
        find = False
        for c in cls.__subclasses__():
            if hasattr(obj, c.__name__.lower()):
                cls  = c
                obj = getattr(obj, c.__name__.lower())
                find = True
    user = models.User.objects.all()[0]
    controller_cls = get_controller(object_type_value)
    return controller_cls(obj, user)

def get_obj_by_id(obj_id, user):
    obj = models.PLMObject.objects.get(id=obj_id)
    obj = models.get_all_plmobjects()[obj.type].objects.get(id=obj_id)
    return get_controller(obj.type)(obj, user)

@login_required
@json_view
def get_all_types(request):
    return {"types" : sorted(models.get_all_plmobjects().keys())}

@login_required
@json_view
def get_all_docs(request):
    return {"types" : sorted(models.get_all_documents().keys())}


@login_required
@json_view
def search(request):
        
    if request.GET and "type" in request.GET:
        attributes_form = forms.attributes_form(request.GET)
        if attributes_form.is_valid():
            query_dict = {}
            cls = models.get_all_plmobjects()[attributes_form.cleaned_data["type"]]
            extra_attributes_form = forms.get_search_form(cls, request.GET)
            for field, value in attributes_form.cleaned_data.items():
                if value and field != "type":
                    query_dict["%s__icontains"%field]=value
            results = cls.objects.filter(**query_dict)
            if extra_attributes_form.is_valid():
                results = extra_attributes_form.search(results)
                objects = []
                for res in results:
                    objects.append(dict(id=res.id, name=res.name, type=res.type,
                                revision=res.revision, reference=res.reference))
                return {"objects" : objects} 
    return {"result": "error"}

@login_required
@json_view
def get_files(request, doc_id):
    document = models.Document.objects.get(id=doc_id)
    document = models.get_all_plmobjects()[document.type].objects.get(id=doc_id)
    files = []
    for df in document.files:
        files.append(dict(id=df.id, filename=df.filename, size=df.size,
                         url=df.path.url))
    return {"files" : files}

@login_required
@json_view
def check_out(request, doc_id, df_id):
    doc = get_obj_by_id(doc_id, request.user)
    df = models.DocumentFile.objects.get(id=df_id)
    doc.lock(df)
    return {}
