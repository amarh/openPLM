from django.shortcuts import render_to_response, get_object_or_404
import datetime

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController, get_controller

from django.db.models import Q
from django.http import HttpResponseRedirect

from openPLM.plmapp.forms import *


# Replace all whitespace characteres by %20 in order to be compatible with an URL
def ReplaceWhitespaces(Chain):
    return Chain.replace(" ","%20")

# Build a list for the html page menu
def BuildMenu():
    return ["attributes", "lifecycle", "revisions", "history", "BOM-child", "parents", "doc-cad"]

# Get Type, Reference and Revision and return an object
def get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
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

# Initiate VariablesDictionnary we used after to transfer parameters to html pages
def InitVariablesDictionnary(InitTypeValue, InitReferenceValue, InitRevisionValue):
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

# Manage html page for attributes
def DisplayObject(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
    obj = get_obj(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    MenuList = obj.menu_items
    ObjectAttributesList = []
    for attr in obj.attributes:
        item = obj._meta.get_field(attr).verbose_name
        ObjectAttributesList.append((item, getattr(obj, attr)))
    VariablesDictionnary = InitVariablesDictionnary(ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue)
    VariablesDictionnary.update({'ObjectMenu': MenuList, 'ObjectAttributes': ObjectAttributesList})
    return render_to_response('DisplayObject.htm', VariablesDictionnary)

# Manage html page for Lifecycle    
def DisplayObjectLifecycle(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
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

# Manage html page for revisions
def DisplayObjectRevisions(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
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

# Manage html page for history
def DisplayObjectHistory(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
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

# Manage html page for BOM and children of the part
def DisplayObjectChild(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
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

# Manage html page for "where is used / parents" of the part 
def DisplayObjectParents(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
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

# Manage html page for related documents and CAD of the part
def DisplayObjectDocCad(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
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

#########################
# Manage html Home Page #
#########################
def DisplayHomePage(request):
    now = datetime.datetime.now()
    LoggedPerson="pjoulaud"
    VariablesDictionnary = {'LoggedPerson' : LoggedPerson}

    if request.GET:
        TypeChoiceFormInstance = TypeChoiceForm(request.GET)
        ChoiceFormInstance = ChoiceForm(request.GET)
    else:
        TypeChoiceFormInstance = TypeChoiceForm()
        ChoiceFormInstance = ChoiceForm()
    QueryType = ""
    QueryReference = ""
    QueryRevision = ""
    if ChoiceFormInstance.is_valid():
        QueryType = ChoiceFormInstance.cleaned_data["type"]
        QueryReference = ChoiceFormInstance.cleaned_data["reference"]
        QueryRevision = ChoiceFormInstance.cleaned_data["revision"]
    if QueryType or QueryReference or QueryRevision:
        results = models.PLMObject.objects.filter(type__icontains=QueryType, reference__icontains=QueryReference, revision__icontains=QueryRevision)
    else:
        results = []
    
    VariablesDictionnary.update({'results': results, 'QueryType': QueryType, 'QueryReference': QueryReference, 'QueryRevision': QueryRevision, 'TypeChoiceForm': TypeChoiceFormInstance, 'ChoiceForm': ChoiceFormInstance})
    return render_to_response('DisplayHomePage.htm', VariablesDictionnary)

######################################################
# Manage html pages for part creation / modification #
######################################################

# Create a list of an object's attributes we can't modify' and set them a value
def CreateNonModifyableAttributesList(Classe=models.PLMObject):
    NonModifyableFieldsList = Classe.excluded_creation_fields()
    NonModifyableAttributesList=[]
    NonModifyableAttributesList.append((NonModifyableFieldsList[0], 'Person'))
    NonModifyableAttributesList.append((NonModifyableFieldsList[1], 'Person'))
    NonModifyableAttributesList.append((NonModifyableFieldsList[2], 'Date'))
    NonModifyableAttributesList.append((NonModifyableFieldsList[3], 'Date'))
    return NonModifyableAttributesList

# Manage html page for the part creation
def CreateObject(request):
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

# Manage html page for part modification
def ModifyObject(request, ObjectTypeValue, ObjectReferenceValue, ObjectRevisionValue):
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









