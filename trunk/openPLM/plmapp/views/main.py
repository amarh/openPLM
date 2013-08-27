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

"""
This module contains all "html" views, i.e. views that renders an HTML page
from a standard (not ajax) HTTP request.
Ajax views are in :mod:`.ajax` and API views are in :mod:`.api`

Most of the views are decorated with :func:`.handle_errors` and
render HTML with the django template engine.
"""

import os
import csv
import json
import tempfile
import datetime
import itertools

from django.conf import settings
from django.contrib import messages
from django.contrib.admin import DateFieldListFilter
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.contrib.comments.views.comments import post_comment
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist
from django.http import (HttpResponseRedirect, HttpResponse, Http404,
                        HttpResponsePermanentRedirect)
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.i18n import set_language as dj_set_language
from django.forms.util import from_current_timezone

from haystack.views import SearchView

import openPLM.plmapp.csvimport as csvimport
import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms
from openPLM.plmapp.views.base import (init_ctx, get_obj,
    get_obj_by_id, handle_errors, get_generic_data, get_navigate_data,
    get_creation_view, secure_required, get_pagination)
from openPLM.plmapp.controllers import get_controller
from openPLM.plmapp.exceptions import ControllerError, PermissionError
from openPLM.plmapp.utils import filename_to_name, r2r


def set_language(request):
    """
    A wrapper arround :func:`django.views.i18n.set_language` that
    stores the language in the user profile.
    """
    response = dj_set_language(request)
    if request.method == "POST" and request.user.is_authenticated():
        language = request.session.get('django_language')
        if language:
            request.user.profile.language = language
            request.user.profile.save()
    return response


@handle_errors
def comment_post_wrapper(request):
    # from http://thejaswi.info/tech/blog/2008/11/20/part-2-django-comments-authenticated-users/
    # Clean the request to prevent form spoofing
    user = request.user
    if user.is_authenticated() and not user.profile.restricted:
        if not (user.get_full_name() == request.POST['name'] and \
                user.email == request.POST['email']):
            return HttpResponse("You registered user...trying to spoof a form...eh?")
        resp = post_comment(request)
        if isinstance(resp, HttpResponseRedirect):
            messages.success(request, _(u"Your comment was posted."))
        return resp
    return HttpResponse("You anonymous cheater...trying to spoof a form?")


@handle_errors(restricted_access=False)
def display_home_page(request):
    """
    Home page view.

    :url: :samp:`/home/`

    **Template:**

    :file:`home.html`

    **Context:**

    ``RequestContext``

    ``pending_invitations_owner``
        QuerySet of pending invitations to groups owned by the user

    ``pending_invitations_guest``
        QuerySet of pending invitations to groups that the user can joined

    """
    obj, ctx = get_generic_data(request, "User", request.user.username)
    del ctx["object_menu"]
    if not obj.restricted:
        # always empty if restricted -> do not hit the database
        pending_invitations_owner = obj.invitation_inv_owner. \
                filter(state=models.Invitation.PENDING).order_by("group__name").\
                select_related("guest", "owner", "group")
        ctx["pending_invitations_owner"] = pending_invitations_owner
        pending_invitations_guest = obj.invitation_inv_guest. \
                filter(state=models.Invitation.PENDING).order_by("group__name").\
                select_related("guest", "owner", "group")
        ctx["pending_invitations_guest"] = pending_invitations_guest
        ctx["display_group"] = True

    return r2r("home.html", ctx, request)


def render_attributes(obj, attrs):
    if getattr(settings, "HIDE_EMAILS", False):
        if obj.has_permission(models.ROLE_OWNER):
            attrs = (attr for attr in attrs if attr != "email")
    object_attributes = []
    meta = obj.object._meta
    for attr in attrs:
        item = obj.get_verbose_name(attr)
        richtext = False
        try:
            field = meta.get_field(attr)
            richtext = getattr(field, "richtext", False)
        except FieldDoesNotExist:
            richtext = False
        object_attributes.append((item, getattr(obj, attr), richtext))
    return object_attributes


