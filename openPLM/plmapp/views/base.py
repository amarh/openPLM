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


import datetime
import functools
import json
import traceback
import re
import sys

from django.conf import settings
from django.core.mail import mail_admins
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.http import (HttpResponse, HttpResponseForbidden, Http404,
     HttpResponseRedirect, HttpResponseServerError)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.translation import ugettext as _

from openPLM import get_version
import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import get_controller
from openPLM.plmapp.exceptions import ControllerError
from openPLM.plmapp.forms import get_navigate_form, SimpleSearchForm
from openPLM.plmapp.navigate import NavigationGraph, OSR
from openPLM.plmapp.utils import can_generate_pdf


def get_obj(obj_type, obj_ref, obj_revi, user):
    """
    Get type, reference and revision of an object and return the related controller

    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`PLMObjectController` or a :class:`UserController`
    """
    controller_cls = get_controller(obj_type)
    return controller_cls.load(obj_type, obj_ref, obj_revi, user)

# from http://www.redrobotstudios.com/blog/2009/02/18/securing-django-with-ssl/
def secure_required(view_func):
    """Decorator which makes sure URL is accessed over https."""
    @functools.wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.is_secure():
            if getattr(settings, 'FORCE_HTTPS', False):
                request_url = request.build_absolute_uri(request.get_full_path())
                secure_url = request_url.replace('http://', 'https://')
                return HttpResponseRedirect(secure_url)
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

def json_view(func, API_VERSION=""):
    """
    Decorator which converts the result from *func* into a json response.

    The result from *func* must be serializable by :mod:`json`

    This decorator automatically adds a ``result`` field to the response if it
    was not present. Its value is ``'ok'`` if no exception was raised, and else,
    it is ``'error'``. In that case, a field ``'error'`` is added with a short
    message describing the exception.
    """
    @functools.wraps(func)
    def wrapper(request, *a, **kw):
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
            msg = _('Internal error') + ': ' + str(e)
            response = {'result' : 'error', 'error' : msg}
        response["api_version"] = API_VERSION
        json_data = json.dumps(response, cls=DjangoJSONEncoder)
        return HttpResponse(json_data, content_type='application/json')

    return secure_required(wrapper)


def get_obj_by_id(obj_id, user):
    u"""
    Returns an adequate controller for the object identify by *obj_id*.
    The returned controller is instanciate with *user* as the user
    who modify the object.

    :param obj_id: id of a :class:`.PLMObject`
    :param user: a :class:`.django.contrib.auth.models.User`
    :return: a subinstance of a :class:`.PLMObjectController`
    """

    obj = get_object_or_404(models.PLMObject, id=obj_id)
    obj = models.get_all_plmobjects()[obj.type].objects.get(id=obj_id)
    return get_controller(obj.type)(obj, user)


def get_obj_from_form(form, user):
    u"""
    Returns an adequate controller for the object identify by form.
    The returned controller is instanciate with *user* as the user
    who modify the object.

    :param form: a valid :class:`.PLMObjectForm`
    :param user: a :class:`.django.contrib.auth.models.User`
    :return: a subinstance of a :class:`.PLMObjectController`
    """

    type_ = form.cleaned_data["type"]
    if type_ == "User":
        reference = form.cleaned_data["username"]
        revision = "-"
    elif type_ == "Group":
        reference = form.cleaned_data["name"]
        revision = "-"
    else:
        reference = form.cleaned_data["reference"]
        revision = form.cleaned_data["revision"]
    return get_obj(type_, reference, revision, user)

def object_to_dict(plmobject):
    """
    Returns a dictionary representing *plmobject*. The returned dictionary
    respects the format described in :ref:`http-api-object`
    """
    return dict(id=plmobject.id, name=plmobject.name, type=plmobject.type,
                revision=plmobject.revision, reference=plmobject.reference)

