#-!- coding:utf-8 -!-

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

import os
import glob
import tempfile
from mimetypes import guess_type

from django.conf import settings
from django.http import (HttpResponseRedirect, HttpResponse, Http404,
                        HttpResponseForbidden,
                        HttpResponseBadRequest, StreamingHttpResponse)
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib import messages

import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms
from openPLM.plmapp.utils.archive import ARCHIVE_FORMATS
from openPLM.plmapp.views.base import (get_obj, get_obj_from_form, get_id_card_data,
    get_obj_by_id, handle_errors, get_generic_data,  secure_required)
from openPLM.plmapp.controllers import UserController
from openPLM.plmapp.utils import r2r
from openPLM.plmapp.filehandlers.progressbarhandler import (ProgressBarUploadHandler,
    get_upload_suffix)


@handle_errors
def display_parts(request, obj_type, obj_ref, obj_revi):
    """
    Attached parts view.

    That view displays the parts attached to the selected object that must be a document.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/parts/`

    .. include:: views_params.txt

    **Template:**

    :file:`documents/parts.html`

    **Context:**

    ``RequestContext``

    ``parts``
        a queryset of :class:`.DocumentPartLink` bound to the document

    ``parts_formset``
        a formset to detach parts

    ``forms``
        a dictionary (link_id -> form) to get the form related to a link
        (a part may not be "detachable")
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if not hasattr(obj, "get_attached_parts"):
        return HttpResponseBadRequest("object must be a document")
    if request.method == "POST":
        formset = forms.get_rel_part_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_rel_part(formset)
            return HttpResponseRedirect(".")
    else:
        formset = forms.get_rel_part_formset(obj)
    rforms = dict((form.instance.id, form) for form in formset.forms)
    parts = obj.get_attached_parts()
    ctx.update({'current_page':'parts',
                'parts': parts,
                'forms' : rforms,
                'parts_formset': formset})
    if request.session.get("as_table"):
        ctx.update(get_id_card_data([p.id for p in parts]))
    return r2r('documents/parts.html', ctx, request)


@handle_errors
def add_part(request, obj_type, obj_ref, obj_revi):
    """
    View to attach a part to a document.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/parts/add/`

    .. include:: views_params.txt

    **Template:**

    :file:`documents/parts_add.html`

    **Context:**

    ``RequestContext``

    ``add_part_form``
        a form to attach a part (:class:`.AddPartForm`)

    ``link_creation``
        Set to True

    ``attach``
        set to (*obj*, "attach_part")
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if request.POST:
        add_part_form = forms.AddPartForm(request.POST)
        if add_part_form.is_valid():
            part_obj = get_obj_from_form(add_part_form, request.user)
            obj.attach_to_part(part_obj)
            messages.info(request, _(u"The part has been successfully attached to the document."))
            return HttpResponseRedirect(obj.plmobject_url + "parts/")
    else:
        add_part_form = forms.AddPartForm()
    ctx.update({'link_creation': True,
                'add_part_form': add_part_form,
                'attach' : (obj, "attach_part") })
    return r2r('documents/parts_add.html', ctx, request)

@handle_errors
def delete_part(request, obj_type, obj_ref, obj_revi):
    """
    View to detach a part referred by the POST parameter ``plmobject``.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/parts/delete/`

    .. include:: views_params.txt
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if request.POST:
        part_id = int(request.POST["plmobject"])
        part = get_obj_by_id(part_id, request.user)
        obj.detach_part(part)
        msg = _("The part {part.type}/{part.reference}/{part.revision} has been detached.")
        messages.info(request, msg.format(part=part))
    return HttpResponseRedirect(obj.plmobject_url + "parts/")