@handle_errors(restricted_access=False)
def display_object_attributes(request, obj_type, obj_ref, obj_revi):
    """
    Attributes view of the given object.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/attributes/`

    .. include:: views_params.txt

    **Template:**

    :file:`attribute.html`

    **Context:**

    ``RequestContext``

    ``object_attributes``
        list of tuples(verbose attribute name, value)

    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    object_attributes = render_attributes(obj, obj.attributes)
    ctx["is_contributor"] = obj._user.profile.is_contributor
    ctx.update({'current_page' : 'attributes',
                'object_attributes' : object_attributes})
    if isinstance(obj.object, models.PLMObject):
        if obj.is_part:
            ctx["attach"] = (obj, "attach_doc")
            ctx["link_creation_action"] = u"%sdoc-cad/add/" % obj.plmobject_url
        elif obj.is_document:
            ctx["attach"] = (obj, "attach_part")
            ctx["link_creation_action"] = u"%sparts/add/" % obj.plmobject_url
    return r2r('attributes.html', ctx, request)


@handle_errors(restricted_access=False)
def display_object(request, obj_type, obj_ref, obj_revi):
    """
    Generic object view.

    Permanently redirects to the attribute page of the given object if it
    is a part, a user or a group and to the files page if it is a document.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/`
    """

    if obj_type in ('User', 'Group'):
        url = u"/%s/%s/attributes/" % (obj_type.lower(), obj_ref)
    else:
        model_cls = models.get_all_plmobjects()[obj_type]
        page = "files" if issubclass(model_cls, models.Document) else "attributes"
        url = u"/object/%s/%s/%s/%s/" % (obj_type, obj_ref, obj_revi, page)
    return HttpResponsePermanentRedirect(iri_to_uri(url))


ITEMS_PER_HISTORY = 50

def redirect_history(request, type, hid):
    """
    Redirects to the history page that contains the history item
    numbered *hid*.
    """
    H = {"group" : models.GroupHistory,
         "user" : models.UserHistory,
         "object" : models.History,}[type]
    h = H.objects.get(id=int(hid))
    date_page = str(h.date)[:10]
    items = H.objects.filter(plmobject=h.plmobject, date__gte=h.date).count() - 1
    page = items // ITEMS_PER_HISTORY + 1
    url = u"%shistory/?date_history_begin=%s&number_days=30#%s" % (h.plmobject.plmobject_url, date_page, hid)
    return HttpResponseRedirect(url)


@handle_errors
def display_object_history(request, obj_type="-", obj_ref="-", obj_revi="-", timeline=False,
        template="history.html"):
    """
    History view.

    This view displays a history of the selected object and its revisions.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/history/`
    :url: :samp:`/user/{username}/history/`
    :url: :samp:`/group/{group_name}/history/`
    :url: :samp:`/timeline/`

    .. include:: views_params.txt

    **Template:**

    :file:`history.html`

    **Context:**

    ``RequestContext``

    ``object_history``
        list of :class:`.AbstractHistory`

    ``show_revisions``
        True if the template should show the revision of each history row

    ``show_identifiers``
        True if the template should show the type, reference and revision
        of each history row
    """


    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    form_date = forms.HistoryDateForm(request.GET if request.GET else None)
    if form_date.is_valid():
        date_begin = form_date.cleaned_data["date_history_begin"]
        number_days = form_date.cleaned_data["number_days"]
        done_by = form_date.cleaned_data["done_by"]
    else:
        done_by = ""
        if 'date_history_begin' in request.GET:
            if len(request.GET['date_history_begin']) == 10 :
                date_begin = request.GET['date_history_begin']
                date_begin = datetime.datetime(int(date_begin[:4]), int(date_begin[5:7]), int(date_begin[8:10]))
            else:
                date_begin = datetime.datetime.today()
        else :
            date_begin = datetime.datetime.today()
        number_days = 30
    date_begin = from_current_timezone(date_begin)
    if date_begin >  from_current_timezone(datetime.datetime.today()):
        date_begin = from_current_timezone(datetime.datetime.today())
    date_end = date_begin - datetime.timedelta(days = int(number_days))
    date_end = from_current_timezone(date_end)


    if timeline:
        # global timeline: shows objects owned by the company and readable objects
        ctx["timeline"] = True
        ctx['object_type'] = _("Timeline")

        form_object = forms.HistoryObjectForm(request.GET if request.GET else None)
        if form_object.is_valid():
            display_part = form_object.cleaned_data["part"]
            display_document = form_object.cleaned_data["document"]
            display_group = form_object.cleaned_data["group"]
        else:
            display_part = True
            display_document = True
            display_group = True
        list_display = {"display_document": display_document, "display_part": display_part, "display_group" : display_group}
        history = models.timeline_histories(obj, from_current_timezone(date_begin + datetime.timedelta(days = 1)), date_end, done_by, list_display)
        ctx['form_object'] = form_object

        if display_document:
            display_document = 'on'
        if display_part:
            display_part = 'on'
        if display_group:
            display_group = 'on'

        ctx['display_document'] = display_document
        ctx['display_part'] = display_part
        ctx['display_group'] = display_group


    else:
        history = obj.histories
        history = history.filter(date__gte = date_end, date__lt = from_current_timezone(date_begin + datetime.timedelta(days = 1)))
        if done_by != "":
            if models.User.objects.filter(username= done_by).exists():
                history = history.filter(user__username = done_by)
            else:
                history = history.none()
                messages.error(request, "This user doesn't exist")
        elif hasattr(obj, "revision"):
            # display history of all revisions
            ctx["show_revisions"] = True
        else:
            ctx["show_revisions"] = False
        history = history.select_related("plmobject", "user__profile")



    date_after = from_current_timezone(date_begin + datetime.timedelta(days = 1))

    if date_after < from_current_timezone(datetime.datetime.today()):
        ctx['date_after'] = (date_begin + datetime.timedelta(days = number_days +1)).strftime('%Y-%m-%d')
    ctx.update({
        'date_before' : (date_begin - datetime.timedelta(days = number_days +1)).strftime('%Y-%m-%d'),
        'form_date': form_date,
        'date_begin_period' : date_begin.strftime('%Y-%m-%d'),
        'date_end_period':date_end.strftime('%Y-%m-%d'),
        "number_days" : number_days,
        'current_page' : 'history',
        'object_history' : history,
        'show_identifiers' : timeline
        })
    return r2r(template, ctx, request)


@handle_errors
def create_object(request, from_registered_view=False, creation_form=None):
    """
    View to create a :class:`.PLMObject` or a :class:`.GroupInfo`.

    :url: ``/object/create/``

    Requests (POST and GET) must contain a ``type`` variable that validates a
    :class:`.TypeForm`.

    POST requests must validate the creation form, fields depend on the
    given type. If the creation form is valid, an object is created and
    in case of success, this view redirects to the created object.

    Requests may contain a ``__next__`` variable. A successful creation will
    redirect to this URL. Some special strings are replaced:

        * ``##type##`` with the created object's type
        * ``##ref##`` with the created object's reference
        * ``##rev##`` with the created object's reference

    Requests may also contain other special variables (at most one of
    them):

        ``related_doc``
            Id of a document. The created part will be attached to this
            document. Object's type is restricted to part types.
            Two context variables (``related_doc`` and ``related``)
            are set to the document controller.

        ``related_part``
            Id of a part. The created document will be attached to this
            part. Object's type is restricted to document types.
            Two context variables (``related_part`` and ``related``)
            are set to the part controller.

        ``related_parent``
            Id of a part. Object's type is restricted to part types.
            Two context variables (``related_parent`` and ``related``)
            are set to the part controller.

    .. note::
        If *from_registered_view* is False, this view delegates its
        treatment to a registered view that handles creation of
        objects of the given type.
        (see :func:`.get_creation_view` and :func:`.register_creation_view`)

    :param from_registered_view: True if this function is called by another
         creation view
    :param creation_form: a creation form that will be used instead of the
         default one

    **Template:**

    :file:`create.html`

    **Context:**

    ``RequestContext``

    ``creation_form``

    ``creation_type_form``
        :class:`.TypeForm` to select the type of the created object

    ``object_type``
        type of the created object

    ``next``
        value of the ``__next__`` request variable if given
    """

    obj, ctx = get_generic_data(request)
    Form = forms.TypeForm
    # it is possible that the created object must be attached to a part
    # or a document
    # related_doc and related_part should be a plmobject id
    # If the related_doc/part is not a doc/part, we let python raise
    # an AttributeError, since a user should not play with the URL
    # and openPLM must be smart enough to produce valid URLs
    attach = related = None
    if "related_doc" in request.REQUEST:
        Form = forms.PartTypeForm
        doc = get_obj_by_id(int(request.REQUEST["related_doc"]), request.user)
        attach = doc.attach_to_part
        ctx["related_doc"] = request.REQUEST["related_doc"]
        related = ctx["related"] = doc
    elif "related_part" in request.REQUEST:
        Form = forms.DocumentTypeForm
        part = get_obj_by_id(int(request.REQUEST["related_part"]), request.user)
        attach = part.attach_to_document
        ctx["related_part"] = request.REQUEST["related_part"]
        related = ctx["related"] = part
    elif "related_parent" in request.REQUEST:
        Form = forms.PartTypeForm
        parent = get_obj_by_id(int(request.REQUEST["related_parent"]), request.user)
        ctx["related_parent"] = request.REQUEST["related_parent"]
        related = ctx["related"] = parent
    if "pfiles" in request.REQUEST:
        Form = forms.Document2TypeForm

    if "__next__" in request.REQUEST:
        redirect_to = request.REQUEST["__next__"]
        ctx["next"] = redirect_to
    else:
        # will redirect to the created object
        redirect_to = None

    type_form = Form(request.REQUEST)
    if type_form.is_valid():
        type_ = type_form.cleaned_data["type"]
        cls = models.get_all_users_and_plmobjects()[type_]
        if not from_registered_view:
            view = get_creation_view(cls)
            if view is not None:
                # view has been registered to create an object of type 'cls'
                return view(request)
    else:
        ctx["creation_type_form"] = type_form
        return r2r('create.html', ctx, request)

    if request.method == 'GET' and creation_form is None:
        creation_form = forms.get_creation_form(request.user, cls)
        if related is not None:
            creation_form.fields["group"].initial = related.group
            creation_form.initial["lifecycle"] = related.lifecycle
        if "pfiles" in request.GET:
            pfiles = request.GET.getlist("pfiles")
            creation_form.initial["pfiles"] = pfiles
            try:
                name = filename_to_name(obj.files.get(id=int(pfiles[0])).filename)
                creation_form.initial["name"] = name
            except Exception:
                pass
    elif request.method == 'POST':
        if creation_form is None:
            creation_form = forms.get_creation_form(request.user, cls, request.POST)
        if creation_form.is_valid():
            ctrl_cls = get_controller(type_)
            ctrl = ctrl_cls.create_from_form(creation_form, request.user)
            message = _(u"The %(Object_type)s has been created") % dict(Object_type = type_)
            messages.info(request, message)
            if attach is not None:
                try:
                    attach(ctrl)
                    message = _(u"The %(Object_type)s has been attached") % dict(Object_type = type_)
                    messages.info(request, message)
                except (ControllerError, ValueError) as e:
                    # crtl cannot be attached (maybe the state of the
                    # related object as changed)
                    # alerting the user using the messages framework since
                    # the response is redirected
                    message = _(u"Error: %(details)s") % dict(details=unicode(e))
                    messages.error(request, message)
                    # redirecting to the ctrl page that lists its attached
                    # objects
                    if ctrl.is_document:
                        return HttpResponseRedirect(ctrl.plmobject_url + "parts/")
                    else:
                        return HttpResponseRedirect(ctrl.plmobject_url + "doc-cad/")
            if redirect_to:
                redirect_to = redirect_to.replace("##ref##", ctrl.reference)
                redirect_to = redirect_to.replace("##rev##", ctrl.revision)
                redirect_to = redirect_to.replace("##type##", ctrl.type)
            return HttpResponseRedirect(redirect_to or ctrl.plmobject_url)
    ctx.update({
        'creation_form' : creation_form,
        'object_type' : type_,
        'creation_type_form' : type_form,
    })
    return r2r('create.html', ctx, request)


@handle_errors(undo="../attributes/", restricted_access=False)
def modify_object(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the modification of the selected object.
    It computes a context dictionary based on

    .. include:: views_params.txt
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    cls = models.get_all_plmobjects()[obj_type]
    if request.method == 'POST' and request.POST:
        modification_form = forms.get_modification_form(cls, request.POST)
        if modification_form.is_valid():
            obj.update_from_form(modification_form)
            return HttpResponseRedirect(obj.plmobject_url + "attributes/")
    else:
        modification_form = forms.get_modification_form(cls, instance=obj.object)

    ctx['modification_form'] = modification_form
    return r2r('edit.html', ctx, request)


@handle_errors
def navigate(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays a graphical picture the different links
    between :class:`~django.contrib.auth.models.User` and  :class:`.models.PLMObject`.
    This function uses Graphviz (http://graphviz.org/).
    Some filters let user defines which type of links he/she wants to display.
    It computes a context dictionary based on

    .. include:: views_params.txt
    """
    ctx = get_navigate_data(request, obj_type, obj_ref, obj_revi)
    ctx["edges"] = json.dumps(ctx["edges"])
    return r2r('navigate.html', ctx, request)