def handle_errors(func=None, undo="..", restricted_access=True, no_cache=True):
    """
    Decorators which ensures that the user is connected and handles exceptions
    raised by a controller.

    If an exception of type :exc:`.django.http.Http404` is raised, the exception
    is re-raised.

    If an exception of type :exc:`.ControllerError` is raised, a
    :class:`.django.http.HttpResponse` is returned with an explanation message.

    If :attr:`settings.DEBUG` is False and another exception is raised,
    a :class:`.django.http.HttpResponseServerError` is returned.
    """
    def decorator(f):
        @functools.wraps(f)
        @secure_required
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.method == "POST" and request.POST.get("_undo"):
                return HttpResponseRedirect(undo)
            if restricted_access and request.user.profile.restricted:
                return HttpResponseForbidden()
            try:
                response = f(request, *args, **kwargs)
                if no_cache:
                    response['Pragma'] = 'no-cache'
                    response['Cache-Control'] = 'no-cache must-revalidate proxy-revalidate'
                return response
            except (ControllerError, ValueError) as exc:
                ctx = init_ctx("-", "-", "-")
                ctx["message"] = _(str(exc))
                return render_to_response("error.html", ctx, context_instance=RequestContext(request))
            except Http404:
                raise
            except StandardError:
                if settings.DEBUG:
                    raise
            return HttpResponseServerError()
        return wrapper
    if func:
        return decorator(func)
    return decorator

_version = get_version()
def init_ctx(init_type_, init_reference, init_revision):
    """
    Initiate the context dictionnary we used to transfer parameters to html pages.
    Get type, reference and revision of an object and return a dictionnary with them
    plus current time, :attr:`settings.THUMBNAILS_URL` the begining of the URL to
    get thumbnail of a file and :attr:`settings.LANGUAGES`.

    Example::

        >>> init_ctx('BiosOs','BI-0044','1.4.3')
        {'THUMBNAILS_URL': '/media/thumbnails',
         'object_reference': 'BI-0044',
         'object_revision': '1.4.3',
         'object_type': 'BiosOs'}

    :param init_type_: type of the object
    :type init_type_: str
    :param init_reference: reference of the object
    :type init_reference: str
    :param init_revision: revision of the object
    :type init_revision: str
    :return: a dictionnary
    """
    return {
        'object_reference': init_reference,
        'object_revision': init_revision,
        'object_type': init_type_,
        'THUMBNAILS_URL' : settings.THUMBNAILS_URL,
        'DOCUMENTATION_URL' : settings.DOCUMENTATION_URL,
        'can_generate_pdf' : can_generate_pdf(),
        'openPLM_version' : _version,
        'site' : Site.objects.get_current(),
        }

##########################################################################################
###   Manage html code for Search and Results function and other global parameters     ###
##########################################################################################
def update_navigation_history(request, obj, type_, reference, revision):
    old_history = request.session.get("navigation_history", [])
    links = tuple(obj.menu_items) + ("navigate",)
    value = (obj.plmobject_url, type_, reference, revision, links)
    history = list(old_history)
    if value in history:
        # move value at the end
        history.remove(value)
    history.append(value)
    if len(history) > 7:
        history = history[-7:]
    if old_history != history:
        request.session["navigation_history"] = history
        return True
    return False