@handle_errors
def display_files(request, obj_type, obj_ref, obj_revi):
    """
    Files view.

    That view displays files of the given document.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/files/`

    .. include:: views_params.txt

    **Template:**

    :file:`documents/files.html`

    **Context:**

    ``RequestContext``

    ``file_formset``
        a formset to remove files

    ``archive_formats``
        list of available archive formats

    ``add_file_form``
        form to add a file
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if not hasattr(obj, "files"):
        return HttpResponseBadRequest("object must be a document")
    if request.method == "POST":
        if request.FILES:
            # from a browser where js is disabled
            return add_file(request, obj_type, obj_ref, obj_revi)
        formset = forms.get_file_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_file(formset)
            return HttpResponseRedirect(".")
    else:
        formset = forms.get_file_formset(obj)
    add_file_form = forms.AddFileForm()

    ctx.update({'current_page':'files',
                'file_formset': formset,
                'archive_formats' : ARCHIVE_FORMATS,
                'deprecated_files' : obj.deprecated_files.filter(last_revision__isnull=True),
                'add_file_form': add_file_form,
               })
    return r2r('documents/files.html', ctx, request)


@handle_errors
def upload_and_create(request, obj_ref):
    obj, ctx = get_generic_data(request)
    if not obj.profile.is_contributor:
        raise ValueError("You are not a contributor")
    if request.method == "POST":
        if request.FILES:
            # from a browser where js is disabled
            return add_file(request, "User", obj.username, "-")
    add_file_form = forms.AddFileForm()
    ctx.update({
                'add_file_form': add_file_form,
                'object_reference': "-",
                'object_type': _("Upload"),
               })
    return r2r('users/files.html', ctx, request)


def _get_redirect_url(obj, added_files):
    if isinstance(obj, UserController):
        dtype = models.get_best_document_type(added_files)
        pfiles = "&".join("pfiles=%d" % f.id for f in added_files)
        url = "/object/create/?type=%s&%s" % (dtype, pfiles)
    else:
        url = obj.plmobject_url + "files/"
    return url

@csrf_protect
@handle_errors(undo="..")
def add_file(request, obj_type, obj_ref, obj_revi):
    """
    That view displays the form to upload a file.

    .. note::

        This view show a simple form (no javascript) and is here

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/files/add/`

    .. include:: views_params.txt

    **Template:**

    :file:`documents/files_add_noscript.html`

    **Context:**

    ``RequestContext``

    ``add_file_form``
        form to add a file
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.method == "POST":
        add_file_form = forms.AddFileForm(request.POST, request.FILES)
        if add_file_form.is_valid():
            added_files = []
            for fkey, f in request.FILES.iteritems():
                added_files.append(obj.add_file(request.FILES[fkey]))
            return HttpResponseRedirect(_get_redirect_url(obj, added_files))
    else:
        if obj_type != "User" and 'file_name' in request.GET:
            f_name = request.GET['file_name'].encode("utf-8")
            if obj.has_standard_related_locked(f_name):
                return HttpResponse("true:Native file has a standard related locked file.")
            else:
                return HttpResponse("false:")
        add_file_form = forms.AddFileForm()
    if obj_type == "User":
        ctx["object_reference"] = "-"
        ctx["object_type"] = _("Upload")
        del ctx["object_menu"]
    ctx['add_file_form'] = add_file_form
    return r2r('documents/files_add_noscript.html', ctx, request)


@csrf_exempt
def up_file(request, obj_type, obj_ref, obj_revi):
    """
    This view process the file(s) upload.

    The upload is done asynchronously.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/files/up/`

    .. include:: views_params.txt

    :post params:
        files
            uploaded files

    :get params:
        list of pair (filename, id)

    The response contains "failed" if the submitted form is not valid.
    """
    request.upload_handlers.insert(0, ProgressBarUploadHandler(request))
    return _up_file(request, obj_type, obj_ref, obj_revi)


@csrf_protect
@handle_errors
def _up_file(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.method == "POST":
        add_file_form = forms.AddFileForm(request.POST, request.FILES)
        if add_file_form.is_valid():
            added_files = []
            for fkey, f in request.FILES.iteritems():
                added_files.append(obj.add_file(request.FILES[fkey]))
            return HttpResponse(_get_redirect_url(obj, added_files))
        else:
            return HttpResponse("failed")


@handle_errors
@csrf_protect
def up_progress(request, obj_type, obj_ref, obj_revi):
    """
    Show upload progress for a given progress_id

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/files/_up/`

    .. include:: views_params.txt

    :get params:
        X-Progress-ID
            progress id to search

        f_size
            size of the original file

    The response contains the uploaded size and a status :

        * waiting if the corresponding file has not been created yet

        * writing if the file is being written

        * linking if the size of the uploaded file equals the size of the original
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ret = ""
    suffix = get_upload_suffix(request.GET['X-Progress-ID'])
    tempdir = settings.FILE_UPLOAD_TEMP_DIR or tempfile.gettempdir()
    f = glob.glob(os.path.join(tempdir, "*" + suffix))
    if f:
        ret = str(os.path.getsize(f[0]))
    if not ret:
        ret = "0:waiting"
    else:
        if ret == request.GET['f_size']:
            ret += ":linking"
        else:
            ret += ":writing"
    return HttpResponse(ret)


@csrf_exempt
def get_checkin_file(request, obj_type, obj_ref, obj_revi, file_id_value):
    """
    Process to the checkin asynchronously in order to show progress
    when the checked-in file is uploaded.

    Calls :func:`.checkin_file` .
    """
    request.upload_handlers.insert(0, ProgressBarUploadHandler(request))
    return checkin_file(request, obj_type, obj_ref, obj_revi,file_id_value)


@handle_errors(undo="../..")
@csrf_protect
def checkin_file(request, obj_type, obj_ref, obj_revi, file_id_value):
    """
    Manage html page for the files (:class:`DocumentFile`) checkin in the selected object.
    It computes a context dictionary based on

    .. include:: views_params.txt
    :param file_id_value: :attr:`.DocumentFile.id`
    :type file_id_value: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.POST:
        checkin_file_form = forms.AddFileForm(request.POST, request.FILES)
        if checkin_file_form.is_valid():
            obj.checkin(models.DocumentFile.objects.get(id=file_id_value),
                        request.FILES["filename"])
            return HttpResponseRedirect(obj.plmobject_url + "files/")
    else:
        checkin_file_form = forms.AddFileForm()
    ctx['add_file_form'] =  checkin_file_form
    return r2r('documents/files_add_noscript.html', ctx, request)


@handle_errors
def file_revisions(request, docfile_id):
    """
    View to download a document file.

    :param request: :class:`django.http.QueryDict`
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id: str
    :return: a :class:`django.http.HttpResponse`
    """
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    obj, ctx = get_generic_data(request, doc_file.document.type, doc_file.document.reference,
            doc_file.document.revision)
    last_revision = doc_file.last_revision if doc_file.last_revision else doc_file
    doc_files = last_revision.older_files.order_by("-revision")
    ctx["last_revision"] = last_revision
    ctx["doc_files"] = doc_files
    checkin_file_form = forms.AddFileForm()
    ctx['add_file_form'] =  checkin_file_form
    ctx["action"] = "%sfiles/checkin/%d/" % (obj.plmobject_url, last_revision.id)
    return r2r("documents/file_revisions.html", ctx, request)


@handle_errors
def checkout_file(request, obj_type, obj_ref, obj_revi, docfile_id):
    """
    Manage html page for the files (:class:`DocumentFile`) checkout from the selected object.
    It locks the :class:`DocumentFile` and, after, calls :func:`.views.download`

    .. include:: views_params.txt
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id_value: str
    """
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    obj.lock(doc_file)
    return download(request, docfile_id)


@handle_errors
def download(request, docfile_id):
    """
    View to download a document file.

    :param request: :class:`django.http.QueryDict`
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id: str
    :return: a :class:`django.http.HttpResponse`
    """
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    ctrl = get_obj_by_id(int(doc_file.document.id), request.user)
    ctrl.check_readable()
    return serve(ctrl, doc_file, "view" in request.GET)


@secure_required
def public_download(request, docfile_id):
    """
    View to download a published document file.

    It returns an :class: `HttpResponseForbidden` if the document is
    not published.

    :param request: :class:`django.http.QueryDict`
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id: str
    :return: a :class:`django.http.HttpResponse`
    """
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    ctrl = get_obj_by_id(int(doc_file.document.id), request.user)
    if request.user.is_authenticated():
        if not ctrl.published and not ctrl.check_restricted_readable(False):
            raise Http404
    elif not ctrl.published:
        return HttpResponseForbidden()
    return serve(ctrl, doc_file)


def serve(ctrl, doc_file, view=False):
    name = doc_file.filename.encode("utf-8", "ignore")
    content_type = guess_type(name, False)[0]
    if not content_type:
        content_type = 'application/octet-stream'
    f, size = ctrl.get_content_and_size(doc_file)
    response = StreamingHttpResponse(f, content_type=content_type)
    response["Content-Length"] = size
    if not view:
        response['Content-Disposition'] = 'attachment; filename="%s"' % name
    return response


