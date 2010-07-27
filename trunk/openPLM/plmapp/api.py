import traceback
import sys

from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson
from django.core.mail import mail_admins
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, QueryDict, HttpResponse
import django.forms

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController, get_controller, DocumentController
import openPLM.plmapp.forms as forms
from openPLM.plmapp.utils import get_next_revision

API_VERSION = "1.0"
api_login_required = user_passes_test(lambda u: u.is_authenticated(), 
                                      login_url="/api/needlogin/")

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
                        'error': msg}
        response["api_version"] = API_VERSION
        json = simplejson.dumps(response)
        return HttpResponse(json, mimetype='application/json')
    return wrap


login_json = lambda f: api_login_required(json_view(f))


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

@json_view
def need_login(request):
    return {'result' : 'error', 'error' : 'user must be login'}

@login_json
def get_all_types(request):
    return {"types" : sorted(models.get_all_plmobjects().keys())}

@login_json
def get_all_docs(request):
    return {"types" : sorted(models.get_all_documents().keys())}

@login_json
def get_all_parts(request):
    return {"types" : sorted(models.get_all_parts().keys())}

@login_json
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

@login_json
def get_files(request, doc_id, all_files=False):
    document = models.Document.objects.get(id=doc_id)
    document = models.get_all_plmobjects()[document.type].objects.get(id=doc_id)
    files = []
    for df in document.files:
        if all_files or not df.locked:
            files.append(dict(id=df.id, filename=df.filename, size=df.size))
    return {"files" : files}

@login_json
def check_out(request, doc_id, df_id):
    doc = get_obj_by_id(doc_id, request.user)
    df = models.DocumentFile.objects.get(id=df_id)
    doc.lock(df)
    return {}


@login_json
def check_in(request, doc_id, df_id):
    doc = get_obj_by_id(doc_id, request.user)
    df = models.DocumentFile.objects.get(id=df_id)
    form = forms.AddFileForm(request.POST, request.FILES)
    if form.is_valid():
        doc.checkin(df, request.FILES['filename'])
    return {}

@login_json
def is_locked(request, doc_id, df_id):
    doc = get_obj_by_id(doc_id, request.user)
    df = models.DocumentFile.objects.get(id=df_id)
    return {"locked" : df.locked}

@login_json
def unlock(request, doc_id, df_id):
    doc = get_obj_by_id(doc_id, request.user)
    df = models.DocumentFile.objects.get(id=df_id)
    if df.locked:
        doc.unlock(df)
    return {}

def field_to_type(field):
    types = {django.forms.IntegerField : "int",
             django.forms.DecimalField : "decimal",
             django.forms.FloatField : "float",
             django.forms.BooleanField : "boolean",
             django.forms.ChoiceField : "choice",
           }
    if type(field) in types:
        return types[type(field)]
    for key in types:
        if isinstance(field, key):
            return types[key]
    return "text"

def get_fields_from_form(form):
    fields = []
    for field_name, field in form.fields.iteritems():
        data = dict(name=field_name, label=field.label, initial=field.initial)
        if callable(field.initial):
            data["initial"] = field.initial()
            if hasattr(data["initial"], "pk"):
                data["initial"] = data["initial"].pk
        data["type"] = field_to_type(field)
        if hasattr(field, "choices"):
            data["choices"] =  tuple(field.choices)
        for attr in ("min_value", "max_value", "min_length", "max_length"):
            if hasattr(field, attr):
                data[attr] = getattr(field, attr)
        fields.append(data)
    return fields

@login_json
def get_advanced_search_fields(request, typename):
    try:
        form = forms.get_search_form(models.get_all_plmobjects()[typename])
    except KeyError:
        return {"result" : "error", "fields" : []}
    return {"fields" : get_fields_from_form(form)}

@login_json
def get_creation_fields(request, typename):
    try:
        form = forms.get_creation_form(models.get_all_plmobjects()[typename])
    except KeyError:
        return {"result" : "error", "fields" : []}
    return {"fields" : get_fields_from_form(form)}

@json_view
def api_login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return {"username" : username, "first_name" : user.first_name,
                    "last_name" : user.last_name}
        else:
            return {"result" : 'error', 'error' : 'user is inactive'}
    else:
        return {"result" : 'error', 'error' : 'login invalid'}


@login_json
def test_login(request):
    # do nothing, if user is authenticated, json_view sets *result* to 'ok'
    return {}

@login_json
def next_revision(request, doc_id):
    doc = get_obj_by_id(doc_id, request.user)
    return {"revision" : get_next_revision(doc.revision)}

@login_json
def revise(request, doc_id):
    doc = get_obj_by_id(doc_id, request.user)
    form = forms.AddRevisionForm(request.POST)
    if form.is_valid():
        rev = doc.revise(form.cleaned_data["revision"])
        ret = {"doc" : dict(id=rev.id, name=rev.name, type=rev.type,
                            revision=rev.revision, reference=rev.reference)}
        files = []
        for df in rev.files:
            files.append(dict(id=df.id, filename=df.filename, size=df.size))
        ret["files"] = files
        return ret
    else:
        return {"result" : 'error'}

@login_json
def is_revisable(request, doc_id):
    doc = get_obj_by_id(doc_id, request.user)
    return {"revisable" : doc.is_revisable()}


@login_json
def attach_to_part(request, doc_id, part_id):
    doc = get_obj_by_id(doc_id, request.user)
    part = get_obj_by_id(part_id, request.user)
    doc.attach_to_part(part)
    return {}

@login_json
def create(request):
    try:
        type_name = request.POST["type"]
        cls = models.get_all_plmobjects()[type_name]
    except KeyError:
        return {"result" : "error", 'error' : 'bad type'}
    form = forms.get_creation_form(cls, request.POST)
    if form.is_valid():
        controller_cls = get_controller(type_name)
        controller = controller_cls.create_from_form(form, request.user)
        ret = {"object" : dict(id=controller.id, name=controller.name,
                               type=controller.type, revision=controller.revision,
                               reference=controller.reference)}
        return ret
    else:
        return {"result" : "error", "error" : form.errors.as_text()}

@login_json
def add_file(request, doc_id):
    doc = get_obj_by_id(doc_id, request.user)
    add_file_form_instance = forms.AddFileForm(request.POST, request.FILES)
    df = doc.add_file(request.FILES["filename"])
    return {"doc_file" : dict(id=df.id, filename=df.filename, size=df.size)}


@login_json
def add_thumbnail(request, doc_id, df_id):
    doc = get_obj_by_id(doc_id, request.user)
    add_file_form_instance = forms.AddFileForm(request.POST, request.FILES)
    df = models.DocumentFile.objects.get(id=df_id)
    doc.add_thumbnail(df, request.FILES["filename"])
    return {}

