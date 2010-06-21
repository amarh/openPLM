from django.shortcuts import render_to_response, get_object_or_404
import datetime
from operator import attrgetter

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController, get_controller

from django.db.models import Q
from django.http import HttpResponseRedirect, QueryDict

from openPLM.plmapp.forms import *

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

def init_context_dict(init_type_value, init_reference_value, init_revision_value):
    """ Initiate context_dict we used after to transfer parameters to html pages"""
    now = datetime.datetime.now()
    return {
        'current_date': now,
        'object_reference': init_reference_value,
        'object_revision': init_revision_value,
        'object_type': init_type_value,
        }

###################################
# Manage html pages for Home Page #
###################################

def display_global_page(request_dict):
    """ Get a request and return a dictionnary with elements common to all pages """
    now = datetime.datetime.now()
    log_in_person="pjoulaud"
    context_dict = {'log_in_person' : log_in_person}
    query_dict = {}
    type_form_instance = type_form()
    attributes_form_instance = attributes_form()
    extra_attributes_form_instance = get_search_form()
    results=[]
    if request_dict.GET:
        type_form_instance = type_form(request_dict.GET)
        attributes_form_instance = attributes_form(request_dict.GET)
        for key, value in request_dict.GET.items():
            request_dict.session[key] = value
        if attributes_form_instance.is_valid():
            cls = models.get_all_plmobjects()[attributes_form_instance.cleaned_data["type"]]
            extra_attributes_form_instance = get_search_form(cls, request_dict.GET)
            for field, value in attributes_form_instance.cleaned_data.items():
                if value:
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
        else:
            print "Donnees non valides"
    elif request_dict.session:
        type_form_instance = type_form(request_dict.session)
        attributes_form_instance = attributes_form(request_dict.session)
        request_dict.session.update(request_dict.session)
        if attributes_form_instance.is_valid():
            cls = models.get_all_plmobjects()[attributes_form_instance.cleaned_data["type"]]
            extra_attributes_form_instance = get_search_form(cls, request_dict.session)
            for field, value in attributes_form_instance.cleaned_data.items():
                if value:
                    query_dict["%s__icontains"%field]=value
            results = cls.objects.filter(**query_dict)
            query_dict = {}
            if extra_attributes_form_instance.is_valid():
                for field, value in extra_attributes_form_instance.cleaned_data.items():
                    if value:
                        query_dict[field]=value
                results = extra_attributes_form_instance.search(results)
        else:
            print "Donnees non valides"
    else:
        print "Pas de donnees dans .GET ni dans .session"
      
    context_dict.update({'results': results, 'type_form': type_form_instance, 'attributes_form': attributes_form_instance, 'extra_attributes_form': extra_attributes_form_instance})

    return context_dict, request_dict.session
#    return render_to_response('display_home_page.htm', context_dict)


#########################################################################
# All functions which manage the different html pages related to a part #
#########################################################################

def display_home_page(request):
    context_dict, SessionDictionnary= display_global_page(request)
    request.session.update(SessionDictionnary)
    return render_to_response('DisplayHomePage.htm', context_dict)

def display_object(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for attributes """
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    menu_list = obj.menu_items
    object_attributes_list = []
    for attr in obj.attributes:
        item = obj._meta.get_field(attr).verbose_name
        object_attributes_list.append((item, getattr(obj, attr)))
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'object_menu': menu_list, 'object_attributes': object_attributes_list})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObject.htm', context_dict)

def display_object_lifecycle(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for Lifecycle """
    now = datetime.datetime.now()
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
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
    context_dict.update({'object_menu': menu_list, 'object_lifecycle': object_lifecycle_list})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectLifecycle.htm', context_dict)


def display_object_revisions(request, object_type_value, object_reference_value, object_revision_value):
    """Manage html page for revisions"""
    now = datetime.datetime.now()
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    menu_list = obj.menu_items
    object_revisions_list = [
        [object_type_value, object_reference_value, 'a', "obsolete"],
        [object_type_value, object_reference_value, 'b', "official"],
        [object_type_value, object_reference_value, 'c', "draft"],
        ]
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'object_menu': menu_list, 'object_revisions': object_revisions_list})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectRevisions.htm', context_dict)

def display_object_history(request, object_type_value, object_reference_value, object_revision_value):
    """Manage html page for history"""
    now = datetime.datetime.now()
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    menu_list = obj.menu_items
    histos = models.History.objects.filter(plmobject=obj.object).order_by('date')
    object_history_list = []
    for histo in histos:
        object_history_list.append((histo.date, histo.action, histo.details))
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'object_menu': menu_list, 'object_history': object_history_list})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectHistory.htm', context_dict)

