from django.shortcuts import render_to_response, get_object_or_404
import datetime

import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PLMObjectController

# All functions which manage the different html pages related to a part

# Build a list for the html page menu
def BuildMenu():
    return ["attributes", "lifecycle", "revisions", "history", "BOM-child", "parents", "doc-cad"]

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
    return PLMObjectController(obj, user)

# Initiate VariablesDictionnary we used after to transfer parameters to html pages
def InitVariablesDictionnary(InitTypeValue, InitReferenceValue, InitRevisionValue):
    now = datetime.datetime.now()
    return {
        'current_date': now,
        'ObjectReference': InitReferenceValue,
        'ObjectRevision': InitRevisionValue,
        'ObjectType': InitTypeValue,
        }

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

# Replace all whitespace characteres by %20 in order to be compatible with an URL
def ReplaceWhitespaces(Chain):
    return Chain.replace(" ","%20")


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


















