#-!- coding:utf-8 -!-
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

import os
import re
import datetime
import pygraphviz as pgv
from operator import attrgetter
from mimetypes import guess_type

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.http import HttpResponseRedirect, QueryDict, HttpResponse,\
                        HttpResponsePermanentRedirect, HttpResponseForbidden
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.encoding import iri_to_uri

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController, get_controller, DocumentController, PartController
from openPLM.plmapp.user_controller import UserController
from openPLM.plmapp.exceptions import ControllerError
from openPLM.plmapp.utils import level_to_sign_str, get_next_revision
from openPLM.plmapp.forms import *
from openPLM.plmapp.api import get_obj_by_id


##########################################################################################
def replace_white_spaces(Chain):
    """ Replace all whitespace characteres by %20 in order to be compatible with an URL"""
    return Chain.replace(" ","%20")

##########################################################################################
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
    if obj_type=='User':
        obj = get_object_or_404(User,
                                username=obj_ref)
        controller_cls = UserController
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

##########################################################################################
def init_context_dict(init_type_value, init_reference_value, init_revision_value):
    """
    Initiate the context dictionnary we used to transfer parameters to html pages.
    Get type, reference and revision of an object and return a dictionnary with them
    plus current time, :attr:`settings.THUMBNAILS_URL` the begining of the URL to
    get thumbnail of a file and :attr:`settings.LANGUAGES`.
    
    Example::
    
        >>> init_context_dict('BiosOs','BI-0044','1.4.3')
        {'LANGUAGES': (('fr', u'Fran\xc3\xa7ais'), ('en', 'English')),
         'THUMBNAILS_URL': '/media/thumbnails',
         'current_date': datetime.datetime(2010, 8, 27, 11, 34, 21, 639171),
         'object_reference': 'BI-0044',
         'object_revision': '1.4.3',
         'object_type': 'BiosOs'}
    
    :param init_type_value: type of the object
    :type init_type_value: str
    :param init_reference_value: reference of the object
    :type init_reference_value: str
    :param init_revision_value: revision of the object
    :type init_revision_value: str
    :return: a dictionnary
    """
    now = datetime.datetime.now()
    return {
        'current_date': now,
        'object_reference': init_reference_value,
        'object_revision': init_revision_value,
        'object_type': init_type_value,
        'THUMBNAILS_URL' : settings.THUMBNAILS_URL,
        'LANGUAGES' : settings.LANGUAGES,
        }

##########################################################################################
###   Manage html code for Search and Results function and other global parameters     ###
##########################################################################################

