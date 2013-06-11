import os
import json
import zipfile

from django.core.files import File
from django.db import transaction
from django.db.models import Q

import openPLM.plmapp.models as models
from openPLM.plmapp.views.base import get_obj_by_id, object_to_dict
from openPLM.plmapp.views.api import login_json
import openPLM.apps.document3D.models as models3D
from openPLM.apps.document3D.forms import AssemblyForm

from .assembly import AssemblyBuilder, get_assembly_info


def get_document3D(request, doc_id):
    doc = get_obj_by_id(doc_id, request.user)
    if doc.type != "Document3D":
        raise ValueError("Document must be a Document3D")
    doc.check_readable()
    return doc


@login_json
def get_all_3D_docs(request):
    return {"types" : sorted(models.get_all_subtype_documents(models3D.Document3D).keys())}

def get_files(doc, checkout_type):
    if checkout_type == "stp":
        query = models3D.is_stp
    elif checkout_type == "catia":
        query = models3D.is_catia
    else:
        extensions = checkout_type.lower().split(",")
        if not extensions:
            return doc.files.none()
        query = Q()
        for ext in extensions:
            if not ext.isalnum():
                return doc.files.none()
            query != Q(filename__iendswith="." + ext)
    return doc.files.filter(query)



@login_json
def prepare_multi_check_out(request,doc_id):

    root_document = models3D.Document3D.objects.get(id=doc_id)
    controller=models3D.Document3DController(root_document,request.user)
    controller.check_readable()
    controller.check_edit_files()
    dict_args= dict(json.loads(request.POST["args"]))
    type_check_out =dict_args["type_check_out"]
    documents=dict_args["documents"]

    if type_check_out == "stp":
        lock_docfiles(documents,request.user,type_check_out)
        #to avoid weird concurrency events verify all documents were locked by the user
        STP_file=root_document.files.get(models3D.is_stp)
        return {"id" : STP_file.id , "filename" : STP_file.filename , "object" : object_to_dict(controller)}

    elif type_check_out == "catia":
        objects=lock_docfiles(documents,request.user,type_check_out)
        roots=possibles_root_catia(root_document)
        return {"objects" : objects, "roots" : roots ,  "object" : object_to_dict(controller)}
    else:
        objects=lock_docfiles(documents, request.user,type_check_out)
        roots = objects
        return {"objects" : objects, "roots" : roots ,  "object" : object_to_dict(controller)}



@transaction.commit_on_success
def lock_docfiles(documents, user,type_check_out):  # para generar bien el commit on succes

    objects=[]
    for elem in documents:
        doc_id=elem["id"]
        check_out=bool(elem["check-out"])
        document = models3D.Document3D.objects.get(id=doc_id)
        controller=models3D.Document3DController(document,user)

        try:
            for doc_file in get_files(document, type_check_out):
                objects.append(dict(id=doc_file.id,check_out=check_out,filename=doc_file.filename))
                if check_out:
                    controller.lock(doc_file)

        except:
            raise Exception("File related to " + document.__unicode__() + " was locked by other user or it could not be found.Please, restart the process")

    return objects


@login_json
def get_decomposition_documents(request, doc_id, type_check_out):
    """
    """

    #root
    objects=[]
    document = models3D.Document3D.objects.get(id=doc_id)
    ctrl = models3D.Document3DController(document, request.user)
    ctrl.check_readable()

    ids = set()
    files, check_out_valide = files_for_decomposition(document, type_check_out)
    ids.add(document.id)

    objects.append(dict(id=document.id, name=document.name, type=document.type,
        revision=document.revision, reference=document.reference,
        files=files, check_out_valide=check_out_valide))

    #children
    if files:
        exploreAroborescense(document, type_check_out, objects,ids)

    return {"objects" : objects  }


def exploreAroborescense(document,type_check_out,objects,ids):

    doc_related=document.documents_related

    for doc in doc_related:
        if doc.id in ids: # avoiding duplicated results
            continue
        files, check_out_valide = files_for_decomposition(doc,type_check_out)
        ids.add(doc.id)
        objects.append(dict(id=doc.id, name=doc.name, type=doc.type,
            revision=doc.revision, reference=doc.reference, files=files,
            check_out_valide=check_out_valide))
        if files:
            exploreAroborescense(doc,type_check_out,objects,ids)


