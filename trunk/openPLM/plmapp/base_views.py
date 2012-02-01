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
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################


import re
import datetime
from functools import wraps
import functools
import traceback
import sys

import Image

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.core.mail import mail_admins
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseServerError, Http404
from django.contrib.auth.decorators import login_required

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import get_controller, \
        DocumentController
from openPLM.plmapp.controllers.user import UserController
from openPLM.plmapp.controllers.group import GroupController
from openPLM.plmapp.exceptions import ControllerError
from openPLM.plmapp.navigate import NavigationGraph
from openPLM.plmapp.forms import TypeForm, TypeFormWithoutUser, get_navigate_form, \
        SimpleSearchForm

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
    if obj_type == 'User':
        obj = get_object_or_404(User, username=obj_ref)
        controller_cls = UserController
    elif obj_type == 'Group':
        obj = get_object_or_404(Group, name=obj_ref)
        controller_cls = GroupController
    else:
        obj = get_object_or_404(models.PLMObject, type=obj_type,
                                reference=obj_ref,
                                revision=obj_revi)
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
        controller_cls = get_controller(obj_type)
    return controller_cls(obj, user)

# from http://www.redrobotstudios.com/blog/2009/02/18/securing-django-with-ssl/
def secure_required(view_func):
    """Decorator makes sure URL is accessed over https."""
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
    
    The result from *func* must be serializable by :mod:`django.utils.simple_json`
    
    This decorator automatically adds a ``result`` field to the response if it
    was not present. Its value is ``'ok'`` if no exception was raised, and else,
    it is ``'error'``. In that case, a field ``'error'`` is had with a short
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
        json = simplejson.dumps(response)
        return HttpResponse(json, mimetype='application/json')

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
    respects the format described in :ref`http-api-object`
    """
    return dict(id=plmobject.id, name=plmobject.name, type=plmobject.type,
                revision=plmobject.revision, reference=plmobject.reference)

def handle_errors(func=None, undo=".."):
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
        @wraps(f)
        @secure_required
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.method == "POST" and request.POST.get("_undo"):
                return HttpResponseRedirect(undo)
            try:
                return f(request, *args, **kwargs)
            except (ControllerError, ValueError) as exc:
                return render_to_response("error.html", {"message" : str(exc)})
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

def init_ctx(init_type_, init_reference, init_revision):
    """
    Initiate the context dictionnary we used to transfer parameters to html pages.
    Get type, reference and revision of an object and return a dictionnary with them
    plus current time, :attr:`settings.THUMBNAILS_URL` the begining of the URL to
    get thumbnail of a file and :attr:`settings.LANGUAGES`.
    
    Example::
    
        >>> init_ctx('BiosOs','BI-0044','1.4.3')
        {'LANGUAGES': (('fr', u'Fran\xc3\xa7ais'), ('en', 'English')),
         'THUMBNAILS_URL': '/media/thumbnails',
         'current_date': datetime.datetime(2010, 8, 27, 11, 34, 21, 639171),
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
    now = datetime.datetime.now()
    return {
        'current_date': now,
        'object_reference': init_reference,
        'object_revision': init_revision,
        'object_type': init_type_,
        'search_query' : "",
        'THUMBNAILS_URL' : settings.THUMBNAILS_URL,
        'LANGUAGES' : settings.LANGUAGES,
        }

##########################################################################################
###   Manage html code for Search and Results function and other global parameters     ###
##########################################################################################

def get_generic_data(request, type_='-', reference='-', revision='-', search=True):
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
    :return: a :class:`PLMObjectController` or a :class:`UserController`
    :return: ctx
    :type ctx: dic
    :return: request.session
    :type request.session: dic
    """
    ctx = init_ctx(type_, reference, revision)
    # This case happens when we create an object (and therefore can't get a controller)
    if type_ == reference == revision == '-':
        obj = request.user
    else:
        obj = get_obj(type_, reference, revision, request.user)
    # Builds, update and treat Search form
    search_needed = "results" not in request.session
    search_id = "search_id_%s" 
    if request.method == "GET" and "type" in request.GET:
        type_form4creation = TypeFormWithoutUser(request.GET)
        search_form = SimpleSearchForm(request.GET, auto_id=search_id)
        request.session["type"] = request.GET["type"]
        request.session["q"] = request.GET.get("q", "")
        search_needed = True
    elif "type" in request.session:
        type_form4creation = TypeFormWithoutUser(request.session)
        search_form = SimpleSearchForm(request.session, auto_id=search_id)
    else:
        type_form4creation = TypeFormWithoutUser()
        request.session['type'] = 'Part'
        search_form = SimpleSearchForm(auto_id=search_id)

    if search and search_needed and search_form.is_valid():
        search_query = search_form.cleaned_data["q"]
        qset = search_form.search()
        request.session["search_query"] = search_query
        search_count = request.session["search_count"] = qset.count()
        qset = qset[:30]
        request.session["results"] = qset
    else:
        qset = request.session.get("results", [])
        search_query = request.session.get("search_query", "")
        search_count = request.session.get("search_count", 0)

    ctx.update({'results' : qset, 
                'search_query' : search_query,
                'search_count' : search_count,
                'type_form4creation' : type_form4creation,
                'search_form' : search_form,
                'link_creation' : False,
                'attach' : (obj, False),
                'obj' : obj,
              })
    if hasattr(obj, "menu_items"):
        ctx['object_menu'] = obj.menu_items
    if hasattr(obj, "check_permission"):
        ctx["is_owner"] = obj.check_permission("owner", False)
    if hasattr(obj, "check_readable"):
        ctx["is_readable"] = obj.check_readable(False)
    else:
        ctx["is_readable"] = True

    # little hack to avoid a KeyError
    # see https://github.com/toastdriven/django-haystack/issues/404
    from haystack import site
    for r in request.session.get("results", []):
        r.searchsite = site

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
        raise ValueError("Invalid form")
    graph = NavigationGraph(obj, [r.object for r in ctx.get("results", [])])
    options = form.cleaned_data
    if options["update"]:
        options["doc_parts"] = [int(o)
                                for o in options["doc_parts"].split("#")
                                if o.isnumeric()]
    else:
        options["doc_parts"] = []
        request.session.update(dict(doc_parts = ""))
    graph.set_options(options)
    graph.create_edges()
    map_string, url, path = graph.render()
    top, left, w, h = map(int, re.search(coords_rx, map_string).groups())
    x_part_node_position = (2 * left + w) // 2
    y_part_node_position = (2 * top + h) // 2
    x_img_position_corrected = 1172 // 2 - x_part_node_position
    y_img_position_corrected = 500 // 2 - y_part_node_position
    img = Image.open(path)
    width, height = img.size
    ctx.update({
        'filter_object_form': form,
        'map_areas': map_string,
        'picture_path': "/"+url,
        'x_img_position': x_img_position_corrected,
        'y_img_position': y_img_position_corrected,
        'img_width' : width,
        'img_height' : height,
        'center_x' : left + w // 2,
        'center_y' : top + h //2,
        'navigate_bool': True,
    })
    return ctx


