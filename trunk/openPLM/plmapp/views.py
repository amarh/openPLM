from django.shortcuts import render_to_response, get_object_or_404
import datetime

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController, get_controller

from django.db.models import Q
from django.http import HttpResponseRedirect, QueryDict

from openPLM.plmapp.forms import *



def ReplaceWhitespaces(Chain):
    """ Replace all whitespace characteres by %20 in order to be compatible with an URL"""
    return Chain.replace(" ","%20")


def BuildMenu():
    """ Build a list for the html page menu"""
    return ["attributes", "lifecycle", "revisions", "history", "BOM-child", "parents", "doc-cad"]


def get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """ Get Type, Reference and Revision and return an object """
    obj = get_object_or_404(models.PLMObject, type=ObjectTypeValue,
                            reference=ObjectReferenceValue,
                            revision=ObjectRevisionValue)
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
    controller_cls = get_controller(ObjectTypeValue)
    return controller_cls(obj, user)

def InitVariablesDictionnary(InitTypeValue, InitReferenceValue, InitRevisionValue):
    """ Initiate VariablesDictionnary we used after to transfer parameters to html pages"""
    now = datetime.datetime.now()
    return {
        'current_date': now,
        'ObjectReference': InitReferenceValue,
        'ObjectRevision': InitRevisionValue,
        'ObjectType': InitTypeValue,
        }

#########################################################################
# All functions which manage the different html pages related to a part #
#########################################################################