def display_object_child(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for BOM and children of the part """
    now = datetime.datetime.now()
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
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
    context_dict.update({'object_menu': menu_list, 'obj' : obj,
                                 'children': children, "display_form" : display_form})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectChild.htm', context_dict)

def edit_children(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """ Manage html page for BOM and children of the part : edition"""
    now = datetime.datetime.now()
    obj = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    MenuList = obj.menu_items
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
    context_dict = init_context_dict(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    context_dict.update({'ObjectMenu': MenuList, 'obj' : obj,
                                 'children_formset': formset, })
    return render_to_response('DisplayObjectChildEdit.htm', context_dict)
    
def display_object_parents(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for "where is used / parents" of the part """
    now = datetime.datetime.now()
    obj = get_obj( object_type_value, object_reference_value, object_revision_value)
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
    context_dict.update({'object_menu': menu_list, 'parents' :  parents,
                                 'display_form' : display_form, 'obj': obj})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectParents.htm', context_dict)


def display_object_doc_cad(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for related documents and CAD of the part"""
    now = datetime.datetime.now()
    obj = get_obj(object_type_value, object_reference_value, object_revision_value)
    menu_list = obj.menu_items
    object_doc_cad_list = [
        (["Type", "Reference", "Revision", "Name", "Status"], ""),
        (["Rapport essais", "Doc0045", "a", "Essais de compatibilite electro-magnetique", "official"], replace_white_spaces("/object/Rapport essais/Doc0045/a/")),
        (["Incident Qualite", "Doc0066", "b", "Probleme de casse chaine", "obsolete"], replace_white_spaces("/object/Incident Qualite/Doc0066/b/")),
        (["CatDrawing", "Cad00123", "a", "Vue d'ensemble", "official"], replace_white_spaces("/object/CatDrawing/Cad00123/a/")),
        ]
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'object_menu': menu_list, 'object_doc_cad': object_doc_cad_list})
    var_dict, request_dict = display_global_page(request)
    request.session.update(request_dict)
    context_dict.update(var_dict)
    return render_to_response('DisplayObjectDocCad.htm', context_dict)


######################################################
# Manage html pages for part creation / modification #
######################################################

def create_non_modifyable_attributes_list(Classe=models.PLMObject):
    """ Create a list of an object's attributes we can't modify' and set them a value """
    non_modifyable_fields_list = Classe.excluded_creation_fields()
    non_modifyable_attributes_list=[]
    non_modifyable_attributes_list.append((non_modifyable_fields_list[0], 'Person'))
    non_modifyable_attributes_list.append((non_modifyable_fields_list[1], 'Person'))
    non_modifyable_attributes_list.append((non_modifyable_fields_list[2], 'Date'))
    non_modifyable_attributes_list.append((non_modifyable_fields_list[3], 'Date'))
    return non_modifyable_attributes_list

def create_object(request):
    """ Manage html page for the part creation """
    now = datetime.datetime.now()
    log_in_person="pjoulaud"
    context_dict = {'CurrentDate': now, 'log_in_person' : log_in_person}
    if request.method == 'GET':
        if request.GET:
            type_form_instance = type_form(request.GET)
            if type_form_instance.is_valid():
                cls = models.get_all_plmobjects()[type_form_instance.cleaned_data["type"]]
                creation_form_instance = get_creation_form(cls, {'revision':'a', 'lifecycle': str(models.get_default_lifecycle()), }, True)
                non_modifyable_attributes_list = create_non_modifyable_attributes_list(cls)
    elif request.method == 'POST':
        if request.POST:
            type_form_instance = type_form(request.POST)
            if type_form_instance.is_valid():
                type_name = type_form_instance.cleaned_data["type"]
                cls = models.get_all_plmobjects()[type_name]
                non_modifyable_attributes_list = create_non_modifyable_attributes_list(cls)
                creation_form_instance = get_creation_form(cls, request.POST)
                if creation_form_instance.is_valid():
                    user = models.User.objects.get(username=log_in_person)
                    controller_cls = get_controller(type_name)
                    controller = PLMObjectController.create_from_form(creation_form_instance, user)
                    return HttpResponseRedirect("/object/%s/%s/%s/" % (controller.type, controller.reference, controller.revision) )
            else:
                return HttpResponseRedirect("/home/")
    context_dict.update({'creation_form': creation_form_instance, 'object_type': type_form_instance.cleaned_data["type"], 'non_modifyable_attributes': non_modifyable_attributes_list })
    return render_to_response('DisplayObject4creation.htm', context_dict)

def modify_object(request, object_type_value, object_reference_value, object_revision_value):
    """ Manage html page for part modification """
    now = datetime.datetime.now()
    log_in_person="pjoulaud"
    context_dict = init_context_dict(object_type_value, object_reference_value, object_revision_value)
    context_dict.update({'CurrentDate': now, 'log_in_person' : log_in_person})
    cls = models.get_all_plmobjects()[object_type_value]
    non_modifyable_attributes_list = create_non_modifyable_attributes_list(cls)
    current_object = get_obj(object_type_value, object_reference_value, object_revision_value)
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
        pass
    context_dict.update({'modification_form': modification_form_instance, 'non_modifyable_attributes': non_modifyable_attributes_list })
    return render_to_response('DisplayObject4modification.htm', context_dict)