def display_global_page(request_dict, type_value='-', reference_value='-', revision_value='-'):
    """
    Get a request and return a controller, a context dictionnary with elements common to all pages
    (search form, search data, search results, ...) and another dictionnary to update the
    request.session dictionnary.
    
    :param request_dict: :class:`django.http.QueryDict`
    :param type_value: :attr:`.PLMObject.type`
    :type type_value: str
    :param reference_value: :attr:`.PLMObject.reference`
    :type reference_value: str
    :param revision_value: :attr:`.PLMObject.revision`
    :type revision_value: str
    :return: a :class:`PLMObjectController` or a :class:`UserController`
    :return: context_dict
    :type context_dict: dic
    :return: request_dict.session
    :type request_dict.session: dic
    """
    context_dict = init_context_dict(type_value, reference_value, revision_value)
    # This case happens when we create an object (and therefore can't get a controller)
    if type_value=='-' and reference_value=='-' and revision_value=='-':
        selected_object = request_dict.user
    else:
        selected_object = get_obj(type_value, reference_value, revision_value, request_dict.user)
    # Defines a variable for background color selection
    if isinstance(selected_object, UserController):
        class_for_div="NavigateBox4User"
    elif isinstance(selected_object, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    qset=[]
    # Builds, update and treat Search form
    if request_dict.GET and "type" in request_dict.GET:
        type_form_instance = type_form(request_dict.GET)
        if type_form_instance.is_valid():
            cls = models.get_all_users_and_plmobjects()[type_form_instance.cleaned_data["type"]]
        attributes_form_instance = get_search_form(cls, request_dict.GET)
        for key, value in request_dict.GET.items():
            request_dict.session[key] = value
    elif request_dict.session and "type" in request_dict.session:
        type_form_instance = type_form(request_dict.session)
        cls = models.get_all_users_and_plmobjects()[request_dict.session["type"]]
        attributes_form_instance = get_search_form(cls, request_dict.session)
    else:
        type_form_instance = type_form()
        request_dict.session['type'] = 'Part'
        cls = models.get_all_users_and_plmobjects()['Part']
        attributes_form_instance = get_search_form(cls)
    if attributes_form_instance.is_valid():
        qset = cls.objects.all()
        qset = attributes_form_instance.search(qset)[:30]
    if qset is None:
        qset = []
    if issubclass(cls, User):
        qset = (UserController(u, request_dict.user) for u in qset)
    else :
        request_dict.session["results"] = qset
    context_dict.update({'results': qset, 'type_form': type_form_instance, 'attributes_form': attributes_form_instance, 'class4search_div': 'DisplayHomePage.htm', 'class4div': class_for_div})
    return selected_object, context_dict, request_dict.session


##########################################################################################
###                    Function which manage the html home page                        ###
##########################################################################################
@login_required
def display_home_page(request):
    """
    Once the user is logged in, redirection to his/her own user object with :func:navigate
    """
    return HttpResponseRedirect("/user/%s/navigate/" % request.user)

#############################################################################################
###All functions which manage the different html pages related to a part, a doc and a user###
#############################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    object_attributes_list = []
    for attr in obj.attributes:
        item = obj.get_verbose_name(attr)
        object_attributes_list.append((item, getattr(obj, attr)))
    if isinstance(obj, UserController):
        item = obj.get_verbose_name('rank')
        object_attributes_list.append((item, getattr(obj, 'rank')))
    context_dict.update({'current_page':'attributes', 'object_menu': menu_list, 'object_attributes': object_attributes_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObject.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required
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
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    if request.method == 'POST':
        if request.POST["action"] == "DEMOTE":
            obj.demote()
        elif request.POST["action"] == "PROMOTE":
            obj.promote()
    menu_list = obj.menu_items
    state = obj.state.name
    lifecycle = obj.lifecycle
    object_lifecycle_list = []
    for st in lifecycle:
        object_lifecycle_list.append((st, st == state))
    context_dict.update({'current_page':'lifecycle', 'object_menu': menu_list, 'object_lifecycle': object_lifecycle_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectLifecycle.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
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
    context_dict.update({'current_page':'revisions', 'object_menu': menu_list, 'revisions': revisions,
                         'add_revision_form' : add_form})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectRevisions.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    if isinstance(obj, UserController):
        histos = models.UserHistory.objects.filter(plmobject=obj.object).order_by('date')
    elif isinstance(obj, DocumentController):
        histos = models.History.objects.filter(plmobject=obj.object).order_by('date')
    else:
        histos = models.History.objects.filter(plmobject=obj.object).order_by('date')
    menu_list = obj.menu_items
    object_history_list = []
    for histo in histos:
        object_history_list.append((histo.date, histo.action, histo.details))
    context_dict.update({'current_page':'history', 'object_menu': menu_list, 'object_history': object_history_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectHistory.htm', context_dict, context_instance=RequestContext(request))

#############################################################################################
###         All functions which manage the different html pages specific to part          ###
#############################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
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

    context_dict.update({'current_page':'BOM-child', 'object_menu': menu_list, 'obj' : obj,
                                 'children': children, "display_form" : display_form})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectChild.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
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
    context_dict.update({'current_page':'BOM-child', 'object_menu': menu_list, 'obj' : obj,
                                 'children_formset': formset, })
    request.session.update(request_dict)
    return render_to_response('DisplayObjectChildEdit.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################    
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    request.session.update(request_dict)
    menu_list = obj.menu_items
    if request.POST:
        add_child_form_instance = add_child_form(request.POST)
        if add_child_form_instance.is_valid():
            child_obj = get_obj(add_child_form_instance.cleaned_data["type"], \
                        add_child_form_instance.cleaned_data["reference"], \
                        add_child_form_instance.cleaned_data["revision"],
                        request.user)
            obj.add_child(child_obj, \
                            add_child_form_instance.cleaned_data["quantity"], \
                            add_child_form_instance.cleaned_data["order"])
            context_dict.update({'object_menu': menu_list, 'add_child_form': add_child_form_instance, })
            return HttpResponseRedirect(obj.plmobject_url + "BOM-child/") 
        else:
            add_child_form_instance = add_child_form(request.POST)
            context_dict.update({'class4search_div': 'DisplayHomePage4Addition.htm', 'object_menu': menu_list, 'add_child_form': add_child_form_instance, })
            return render_to_response('DisplayObjectChildAdd.htm', context_dict, context_instance=RequestContext(request))
    else:
        add_child_form_instance = add_child_form()
        context_dict.update({'current_page':'BOM-child', 'class4search_div': 'DisplayHomePage4Addition.htm', 'object_menu': menu_list, 'add_child_form': add_child_form_instance, })
        return render_to_response('DisplayObjectChildAdd.htm', context_dict, context_instance=RequestContext(request))
    
##########################################################################################    
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
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
    context_dict.update({'current_page':'parents', 'object_menu': menu_list, 'parents' :  parents,
                                 'display_form' : display_form, 'obj': obj})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectParents.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
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
    context_dict.update({'current_page':'doc-cad', 'object_menu': menu_list, 'object_doc_cad': object_doc_cad_list, 'doc_cad_formset': formset})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectDocCad.htm', context_dict, context_instance=RequestContext(request))


##########################################################################################    
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    request.session.update(request_dict)
    if request.POST:
        add_doc_cad_form_instance = AddDocCadForm(request.POST)
        if add_doc_cad_form_instance.is_valid():
            doc_cad_obj = get_obj(add_doc_cad_form_instance.cleaned_data["type"], \
                        add_doc_cad_form_instance.cleaned_data["reference"], \
                        add_doc_cad_form_instance.cleaned_data["revision"],\
                        request.user)
            obj.attach_to_document(doc_cad_obj)
            context_dict.update({'object_menu': menu_list, 'add_doc_cad_form': add_doc_cad_form_instance, })
            return HttpResponseRedirect(obj.plmobject_url + "doc-cad/")
        else:
            add_doc_cad_form_instance = AddDocCadForm(request.POST)
            context_dict.update({'class4search_div': 'DisplayHomePage4Addition.htm', 'class4div': class_for_div, 'object_menu': menu_list, 'add_doc_cad_form': add_doc_cad_form_instance, })
            return render_to_response('DisplayDocCadAdd.htm', context_dict, context_instance=RequestContext(request))
    else:
        add_doc_cad_form_instance = AddDocCadForm()
        context_dict.update({'class4search_div': 'DisplayHomePage4Addition.htm', 'object_menu': menu_list, 'add_doc_cad_form': add_doc_cad_form_instance, })
        return render_to_response('DisplayDocCadAdd.htm', context_dict, context_instance=RequestContext(request))
    
#############################################################################################
###      All functions which manage the different html pages specific to documents        ###
#############################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
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
    context_dict.update({'current_page':'parts', 'object_menu': menu_list, 'object_rel_part': object_rel_part_list, 'rel_part_formset': formset})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectRelPart.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################    
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    request.session.update(request_dict)
    if request.POST:
        add_rel_part_form_instance = AddRelPartForm(request.POST)
        if add_rel_part_form_instance.is_valid():
            part_obj = get_obj(add_rel_part_form_instance.cleaned_data["type"], \
                        add_rel_part_form_instance.cleaned_data["reference"], \
                        add_rel_part_form_instance.cleaned_data["revision"], request.user)
            obj.attach_to_part(part_obj)
            context_dict.update({'object_menu': menu_list, 'add_rel_part_form': add_rel_part_form_instance, })
            return HttpResponseRedirect(obj.plmobject_url + "parts/")
        else:
            add_rel_part_form_instance = add_rel_part_form(request.POST)
            context_dict.update({'class4search_div': 'DisplayHomePage4Addition.htm', 'object_menu': menu_list, 'add_rel_part_form': add_rel_part_form_instance, })
            return render_to_response('DisplayRelPartAdd.htm', context_dict, context_instance=RequestContext(request))
    else:
        add_rel_part_form_instance = AddRelPartForm()
        context_dict.update({'class4search_div': 'DisplayHomePage4Addition.htm',
                             'object_menu': menu_list, 'add_rel_part_form': add_rel_part_form_instance, })
        return render_to_response('DisplayRelPartAdd.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items

    if not hasattr(obj, "files"):
        # TODO
        raise TypeError()
    if request.method == "POST":
        formset = get_file_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_file(formset)
            return HttpResponseRedirect(".")
    else:
        formset = get_file_formset(obj)
    is_owner_bool = (request.user == models.PLMObject.objects.get(type=obj_type, \
                                        reference=obj_ref, revision=obj_revi).owner)
    object_files_list = obj.files
    context_dict.update({'is_owner':is_owner_bool, 'current_page':'files', 'object_menu': menu_list, 'object_files': object_files_list, 'file_formset': formset})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectFiles.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    request.session.update(request_dict)
    if request.POST:
        add_file_form_instance = AddFileForm(request.POST, request.FILES)
        if add_file_form_instance.is_valid():
            obj.add_file(request.FILES["filename"])
            context_dict.update({'object_menu': menu_list, 'add_file_form': add_file_form_instance, })
            return HttpResponseRedirect(obj.plmobject_url + "files/")
        else:
            add_file_form_instance = AddFileForm(request.POST)
            context_dict.update({'class4search_div': 'DisplayHomePage4Addition.htm', 'object_menu': menu_list, 'add_file_form': add_file_form_instance, })
            return render_to_response('DisplayRelPartAdd.htm', context_dict, context_instance=RequestContext(request))
    else:
        add_file_form_instance = AddFileForm()
        context_dict.update({'class4search_div': 'DisplayHomePage4Addition.htm', 'object_menu': menu_list, 'add_file_form': add_file_form_instance, })
        return render_to_response('DisplayFileAdd.htm', context_dict, context_instance=RequestContext(request))

#############################################################################################
###    All functions which manage the different html pages specific to part and document  ###
#############################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    object_management_list = models.PLMObjectUserLink.objects.filter(plmobject=obj)
    object_management_list = object_management_list.order_by("role")
    context_dict.update({'current_page':'management', 'object_menu': menu_list, 'object_management': object_management_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectManagement.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    link = models.PLMObjectUserLink.objects.get(id=int(link_id))
    assert obj.object.id == link.plmobject.id
    menu_list = obj.menu_items
    if request.method == "POST":
#        if request.POST.get("action", "Undo") == "Undo":
#            return HttpResponseRedirect("/home/")
        replace_management_form_instance = replace_management_form(request.POST)
        if replace_management_form_instance.is_valid():
            if replace_management_form_instance.cleaned_data["type"]=="User":
                user_obj = get_obj(\
                                    replace_management_form_instance.cleaned_data["type"],\
                                    replace_management_form_instance.cleaned_data["username"],\
                                    "-",\
                                    request.user)
                obj.set_role(user_obj.object, link.role)
                obj.remove_notified(link.user)
                return HttpResponseRedirect("../..")
            else:
                return HttpResponseRedirect("../..")
        else:
            replace_management_form_instance = replace_management_form(request.POST)
    else:
        replace_management_form_instance = replace_management_form()
    request.session.update(request_dict)
    context_dict.update({'current_page':'management', 'object_menu': menu_list, 'obj' : obj,
                                 'replace_management_form': replace_management_form_instance,
                                 'class4search_div': 'DisplayHomePage4Addition.htm',})
    return render_to_response('DisplayObjectManagementReplace.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################    
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    if request.method == "POST":
#        if request.POST.get("action", "Undo") == "Undo":
#            return HttpResponseRedirect("/home/")
        add_management_form_instance = replace_management_form(request.POST)
        if add_management_form_instance.is_valid():
            if add_management_form_instance.cleaned_data["type"]=="User":
                user_obj = get_obj(\
                                    add_management_form_instance.cleaned_data["type"],\
                                    add_management_form_instance.cleaned_data["username"],\
                                    "-",\
                                    request.user)
                obj.set_role(user_obj.object, "notified")
                return HttpResponseRedirect("..")
            else:
                return HttpResponseRedirect("..")
        else:
            add_management_form_instance = replace_management_form(request.POST)
    else:
        add_management_form_instance = replace_management_form()
    request.session.update(request_dict)
    context_dict.update({'current_page':'management', 'object_menu': menu_list, 'obj' : obj,
                                 'replace_management_form': add_management_form_instance,
                                 'class4search_div': 'DisplayHomePage4Addition.htm',})
    return render_to_response('DisplayObjectManagementReplace.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################    
@login_required
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
def create_non_modifyable_attributes_list(Classe=models.PLMObject):
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
    non_modifyable_attributes_list.append((non_modifyable_fields_list[0], 'Person'))
    non_modifyable_attributes_list.append((non_modifyable_fields_list[1], 'Person'))
    non_modifyable_attributes_list.append((non_modifyable_fields_list[2], 'Date'))
    non_modifyable_attributes_list.append((non_modifyable_fields_list[3], 'Date'))
    return non_modifyable_attributes_list

##########################################################################################
@login_required
def create_object(request):
    """
    Manage html page for the creation of an instance of `models.PLMObject` subclass.
    It computes a context dictionnary based on
    
    :param request: :class:`django.http.QueryDict`
    :return: a :class:`django.http.HttpResponse`
    """
#    context_dict, request_dict = display_global_page(request)
    obj, context_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    if request.method == 'GET':
        if request.GET:
            type_form_instance = type_form(request.GET)
            if type_form_instance.is_valid():
                cls = models.get_all_userprofiles_and_plmobjects()[type_form_instance.cleaned_data["type"]]
                if issubclass(cls, models.Document):
                    class_for_div="NavigateBox4Doc"
                else:
                    class_for_div="NavigateBox4Part"
                creation_form_instance = get_creation_form(cls, {'revision':'a', 'lifecycle': str(models.get_default_lifecycle()), }, True)
                non_modifyable_attributes_list = create_non_modifyable_attributes_list(cls)
    elif request.method == 'POST':
        if request.POST:
            type_form_instance = type_form(request.POST)
            if type_form_instance.is_valid():
                type_name = type_form_instance.cleaned_data["type"]
                cls = models.get_all_userprofiles_and_plmobjects()[type_name]
                if issubclass(cls, models.Document):
                    class_for_div="NavigateBox4Doc"
                else:
                    class_for_div="NavigateBox4Part"
                non_modifyable_attributes_list = create_non_modifyable_attributes_list(cls)
                creation_form_instance = get_creation_form(cls, request.POST)
                if creation_form_instance.is_valid():
                    user = request.user
                    controller_cls = get_controller(type_name)
                    controller = PLMObjectController.create_from_form(creation_form_instance, user)
                    return HttpResponseRedirect(controller.plmobject_url)
    context_dict.update({'class4div': class_for_div, 'creation_form': creation_form_instance, 'object_type': type_form_instance.cleaned_data["type"], 'non_modifyable_attributes': non_modifyable_attributes_list })
    return render_to_response('DisplayObject4creation.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required
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
    current_object, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    if obj_type=='User':
        cls = models.get_all_plmobjects()['UserProfile']
    else:
        cls = models.get_all_plmobjects()[obj_type]
    non_modifyable_attributes_list = create_non_modifyable_attributes_list(cls)
    if request.method == 'POST':
        if request.POST:
            modification_form_instance = get_modification_form(cls, request.POST)
            if modification_form_instance.is_valid():
                current_object.update_from_form(modification_form_instance)
                return HttpResponseRedirect(current_object.plmobject_url)
            else:
                pass
        else:
            modification_form_instance = get_modification_form(cls, instance = current_object.object)
    else:
        modification_form_instance = get_modification_form(cls, instance = current_object.object)
    request.session.update(request_dict)
    context_dict.update({'modification_form': modification_form_instance, 'non_modifyable_attributes': non_modifyable_attributes_list})
    return render_to_response('DisplayObject4modification.htm', context_dict, context_instance=RequestContext(request))

#############################################################################################
###         All functions which manage the different html pages specific to user          ###
#############################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    current_object = get_obj(obj_type, obj_ref, obj_revi, request.user)
    class_for_div="NavigateBox4User"
    if request.method == 'POST':
        if request.POST:
            modification_form_instance = OpenPLMUserChangeForm(request.POST)
            if modification_form_instance.is_valid():
                current_object.update_from_form(modification_form_instance)
                return HttpResponseRedirect("/user/%s/" % current_object.username)
            else:
                modification_form_instance = OpenPLMUserChangeForm(request.POST)
    else:
        modification_form_instance = OpenPLMUserChangeForm(instance=current_object.object)
    request.session.update(request_dict)
    context_dict.update({'class4div': class_for_div, 'modification_form': modification_form_instance})
    return render_to_response('DisplayObject4modification.htm', context_dict, context_instance=RequestContext(request))
    
##########################################################################################
@login_required
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
    current_object, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    class_for_div="NavigateBox4User"
    if request.method == 'POST':
        if request.POST:
            modification_form_instance = PasswordChangeForm(current_object, request.POST)
            if modification_form_instance.is_valid():
                current_object.set_password(modification_form_instance.cleaned_data['new_password2'])
                current_object.save()
                return HttpResponseRedirect("/user/%s/" % current_object.username)
            else:
                #assert False
                modification_form_instance = PasswordChangeForm(current_object, request.POST)
    else:
        modification_form_instance = PasswordChangeForm(current_object)
    request.session.update(request_dict)
    context_dict.update({'class4div': class_for_div, 'modification_form': modification_form_instance})
    return render_to_response('DisplayObject4PasswordModification.htm', context_dict, context_instance=RequestContext(request))

#############################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    if not hasattr(obj, "get_object_user_links"):
        # TODO
        raise TypeError()
    object_user_link_list = obj.get_object_user_links()
    context_dict.update({'current_page':'parts-doc-cad', 'object_menu': menu_list, 'object_user_link': object_user_link_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectRelPLMObject.htm', context_dict, context_instance=RequestContext(request))

#############################################################################################
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    if not hasattr(obj, "get_user_delegation_links"):
        # TODO
        raise TypeError()
    if request.method == "POST":
        selected_link_id = request.POST.get('link_id')
        obj.remove_delegation(models.DelegationLink.objects.get(pk=int(selected_link_id)))
    user_delegation_link_list = obj.get_user_delegation_links()
    context_dict.update({'current_page':'delegation', 'object_menu': menu_list, 'user_delegation_link': user_delegation_link_list})
    request.session.update(request_dict)
    return render_to_response('DisplayObjectDelegation.htm', context_dict, context_instance=RequestContext(request))


##########################################################################################    
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    if request.method == "POST":
#        if request.POST.get("action", "Undo") == "Undo":
#            return HttpResponseRedirect("/home/")
        delegation_form_instance = replace_management_form(request.POST)
        if delegation_form_instance.is_valid():
            if delegation_form_instance.cleaned_data["type"]=="User":
                user_obj = get_obj(\
                                    delegation_form_instance.cleaned_data["type"],\
                                    delegation_form_instance.cleaned_data["username"],\
                                    "-",\
                                    request.user)
                if role=="notified" or role=="owner":
                    obj.delegate(user_obj.object, role)
                    return HttpResponseRedirect("../..")
                elif role=="sign":
                    if sign_level=="all":
                        obj.delegate(user_obj.object, "sign*")
                        return HttpResponseRedirect("../../..")
                    elif sign_level.isdigit():
                        obj.delegate(user_obj.object, level_to_sign_str(int(sign_level)-1))
                        return HttpResponseRedirect("../../..")
                    else:
                        delegation_form_instance = replace_management_form(request.POST)
                else:
                     delegation_form_instance = replace_management_form(request.POST)
            else:
                delegation_form_instance = replace_management_form(request.POST)
        else:
            delegation_form_instance = replace_management_form(request.POST)
    else:
        delegation_form_instance = replace_management_form()
    action_message_string="Select a user for your \"%s\" role delegation :" % role
    request.session.update(request_dict)
    context_dict.update({'current_page':'delegation',
                                 'object_menu': menu_list, 'obj' : obj,
                                 'replace_management_form': delegation_form_instance,
                                 'class4search_div': 'DisplayHomePage4Addition.htm',
                                 'action_message': action_message_string})
    return render_to_response('DisplayObjectManagementReplace.htm', context_dict, context_instance=RequestContext(request))
    
##########################################################################################    
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    if request.method == "POST":
#        if request.POST.get("action", "Undo") == "Undo":
#            return HttpResponseRedirect("/home/")
        delegation_form_instance = replace_management_form(request.POST)
        if delegation_form_instance.is_valid():
            if delegation_form_instance.cleaned_data["type"]=="User":
                user_obj = get_obj(\
                                    add_management_form_instance.cleaned_data["type"],\
                                    add_management_form_instance.cleaned_data["username"],\
                                    "-",\
                                    request.user)
                if role=="notified":
                    obj.set_role(user_obj.object, "notified")
                    return HttpResponseRedirect("..")
                elif role=="owner":
                    return HttpResponseRedirect("..")
                    pass
                elif role=="sign":
                    if sign_level=="all":
                        return HttpResponseRedirect("..")
                        pass
                    elif sign_level.is_digit():
                        return HttpResponseRedirect("../..")
                        pass
                    else:
                        delegation_form_instance = replace_management_form(request.POST)
                else:
                     delegation_form_instance = replace_management_form(request.POST)
            else:
                delegation_form_instance = replace_management_form(request.POST)
        else:
            delegation_form_instance = replace_management_form(request.POST)
    else:
        delegation_form_instance = replace_management_form()
    action_message_string="Select the user you no longer want for your \"%s\" role delegation :" % role
    request.session.update(request_dict)
    context_dict.update({'current_page':'parts-doc-cad',
                                 'object_menu': menu_list, 'obj' : obj,
                                 'replace_management_form': delegation_form_instance,
                                 'class4search_div': 'DisplayHomePage4Addition.htm',
                                 'action_message': action_message_string})
    return render_to_response('DisplayObjectManagementReplace.htm', context_dict, context_instance=RequestContext(request))
    
##########################################################################################
###             Manage html pages for file check-in / check-out / download             ###
##########################################################################################    
@login_required
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    menu_list = obj.menu_items
    request.session.update(request_dict)
    if request.POST :
        checkin_file_form_instance = AddFileForm(request.POST, request.FILES)
        if checkin_file_form_instance.is_valid():
            obj.checkin(models.DocumentFile.objects.get(id=file_id_value), request.FILES["filename"])
            context_dict.update({'object_menu': menu_list, })
            return HttpResponseRedirect(obj.plmobject_url + "files/")
        else:
            checkin_file_form_instance = AddFileForm(request.POST)
            context_dict.update({'class4search_div': 'DisplayHomePage4Addition.htm', \
                                 'object_menu': menu_list, 'add_file_form': add_file_form_instance, })
            return render_to_response('DisplayFileAdd.htm', context_dict, context_instance=RequestContext(request))
    else:
        checkin_file_form_instance = AddFileForm()
        context_dict.update({'class4search_div': 'DisplayHomePage4Addition.htm',                             'object_menu': menu_list, 'add_file_form': checkin_file_form_instance, })
        return render_to_response('DisplayFileAdd.htm', context_dict, context_instance=RequestContext(request))

##########################################################################################
@login_required 
def download(request, docfile_id):
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
    response['Content-Disposition'] = 'attachment; filename="%s"' % name
    return response
    
##########################################################################################
@login_required 
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
regex_pattern = re.compile(r'coords\=\"(\d{1,5}),(\d{1,5}),(\d{1,5}),(\d{1,5})')
@login_required
    
def navigate(request, obj_type, obj_ref, obj_revi):
    """
    Manage html page which displays a graphical picture the different links
    between :class:`~django.contrib.auth.models.User` and  :class:`.models.PLMObject`.
    This function uses Graphviz (http://graphviz.org/).
    Some filters let user defines which type of links he/she wants to display.
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
    obj, context_dict, request_dict = display_global_page(request, obj_type, obj_ref, obj_revi)
    request.session.update(request_dict)
    if isinstance(obj, UserController):
        FilterObjectFormFunction = FilterObjectForm4User
        first_node_color = '#94bd5e'
        first_node_label = obj.user.username.encode('utf-8')
        first_node_url = "/user/"+obj.user.username.encode('utf-8')+"/navigate/"
    elif isinstance(obj, DocumentController):
        FilterObjectFormFunction = FilterObjectForm4Doc
        first_node_color = '#fef176'
        first_node_label = obj.type.encode('utf-8')\
                            +"\\n"+obj.reference.encode('utf-8')\
                            +"\\n"+obj.revision.encode('utf-8')
        first_node_url = "/object/"+obj.type.encode('utf-8')\
                            +"/"+obj.reference.encode('utf-8')\
                            +"/"+obj.revision.encode('utf-8')+"/navigate/"
    else:
        FilterObjectFormFunction = FilterObjectForm4Part
        first_node_color = '#5588bb'
        first_node_label = obj.type.encode('utf-8')\
                            +"\\n"+obj.reference.encode('utf-8')\
                            +"\\n"+obj.revision.encode('utf-8')
        first_node_url = "/object/"+obj.type.encode('utf-8')\
                            +"/"+obj.reference.encode('utf-8')\
                            +"/"+obj.revision.encode('utf-8')+"/navigate/"
    session_bool = False
    for field in FilterObjectFormFunction.base_fields.keys():
        session_bool = session_bool or request.session.get(field)
    if request.method == 'POST' and request.POST:
        filter_object_form_instance = FilterObjectFormFunction(request.POST)
        for key, value in request.POST.items():
            request.session[key] = value
    elif session_bool :
        filter_object_form_instance = FilterObjectFormFunction(request.session)
    else:
        filter_object_form_instance = FilterObjectFormFunction(FilterObjectFormFunction.data)
        for key, value in FilterObjectFormFunction.data.items():
            request.session[key] = value
    if not filter_object_form_instance.is_valid():
        return HttpResponse('mauvaise requete post')
    else :
        navigate_graph=pgv.AGraph()
        navigate_graph.clear()
        navigate_graph.graph_attr.update(dpi='96.0', aspect='2', size='16.28, 8.88',\
                                            center='true', ranksep='1.2', pad='0.1')
        navigate_graph.node_attr.update(shape='none', fixedsize='true', fontsize='10',\
                                            style='filled', width='1.0', height='0.6')
        navigate_graph.edge_attr.update(color='#000000', len='1.5', arrowhead='normal')
        navigate_graph.node_attr.update(image="media/img/part.png", color='#99ccff', shape='none')
        def create_child_edges(object_id, arg):
            object_item = get_obj_by_id(object_id, request.user)
            children_list = object_item.get_children()
            navigate_graph.node_attr.update(image="media/img/part.png", color='#99ccff', shape='none')
            for children in children_list:
                child_id = children.link.child.id
                navigate_graph.add_edge(object_id, child_id)
                child_node = navigate_graph.get_node(child_id)
                child_node.attr['label'] = children.link.child.type.encode('utf-8')\
                                            +"\\n"+children.link.child.reference.encode('utf-8')\
                                            +"\\n"+children.link.child.revision.encode('utf-8')
                child_node.attr['URL'] = "/object/"+children.link.child.type.encode('utf-8')\
                                            +"/"+children.link.child.reference.encode('utf-8')\
                                            +"/"+children.link.child.revision.encode('utf-8')+"/navigate/"
                if filter_object_form_instance.cleaned_data.get('doc') :
                    create_doc_edges(child_id, 'none')
                create_child_edges(child_id, arg)
        def create_parents_edges(object_id, arg):
            object_item = get_obj_by_id(object_id, request.user)
            parent_list = object_item.get_parents()
            navigate_graph.node_attr.update(image="media/img/part.png", color='#99ccff', shape='none')
            for parent in parent_list:
                parent_id = parent.link.parent.id
                navigate_graph.add_edge(parent_id, object_id)
                parent_node = navigate_graph.get_node(parent_id)
                parent_node.attr['label'] = parent.link.parent.type.encode('utf-8')\
                                            +"\\n"+parent.link.parent.reference.encode('utf-8')\
                                            +"\\n"+parent.link.parent.revision.encode('utf-8')
                parent_node.attr['URL'] = "/object/"+parent.link.parent.type.encode('utf-8')\
                                            +"/"+parent.link.parent.reference.encode('utf-8')\
                                            +"/"+parent.link.parent.revision.encode('utf-8')+"/navigate/"
                if filter_object_form_instance.cleaned_data['doc'] :
                    create_doc_edges(parent_id, 'none')
                create_parents_edges(parent_id, 'none')
        def create_part_edges(object_id, arg):
            object_item = get_obj_by_id(object_id, request.user)
            part_list = object_item.get_attached_parts()
            navigate_graph.node_attr.update(image="media/img/part.png", color='#99ccff', shape='none')
            for link in part_list:
                part_id = link.part_id
                navigate_graph.add_edge(object_id, part_id)
                part_node = navigate_graph.get_node(part_id)
                part_node.attr['label'] = link.part.type.encode('utf-8')\
                                            +"\\n"+link.part.reference.encode('utf-8')\
                                            +"\\n"+link.part.revision.encode('utf-8')
                part_node.attr['URL'] = "/object/"+link.part.type.encode('utf-8')\
                                            +"/"+link.part.reference.encode('utf-8')\
                                            +"/"+link.part.revision.encode('utf-8')+"/navigate/"
        def create_doc_edges(object_id, arg):
            object_item = get_obj_by_id(object_id, request.user)
            document_list = object_item.get_attached_documents()
            navigate_graph.node_attr.update(image="none", color='#fef176', shape='note')
            for document_item in document_list:
                document_id = document_item.document.id
                navigate_graph.add_edge(object_id, document_id)
                document_node = navigate_graph.get_node(document_id)
                document_node.attr['label'] = document_item.document.type.encode('utf-8')\
                                            +"\\n"+document_item.document.reference.encode('utf-8')\
                                            +"\\n"+document_item.document.revision.encode('utf-8')
                document_node.attr['URL'] = "/object/"+document_item.document.type.encode('utf-8')\
                                            +"/"+document_item.document.reference.encode('utf-8')\
                                            +"/"+document_item.document.revision.encode('utf-8')\
                                            +"/navigate/"
        def create_user_edges(object_id, required_role):
            object_item = get_obj_by_id(object_id, request.user)
            user_list = object_item.plmobjectuserlink_plmobject.filter(role__istartswith=required_role)
            navigate_graph.node_attr.update(image="none", color='#94bd5e', shape='note')
            for user_item in user_list:
                user_id = str(user_item.role)+str(user_item.user.id)
                navigate_graph.add_edge(user_id, object_id)
                user_node = navigate_graph.get_node(user_id)
                user_node.attr['label'] = user_item.user.username.encode('utf-8')\
                                            +"\\n"+user_item.role.encode('utf-8')
                user_node.attr['URL'] = "/user/"+user_item.user.username.encode('utf-8')+"/navigate/"
        def create_object_edges(object_id, required_role):
            object_item = User.objects.get(pk=object_id)
            part_doc_list = object_item.plmobjectuserlink_user.filter(role__istartswith=required_role)
            for part_doc_item in part_doc_list:
                part_doc_id = str(part_doc_item.role)+str(part_doc_item.plmobject_id)
                navigate_graph.add_edge(object_id, part_doc_id)
                part_doc_node = navigate_graph.get_node(part_doc_id)
                if hasattr(part_doc_item.plmobject, 'document'):
                    part_doc_node.attr.update(image='none', color='#fef176', shape='note')
                else:
                    part_doc_node.attr.update(image="media/img/part.png", color='#99ccff', shape='none')
                part_doc_node.attr['label'] = part_doc_item.plmobject.type.encode('utf-8')\
                                            +"\\n"+part_doc_item.plmobject.reference.encode('utf-8')\
                                            +"\\n"+part_doc_item.plmobject.revision.encode('utf-8')
                part_doc_node.attr['URL'] = "/object/"+part_doc_item.plmobject.type.encode('utf-8')\
                                            +"/"+part_doc_item.plmobject.reference.encode('utf-8')\
                                            +"/"+part_doc_item.plmobject.revision.encode('utf-8')+"/navigate/"
        part_id = obj.id
        navigate_graph.add_node(part_id)
        part_node = navigate_graph.get_node(part_id)
        part_node.attr.update(root='true', color=first_node_color, label=first_node_label,\
                                URL=first_node_url, shape='box')
        basedir = os.path.dirname(__file__)
        if isinstance(obj, PartController):
            part_node.attr['image'] = os.path.join(basedir, "..", "media/img/part.png")
        picture_path = "media/navigate/" + str(obj.id)+"-"
        functions_dic = {'child':(create_child_edges, 'none'),
                         'parents':(create_parents_edges, 'none'),
                         'doc':(create_doc_edges, 'none'),
                         'cad':(create_doc_edges, 'none'),
                         'owner':(create_user_edges, 'owner'),
                         'signer':(create_user_edges, 'sign'),
                         'notified':(create_user_edges, 'notified'),
                         'part': (create_part_edges, 'none'),
                         'owned':(create_object_edges, 'owner'),
                         'to_sign':(create_object_edges, 'sign'),
                         'request_notification_from':(create_object_edges, 'notified'),}
        for field in FilterObjectFormFunction.base_fields.keys():
            if filter_object_form_instance.cleaned_data[field] : 
                function, argument = functions_dic[field]
                function(part_id, argument)
            picture_path+=str(int(filter_object_form_instance.cleaned_data[field]))
        navigate_graph.layout()
        picture_path2 = os.path.join(basedir, "..", picture_path)
        map_path= picture_path2 + ".map"
        dot_path= picture_path2 + ".dot"
        picture_path +=".gif"
        picture_path2 +=".gif"
        navigate_graph.draw(dot_path, format='dot', prog='dot')
        navigate_graph.draw(picture_path2, format='gif', prog='neato')
        navigate_graph.draw(map_path, format='cmapx', prog='neato')
        file_object = open(map_path,"rb",0)
        map_string = file_object.read()
        file_object.close()
        x_1st_point, y_1st_point, x_2nd_point, y_2nd_point = re.search(regex_pattern, map_string).groups()
        x_part_node_position = (int(x_1st_point)+int(x_2nd_point))/2
        y_part_node_position = (int(y_1st_point)+int(y_2nd_point))/2
        x_img_position_corrected = 790/2 - int(x_part_node_position) -100
        y_img_position_corrected = 405/2 - int(y_part_node_position)
        context_dict.update({'filter_object_form': filter_object_form_instance ,\
                            'map_areas': map_string, 'picture_path': "/"+picture_path,\
                             'x_img_position': int(x_img_position_corrected),\
                             'y_img_position': int(y_img_position_corrected)})
        navigate_graph.clear()
        return render_to_response('Navigate.htm', context_dict, context_instance=RequestContext(request))
        
        
        
        
        
        