def DisplayObject(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """ Manage html page for attributes """
    obj = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    MenuList = obj.menu_items
    ObjectAttributesList = []
    for attr in obj.attributes:
        item = obj._meta.get_field(attr).verbose_name
        ObjectAttributesList.append((item, getattr(obj, attr)))
    VariablesDictionnary = InitVariablesDictionnary(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    VariablesDictionnary.update({'ObjectMenu': MenuList, 'ObjectAttributes': ObjectAttributesList})
    return render_to_response('DisplayObject.htm', VariablesDictionnary)
    
def DisplayObjectLifecycle(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """ Manage html page for Lifecycle """
    now = datetime.datetime.now()
    obj = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    if request.method == 'POST':
        if request.POST["action"] == "DEMOTE":
            obj.demote()
        elif request.POST["action"] == "PROMOTE":
            obj.promote()
    MenuList = obj.menu_items
    state = obj.state.name
    lifecycle = obj.lifecycle
    ObjectLifecycleList = []
    for st in lifecycle:
        ObjectLifecycleList.append((st, st == state))
    VariablesDictionnary = InitVariablesDictionnary(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    VariablesDictionnary.update({'ObjectMenu': MenuList, 'ObjectLifecycle': ObjectLifecycleList})
    return render_to_response('DisplayObjectLifecycle.htm', VariablesDictionnary)


def DisplayObjectRevisions(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """Manage html page for revisions"""
    now = datetime.datetime.now()
    obj = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    MenuList = obj.menu_items
    ObjectRevisionsList = [
        [ObjectTypeValue, ObjectReferenceValue, 'a', "obsolete"],
        [ObjectTypeValue, ObjectReferenceValue, 'b', "official"],
        [ObjectTypeValue, ObjectReferenceValue, 'c', "draft"],
        ]
    VariablesDictionnary = InitVariablesDictionnary(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    VariablesDictionnary.update({'ObjectMenu': MenuList, 'ObjectRevisions': ObjectRevisionsList})
    return render_to_response('DisplayObjectRevisions.htm', VariablesDictionnary)

def DisplayObjectHistory(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """Manage html page for history"""
    now = datetime.datetime.now()
    obj = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    MenuList = obj.menu_items
    histos = models.History.objects.filter(plmobject=obj.object).order_by('date')
    ObjectHistoryList = []
    for histo in histos:
        ObjectHistoryList.append((histo.date, histo.action, histo.details))
    VariablesDictionnary = InitVariablesDictionnary(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    VariablesDictionnary.update({'ObjectMenu': MenuList, 'ObjectHistory': ObjectHistoryList})
    return render_to_response('DisplayObjectHistory.htm', VariablesDictionnary)

def DisplayObjectChild(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """ Manage html page for BOM and children of the part """
    now = datetime.datetime.now()
    obj = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    MenuList = obj.menu_items
    ObjectChildList = [
        (["", 1, 1, ObjectReferenceValue, ObjectRevisionValue, ObjectTypeValue, "Assemble superieur de velo", "official"], ""),
        ([range(1), 10, 1, "part011", "a", "assembly", "pedalier", "obsolete"], ReplaceWhitespaces("/object/assembly/part011/a/")),
        ([range(2), 10, 1, "part012", "a", "part", "couronne", "officiel"], ReplaceWhitespaces("/object/part/part012/a/")),
        ([range(2), 20, 1, "part013", "a", "part", "pedale", "officiel"], ReplaceWhitespaces("/object/part/part013/a/")),
        ([range(1), 20, 2, "part077", "b", "assembly", "roue", "officiel"], ReplaceWhitespaces("/object/assembly/part077/a/")),
        ]
    VariablesDictionnary = InitVariablesDictionnary(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    VariablesDictionnary.update({'ObjectMenu': MenuList, 'ObjectChild': ObjectChildList})
    return render_to_response('DisplayObjectChild.htm', VariablesDictionnary)
 
def DisplayObjectParents(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """ Manage html page for "where is used / parents" of the part """
    now = datetime.datetime.now()
    obj = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    MenuList = obj.menu_items
    ObjectParentList = [
        (["", ObjectReferenceValue, ObjectRevisionValue, ObjectTypeValue, "Assemble superieur de velo", "official"], ""),
        ([-1, "part011", "a", "assembly", "pedalier", "obsolete"], ReplaceWhitespaces("/object/assembly/part011/a/")),
        ([-2, "part012", "a", "part", "couronne", "officiel"], ReplaceWhitespaces("/object/part/part012/a/")),
        ([-2, "part013", "a", "part", "pedale", "officiel"], ReplaceWhitespaces("/object/part/part013/a/")),
        ([-1, "part077", "b", "assembly", "roue", "officiel"], ReplaceWhitespaces("/object/assembly/part077/a/")),
        ]
    VariablesDictionnary = InitVariablesDictionnary(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    VariablesDictionnary.update({'ObjectMenu': MenuList, 'ObjectParent': ObjectParentList})
    return render_to_response('DisplayObjectParents.htm', VariablesDictionnary)

def DisplayObjectDocCad(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """ Manage html page for related documents and CAD of the part"""
    now = datetime.datetime.now()
    obj = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    MenuList = obj.menu_items
    ObjectDocCadList = [
        (["Type", "Reference", "Revision", "Name", "Status"], ""),
        (["Rapport essais", "Doc0045", "a", "Essais de compatibilite electro-magnetique", "official"], ReplaceWhitespaces("/object/Rapport essais/Doc0045/a/")),
        (["Incident Qualite", "Doc0066", "b", "Probleme de casse chaine", "obsolete"], ReplaceWhitespaces("/object/Incident Qualite/Doc0066/b/")),
        (["CatDrawing", "Cad00123", "a", "Vue d'ensemble", "official"], ReplaceWhitespaces("/object/CatDrawing/Cad00123/a/")),
        ]
    VariablesDictionnary = InitVariablesDictionnary(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    VariablesDictionnary.update({'ObjectMenu': MenuList, 'ObjectDocCad': ObjectDocCadList})
    return render_to_response('DisplayObjectDocCad.htm', VariablesDictionnary)

def DisplayHomePage(request):
    """ Manage html Home Page """
    now = datetime.datetime.now()
    LoggedPerson="pjoulaud"
    VariablesDictionnary = {'LoggedPerson' : LoggedPerson}

    if request.GET:
        TypeChoiceFormInstance = TypeChoiceForm(request.GET)
        ChoiceFormInstance = ChoiceForm(request.GET)
        if TypeChoiceFormInstance.is_valid():
            print(TypeChoiceFormInstance.cleaned_data["type"])
            cls = models.get_all_plmobjects()[TypeChoiceFormInstance.cleaned_data["type"]]
            AttributesFormInstance = get_search_form(cls)
        else:
            print "Donnees non valides"
    else:
        TypeChoiceFormInstance = TypeChoiceForm()
        ChoiceFormInstance = ChoiceForm()
        AttributesFormInstance = get_search_form()
    QueryDict = {}
    if ChoiceFormInstance.is_valid():
        for field, value in ChoiceFormInstance.cleaned_data.items():
            if value:
                QueryDict[field]=value
        if AttributesFormInstance.is_valid():
            for field, value in AttributesFormInstance.cleaned_data.items():
                print "voici la liste"
                print field
                QueryDict[field]=value
    print "QueryDict : "
    print QueryDict    
    if QueryDict :
        results = models.PLMObject.objects.filter(**QueryDict)
        print "results"
        print results
    else:
        results = []
    
    VariablesDictionnary.update({'results': results, 'TypeChoiceForm': TypeChoiceFormInstance, 'ChoiceForm': ChoiceFormInstance, 'AttributesForm': AttributesFormInstance})
    return render_to_response('DisplayHomePage.htm', VariablesDictionnary)

######################################################
# Manage html pages for part creation / modification #
######################################################

def CreateNonModifyableAttributesList(Classe=models.PLMObject):
    """ Create a list of an object's attributes we can't modify' and set them a value """
    NonModifyableFieldsList = Classe.excluded_creation_fields()
    NonModifyableAttributesList=[]
    NonModifyableAttributesList.append((NonModifyableFieldsList[0], 'Person'))
    NonModifyableAttributesList.append((NonModifyableFieldsList[1], 'Person'))
    NonModifyableAttributesList.append((NonModifyableFieldsList[2], 'Date'))
    NonModifyableAttributesList.append((NonModifyableFieldsList[3], 'Date'))
    return NonModifyableAttributesList

def CreateObject(request):
    """ Manage html page for the part creation """
    now = datetime.datetime.now()
    LoggedPerson="pjoulaud"
    VariablesDictionnary = {'CurrentDate': now, 'LoggedPerson' : LoggedPerson}
    if request.method == 'GET':
        if request.GET:
            TypeChoiceFormInstance = TypeChoiceForm(request.GET)
            if TypeChoiceFormInstance.is_valid():
                cls = models.get_all_plmobjects()[TypeChoiceFormInstance.cleaned_data["type"]]
                CreationFormInstance = get_creation_form(cls, {'revision':'a', 'lifecycle': str(models.get_default_lifecycle()), }, True)
                NonModifyableAttributesList = CreateNonModifyableAttributesList(cls)
    elif request.method == 'POST':
        if request.POST:
            TypeChoiceFormInstance = TypeChoiceForm(request.POST)
            if TypeChoiceFormInstance.is_valid():
                type_name = TypeChoiceFormInstance.cleaned_data["type"]
                cls = models.get_all_plmobjects()[type_name]
                NonModifyableAttributesList = CreateNonModifyableAttributesList(cls)
                CreationFormInstance = get_creation_form(cls, request.POST)
                if CreationFormInstance.is_valid():
                    user = models.User.objects.get(username=LoggedPerson)
                    controller_cls = get_controller(type_name)
                    controller = PLMObjectController.create_from_form(CreationFormInstance, user)
                    return HttpResponseRedirect("/object/%s/%s/%s/" % (controller.type, controller.reference, controller.revision) )
            else:
                return HttpResponseRedirect("/home/")
    VariablesDictionnary.update({'CreationForm': CreationFormInstance, 'ObjectType': TypeChoiceFormInstance.cleaned_data["type"], 'NonModifyableAttributes': NonModifyableAttributesList })
    return render_to_response('DisplayObject4creation.htm', VariablesDictionnary)

def ModifyObject(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    """ Manage html page for part modification """
    now = datetime.datetime.now()
    LoggedPerson="pjoulaud"
    VariablesDictionnary = InitVariablesDictionnary(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    VariablesDictionnary.update({'CurrentDate': now, 'LoggedPerson' : LoggedPerson})
    cls = models.get_all_plmobjects()[ObjectTypeValue]
    NonModifyableAttributesList = CreateNonModifyableAttributesList(cls)
    CurrentObject = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    if request.method == 'POST':
        if request.POST:
            ModificationFormInstance = get_modification_form(cls, request.POST)
            if ModificationFormInstance.is_valid():
                user = models.User.objects.get(username=LoggedPerson)
                CurrentObject.update_from_form(ModificationFormInstance)
                return HttpResponseRedirect("/object/%s/%s/%s/" % (CurrentObject.type, CurrentObject.reference, CurrentObject.revision) )
            else:
                pass
        else:
            ModificationFormInstance = get_modification_form(cls, instance = CurrentObject.object)
    else:
        pass
    VariablesDictionnary.update({'ModificationForm': ModificationFormInstance, 'NonModifyableAttributes': NonModifyableAttributesList })
    return render_to_response('DisplayObject4modification.htm', VariablesDictionnary)