_SEARCH_ID = "search_id_%s"
def get_generic_data(request, type_='-', reference='-', revision='-', search=True,
        load_all=False):
    """
    Get a request and return a controller, a context dictionnary with elements common to all pages
    (search form, search data, search results, ...) and another dictionnary to update the
    request.session dictionnary.

    :param request: :class:`django.http.QueryDict`
    :param type_: :attr:`.PLMObject.type`
    :type type_: str
    :param reference: :attr:`.PLMObject.reference`
    :type reference: str
    :param revision: :attr:`.PLMObject.revision`
    :type revision: str
    :return: a :class:`.PLMObjectController` or a :class:`.UserController`
    :return: ctx
    :type ctx: dic
    :return: request.session
    :type request.session: dic
    """
    ctx = init_ctx(type_, reference, revision)
    # This case happens when we create an object (and therefore can't get a controller)
    save_session = False
    profile = request.user.profile
    restricted = profile.restricted
    if type_ == reference == revision == '-':
        obj = request.user
        obj_url = profile.plmobject_url
    else:
        obj = get_obj(type_, reference, revision, request.user)
        obj_url = obj.plmobject_url
        if not restricted:
            save_session = update_navigation_history(request, obj,
                type_, reference, revision)

    table = request.GET.get("table", "")
    save_session = save_session or table != ""
    if table == "1":
        request.session["as_table"] = True
    elif table == "0":
        request.session["as_table"] = False
    ctx["as_table"] = request.session.get("as_table")

    if not restricted: # a restricted account can not perform a search
        # Builds, update and treat Search form
        search_needed = "results" not in request.session or load_all
        if request.method == "GET" and "type" in request.GET:
            search_form = SimpleSearchForm(request.GET, auto_id=_SEARCH_ID)
            request.session["type"] = request.GET["type"]
            request.session["q"] = request.GET.get("q", "")
            request.session["search_official"] = request.GET.get("search_official", "")
            search_needed = True
            save_session = True
        elif "type" in request.session:
            search_form = SimpleSearchForm(request.session, auto_id=_SEARCH_ID)
        else:
            request.session['type'] = 'all'
            search_form = SimpleSearchForm(auto_id=_SEARCH_ID)
            save_session = True

        if search and search_needed and search_form.is_valid():
            search_query = search_form.cleaned_data["q"]
            qset = search_form.search()
            if load_all:
                qset = qset.load_all()
            request.session["search_query"] = search_query
            search_official = ["", "1"][search_form.cleaned_data["search_official"]]
            request.session["search_official"] = search_official
            search_count = request.session["search_count"] = qset.count()
            qset = qset[:30]
            request.session["results"] = qset
            save_session = True
        else:
            qset = request.session.get("results", [])
            search_query = request.session.get("search_query", "")
            search_count = request.session.get("search_count", 0)
            search_official = request.session.get("search_official", "")

        ctx.update({
           'results' : qset,
           'search_query' : search_query,
           'search_count' : search_count,
           'search_form' : search_form,
           'navigation_history' : request.session.get("navigation_history", []),
           'ctype': "Part" if request.session["type"] in ("all", "User") else request.session["type"],
        })

    ctx.update({
       'link_creation' : False,
       'attach' : (obj, False),
       'obj' : obj,
       'obj_url': obj_url,
       'restricted' : restricted,
       'is_contributor': profile.is_contributor,
    })
    if hasattr(obj, "menu_items"):
        ctx['object_menu'] = obj.menu_items
    if hasattr(obj, "check_permission"):
        ctx["is_owner"] = obj.check_permission("owner", False)
    if hasattr(obj, "check_readable"):
        ctx["is_readable"] = readable = obj.check_readable(False)
        if restricted and not readable:
            raise Http404
    else:
        ctx["is_readable"] = True
    # little hack to avoid a KeyError
    # see https://github.com/toastdriven/django-haystack/issues/404
    from haystack import site
    for r in request.session.get("results", []):
        r.searchsite = site

    if save_session:
        request.session.save()
    return obj, ctx

coords_rx = re.compile(r'top:(\d+)px;left:(\d+)px;width:(\d+)px;height:(\d+)px;')

