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
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

"""
This modules contains all stuff related to the api

.. seealso:: The public api :mod:`http_api`,
"""
import json
import functools

import django.forms
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import get_controller, DocumentController
import openPLM.plmapp.forms as forms
from openPLM.plmapp.utils import get_next_revision
from openPLM.plmapp.views.base import json_view, get_obj_by_id, object_to_dict,\
        secure_required

#: Version of the API (value: ``'1.1'``)
API_VERSION = "1.1"
#: Decorator whichs requires that the user is login
api_login_required = user_passes_test(lambda u: (u.is_authenticated()
    and u.is_active and not u.profile.restricted), login_url="/api/needlogin/")

@json_view
def need_login(request):
    """ Helper function for :func:`api_login_required` """
    return {'result' : 'error', 'error' : 'user must be login'}

def login_json(func):
    """
    Decorator which requires a login user and converts returned value into
    a json response.

    This also checks if the user agent is ``"openplm"`` and, if not,
    returns a 403 HTTP RESPONSE.
    """

    json_func = json_view(func, API_VERSION)
    @functools.wraps(func)
    @csrf_exempt
    @secure_required
    @api_login_required
    def wrapper(request, *args, **kwargs):
        if request.META["HTTP_USER_AGENT"] != "openplm":
            return HttpResponseForbidden()
        if request.user.profile.restricted:
            return HttpResponseForbidden()
        return json_func(request, *args, **kwargs)
    return wrapper


@login_json
def get_all_types(request):
    """
    Returns all the subtypes of :class:`.PLMObject` managed by the server.

    :implements: :func:`http_api.types`
    """
    return {"types" : sorted(models.get_all_plmobjects().keys())}

@login_json
def get_all_docs(request):
    """
    Returns all  the types of :class:`.Document` managed by the server.

    :implements: :func:`http_api.docs`
    """
    return {"types" : sorted(models.get_all_documents().keys())}

@login_json
def get_all_parts(request):
    """
    Returns all the types of :class:`.Part` managed by the server.

    :implements: :func:`http_api.parts`
    """
    return {"types" : sorted(models.get_all_parts().keys())}

@login_json
def search(request, editable_only="true", with_file_only="true"):
    """
    Returns all objects matching a query.

    :param editable_only: if ``"true"`` (the default), returns only editable objects
    :param with_file_only: if ``"true"`` (the default), returns only documents with
                           at least one file

    :implements: :func:`http_api.search`
    """
    if request.GET and "type" in request.GET:
        form = forms.SimpleSearchForm(request.GET)
        if form.is_valid():
            # object may have been deleted but not yet unindexed
            results = [r.object for r in form.search().load_all()[:30] if r is not None]
            objects = []
            ids = set()
            for res in results:
                if isinstance(res, models.DocumentFile):
                    res = res.document.get_leaf_object()
                if res.id in ids: # avoiding duplicated results
                    continue
                if editable_only == "false" or res.is_editable:
                    if with_file_only == "true" and hasattr(res, "files") \
                       and not bool(res.files):
                        continue
                    if editable_only == "true":
                        obj = DocumentController(res, request.user)
                        if not obj.check_in_group(request.user, False):
                            continue
                    ids.add(res.id)
                    objects.append(object_to_dict(res))
            return {"objects" : objects}
    return {"result": "error"}

@login_json
def create(request):
    """
    Creates a :class:`.PLMObject` and returns it

    :implements: :func:`http_api.create`
    """
    try:
        type_name = request.POST["type"]
        cls = models.get_all_plmobjects()[type_name]
    except KeyError:
        return {"result" : "error", 'error' : 'bad type'}
    form = forms.get_creation_form(request.user, cls, request.POST)
    if form.is_valid():
        controller_cls = get_controller(type_name)
        controller = controller_cls.create_from_form(form, request.user)
        ret = {"object" : object_to_dict(controller)}
        return ret
    else:
        return {"result" : "error", "error" : form.errors.as_text()}

@login_json
def get_files(request, doc_id, all_files=False):
    """
    Returns the list of files of the :class:`.Document` identified by *doc_id*.
    If *all_files* is False (the default), only unlocked files are returned.

    :implements: :func:`http_api.files`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :param all_files: boolean, False if only unlocked files should be returned
    :returned fields: files, a list of files (see :ref:`http-api-file`)
    """

    document = models.Document.objects.get(id=doc_id)
    document = models.get_all_plmobjects()[document.type].objects.get(id=doc_id)
    files = []
    for df in document.files:
        if all_files or not df.locked:
            files.append(dict(id=df.id, filename=df.filename, size=df.size))
    return {"files" : files}

@login_json
def check_out(request, doc_id, df_id):
    """
    Locks the :class:`.DocumentFile` identified by *df_id* from
    the :class:`.Document` identified by *doc_id*.

    :implements: :func:`http_api.lock`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :param df_id: id of a :class:`.DocumentFile`
    :returned fields: None
    """
    doc = get_obj_by_id(doc_id, request.user)
    df = models.DocumentFile.objects.get(id=df_id)
    doc.lock(df)
    return {}


