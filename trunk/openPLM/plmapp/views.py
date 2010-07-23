import os
from django.shortcuts import render_to_response, get_object_or_404
import datetime
from operator import attrgetter
from mimetypes import guess_type

from django.conf import settings

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController, get_controller, DocumentController

from django.db.models import Q
from django.http import HttpResponseRedirect, QueryDict, HttpResponse, HttpResponsePermanentRedirect

from openPLM.plmapp.forms import *
from openPLM.plmapp.utils import get_next_revision

from django.contrib import auth
from django.contrib.auth.decorators import login_required

import pygraphviz as pgv

from openPLM.plmapp.api import get_obj_by_id

import Image

##########################################################################################
def replace_white_spaces(Chain):
    """ Replace all whitespace characteres by %20 in order to be compatible with an URL"""
    return Chain.replace(" ","%20")

##########################################################################################
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

##########################################################################################
def init_context_dict(init_type_value, init_reference_value, init_revision_value):
    """ Initiate context_dict we used after to transfer parameters to html pages"""
    now = datetime.datetime.now()
    return {
        'current_date': now,
        'object_reference': init_reference_value,
        'object_revision': init_revision_value,
        'object_type': init_type_value,
        'THUMBNAILS_URL' : settings.THUMBNAILS_URL,
        }

##########################################################################################
###                   Manage html pages for Home Page                                  ###
##########################################################################################

def display_global_page(request_dict):
    """ Get a request and return a dictionnary with elements common to all pages """
#    log_in_person="pjoulaud"
    context_dict = {'log_in_person' : request_dict.user}
    query_dict = {}
    request_dict.session['type'] = 'Part'
    attributes_form_instance = attributes_form()
    extra_attributes_form_instance = get_search_form()
    results=[]
    if request_dict.GET and "type" in request_dict.GET:
        type_form_instance = type_form(request_dict.GET)
        attributes_form_instance = attributes_form(request_dict.GET)
        for key, value in request_dict.GET.items():
            request_dict.session[key] = value
        if attributes_form_instance.is_valid():
            cls = models.get_all_plmobjects()[attributes_form_instance.cleaned_data["type"]]
            extra_attributes_form_instance = get_search_form(cls, request_dict.GET)
            for field, value in attributes_form_instance.cleaned_data.items():
                if value and field != "type":
                    query_dict["%s__icontains"%field]=value
            results = cls.objects.filter(**query_dict)
            request_dict.session["results"] = results
            query_dict = {}
            if extra_attributes_form_instance.is_valid():
                for field, value in extra_attributes_form_instance.cleaned_data.items():
                    if value:
                        query_dict[field]=value
                results = extra_attributes_form_instance.search(results)
                request_dict.session["results"] = results
    elif request_dict.session:
        type_form_instance = type_form(request_dict.session)
        attributes_form_instance = attributes_form(request_dict.session)
#        request_dict.session.update(request_dict.session)
        if attributes_form_instance.is_valid():
            cls = models.get_all_plmobjects()[attributes_form_instance.cleaned_data["type"]]
            extra_attributes_form_instance = get_search_form(cls, request_dict.session)
            for field, value in attributes_form_instance.cleaned_data.items():
                if value and field != "type":
                    query_dict["%s__icontains"%field]=value
            results = cls.objects.filter(**query_dict)
            query_dict = {}
            if extra_attributes_form_instance.is_valid():
                for field, value in extra_attributes_form_instance.cleaned_data.items():
                    if value:
                        query_dict[field]=value
                print results
                results = extra_attributes_form_instance.search(results)
            request_dict.session["results"] = results
      
    context_dict.update({'results': results, 'type_form': type_form_instance, 'attributes_form': attributes_form_instance, 'extra_attributes_form': extra_attributes_form_instance})

    return context_dict, request_dict.session
#    return render_to_response('display_home_page.htm', context_dict)

##########################################################################################
###                    Function which manage the html login page                        ###
##########################################################################################

def display_login_page(request):
    if request.method == 'POST':
        if request.POST:
            username_value = request.POST['username']
            password_value = request.POST['password']
            user = auth.authenticate(username=username_value, password=password_value)
            if user is not None and user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect("/home/")
            else:
                return HttpResponse('Mauvais login, mauvais mot de passe ou compte inactif')
        else:
            return HttpResponse('mauvaise requete post')
    else:
        return render_to_response('DisplayLoginPage.htm', {})