def get_navigate_data(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    FilterForm = get_navigate_form(obj)

    has_session = any(field in request.session for field in FilterForm.base_fields)
    initial = dict((k, v.initial) for k, v in FilterForm.base_fields.items())
    if request.method == 'POST' and request.POST:
        form = FilterForm(request.POST)
        if form.is_valid():
            request.session.update(form.cleaned_data)
    elif has_session:
        request.session.update(dict(doc_parts = ""))
        initial.update(request.session)
        form = FilterForm(initial)
    else:
        form = FilterForm(initial)
        request.session.update(initial)
    if not form.is_valid():
        options = initial
    else:
        options = form.cleaned_data
    if options[OSR]:
        results = [r.object for r in ctx.get("results", [])]
    else:
        results = []
    graph = NavigationGraph(obj, results)
    if options["update"]:
        options["doc_parts"] = [int(o)
                                for o in options["doc_parts"].split("#")
                                if o.isnumeric()]
    else:
        options["doc_parts"] = []
        request.session.update(dict(doc_parts = ""))
    graph.set_options(options)
    graph.create_edges()
    map_string, edges = graph.render()
    width, height = edges["width"], edges["height"]
    past = graph.time and timezone.now() - graph.time > datetime.timedelta(minutes=5)
    ctx.update({
        'filter_object_form': form,
        'map_areas': map_string,
        'img_width' : width,
        'img_height' : height,
        'navigate_bool': True,
        'edges' : edges,
        'past' : past,
    })
    return ctx

_creation_views = {}
def register_creation_view(type_, view):
    """
    Register a creation view for *type_* (a subclass of :class:`.PLMObject`).

    Most of the applications does not need to call this function which is
    available for special cases which cannot be handled by :func:`.create_object`.

    .. note::

        You must ensure that the module that calls this function has been imported.
        For example, you can import it in your :file:`urls.py` file.
    """
    _creation_views[type_] = view

def get_creation_view(type_):
    """
    Returns a registed view for *type_* (a subclass of :class:`.PLMObject`)
    or None if no views are registered.
    """
    return _creation_views.get(type_)


def get_id_card_data(doc_ids):
    """
    Get informations to display in the id-cards of all Document which id is in doc_ids

    :param doc_ids: list of Document ids to treat

    :return: a dictionary which contains the following data

        * ``thumbnails``
            list of tuple (document,thumbnail)

        * ``num_files``
            list of tuple (document, number of file)
    """
    ctx = { "thumbnails" : {}, "num_files" : {} }
    if doc_ids:
        thumbnails = models.DocumentFile.objects.filter(deprecated=False,
            document__in=doc_ids, thumbnail__isnull=False).exclude(thumbnail="")
        ctx["thumbnails"].update(thumbnails.values_list("document", "thumbnail"))
        num_files = dict.fromkeys(doc_ids, 0)
        for doc_id in models.DocumentFile.objects.filter(deprecated=False,
            document__in=doc_ids).values_list("document", flat=True):
            num_files[doc_id] += 1
        ctx["num_files"] = num_files
    return ctx


def get_pagination(request, object_list, type):
    """
    Returns a dictionary with pagination data.

    Called in view which returns a template where object id cards are displayed.
    """
    ctx = {}
    sort = request.GET.get("sort", "children" if type == "topassembly" else "recently-added")
    ctime = "date_joined" if type == "user" else "ctime"
    if sort == "name" :
        sort_critera = "username" if type == "user" else "name"
    elif type in ("part", "topassembly") and sort == "children":
        object_list = object_list.with_children_counts()
        sort_critera = "-num_children,reference,revision"
    elif type == "part" and sort == "most-used":
        object_list = object_list.with_parents_counts()
        sort_critera = "-num_parents,reference,revision"
    else:
        sort_critera = "-%s" % ctime
    object_list = object_list.order_by(*sort_critera.split(","))

    paginator = Paginator(object_list, 24) # Show 24 objects per page

    page = request.GET.get('page', 1)
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        objects = paginator.page(1)
        page = 1
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        objects = paginator.page(paginator.num_pages)
    ctx["thumbnails"] = {}
    ctx["num_files"] = {}

    if type in ("object", "document"):
         ids = objects.object_list.values_list("id", flat=True)
         ctx.update(get_id_card_data(ids))
    ctx.update({
         "objects": objects,
         "sort": sort,
    })
    return ctx