@login_json
def check_in(request, doc_id, df_id, thumbnail=False):
    """
    Checks-in the :class:`.DocumentFile` identified by *df_id* from
    the :class:`.Document` identified by *doc_id*

    :implements: :func:`http_api.check_in`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :param df_id: id of a :class:`.DocumentFile`
    :returned fields: None
    """
    doc = get_obj_by_id(doc_id, request.user)
    df = models.DocumentFile.objects.get(id=df_id)
    form = forms.AddFileForm(request.POST, request.FILES)
    if form.is_valid():
        doc.checkin(df, request.FILES['filename'], thumbnail=thumbnail)
    return {}

@login_json
def is_locked(request, doc_id, df_id):
    """
    Returns True if the :class:`.DocumentFile` identified by *df_id* from
    the :class:`.Document` identified by *doc_id* is locked.

    :implements: :func:`http_api.is_locked`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :param df_id: id of a :class:`.DocumentFile`
    :returned fields: locked, True if the file is locked.
    """

    doc = get_obj_by_id(doc_id, request.user)
    df = models.DocumentFile.objects.get(id=df_id)
    return {"locked" : df.locked}

@login_json
def unlock(request, doc_id, df_id):
    """
    Unlocks the :class:`.DocumentFile` identified by *df_id* from
    the :class:`.Document` identified by *doc_id*.

    :implements: :func:`http_api.unlock`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :param df_id: id of a :class:`.DocumentFile`
    :returned fields: None
    """
    doc = get_obj_by_id(doc_id, request.user)
    df = models.DocumentFile.objects.get(id=df_id)
    if df.locked:
        doc.unlock(df)
    return {}

def field_to_type(field):
    """
    Converts *field* (a django FormField) to a type as described in
    :ref:`http-api-types`.
    """
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
    """
    Returns a list of fields from *form* converted to the format described in
    :ref:`http-api-fields`.
    """
    fields = []
    for field_name, field in form.fields.items():
        if field_name == "pfiles":
            continue
        initial = form.initial.get(field_name, field.initial)
        if callable(initial):
            initial = initial()
        if hasattr(initial, "pk"):
            initial = initial.pk
        data = dict(name=field_name,
                    label=(field.label or field_name).capitalize(),
                    initial=initial,
               )
        data["type"] = field_to_type(field)
        if hasattr(field, "choices"):
            data["choices"] =  tuple(field.choices)
        for attr in ("min_value", "max_value", "min_length", "max_length"):
            if hasattr(field, attr):
                data[attr] = getattr(field, attr)
        fields.append(data)
    return fields

@login_json
def get_search_fields(request, typename):
    """
    Returns search fields associated to *typename*.

    :implements: :func:`http_api.search_fields`
    """
    form = forms.SimpleSearchForm()
    return {"fields" : get_fields_from_form(form)[1:]}

@login_json
def get_creation_fields(request, typename):
    """
    Returns creation fields associated to *typename*

    :implements: :func:`http_api.creation_fields`
    """
    try:
        form = forms.get_creation_form(request.user,
                models.get_all_plmobjects()[typename])
    except KeyError:
        return {"result" : "error", "fields" : []}
    return {"fields" : get_fields_from_form(form)}

@csrf_exempt
@secure_required
@json_view
def api_login(request):
    """
    Authenticates the user

    :implements: :func:`http_api.login`
    """
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active and not user.profile.restricted:
            login(request, user)
            return {"username" : username, "first_name" : user.first_name,
                    "last_name" : user.last_name}
        else:
            return {"result" : 'error', 'error' : 'user is inactive'}
    else:
        return {"result" : 'error', 'error' : 'login invalid'}


@login_json
def test_login(request):
    """
    Tests if user is authenticated

    :implement: :func:`http_api.testlogin`
    """
    # do nothing, if user is authenticated, json_view sets *result* to 'ok'
    return {}

@login_json
def next_revision(request, doc_id):
    """
    Returns a possible new revision for the :class:`.Document` identified by
    *doc_id*.

    :implements: :func:`http_api.next_revision`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :returned fields: revision, the new revision (may be an empty string)

    .. seealso:: :func:`.utils.get_next_revision` for possible results
    """

    doc = get_obj_by_id(doc_id, request.user)
    return {"revision" : get_next_revision(doc.revision)}