##########################################################################################
###                    Function which manage the html home page                        ###
##########################################################################################
@login_required
def display_home_page(request):
    now = datetime.datetime.now()
    context_dict, SessionDictionnary= display_global_page(request)
    class_for_div="NavigateBox4Part"
    context_dict.update({'class4div': class_for_div, 'current_date': now,})
    request.session.update(SessionDictionnary)
    return render_to_response('DisplayHomePage.htm', context_dict)

##########################################################################################
###     All functions which manage the different html pages related to a part          ###
##########################################################################################
@login_required
def display_object_attributes(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for attributes """
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    menu_list = obj.menu_items
    object_attributes_list = []
    for attr in obj.attributes:
        item = obj._meta.get_field(attr).verbose_name
        object_attributes_list.append((item, getattr(obj, attr)))
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'current_page':'attributes', 'class4div': class_for_div, 'object_menu': menu_list, 'object_attributes': object_attributes_list})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObject.htm', context_dict)

##########################################################################################
@login_required
def display_object(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for attributes """
    return HttpResponsePermanentRedirect("/object/%s/%s/%s/attributes/" \
                                        % (object_type_value, object_reference_value, object_revision_value) )

##########################################################################################
@login_required
def display_object_lifecycle(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for Lifecycle """
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
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
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'current_page':'lifecycle', 'class4div': class_for_div, 'object_menu': menu_list, 'object_lifecycle': object_lifecycle_list})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectLifecycle.htm', context_dict)

##########################################################################################
@login_required
def display_object_revisions(request, object_type_value, object_reference_value, object_revision_value):
    """Manage html page for revisions"""
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    menu_list = obj.menu_items
    if obj.is_revisable():
        if request.method == "POST" and request.POST:
            add_form = AddRevisionForm(request.POST)
            if add_form.is_valid():
                obj.revise(add_form.cleaned_data["revision"])
        else:
            add_form = AddRevisionForm({"revision" : get_next_revision(object_revision_value)})
    else:
        add_form = None
    revisions = obj.get_all_revisions()
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'current_page':'revisions', 'class4div': class_for_div, 'object_menu': menu_list, 'revisions': revisions,
                         'add_revision_form' : add_form})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectRevisions.htm', context_dict)

##########################################################################################
@login_required
def display_object_history(request, object_type_value, object_reference_value, object_revision_value):
    """Manage html page for history"""
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    menu_list = obj.menu_items
    histos = models.History.objects.filter(plmobject=obj.object).order_by('date')
    object_history_list = []
    for histo in histos:
        object_history_list.append((histo.date, histo.action, histo.details))
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'current_page':'history', 'class4div': class_for_div, 'object_menu': menu_list, 'object_history': object_history_list})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectHistory.htm', context_dict)

##########################################################################################
@login_required
def display_object_child(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for BOM and children of the part """
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
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

    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'current_page':'BOM-child', 'class4div': class_for_div, 'object_menu': menu_list, 'obj' : obj,
                                 'children': children, "display_form" : display_form})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectChild.htm', context_dict)

##########################################################################################
@login_required
def edit_children(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for BOM and children of the part : edition"""
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
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
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'current_page':'BOM-child', 'class4div': class_for_div, 'object_menu': menu_list, 'obj' : obj,
                                 'children_formset': formset, })
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectChildEdit.htm', context_dict)

##########################################################################################    
@login_required
def add_children(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for BOM and children of the part : add new link"""
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    menu_list = obj.menu_items
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    if request.POST:
        add_child_form_instance = add_child_form(request.POST)
        if add_child_form_instance.is_valid():
            child_obj = get_obj(add_child_form_instance.cleaned_data["type"], \
                        add_child_form_instance.cleaned_data["reference"], \
                        add_child_form_instance.cleaned_data["revision"])
            obj.add_child(child_obj, \
                            add_child_form_instance.cleaned_data["quantity"], \
                            add_child_form_instance.cleaned_data["order"])
            context_dict.update({'object_menu': menu_list, 'add_child_form': add_child_form_instance, })
            return HttpResponseRedirect("/object/%s/%s/%s/BOM-child/" \
                                        % (object_type_value, object_reference_value, object_revision_value) )
        else:
            add_child_form_instance = add_child_form(request.POST)
            context_dict.update({'class4search_div': True, 'class4div': class_for_div, 'object_menu': menu_list, 'add_child_form': add_child_form_instance, })
            return render_to_response('DisplayObjectChildAdd.htm', context_dict)
    else:
        add_child_form_instance = add_child_form()
        context_dict.update({'current_page':'BOM-child', 'class4search_div': True, 'class4div': class_for_div, 'object_menu': menu_list, 'add_child_form': add_child_form_instance, })
        return render_to_response('DisplayObjectChildAdd.htm', context_dict)
    
##########################################################################################    
@login_required
def display_object_parents(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for "where is used / parents" of the part """
    obj = get_obj( object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
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

    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'current_page':'parents', 'class4div': class_for_div, 'object_menu': menu_list, 'parents' :  parents,
                                 'display_form' : display_form, 'obj': obj})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectParents.htm', context_dict)

##########################################################################################
@login_required
def display_object_doc_cad(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for related documents and CAD of the part"""
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
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
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'current_page':'doc-cad', 'class4div': class_for_div, 'object_menu': menu_list, 'object_doc_cad': object_doc_cad_list, 'doc_cad_formset': formset})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectDocCad.htm', context_dict)