@handle_errors(undo="../..")
def import_csv_init(request, target="csv"):
    """
    Manage page to import a csv file.
    """
    if not request.user.profile.is_contributor:
        raise PermissionError("You are not a contributor.")
    obj, ctx = get_generic_data(request)
    if request.method == "POST":
        csv_form = forms.CSVForm(request.POST, request.FILES)
        if csv_form.is_valid():
            f = request.FILES["file"]
            prefix = "openplmcsv" + request.user.username
            tmp = tempfile.NamedTemporaryFile(prefix=prefix, delete=False)
            for chunk in f.chunks():
                tmp.write(chunk)
            name = os.path.split(tmp.name)[1][len(prefix):]
            tmp.close()
            encoding = csv_form.cleaned_data["encoding"]
            return HttpResponseRedirect("/import/%s/%s/%s/" % (target, name,
                                        encoding))
    else:
        csv_form = forms.CSVForm()
    ctx["csv_form"] = csv_form
    ctx["step"] = 1
    ctx["target"] = target
    return r2r("import/csv.html", ctx, request)


@handle_errors(undo="../..")
def import_csv_apply(request, target, filename, encoding):
    """
    View that display a preview of an uploaded csv file.
    """
    obj, ctx = get_generic_data(request)
    if not request.user.profile.is_contributor:
        raise PermissionError("You are not a contributor.")
    ctx["encoding_error"] = False
    ctx["io_error"] = False
    Importer = csvimport.IMPORTERS[target]
    Formset = forms.get_headers_formset(Importer)
    try:
        path = os.path.join(tempfile.gettempdir(),
                            "openplmcsv" + request.user.username + filename)
        with open(path, "rb") as csv_file:
            importer = Importer(csv_file, request.user, encoding)
            preview = importer.get_preview()
        if request.method == "POST":
            headers_formset = Formset(request.POST)
            if headers_formset.is_valid():
                headers = headers_formset.headers
                try:
                    with open(path, "rb") as csv_file:
                        importer = Importer(csv_file, request.user, encoding)
                        importer.import_csv(headers)
                except csvimport.CSVImportError as exc:
                    ctx["errors"] = exc.errors.iteritems()
                else:
                    os.remove(path)
                    return HttpResponseRedirect("/import/done/")
        else:
            initial = [{"header": header} for header in preview.guessed_headers]
            headers_formset = Formset(initial=initial)
        ctx.update({
            "preview" :  preview,
            "preview_data" : itertools.izip((f["header"] for f in headers_formset.forms),
                preview.headers, *preview.rows),
            "headers_formset" : headers_formset,
        })
    except UnicodeError:
        ctx["encoding_error"] = True
    except (IOError, csv.Error):
        ctx["io_error"] = True
    ctx["has_critical_error"] = ctx["io_error"] or ctx["encoding_error"] \
            or "errors" in ctx
    ctx["csv_form"] = forms.CSVForm(initial={"encoding" : encoding})
    ctx["step"] = 2
    ctx["target"] = target
    return r2r("import/csv.html", ctx, request)