@login_json
def revise(request, doc_id):
    """
    Makes a new revision of the :class:`.Document` identified by *doc_id*.

    :implements: :func:`http_api.revise`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :returned fields:
        * doc, the new document (see :ref:`http-api-object`)
        * files, a list of files (see :ref:`http-api-file`)
    """

    doc = get_obj_by_id(doc_id, request.user)
    form = forms.AddRevisionForm(doc, request.user, request.POST)
    if form.is_valid():
        rev = doc.revise(form.cleaned_data["revision"], group=form.cleaned_data["group"])
        ret = {"doc" : object_to_dict(rev)}
        files = []
        for df in rev.files:
            files.append(dict(id=df.id, filename=df.filename, size=df.size))
        ret["files"] = files
        return ret
    else:
        return {"result" : 'error'}

@login_json
def is_revisable(request, doc_id):
    """
    Returns True if the :class:`.Document` identified by *doc_id* can be revised.

    :implements: :func:`http_api.is_revisable`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :returned fields: revisable, True if it can be revised
    """

    doc = get_obj_by_id(doc_id, request.user)
    return {"revisable" : doc.is_revisable()}


@login_json
def attach_to_part(request, doc_id, part_id):
    """
    Links the :class:`.Document` identified by *doc_id* with the :class:`.Part`
    identified by *part_id*.

    :implements: :func:`http_api.attach_to_part`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :param part_id: id of a :class:`.Part`
    :returned fields: None
    """
    doc = get_obj_by_id(doc_id, request.user)
    part = get_obj_by_id(part_id, request.user)
    doc.attach_to_part(part)
    return {}


@login_json
def add_file(request, doc_id, thumbnail=False):
    """
    Adds a file to the :class:`.Document` identified by *doc_id*.

    :implements: :func:`http_api.add_file`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :returned fields: doc_file, the file that has been had,
                      see :ref:`http-api-file`.
    """
    doc = get_obj_by_id(doc_id, request.user)
    form = forms.AddFileForm(request.POST, request.FILES)
    df = doc.add_file(request.FILES["filename"], thumbnail=thumbnail)
    return {"doc_file" : dict(id=df.id, filename=df.filename, size=df.size)}


@login_json
def add_thumbnail(request, doc_id, df_id):
    """
    Adds a thumbnail to the :class:`.DocumentFile` identified by *df_id* from
    the :class:`.Document` identified by *doc_id*.

    :implements: :func:`http_api.add_thumbnail`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :param df_id: id of a :class:`.DocumentFile`
    :returned fields: None
    """

    doc = get_obj_by_id(doc_id, request.user)
    form = forms.AddFileForm(request.POST, request.FILES)
    df = models.DocumentFile.objects.get(id=df_id)
    doc.add_thumbnail(df, request.FILES["filename"])
    return {}


@login_json
def get_object(request, obj_id):
    """
    .. versionadded:: 2.0

    Returns basic fields of the :class:`.PLMObject` identified by *obj_id*.

    :implements: :func:`http_api.get`

    :param request: the request
    :param obj_id: id of a :class:`.PLMObject`
    :returned fields: object, a dictionary of object fields
    """
    obj = get_obj_by_id(obj_id, request.user)
    obj.check_readable()
    return {"object": object_to_dict(obj)}


@login_json
def get_attached_parts(request, doc_id):
    """
    .. versionadded:: 2.0

    Returns parts attached to the :class:`.Document` identified by *doc_id*.

    :implements: :func:`http_api.attached_parts`

    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :returned fields: parts, a list of dictionaries describing attached parts
    """

    doc = get_obj_by_id(doc_id, request.user)
    doc.check_readable()
    parts = []
    for link in doc.get_attached_parts():
        parts.append(object_to_dict(link.part))
    return {"parts": parts}


@login_json
def get_attached_documents(request, part_id):
    """
    .. versionadded:: 2.0

    Returns documents attached to the :class:`.Part` identified by *part_id*.

    :implements: :func:`http_api.attached_documents`

    :param request: the request
    :param part_id: id of a :class:`.Part`
    :returned fields: documents, a list of dictionaries describing attached documents
    """
    part = get_obj_by_id(part_id, request.user)
    part.check_readable()
    docs = []
    for link in part.get_attached_documents():
        docs.append(object_to_dict(link.document))
    return {"documents": docs}


@login_json
def lock_files(request):
    """
    .. versionadded:: 2.0

    Locks several files in one transactional block.

    Files are set by a POST parameter, ``files`` which must be a json list
    of ids of :class:`.DocumentFile` to be locked.

    If one file can not be locked, no files are locked.

    :implements: :func:`http_api.lock_files`
    """
    try:
        files = map(int, json.loads(request.POST["files"]))
    except (KeyError, ValueError):
        return {"result": "error", "error": "invalid POST parameter ('files')"}
    docfiles = models.DocumentFile.objects.filter(deprecated=False,
        locked=False, id__in=files)
    if len(docfiles) == len(files):
        with transaction.commit_on_success():
            for df in docfiles:
                doc = get_obj_by_id(df.document.id, request.user)
                doc.lock(df)
    else:
        return {"result": "error", "error": "files already locked or deprecated"}
    return {"result": "ok"}