##########################################################################################    
@login_required
def add_doc_cad(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for BOM and children of the part : add new link"""
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    menu_list = obj.menu_items
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    if request.POST:
        add_doc_cad_form_instance = AddDocCadForm(request.POST)
        if add_doc_cad_form_instance.is_valid():
            doc_cad_obj = get_obj(add_doc_cad_form_instance.cleaned_data["type"], \
                        add_doc_cad_form_instance.cleaned_data["reference"], \
                        add_doc_cad_form_instance.cleaned_data["revision"])
            obj.attach_to_document(doc_cad_obj)
            context_dict.update({'object_menu': menu_list, 'add_doc_cad_form': add_doc_cad_form_instance, })
            return HttpResponseRedirect("/object/%s/%s/%s/doc-cad/" \
                                        % (object_type_value, object_reference_value, object_revision_value) )
        else:
            add_doc_cad_form_instance = AddDocCadForm(request.POST)
            context_dict.update({'class4search_div': True, 'class4div': class_for_div, 'object_menu': menu_list, 'add_doc_cad_form': add_doc_cad_form_instance, })
            return render_to_response('DisplayDocCadAdd.htm', context_dict)
    else:
        add_doc_cad_form_instance = AddDocCadForm()
        context_dict.update({'class4search_div': True, 'class4div': class_for_div, 'object_menu': menu_list, 'add_doc_cad_form': add_doc_cad_form_instance, })
        return render_to_response('DisplayDocCadAdd.htm', context_dict)
    
##########################################################################################
@login_required
def display_related_part(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for related parts of the document"""
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
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
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'current_page':'parts', 'class4div': class_for_div, 'object_menu': menu_list, 'object_rel_part': object_rel_part_list, 'rel_part_formset': formset})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectRelPart.htm', context_dict)

##########################################################################################    
@login_required
def add_rel_part(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for related part of the document : add new link"""
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    menu_list = obj.menu_items
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    if request.POST:
        add_rel_part_form_instance = AddRelPartForm(request.POST)
        if add_rel_part_form_instance.is_valid():
            part_obj = get_obj(add_rel_part_form_instance.cleaned_data["type"], \
                        add_rel_part_form_instance.cleaned_data["reference"], \
                        add_rel_part_form_instance.cleaned_data["revision"])
            obj.attach_to_part(part_obj)
            context_dict.update({'object_menu': menu_list, 'add_rel_part_form': add_rel_part_form_instance, })
            return HttpResponseRedirect("/object/%s/%s/%s/parts/" \
                                        % (object_type_value, object_reference_value, object_revision_value) )
        else:
            add_rel_part_form_instance = add_rel_part_form(request.POST)
            context_dict.update({'class4search_div': True, 'class4div': class_for_div, 'object_menu': menu_list, 'add_rel_part_form': add_rel_part_form_instance, })
            return render_to_response('DisplayRelPartAdd.htm', context_dict)
    else:
        add_rel_part_form_instance = AddRelPartForm()
        context_dict.update({'class4search_div': True, 'class4div': class_for_div, 'object_menu': menu_list, 'add_rel_part_form': add_rel_part_form_instance, })
        return render_to_response('DisplayRelPartAdd.htm', context_dict)

##########################################################################################
@login_required
def display_files(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for files contained by the document"""
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
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
    is_owner_bool = (request.user == models.PLMObject.objects.get(type=object_type_value, \
                                        reference=object_reference_value, revision=object_revision_value).owner)
    object_files_list = obj.files
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'is_owner':is_owner_bool, 'current_page':'files', 'class4div': class_for_div, 'object_menu': menu_list, 'object_files': object_files_list, 'file_formset': formset})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectFiles.htm', context_dict)