@handle_errors
def import_csv_done(request):
    obj, ctx = get_generic_data(request)
    return r2r("import/done.html", ctx, request)


class OpenPLMSearchView(SearchView):

    def extra_context(self):
        extra = super(OpenPLMSearchView, self).extra_context()
        obj, ctx = get_generic_data(self.request, search=False)
        ctx["type"] = type = self.request.session["type"]
        ctx["object_type"] = _("Search")
        ctx["suggestion"] = self.suggestion
        ctx["extra_types"] = [c.__name__ for c in models.IObject.__subclasses__()]
        try:
            cls = models.get_all_plmobjects()[type]
            if issubclass(cls, models.PLMObject):
                main_cls = models.Part if issubclass(cls, models.Part) else models.Document
                ctx["subtypes"] = models.get_subclasses(main_cls)
        except KeyError:
            pass
        extra.update(ctx)
        return extra

    def get_query(self):
        query = super(OpenPLMSearchView, self).get_query() or "*"
        self.request.session["search_query"] = query
        return query

    def get_results(self):
        results = super(OpenPLMSearchView, self).get_results()
        # update request.session so that the left panel displays
        # the same results
        session = self.request.session
        self.suggestion = results.spelling_suggestion(self.get_query())
        session["results"] = results[:30]
        session["search_count"] = results.count()
        session["search_official"] = self.request.GET.get("search_official", "")
        from haystack import site
        for r in session.get("results"):
            r.searchsite = site
        session.save()
        return results

    @method_decorator(handle_errors)
    def __call__(self, request):
        return super(OpenPLMSearchView, self).__call__(request)


