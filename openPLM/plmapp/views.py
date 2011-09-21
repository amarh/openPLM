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

"""
Introduction
=============

This module contains all views to display html pages.

All URLs are linked with django's standard views or with plmapp view functions hereafter.
Each of them receives an httprequest object.
Then treat data with the help of different controllers and different models.
Then adress a html template with a context dictionnary via an httpresponse.

We have a view for each :class:`PLMObject` or :class:`UserProfile` :func:`menu_items`.
We have some views which allow link creation between 2 instances of :class:`PLMObject` or between
an instance of :class:`PLMObject` and an instance of :class:`UserProfile`.
We have some views for link deletion.
We have some views for link edition.
We have views for :class:`PLMObject` creation and edition.
Finaly we have :func:`navigate` which draw a picture with a central object and its related objects.

"""

import re
import datetime
from operator import attrgetter
from mimetypes import guess_type
from functools import wraps

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse,\
                        HttpResponsePermanentRedirect, HttpResponseForbidden, \
                        HttpResponseServerError, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.utils.simplejson import JSONEncoder
from django.views.decorators.cache import cache_page

from openPLM.plmapp.exceptions import ControllerError
import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController, get_controller, DocumentController
from openPLM.plmapp.user_controller import UserController
from openPLM.plmapp.utils import level_to_sign_str, get_next_revision
from openPLM.plmapp.forms import *
from openPLM.plmapp.navigate import NavigationGraph
from openPLM.plmapp.base_views import get_obj, get_obj_by_id, json_view


def handle_errors(func):
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
    @wraps(func)
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except (ControllerError, ValueError) as exc:
            return render_to_response("error.html", {"message" : str(exc)})
        except Http404:
            raise
        except StandardError:
            if settings.DEBUG:
                raise
            return HttpResponseServerError()
    return wrapper


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
        'THUMBNAILS_URL' : settings.THUMBNAILS_URL,
        'LANGUAGES' : settings.LANGUAGES,
        }

##########################################################################################
###   Manage html code for Search and Results function and other global parameters     ###
##########################################################################################

def get_generic_data(request_dict, type_='-', reference='-', revision='-'):
    """
    Get a request and return a controller, a context dictionnary with elements common to all pages
    (search form, search data, search results, ...) and another dictionnary to update the
    request.session dictionnary.
    
    :param request_dict: :class:`django.http.QueryDict`
    :param type_: :attr:`.PLMObject.type`
    :type type_: str
    :param reference: :attr:`.PLMObject.reference`
    :type reference: str
    :param revision: :attr:`.PLMObject.revision`
    :type revision: str
    :return: a :class:`PLMObjectController` or a :class:`UserController`
    :return: ctx
    :type ctx: dic
    :return: request_dict.session
    :type request_dict.session: dic
    """
    ctx = init_ctx(type_, reference, revision)
    # This case happens when we create an object (and therefore can't get a controller)
    if type_ == reference == revision == '-':
        selected_object = request_dict.user
    else:
        selected_object = get_obj(type_, reference, revision, request_dict.user)
    # Defines a variable for background color selection
    if isinstance(selected_object, UserController):
        class_for_div="ActiveBox4User"
    elif isinstance(selected_object, DocumentController):
        class_for_div="ActiveBox4Doc"
    else:
        class_for_div="ActiveBox4Part"
    qset = []
    # Builds, update and treat Search form
    search_need = "results" not in request_dict.session
    if request_dict.GET and "type" in request_dict.GET:
        type_form = TypeForm(request_dict.GET)
        type_form4creation = TypeFormWithoutUser(request_dict.GET)
        if type_form.is_valid():
            cls = models.get_all_users_and_plmobjects()[type_form.cleaned_data["type"]]
        attributes_form = get_search_form(cls, request_dict.GET)
        request_dict.session.update(request_dict.GET.items())
        search_need = True
    elif request_dict.session and "type" in request_dict.session:
        type_form = TypeForm(request_dict.session)
        type_form4creation = TypeFormWithoutUser(request_dict.session)
        cls = models.get_all_users_and_plmobjects()[request_dict.session["type"]]
        attributes_form = get_search_form(cls, request_dict.session)
    else:
        type_form = TypeForm()
        type_form4creation = TypeFormWithoutUser()
        request_dict.session['type'] = 'Part'
        attributes_form = get_search_form(models.Part)
    if attributes_form.is_valid():
        if search_need:
            qset = cls.objects.all()
            qset = attributes_form.search(qset)[:30]
            if qset is None:
                qset = []
            if issubclass(cls, User):
                qset = [UserController(u, request_dict.user) for u in qset]
            request_dict.session["results"] = qset
        else:
            qset = request_dict.session["results"] 
    else:
        qset = request_dict.session.get("results", [])
    ctx.update({'results' : qset, 'type_form' : type_form,
                         'type_form4creation' : type_form4creation,
                         'attributes_form' : attributes_form,
                         'link_creation' : False,
                         'class4div' : class_for_div,
                         'obj' : selected_object,
                         })
    if hasattr(selected_object, "menu_items"):
        ctx['object_menu'] = selected_object.menu_items
    if isinstance(selected_object, PLMObjectController):
        ctx["is_owner"] = selected_object.check_permission("owner", False)
    return selected_object, ctx, request_dict.session