##########################################################################################
@login_required
def add_file(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for file addition in the document"""
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    menu_list = obj.menu_items
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    if request.POST:
        add_file_form_instance = AddFileForm(request.POST, request.FILES)
        if add_file_form_instance.is_valid():
            obj.add_file(request.FILES["filename"])
            context_dict.update({'object_menu': menu_list, 'add_file_form': add_file_form_instance, })
            return HttpResponseRedirect("/object/%s/%s/%s/files/" \
                                        % (object_type_value, object_reference_value, object_revision_value) )
        else:
            add_file_form_instance = AddFileForm(request.POST)
            context_dict.update({'class4search_div': True, 'class4div': class_for_div, 'object_menu': menu_list, 'add_file_form': add_file_form_instance, })
            return render_to_response('DisplayRelPartAdd.htm', context_dict)
    else:
        add_file_form_instance = AddFileForm()
        context_dict.update({'class4search_div': False, 'class4div': class_for_div, 'object_menu': menu_list, 'add_file_form': add_file_form_instance, })
        return render_to_response('DisplayFileAdd.htm', context_dict)

##########################################################################################
###             Manage html pages for part creation / modification                     ###
##########################################################################################
def create_non_modifyable_attributes_list(Classe=models.PLMObject):
    """ Create a list of an object's attributes we can't modify' and set them a value """
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
    """ Manage html page for the part creation """
    now = datetime.datetime.now()
    context_dict = {'current_date': now}
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
#    log_in_person="pjoulaud"
#    context_dict.update({'log_in_person' : log_in_person})
    if request.method == 'GET':
        if request.GET:
            type_form_instance = type_form(request.GET)
            if type_form_instance.is_valid():
                cls = models.get_all_plmobjects()[type_form_instance.cleaned_data["type"]]
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
                cls = models.get_all_plmobjects()[type_name]
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
                    return HttpResponseRedirect("/object/%s/%s/%s/" % (controller.type, controller.reference, controller.revision) )
    context_dict.update({'class4div': class_for_div, 'creation_form': creation_form_instance, 'object_type': type_form_instance.cleaned_data["type"], 'non_modifyable_attributes': non_modifyable_attributes_list })
    return render_to_response('DisplayObject4creation.htm', context_dict)

##########################################################################################
@login_required
def modify_object(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for part modification """
    log_in_person="pjoulaud"
    now = datetime.datetime.now()
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'log_in_person' : log_in_person})
    cls = models.get_all_plmobjects()[object_type_value]
    non_modifyable_attributes_list = create_non_modifyable_attributes_list(cls)
    current_object = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(current_object, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    if request.method == 'POST':
        if request.POST:
            modification_form_instance = get_modification_form(cls, request.POST)
            if modification_form_instance.is_valid():
                user = models.User.objects.get(username=log_in_person)
                current_object.update_from_form(modification_form_instance)
                return HttpResponseRedirect("/object/%s/%s/%s/" % (current_object.type, current_object.reference, current_object.revision) )
            else:
                pass
        else:
            modification_form_instance = get_modification_form(cls, instance = current_object.object)
    else:
        modification_form_instance = get_modification_form(cls, instance = current_object.object)
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    context_dict.update({'class4div': class_for_div, 'modification_form': modification_form_instance, 'non_modifyable_attributes': non_modifyable_attributes_list})
    return render_to_response('DisplayObject4modification.htm', context_dict)
    
##########################################################################################
def display_bollox(request):
    context_dict={}
    return render_to_response('Navigate2.htm', context_dict)
    
##########################################################################################
###             Manage html pages for file check-in / check-out / download             ###
##########################################################################################    
@login_required
def checkin_file(request, object_type_value, object_reference_value, object_revision_value, file_id_value):
    """ Manage html page for file checkin in the document"""
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    menu_list = obj.menu_items
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    if request.POST :
        checkin_file_form_instance = AddFileForm(request.POST, request.FILES)
        if checkin_file_form_instance.is_valid():
            obj.checkin(models.DocumentFile.objects.get(id=file_id_value), request.FILES["filename"])
            context_dict.update({'object_menu': menu_list, })
            return HttpResponseRedirect("/object/%s/%s/%s/files/" \
                                        % (object_type_value, object_reference_value, object_revision_value) )
        else:
            checkin_file_form_instance = AddFileForm(request.POST)
            context_dict.update({'class4search_div': True, 'class4div': class_for_div, \
                                 'object_menu': menu_list, 'add_file_form': add_file_form_instance, })
            return render_to_response('DisplayFileAdd.htm', context_dict)
    else:
        checkin_file_form_instance = AddFileForm()
        context_dict.update({'class4search_div': True, 'class4div': class_for_div, \
                            'object_menu': menu_list, 'add_file_form': checkin_file_form_instance, })
        return render_to_response('DisplayFileAdd.htm', context_dict)

##########################################################################################
@login_required 
def download(request, docfile_id):
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    name = doc_file.filename
    base_dir = os.path.dirname(__file__)
    rep1 = os.path.join(base_dir, "..", "docs", "%s/" % docfile_id)
    rep = os.path.join("docs", "%s/" % docfile_id)
    dst1 = os.path.join(rep1, name)
    if not os.path.exists(rep1):
        os.mkdir(rep1)
    if os.path.lexists(dst1):
        os.unlink(dst1)
    os.symlink(doc_file.file.path, dst1)
    dst = os.path.join(rep, name)
    return HttpResponseRedirect("/" + dst)
    
##########################################################################################
@login_required 
def checkout_file(request, object_type_value, object_reference_value, object_revision_value, docfile_id):
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    doc_file = models.DocumentFile.objects.get(id=docfile_id)
    if request.user == models.PLMObject.objects.get(type=object_type_value, reference=object_reference_value, revision=object_revision_value).owner:
        obj.lock(doc_file)
        return download(request, docfile_id)

##########################################################################################
###                     Manage html pages for navigate function                        ###
##########################################################################################    
@login_required
def navigate(request, object_type_value, object_reference_value, object_revision_value):   
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    if isinstance(obj, DocumentController):
        class_for_div="NavigateBox4Doc"
    else:
        class_for_div="NavigateBox4Part"
    if request.method == 'POST' and request.POST:
        filter_object_form_instance = FilterObjectForm(request.POST)
        for key, value in request.POST.items():
            request.session[key] = value
    elif request.session.get('Child')\
            or request.session.get('Parents')\
            or request.session.get('Doc')\
            or request.session.get('Cad')\
            or request.session.get('User') :
        filter_object_form_instance = FilterObjectForm(request.session)
    else:
        data={'Child': True, 'Parents': False, 'Doc': True, 'Cad': False, 'User': False}
        filter_object_form_instance = FilterObjectForm(data)
        for key, value in data.items():
            request.session[key] = value
    if not filter_object_form_instance.is_valid():
        return HttpResponse('mauvaise requete post')
    else :
        navigate_graph=pgv.AGraph()
        navigate_graph.clear()
        navigate_graph.graph_attr['dpi']='96.0'
        navigate_graph.graph_attr['aspect']='1.83'
        navigate_graph.graph_attr['size']= '16.28, 8.88'
        navigate_graph.graph_attr['center']='true'
        navigate_graph.graph_attr['ranksep']='1.2'
        navigate_graph.graph_attr['pad']='0.1'
        navigate_graph.node_attr['shape']='none'
        navigate_graph.node_attr['fixedsize']='true'
        navigate_graph.node_attr['fontsize']='10'
        navigate_graph.node_attr['style']='filled'
        navigate_graph.edge_attr['color']='#000000'
        navigate_graph.edge_attr['len']="1.2"
        navigate_graph.node_attr['width']="0.8"
        navigate_graph.node_attr['height']="0.6"
        navigate_graph.edge_attr['arrowhead']='normal'
        def create_child_edges(object_id):
            object_item = get_obj_by_id(object_id, var_dict['log_in_person'])
            children_list = object_item.get_children()
            navigate_graph.node_attr['color']='#99ccff'
            navigate_graph.node_attr['shape']='none'
            navigate_graph.node_attr['image']="media/img/part.png"
            if children_list:
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
                    if filter_object_form_instance.cleaned_data['Doc'] :
                        create_document_edges(child_id)
                    create_child_edges(child_id)
            else:
                return
        def create_parent_edges(object_id):
            object_item = get_obj_by_id(object_id, var_dict['log_in_person'])
            parent_list = object_item.get_parents()
            navigate_graph.node_attr['color']='#99ccff'
            navigate_graph.node_attr['shape']='none'
            navigate_graph.node_attr['image']="media/img/part.png"
            if parent_list:
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
                    if filter_object_form_instance.cleaned_data['Doc'] :
                        create_document_edges(parent_id)
                    create_parent_edges(parent_id)
            else :
                return
        def create_document_edges(object_id):
            object_item = get_obj_by_id(object_id, var_dict['log_in_person'])
            document_list = object_item.get_attached_documents()
            navigate_graph.node_attr['image']='none'
            navigate_graph.node_attr['color']='#fef176'
            navigate_graph.node_attr['shape']='note'
            if document_list:
                for document_item in document_list:
                    document_id = document_item.document.id
                    navigate_graph.add_edge(object_id, document_id)
                    document_node = navigate_graph.get_node(document_id)
                    document_node.attr['label'] = document_item.document.type.encode('utf-8')\
                                                +"\\n"+document_item.document.reference.encode('utf-8')\
                                                +"\\n"+document_item.document.revision.encode('utf-8')
                    document_node.attr['URL'] = "/object/"+document_item.document.type.encode('utf-8')\
                                                +"/"+document_item.document.reference.encode('utf-8')\
                                                +"/"+document_item.document.revision.encode('utf-8')+"/"
            else :
                return
        part_id = obj.id
        navigate_graph.add_node(part_id)
        part_node = navigate_graph.get_node(part_id)
        part_node.attr['root'] = 'true'
        navigate_graph.node_attr['color']='#5588bb'
        part_node.attr['label'] = obj.type.encode('utf-8')\
                                    +"\\n"+obj.reference.encode('utf-8')\
                                    +"\\n"+obj.revision.encode('utf-8')
        part_node.attr['URL'] = "/object/"+obj.type.encode('utf-8')\
                                                +"/"+obj.reference.encode('utf-8')\
                                                +"/"+obj.revision.encode('utf-8')+"/navigate/"
        part_node.attr['shape']='box'
        part_node.attr['image']="media/img/part.png"
        if filter_object_form_instance.cleaned_data['Doc'] :
            create_document_edges(part_id)
        if filter_object_form_instance.cleaned_data['Child'] :
            create_child_edges(part_id)
        if filter_object_form_instance.cleaned_data['Parents'] :
            create_parent_edges(part_id)
        navigate_graph.layout()
        picture_path = "media/navigate/" + str(obj.id)\
                        +"-"\
                        +str(int(filter_object_form_instance.cleaned_data['Child']))\
                        +str(int(filter_object_form_instance.cleaned_data['Parents']))\
                        +str(int(filter_object_form_instance.cleaned_data['Doc']))\
                        +str(int(filter_object_form_instance.cleaned_data['Cad']))\
                        +str(int(filter_object_form_instance.cleaned_data['User']))
        map_path= picture_path + ".map"
        picture_path +=".gif"
        navigate_graph.draw(picture_path, format='gif', prog='neato')
        navigate_graph.draw(map_path, format='imap', prog='neato')
        file_object = open(map_path,"rb",0)
        map_string = file_object.read()
        file_object.close()
        map_list = map_string.split("\n")
        del map_list[0]
        del map_list[-1]
        i = 0
        for map_line in map_list :
            map_line_item = map_line.split(" ")
            if len(map_line_item)>4:
                for j in range(2, len(map_line_item)-2):
                    map_line_item[1] += " " + map_line_item[j]
                    del map_line_item[j]
            if len(map_line_item)==4:
                map_list[i]={'shape': map_line_item[0], 'url': map_line_item[1],\
                             '1st_point': map_line_item[2], '2nd_point': map_line_item[3]}
            i+=1
        x_1st_point_part_node, y_1st_point_part_node = map_list[0]['1st_point'].split(",")
        x_2nd_point_part_node, y_2nd_point_part_node = map_list[0]['2nd_point'].split(",")
        x_part_node_position = (int(x_1st_point_part_node)+int(x_2nd_point_part_node))/2
        y_part_node_position = (int(y_1st_point_part_node)+int(y_2nd_point_part_node))/2
        x_img_position_corrected = 790/2 - int(x_part_node_position) -100
        y_img_position_corrected = 405/2 - int(y_part_node_position)
        context_dict.update(var_dict)
        context_dict.update({'class4div': class_for_div, 'filter_object_form': filter_object_form_instance ,\
                            'map_areas': map_list, 'picture_path': "/"+picture_path,\
                             'x_img_position': int(x_img_position_corrected),\
                             'y_img_position': int(y_img_position_corrected)})
        navigate_graph.clear()
        return render_to_response('Navigate.htm', context_dict)
        
        
        
        
        
        