class SimpleDateFilter(DateFieldListFilter):
    template = "snippets/time_filter.html"

    def __init__(self, field, request, model, field_path):
        params = {}
        for param, value in request.GET.items():
            params[param.replace(field_path, field)] = value
        self.field_path2 = field_path
        mfield = model._meta.get_field(field)
        super(SimpleDateFilter, self).__init__(mfield, request,
            params, model, None, field)
        self.display = ""

    def filters(self):
        for i, (title, param_dict) in enumerate(self.links):
            params = {
                self.field_path2 + "__gte": "",
                self.field_path2 + "__lt": "",
            }
            for param, value in param_dict.iteritems():
                params[param.replace(self.field_path, self.field_path2)] = value
            selected = (self.date_params == param_dict or
                (i == 0 and not any(self.date_params.itervalues())))
            if selected:
                self.display = title
            yield {
                'selected': selected,
                'param_dict': params,
                'display': title,
            }

    def queryset(self, request, queryset):
        try:
            queryset = super(SimpleDateFilter, self).queryset(request, queryset)
        except IncorrectLookupParameters:
            # wrong query manually entered, ignore it
            pass
        return queryset


@secure_required
def browse(request, type="object"):
    user = request.user
    if user.is_authenticated() and not user.profile.restricted:
        # only authenticated users can see all groups and users
        obj, ctx = get_generic_data(request, search=False)
        plmtypes = ("object", "part", "topassembly", "document")
        try:
            type2manager = {
                "object" : models.PLMObject.objects,
                "part" : models.Part.objects,
                "topassembly" : models.Part.top_assemblies,
                "document" : models.Document.objects,
                "group" : models.GroupInfo.objects,
                "user" : User.objects.select_related("profile"),
            }
            manager = type2manager[type]
            main_cls = manager.model
            stype = request.GET.get("stype")
            plmobjects = ctx["plmobjects"] = type in plmtypes
            if plmobjects and stype and stype != "Object":
                cls = models.get_all_plmobjects()[stype]
                if not issubclass(cls, main_cls):
                    raise Http404
                if type == "topassembly":
                    manager = cls.top_assemblies
                else:
                    manager = cls.objects
            else:
                stype = None
            ctx["stype"] = stype
        except KeyError:
            raise Http404
        object_list = manager.all()
        # this is only relevant for authenticated users
        ctx["state"] = state = request.GET.get("state", "all")
        if plmobjects:
            ctx["subtypes"] = models.get_subclasses(main_cls)
            if type == "object":
                ctx["subtypes"][0] = (0, models.PLMObject, "Object")
            if state != models.get_cancelled_state().name:
                object_list = object_list.exclude_cancelled()
            if state == "official":
                object_list = object_list.officials()
            elif state == "published":
                object_list = object_list.filter(published=True)
            elif state != "all":
                object_list = object_list.filter(state=state)
            ctx["states"] = models.State.objects.order_by("name").values_list("name", flat=True)

        # date filters
        model = object_list.model
        ctime = "date_joined" if type == "user" else "ctime"
        ctime_filter = SimpleDateFilter(ctime, request, model, "ctime")
        object_list = ctime_filter.queryset(request, object_list)
        ctx["time_filters"] = [ctime_filter]
        if plmobjects:
            mtime_filter = SimpleDateFilter("mtime", request, model, "mtime")
            object_list = mtime_filter.queryset(request, object_list)
            ctx["time_filters"].append(mtime_filter)
    else:
        try:
            manager = {
                "object" : models.PLMObject.objects,
                "part" : models.Part.objects,
                "topassembly" : models.Part.top_assemblies,
                "document" : models.Document.objects,
            }[type]
        except KeyError:
            raise Http404
        ctx = init_ctx("-", "-", "-")
        ctx.update({
            'is_readable' : True,
            'is_contributor': False,
            'plmobjects' : True,
            'restricted' : True,
            'object_menu' : [],
            'navigation_history' : [],
        })
        query = Q(published=True)
        if user.is_authenticated():
            readable = user.plmobjectuserlink_user.now().filter(role=models.ROLE_READER)
            query |= Q(id__in=readable.values_list("plmobject_id", flat=True))
        object_list = manager.filter(query).exclude_cancelled()

    ctx.update(get_pagination(request, object_list, type))
    extra_types = [c.__name__ for c in models.IObject.__subclasses__()]
    ctx.update({
        "object_type" : _("Browse"),
        "type" : type,
        "extra_types" : extra_types,
    })
    return r2r("browse.html", ctx, request)