##########################################################################################
###                    Function which manage the html home page                        ###
##########################################################################################
@handle_errors
def display_home_page(request):
    """
    Once the user is logged in, redirection to his/her own user object with :func:navigate
    """
    return HttpResponseRedirect("/user/%s/navigate/" % request.user)

#############################################################################################
###All functions which manage the different html pages related to a part, a doc and a user###
#############################################################################################
@handle_errors
def display_object_attributes(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays attributes of the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    object_attributes_list = []
    for attr in obj.attributes:
        item = obj.get_verbose_name(attr)
        object_attributes_list.append((item, getattr(obj, attr)))
    if isinstance(obj, UserController):
        item = obj.get_verbose_name('rank')
        object_attributes_list.append((item, getattr(obj, 'rank')))
    ctx.update({'current_page' : 'attributes',
                         'object_attributes': object_attributes_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObject.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors
def display_object(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays attributes of the selected object.
    Redirection to :func:display_object_attributes
    """
    
    if obj_type != 'User':
        url = u"/object/%s/%s/%s/attributes/" % (obj_type, obj_ref, obj_revi) 
    else:
        url = u"/user/%s/attributes/" % obj_ref
    return HttpResponsePermanentRedirect(iri_to_uri(url))

##########################################################################################
@handle_errors
def display_object_lifecycle(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays lifecycle of the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.method == 'POST':
        if request.POST["action"] == "DEMOTE":
            obj.demote()
        elif request.POST["action"] == "PROMOTE":
            obj.promote()
    
    state = obj.state.name
    lifecycle = obj.lifecycle
    object_lifecycle_list = []
    for st in lifecycle:
        object_lifecycle_list.append((st, st == state))
    is_signer = obj.check_permission(obj.get_current_sign_level(), False)
    is_signer_dm = obj.check_permission(obj.get_previous_sign_level(), False)
    ctx.update({'current_page':'lifecycle', 
                         'object_lifecycle': object_lifecycle_list,
                         'is_signer' : is_signer, 
                         'is_signer_dm' : is_signer_dm})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectLifecycle.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors
def display_object_revisions(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays all revisions of (objects having :class:`RevisionLink` with)
    the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if obj.is_revisable():
        if request.method == "POST" and request.POST:
            add_form = AddRevisionForm(request.POST)
            if add_form.is_valid():
                obj.revise(add_form.cleaned_data["revision"])
        else:
            add_form = AddRevisionForm({"revision" : get_next_revision(obj_revi)})
    else:
        add_form = None
    revisions = obj.get_all_revisions()
    ctx.update({'current_page' : 'revisions',
                         'revisions' : revisions,
                         'add_revision_form' : add_form})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectRevisions.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors
def display_object_history(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the history of (:class:`History` with) the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if isinstance(obj, UserController):
        histos = models.UserHistory.objects
    else: 
        histos = models.History.objects
    histos = histos.filter(plmobject=obj.object).order_by('date')
    object_history_list = []
    for histo in histos:
        object_history_list.append((histo.date, histo.action, histo.details))
    ctx.update({'current_page' : 'history', 
                         'object_history' : object_history_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectHistory.htm', ctx, context_instance=RequestContext(request))

#############################################################################################
###         All functions which manage the different html pages specific to part          ###
#############################################################################################
@handle_errors
def display_object_child(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the chidren of (:class:`ParentChildLink` with) the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_children"):
        # TODO
        raise TypeError()
    date = None
    level = "first"
    if request.GET:
        display_form = DisplayChildrenForm(request.GET)
        if display_form.is_valid():
            date = display_form.cleaned_data["date"]
            level = display_form.cleaned_data["level"]
    else:
        display_form = DisplayChildrenForm(initial={"date" : datetime.datetime.now(),
                                                    "level" : "first"})
    max_level = 1 if level == "first" else -1
    children = obj.get_children(max_level, date=date)
    if level == "last" and children:
        maximum = max(children, key=attrgetter("level")).level
        children = (c for c in children if c.level == maximum)
    # convert level to html space
    children = (("&nbsp;" * 2 * (level-1), link) for level, link in children)

    ctx.update({'current_page':'BOM-child', 'obj' : obj,
                                 'children': children, "display_form" : display_form})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectChild.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors
def edit_children(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which edits the chidren of (:class:`ParentChildLink` with) the selected object.
    Possibility to modify the `.ParentChildLink.order`, the `.ParentChildLink.quantity` and to
    desactivate the `.ParentChildLink`
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_children"):
        # TODO
        raise TypeError()
    if request.method == "POST":
        if request.POST.get("action", "Undo") == "Undo":
            return HttpResponseRedirect("..")
        formset = get_children_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_children(formset)
            return HttpResponseRedirect("..")
    else:
        formset = get_children_formset(obj)
    ctx.update({'current_page':'BOM-child', 'obj' : obj,
                                 'children_formset': formset, })
    request.session.update(request_dict)
    return render_to_response('DisplayObjectChildEdit.htm', ctx, context_instance=RequestContext(request))

##########################################################################################    
@handle_errors
def add_children(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for chidren creation of (:class:`ParentChildLink` creation with) the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    request.session.update(request_dict)
    
    if request.POST:
        add_child_form = AddChildForm(request.POST)
        if add_child_form.is_valid():
            child_obj = get_obj(add_child_form.cleaned_data["type"], \
                        add_child_form.cleaned_data["reference"], \
                        add_child_form.cleaned_data["revision"],
                        request.user)
            obj.add_child(child_obj, \
                            add_child_form.cleaned_data["quantity"], \
                            add_child_form.cleaned_data["order"])
            ctx.update({'add_child_form': add_child_form, })
            return HttpResponseRedirect(obj.plmobject_url + "BOM-child/") 
        else:
            add_child_form = AddChildForm(request.POST)
            ctx.update({'link_creation': True, 'add_child_form': add_child_form, })
            return render_to_response('DisplayObjectChildAdd.htm', ctx, context_instance=RequestContext(request))
    else:
        add_child_form = AddChildForm()
        ctx.update({'current_page':'BOM-child', 'link_creation': True, 'add_child_form': add_child_form, })
        return render_to_response('DisplayObjectChildAdd.htm', ctx, context_instance=RequestContext(request))
    
##########################################################################################    
@handle_errors
def display_object_parents(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the parent of (:class:`ParentChildLink` with) the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_parents"):
        # TODO
        raise TypeError()
    date = None
    level = "first"
    if request.GET:
        display_form = DisplayChildrenForm(request.GET)
        if display_form.is_valid():
            date = display_form.cleaned_data["date"]
            level = display_form.cleaned_data["level"]
    else:
        display_form = DisplayChildrenForm(initial={"date" : datetime.datetime.now(),
                                                    "level" : "first"})
    max_level = 1 if level == "first" else -1
    parents = obj.get_parents(max_level, date=date)
    if level == "last" and parents:
        maximum = max(parents, key=attrgetter("level")).level
        parents = (c for c in parents if c.level == maximum)
    ctx.update({'current_page':'parents', 'parents' :  parents,
                                 'display_form' : display_form, 'obj': obj})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectParents.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors
def display_object_doc_cad(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the related documents and CAD of (:class:`DocumentPartLink` with) the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_attached_documents"):
        # TODO
        raise TypeError()
    if request.method == "POST":
        formset = get_doc_cad_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_doc_cad(formset)
            return HttpResponseRedirect(".")
    else:
        formset = get_doc_cad_formset(obj)
    object_doc_cad_list = obj.get_attached_documents()
    ctx.update({'current_page':'doc-cad', 'object_doc_cad': object_doc_cad_list, 'doc_cad_formset': formset})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectDocCad.htm', ctx, context_instance=RequestContext(request))


##########################################################################################    
@handle_errors
def add_doc_cad(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for link creation (:class:`DocumentPartLink` link) between the selected object and some documents or CAD.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    request.session.update(request_dict)
    if request.POST:
        add_doc_cad_form = AddDocCadForm(request.POST)
        if add_doc_cad_form.is_valid():
            doc_cad_obj = get_obj(add_doc_cad_form.cleaned_data["type"], \
                        add_doc_cad_form.cleaned_data["reference"], \
                        add_doc_cad_form.cleaned_data["revision"],\
                        request.user)
            obj.attach_to_document(doc_cad_obj)
            ctx.update({'add_doc_cad_form': add_doc_cad_form, })
            return HttpResponseRedirect(obj.plmobject_url + "doc-cad/")
        else:
            add_doc_cad_form = AddDocCadForm(request.POST)
            ctx.update({'link_creation': True, 'class4div': class_for_div, 'add_doc_cad_form': add_doc_cad_form, })
            return render_to_response('DisplayDocCadAdd.htm', ctx, context_instance=RequestContext(request))
    else:
        add_doc_cad_form = AddDocCadForm()
        ctx.update({'link_creation': True, 'add_doc_cad_form': add_doc_cad_form, })
        return render_to_response('DisplayDocCadAdd.htm', ctx, context_instance=RequestContext(request))
    
#############################################################################################
###      All functions which manage the different html pages specific to documents        ###
#############################################################################################
@handle_errors
def display_related_part(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the related part of (:class:`DocumentPartLink` with) the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_attached_parts"):
        # TODO
        raise TypeError()
    if request.method == "POST":
        formset = get_rel_part_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_rel_part(formset)
            return HttpResponseRedirect(".")
    else:
        formset = get_rel_part_formset(obj)
    object_rel_part_list = obj.get_attached_parts()
    ctx.update({'current_page':'parts', 'object_rel_part': object_rel_part_list, 'rel_part_formset': formset})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectRelPart.htm', ctx, context_instance=RequestContext(request))

##########################################################################################    
@handle_errors
def add_rel_part(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for link creation (:class:`DocumentPartLink` link) between the selected object and some parts.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    request.session.update(request_dict)
    if request.POST:
        add_rel_part_form = AddRelPartForm(request.POST)
        if add_rel_part_form.is_valid():
            part_obj = get_obj(add_rel_part_form.cleaned_data["type"], \
                        add_rel_part_form.cleaned_data["reference"], \
                        add_rel_part_form.cleaned_data["revision"], request.user)
            obj.attach_to_part(part_obj)
            ctx.update({'add_rel_part_form': add_rel_part_form, })
            return HttpResponseRedirect(obj.plmobject_url + "parts/")
        else:
            add_rel_part_form = add_rel_part_form(request.POST)
            ctx.update({'link_creation': True, 'add_rel_part_form': add_rel_part_form, })
            return render_to_response('DisplayRelPartAdd.htm', ctx, context_instance=RequestContext(request))
    else:
        add_rel_part_form = AddRelPartForm()
        ctx.update({'link_creation': True,
                             'add_rel_part_form': add_rel_part_form, })
        return render_to_response('DisplayRelPartAdd.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors
def display_files(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the files (:class:`DocumentFile`) uploaded in the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    

    if not hasattr(obj, "files"):
        raise TypeError()
    if request.method == "POST":
        formset = get_file_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_file(formset)
            return HttpResponseRedirect(".")
    else:
        formset = get_file_formset(obj)
    ctx.update({'current_page':'files', 
                         'file_formset': formset})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectFiles.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors
def add_file(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the files (:class:`DocumentFile`) addition in the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    request.session.update(request_dict)
    if request.POST:
        add_file_form = AddFileForm(request.POST, request.FILES)
        if add_file_form.is_valid():
            obj.add_file(request.FILES["filename"])
            ctx.update({'add_file_form': add_file_form, })
            return HttpResponseRedirect(obj.plmobject_url + "files/")
        else:
            add_file_form = AddFileForm(request.POST)
            ctx.update({'link_creation': True, 'add_file_form': add_file_form, })
            return render_to_response('DisplayRelPartAdd.htm', ctx, context_instance=RequestContext(request))
    else:
        add_file_form = AddFileForm()
        ctx.update({'link_creation': True, 'add_file_form': add_file_form, })
        return render_to_response('DisplayFileAdd.htm', ctx, context_instance=RequestContext(request))

#############################################################################################
###    All functions which manage the different html pages specific to part and document  ###
#############################################################################################
@handle_errors
def display_management(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the Users who manage the selected object (:class:`PLMObjectUserLink`).
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    object_management_list = models.PLMObjectUserLink.objects.filter(plmobject=obj)
    object_management_list = object_management_list.order_by("role")
    ctx.update({'current_page':'management', 'object_management': object_management_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectManagement.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors
def replace_management(request, obj_type, obj_ref, obj_revi, link_id):
    """
    Manage html page for the modification of the Users who manage the selected object (:class:`PLMObjectUserLink`).
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :param link_id: :attr:`.PLMObjectUserLink.id`
    :type link_id: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    link = models.PLMObjectUserLink.objects.get(id=int(link_id))
    if obj.object.id != link.plmobject.id:
        raise ValueError("Bad link id")
    
    if request.method == "POST":
#        if request.POST.get("action", "Undo") == "Undo":
#            return HttpResponseRedirect("/home/")
        replace_management_form = ReplaceManagementForm(request.POST)
        if replace_management_form.is_valid():
            if replace_management_form.cleaned_data["type"]=="User":
                user_obj = get_obj(\
                                    replace_management_form.cleaned_data["type"],\
                                    replace_management_form.cleaned_data["username"],\
                                    "-",\
                                    request.user)
                obj.set_role(user_obj.object, link.role)
                if link.role=='notified':
                    obj.remove_notified(link.user)
                return HttpResponseRedirect("../..")
            else:
                return HttpResponseRedirect("../..")
        else:
            replace_management_form = ReplaceManagementForm(request.POST)
    else:
        replace_management_form = ReplaceManagementForm()
    request.session.update(request_dict)
    ctx.update({'current_page':'management', 'obj' : obj,
                                 'replace_management_form': replace_management_form,
                                 'link_creation': True,})
    return render_to_response('DisplayObjectManagementReplace.htm', ctx, context_instance=RequestContext(request))

##########################################################################################    
@handle_errors
def add_management(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the addition of a "notification" link (:class:`PLMObjectUserLink`) between some Users and the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if request.method == "POST":
#        if request.POST.get("action", "Undo") == "Undo":
#            return HttpResponseRedirect("/home/")
        add_management_form = ReplaceManagementForm(request.POST)
        if add_management_form.is_valid():
            if add_management_form.cleaned_data["type"]=="User":
                user_obj = get_obj(\
                                    add_management_form.cleaned_data["type"],\
                                    add_management_form.cleaned_data["username"],\
                                    "-",\
                                    request.user)
                obj.set_role(user_obj.object, "notified")
                return HttpResponseRedirect("..")
            else:
                return HttpResponseRedirect("..")
        else:
            add_management_form = ReplaceManagementForm(request.POST)
    else:
        add_management_form = ReplaceManagementForm()
    request.session.update(request_dict)
    ctx.update({'current_page':'management', 'obj' : obj,
                                 'replace_management_form': add_management_form,
                                 'link_creation': True,})
    return render_to_response('DisplayObjectManagementReplace.htm', ctx, context_instance=RequestContext(request))

##########################################################################################    
@handle_errors
def delete_management(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the deletion of a "notification" link (:class:`PLMObjectUserLink`) between some Users and the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    if request.method == "POST":
        try:
            link_id = request.POST["link_id"]
            link = models.PLMObjectUserLink.objects.get(id=int(link_id))
            obj.remove_notified(link.user)
        except (KeyError, ValueError, ControllerError):
            return HttpResponseForbidden()
    return HttpResponseRedirect("../")

##########################################################################################
###             Manage html pages for part / document creation and modification                     ###
##########################################################################################
def create_non_modifyable_attributes_list(current_obj, current_user, Classe=models.PLMObject):
    """
    Create a list of object's attributes we can't modify' and set them a value
    
    Example::
        >>> MyClass
        <class 'openPLM.plmapp.models.Part'>
        >>> create_non_modifyable_attributes_list(MyClass)
        [('owner', 'Person'),
         ('creator', 'Person'),
         ('ctime', 'Date'),
         ('mtime', 'Date')]
    
    :param Classe: :class: instance of `models.PLMObject`
    :return: list
    """
    non_modifyable_fields_list = Classe.excluded_creation_fields()
    non_modifyable_attributes_list=[]
    if current_obj=='create':
        for field in non_modifyable_fields_list:
            if field=='ctime' or field=='mtime':
                non_modifyable_attributes_list.append(('datetime', field, datetime.datetime.now()))
            elif field=='owner' or field=='creator':
                non_modifyable_attributes_list.append(('User', field, current_user.username))
            elif field=='state':
                non_modifyable_attributes_list.append(('State', field, models.get_default_state()))
    else:
        for field in non_modifyable_fields_list:
            field_value = getattr(current_obj.object, field)
            if type(field_value).__name__=='datetime':
                non_modifyable_attributes_list.append(('datetime', field, field_value))
            elif type(field_value).__name__=='User':
                non_modifyable_attributes_list.append(('User', field, field_value.username))
            elif type(field_value).__name__=='State':
                non_modifyable_attributes_list.append(('State', field, field_value.name))
    return non_modifyable_attributes_list

##########################################################################################
@handle_errors
def create_object(request):
    """
    Manage html page for the creation of an instance of `models.PLMObject` subclass.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :return: a :class:`django.http.HttpResponse`
    """
#    ctx, request_dict = get_generic_data(request)
    obj, ctx, request_dict = get_generic_data(request)
    request.session.update(request_dict)
    if request.method == 'GET':
        if request.GET:
            type_form = TypeForm(request.GET)
            if type_form.is_valid():
                cls = models.get_all_userprofiles_and_plmobjects()[type_form.cleaned_data["type"]]
                if issubclass(cls, models.Document):
                    class_for_div="ActiveBox4Doc"
                else:
                    class_for_div="ActiveBox4Part"
                creation_form = get_creation_form(cls, {'revision':'a', 'lifecycle': str(models.get_default_lifecycle()), }, True)
                non_modifyable_attributes_list = create_non_modifyable_attributes_list('create', request.user, cls)
    elif request.method == 'POST':
        if request.POST:
            type_form = TypeForm(request.POST)
            if type_form.is_valid():
                type_name = type_form.cleaned_data["type"]
                cls = models.get_all_userprofiles_and_plmobjects()[type_name]
                if issubclass(cls, models.Document):
                    class_for_div="ActiveBox4Doc"
                else:
                    class_for_div="ActiveBox4Part"
                non_modifyable_attributes_list = create_non_modifyable_attributes_list('create', request.user, cls)
                creation_form = get_creation_form(cls, request.POST)
                if creation_form.is_valid():
                    user = request.user
                    controller_cls = get_controller(type_name)
                    controller = PLMObjectController.create_from_form(creation_form, user)
                    return HttpResponseRedirect(controller.plmobject_url)
    ctx.update({'class4div': class_for_div, 'creation_form': creation_form, 'object_type': type_form.cleaned_data["type"], 'non_modifyable_attributes': non_modifyable_attributes_list })
    return render_to_response('DisplayObject4creation.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors
def modify_object(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the modification of the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    current_object, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if obj_type=='User':
        cls = models.get_all_plmobjects()['UserProfile']
    else:
        cls = models.get_all_plmobjects()[obj_type]
    non_modifyable_attributes_list = create_non_modifyable_attributes_list(current_object, request.user, cls)
    if request.method == 'POST':
        if request.POST:
            modification_form = get_modification_form(cls, request.POST)
            if modification_form.is_valid():
                current_object.update_from_form(modification_form)
                return HttpResponseRedirect(current_object.plmobject_url)
            else:
                pass
        else:
            modification_form = get_modification_form(cls, instance = current_object.object)
    else:
        modification_form = get_modification_form(cls, instance = current_object.object)
    request.session.update(request_dict)
    ctx.update({'modification_form': modification_form, 'non_modifyable_attributes': non_modifyable_attributes_list})
    return render_to_response('DisplayObject4modification.htm', ctx, context_instance=RequestContext(request))

#############################################################################################
###         All functions which manage the different html pages specific to user          ###
#############################################################################################
@handle_errors
def modify_user(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the modification of the selected :class:`~django.contrib.auth.models.User`.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :type obj_type: str
    :param obj_ref: :attr:`~django.contrib.auth.models.User.username`
    :type obj_ref: str
    :param obj_revi: "-"
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    current_object = get_obj(obj_type, obj_ref, obj_revi, request.user)
    class_for_div="ActiveBox4User"
    if request.method == 'POST':
        if request.POST:
            modification_form = OpenPLMUserChangeForm(request.POST)
            if modification_form.is_valid():
                current_object.update_from_form(modification_form)
                return HttpResponseRedirect("/user/%s/" % current_object.username)
            else:
                modification_form = OpenPLMUserChangeForm(request.POST)
    else:
        modification_form = OpenPLMUserChangeForm(instance=current_object.object)
    request.session.update(request_dict)
    ctx.update({'class4div': class_for_div, 'modification_form': modification_form})
    return render_to_response('DisplayObject4modification.htm', ctx, context_instance=RequestContext(request))
    
##########################################################################################
@handle_errors
def change_user_password(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page for the modification of the selected :class:`~django.contrib.auth.models.User` password.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :type obj_type: str
    :param obj_ref: :attr:`~django.contrib.auth.models.User.username`
    :type obj_ref: str
    :param obj_revi: "-"
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    if request.user.username=='test':
        return HttpResponseRedirect("/user/%s/attributes/" % request.user)
    current_object, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    class_for_div="ActiveBox4User"
    if request.method == 'POST':
        if request.POST:
            modification_form = PasswordChangeForm(current_object, request.POST)
            if modification_form.is_valid():
                current_object.set_password(modification_form.cleaned_data['new_password2'])
                current_object.save()
                return HttpResponseRedirect("/user/%s/" % current_object.username)
            else:
                #assert False
                modification_form = PasswordChangeForm(current_object, request.POST)
    else:
        modification_form = PasswordChangeForm(current_object)
    request.session.update(request_dict)
    ctx.update({'class4div': class_for_div, 'modification_form': modification_form})
    return render_to_response('DisplayObject4PasswordModification.htm', ctx, context_instance=RequestContext(request))

#############################################################################################
@handle_errors
def display_related_plmobject(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the related parts and related documents of (:class:`PLMObjectUserLink` with) the selected :class:`~django.contrib.auth.models.User`.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :type obj_type: str
    :param obj_ref: :attr:`~django.contrib.auth.models.User.username`
    :type obj_ref: str
    :param obj_revi: "-"
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_object_user_links"):
        # TODO
        raise TypeError()
    object_user_link_list = obj.get_object_user_links()
    ctx.update({'current_page':'parts-doc-cad', 'object_user_link': object_user_link_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectRelPLMObject.htm', ctx, context_instance=RequestContext(request))

#############################################################################################
@handle_errors
def display_delegation(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays the delegations of (:class:`DelegationLink` with) the selected :class:`~django.contrib.auth.models.User`.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :type obj_type: str
    :param obj_ref: :attr:`~django.contrib.auth.models.User.username`
    :type obj_ref: str
    :param obj_revi: "-"
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "get_user_delegation_links"):
        # TODO
        raise TypeError()
    if request.method == "POST":
        selected_link_id = request.POST.get('link_id')
        obj.remove_delegation(models.DelegationLink.objects.get(pk=int(selected_link_id)))
    user_delegation_link_list = obj.get_user_delegation_links()
    ctx.update({'current_page':'delegation', 'user_delegation_link': user_delegation_link_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectDelegation.htm', ctx, context_instance=RequestContext(request))


##########################################################################################    
@handle_errors
def delegate(request, obj_type, obj_ref, obj_revi, role, sign_level):
    """
    Manage html page for delegations modification of (:class:`DelegationLink` with) the selected :class:`~django.contrib.auth.models.User`.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :type obj_type: str
    :param obj_ref: :attr:`~django.contrib.auth.models.User.username`
    :type obj_ref: str
    :param obj_revi: "-"
    :type obj_revi: str
    :param role: :attr:`.DelegationLink.role` if role is not "sign"
    :type role: str
    :param sign_level: used for :attr:`.DelegationLink.role` if role is "sign"
    :type sign_level: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if request.method == "POST":
        delegation_form = ReplaceManagementForm(request.POST)
        if delegation_form.is_valid():
            if delegation_form.cleaned_data["type"] == "User":
                user_obj = get_obj("User",
                                   delegation_form.cleaned_data["username"],
                                   "-",
                                   request.user)
                if role == "notified" or role == "owner":
                    obj.delegate(user_obj.object, role)
                    return HttpResponseRedirect("../..")
                elif role == "sign":
                    if sign_level == "all":
                        obj.delegate(user_obj.object, "sign*")
                        return HttpResponseRedirect("../../..")
                    elif sign_level.isdigit():
                        obj.delegate(user_obj.object, level_to_sign_str(int(sign_level)-1))
                        return HttpResponseRedirect("../../..")
    else:
        delegation_form = ReplaceManagementForm()
    if role == 'sign':
        if sign_level.isdigit():
            role = _("signer level") + " " + str(sign_level)
        else:
            role = _("signer all levels")
    elif role == "notified":
        role = _("notified")
    request.session.update(request_dict)
    ctx.update({'current_page':'delegation',
                         'obj' : obj,
                         'replace_management_form': delegation_form,
                         'link_creation': True,
                         'role': role})
    return render_to_response('DisplayObjectManagementReplace.htm', ctx, context_instance=RequestContext(request))
    
##########################################################################################    
@handle_errors
def stop_delegate(request, obj_type, obj_ref, obj_revi, role, sign_level):
    """
    Manage html page to stop delegations of (:class:`DelegationLink` with) the selected :class:`~django.contrib.auth.models.User`.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :type obj_type: str
    :param obj_ref: :attr:`~django.contrib.auth.models.User.username`
    :type obj_ref: str
    :param obj_revi: "-"
    :type obj_revi: str
    :param role: :attr:`.DelegationLink.role` if role is not "sign"
    :type role: str
    :param sign_level: used for :attr:`.DelegationLink.role` if role is "sign"
    :type sign_level: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if request.method == "POST":
        delegation_form = ReplaceManagementForm(request.POST)
        if delegation_form.is_valid():
            if delegation_form.cleaned_data["type"]=="User":
                user_obj = get_obj(\
                                    add_management_form.cleaned_data["type"],\
                                    add_management_form.cleaned_data["username"],\
                                    "-",\
                                    request.user)
                if role=="notified":
                    obj.set_role(user_obj.object, "notified")
                    return HttpResponseRedirect("..")
                elif role=="owner":
                    return HttpResponseRedirect("..")
                elif role=="sign":
                    if sign_level=="all":
                        return HttpResponseRedirect("..")
                    elif sign_level.is_digit():
                        return HttpResponseRedirect("../..")
        delegation_form = ReplaceManagementForm(request.POST)
    else:
        delegation_form = ReplaceManagementForm()
    action_message_string="Select the user you no longer want for your \"%s\" role delegation :" % role
    request.session.update(request_dict)
    ctx.update({'current_page':'parts-doc-cad',
                                 'obj' : obj,
                                 'replace_management_form': delegation_form,
                                 'link_creation': True,
                                 'action_message': action_message_string})
    return render_to_response('DisplayObjectManagementReplace.htm', ctx, context_instance=RequestContext(request))
    
##########################################################################################
###             Manage html pages for file check-in / check-out / download             ###
##########################################################################################    
@handle_errors
def checkin_file(request, obj_type, obj_ref, obj_revi, file_id_value):
    """
    Manage html page for the files (:class:`DocumentFile`) checkin in the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :param file_id_value: :attr:`.DocumentFile.id`
    :type file_id_value: str
    :return: a :class:`django.http.HttpResponse`
    """
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    request.session.update(request_dict)
    if request.POST :
        checkin_file_form = AddFileForm(request.POST, request.FILES)
        if checkin_file_form.is_valid():
            obj.checkin(models.DocumentFile.objects.get(id=file_id_value), request.FILES["filename"])
            ctx.update({})
            return HttpResponseRedirect(obj.plmobject_url + "files/")
        else:
            checkin_file_form = AddFileForm(request.POST)
            ctx.update({'link_creation': True, \
                                 'add_file_form': add_file_form, })
            return render_to_response('DisplayFileAdd.htm', ctx, context_instance=RequestContext(request))
    else:
        checkin_file_form = AddFileForm()
        ctx.update({'link_creation': True,                             'add_file_form': checkin_file_form, })
        return render_to_response('DisplayFileAdd.htm', ctx, context_instance=RequestContext(request))

##########################################################################################
@handle_errors 
def download(request, docfile_id, filename=""):
    """
    Manage html page for the files (:class:`DocumentFile`) download in the selected object.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id: str
    :return: a :class:`django.http.HttpResponse`
    """
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    name = doc_file.filename.encode("utf-8", "ignore")
    mimetype = guess_type(name, False)[0]
    if not mimetype:
        mimetype = 'application/octet-stream'
    response = HttpResponse(file(doc_file.file.path), mimetype=mimetype)
    if not filename:
        response['Content-Disposition'] = 'attachment; filename="%s"' % name
    return response
 
##########################################################################################
@handle_errors 
def checkout_file(request, obj_type, obj_ref, obj_revi, docfile_id):
    """
    Manage html page for the files (:class:`DocumentFile`) checkout from the selected object.
    It locks the :class:`DocumentFile` and, after, calls :func:`.views.download`
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id_value: str
    :return: :func:`.views.download`
    """
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    obj.lock(doc_file)
    return download(request, docfile_id)

##########################################################################################
###                     Manage html pages for navigate function                        ###
##########################################################################################    
coords_rx = re.compile(r'top:(\d+)px;left:(\d+)px;width:(\d+)px;height:(\d+)px;')


def get_navigate_data(request, obj_type, obj_ref, obj_revi):
    obj, ctx, request_dict = get_generic_data(request, obj_type, obj_ref, obj_revi)
    request.session.update(request_dict)
    FilterForm = get_navigate_form(obj)
    has_session = any(field in request.session for field in FilterForm.base_fields)
    if request.method == 'POST' and request.POST:
        form = FilterForm(request.POST)
        if form.is_valid():
            request.session.update(form.cleaned_data)
    elif has_session:
        request.session.update(dict(doc_parts = ""))
        form = FilterForm(request.session)
    else:
        initial = dict((k, v.initial) for k, v in FilterForm.base_fields.items())
        form = FilterForm(initial)
        request.session.update(initial)
    if not form.is_valid():
        raise ValueError("Invalid form")
    graph = NavigationGraph(obj, ctx["results"])
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
    map_string, picture_path = graph.render()
    top, left, w, h = map(int, re.search(coords_rx, map_string).groups())
    x_part_node_position = (2 * left + w) // 2
    y_part_node_position = (2 * top + h) // 2
    x_img_position_corrected = 1172 // 2 - x_part_node_position
    y_img_position_corrected = 500 // 2 - y_part_node_position
    ctx.update({'filter_object_form': form,
                         'map_areas': map_string, 'picture_path': "/"+picture_path,
                         'x_img_position': x_img_position_corrected,
                         'y_img_position': y_img_position_corrected,
                         'navigate_bool': True})
    return ctx

@handle_errors
def navigate(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays a graphical picture the different links
    between :class:`~django.contrib.auth.models.User` and  :class:`.models.PLMObject`.
    This function uses Graphviz (http://graphviz.org/).
    Some filters let user defines which type of links he/she wants to display.
    It computes a context dictionary based on
    
    :param request: :class:`django.http.QueryDict`
    :param obj_type: :class:`~django.contrib.auth.models.User`
    :type obj_type: str
    :param obj_ref: :attr:`~django.contrib.auth.models.User.username`
    :type obj_ref: str
    :param obj_revi: "-"
    :type obj_revi: str
    :return: a :class:`django.http.HttpResponse`
    """
    context = get_navigate_data(request, obj_type, obj_ref, obj_revi)
    return render_to_response('Navigate.htm', context, 
                              context_instance=RequestContext(request))
    
@login_required
def ajax_search_form(request):
    """
    Simple view which returns the html of a search form with the data
    of :attr:`request.GET` as initial values.
    
    The request must contains a get parameter *type* with a valid type,
    otherwise, a :class:`.HttpResponseForbidden` is returned.
    """
    tf = TypeForm(request.GET)
    if tf.is_valid():
        cls = models.get_all_users_and_plmobjects()[tf.cleaned_data["type"]]
        form = get_search_form(cls, request.GET)
        return HttpResponse(form.as_table())
    else:
        return HttpResponseForbidden()

@login_required
@cache_page(60 * 60)
def ajax_autocomplete(request, obj_type, field):
    """
    Simple ajax view for JQquery.UI.autocomplete. This returns the possible
    completions (in JSON format) for *field*. The request must contains
    a get parameter named *term* which should be the string used to filter
    the results. *obj_type* must be a valid typename.

    :param str obj_type: a valid typename (like ``"part"``)
    :param str field: a valid field (like ``"name"``)
    """
    if not request.GET.get('term'):
       return HttpResponse(mimetype='text/plain')
    term = request.GET.get('term')
    limit = 50
    try:
        cls = models.get_all_users_and_plmobjects()[obj_type]
    except KeyError:
        return HttpResponseForbidden()
    if field not in cls._meta.get_all_field_names():
        return HttpResponseForbidden()
    results = cls.objects.filter(**{"%s__icontains" % field : term})
    results = results.values_list(field, flat=True).order_by(field).distinct()
    json = JSONEncoder().encode(list(results[:limit]))  
    return HttpResponse(json, mimetype='application/json')

@login_required
@json_view
def ajax_thumbnails(request, obj_type, obj_ref, obj_revi):
    """
    Ajax view to get files and thumbnails of a document.

    :param request: :class:`django.http.QueryDict`
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    """
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    files = []
    doc = "|".join((obj_type, obj_ref, obj_revi))
    for f in obj.files:
        if f.thumbnail:
            img = "/media/thumbnails/%s" % f.thumbnail 
        else:
            img = "/media/img/image-missing.png"
        files.append((f.filename, "/file/%d/" % f.id, img))
    return dict(files=files, doc=doc)


@login_required
@json_view
def ajax_navigate(request, obj_type, obj_ref, obj_revi):
    context = get_navigate_data(request, obj_type, obj_ref, obj_revi)
    data = {
            "img" : context["picture_path"],
            "divs" : context["map_areas"],
            "left" : context["x_img_position"],
            "top" : context["y_img_position"],
            "form" : context["filter_object_form"].as_ul(),
            }
    return data

@login_required
@json_view
def ajax_add_child(request, part_id):
    part = get_obj_by_id(part_id, request.user)
    data = {}
    if request.GET:
        form = AddChildForm(initial=request.GET)
    else:
        form = AddChildForm(request.POST)
        if form.is_valid():
            child = get_obj(form.cleaned_data["type"],
                                form.cleaned_data["reference"],
                                form.cleaned_data["revision"],
                                request.user)
            part.add_child(child, form.cleaned_data["quantity"], 
                           form.cleaned_data["order"])
            return {"result" : "ok"}
        else:
            data["result"] = "error"
            data["error"] = "invalid form"
    for field in ("type", "reference", "revision"):
        form.fields[field].widget.attrs['readonly'] = 'on' 
    data.update({
            "parent" : {
                "id" : part.id,
                "type" : part.type,
                "reference" : part.reference,
                "revision" : part.revision,
                },
            "form" : form.as_table()
           })
    return data