def possibles_root_catia(doc):

    catia_files=doc.files.filter(models3D.is_catia)
    stp_file=doc.files.filter(models3D.is_stp)
    possibles_root=[]
    if stp_file:
        stp_file=stp_file[0]
        stpName , stpExtension = os.path.splitext(stp_file.filename)

        for doc_file in catia_files:
            nativeName, native_ext = os.path.splitext(doc_file.filename)
            if nativeName == stpName:
                if native_ext.lower()==".catproduct":
                    return [dict(filename=doc_file.filename)]
                possibles_root.append(dict(filename=doc_file.filename))

        if possibles_root:
            return possibles_root
    for doc_file in catia_files:
        possibles_root.append(dict(filename=doc_file.filename))
    return possibles_root


def files_for_decomposition(doc, type_check_out):
    files = []
    check_out_valid = True
    doc_files = get_files(doc, type_check_out)
    for doc_file in doc_files:
        files.append(dict(id=doc_file.id , name=doc_file.filename))
        if not doc_file.checkout_valid or doc_file.locked:
            check_out_valid = False
    return files, check_out_valid


@login_json
def add_zip_file(request, doc_id, unlock, thumbnail_extension="False" , thumbnail=False ):
    """

    """
    doc = get_obj_by_id(doc_id, request.user)
    zip_file = zipfile.ZipFile(request.FILES["filename"])

    files = zip_file.namelist()
    for filename in zip_file.namelist():
        if not filename.endswith(thumbnail_extension):
            tmp_file = zip_file.open(filename)
            dummy_file = File(tmp_file)
            try:
                dummy_file.name = filename.decode("utf-8")
            except UnicodeError:
                # WinZIP always decode filename as cp437,
                dummy_file.name = filename.decode("cp437")
            dummy_file.size = zip_file.getinfo(filename).file_size
            dummy_file.file = tmp_file
            df = doc.add_file(dummy_file,thumbnail=True)
            if unlock == "False" or unlock == "false":
                doc.lock(df)
            th = df.filename + "." + thumbnail_extension
            if thumbnail and th in files:
                tmp_file = zip_file.open(th)
                dummy_file = File(tmp_file)
                dummy_file.name = th
                dummy_file.size = zip_file.get_info(th).file_size
                dummy_file.file = tmp_file
                doc.add_thumbnail(df, dummy_file)
    return {}


@login_json
def add_assembly(request, doc_id):
    doc = get_document3D(request, doc_id)
    form = AssemblyForm(request.POST, request.FILES)
    if form.is_valid():
        builder = AssemblyBuilder(doc)
        tree = form.cleaned_data["assembly"]
        lock = form.cleaned_data["lock"]
        native_files = request.FILES.getlist("native_files")
        step_files = request.FILES.getlist("step_files")
        df = builder.build_assembly(tree, native_files, step_files, lock)
        return {"doc_file" : dict(id=df.id, filename=df.filename, size=df.size)}
    else:
        s = {"result": "error", "error": "invalid form", "form-errors": dict(form.errors)}
        return s


@login_json
def update_assembly(request, doc_id):
    doc = get_document3D(request, doc_id)
    form = AssemblyForm(request.POST, request.FILES)
    if form.is_valid():
        builder = AssemblyBuilder(doc)
        tree = form.cleaned_data["assembly"]
        lock = form.cleaned_data["lock"]
        native_files = request.FILES.getlist("native_files")
        step_files = request.FILES.getlist("step_files")
        df = builder.update_assembly(tree, native_files, step_files, lock)
        return {"doc_file" : dict(id=df.id, filename=df.filename, size=df.size)}
    else:
        s = {"result": "error", "error": "invalid form", "form-errors": dict(form.errors)}
        return s


@login_json
def get_assembly(request, doc_id):
    doc = get_document3D(request, doc_id)
    return get_assembly_info(doc)