@secure_required
def public(request, obj_type, obj_ref, obj_revi, template="public.html"):
    """
    .. versionadded:: 1.1

    Public view of the given object, this view is accessible to anonymous
    users. The object must be a published part or document.

    Redirects to the login page if the object is not published and the user
    is not authenticated.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/public/`

    .. include:: views_params.txt

    **Template:**

    :file:`public.html`

    **Context:**

    ``RequestContext``

    ``obj``
        the controller

    ``object_attributes``
        list of tuples(verbose attribute name, value)

    ``revisions``
        list of published related revisions

    ``attached``
        list of published attached documents and parts
    """
    # do not call get_generic_data to avoid the overhead due
    # to a possible search and the update of the navigation history
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    if not (obj.is_part or obj.is_document):
        raise Http404
    if not obj.published and request.user.is_anonymous():
        return redirect_to_login(request.get_full_path())
    elif not obj.published and not obj.check_restricted_readable(False):
        raise Http404

    ctx = init_ctx(obj_type, obj_ref, obj_revi)
    object_attributes = render_attributes(obj, obj.published_attributes)
    object_attributes.insert(4, (obj.get_verbose_name("state"), obj.state.name, False))
    if request.user.is_anonymous():
        test = lambda x: x.published
        is_contributor = False
    else:
        is_contributor = request.user.profile.is_contributor
        readable = request.user.plmobjectuserlink_user.now().filter(role=models.ROLE_READER)\
                .values_list("plmobject_id", flat=True)
        test = lambda x: x.published or x.id in readable

    revisions = [rev for rev in obj.get_all_revisions() if test(rev)]
    if obj.is_part:
        attached = [d.document for d in obj.get_attached_documents() if test(d.document)]
    else:
        attached = [d.part for d in obj.get_attached_parts() if test(d.part)]
    ctx.update({
        'is_readable' : True,
        'is_contributor': is_contributor,
        # disable the menu and the navigation_history
        'object_menu' : [],
        'navigation_history' : [],
        'obj' : obj,
        'object_attributes': object_attributes,
        'revisions' : revisions,
        'attached' : attached,
    })

    return r2r(template, ctx, request)


@handle_errors
def async_search(request):
    """Perform search_request asynchronously"""
    obj,ctx = get_generic_data(request)
    if request.GET["navigate"]=="true" :
        ctx["navigate_bool"]=True
    return r2r("render_search.html",ctx,request)

