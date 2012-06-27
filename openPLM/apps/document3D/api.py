import io, os
import zipfile

from django.core.files import File
from django.db import transaction
import django.utils.simplejson as json

import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms
from openPLM.plmapp.base_views import get_obj_by_id, object_to_dict
from openPLM.plmapp.views.api import login_json
import openPLM.apps.document3D.models as models3D


@login_json
def get_all_3D_docs(request):
    return {"types" : sorted(models.get_all_subtype_documents(models3D.Document3D).keys())}
    
@login_json
def prepare_multi_check_out(request,doc_id): 

    root_document = models3D.Document3D.objects.get(id=doc_id) 
    controller=models3D.Document3DController(root_document,request.user)
    #dict_args= dict(request.POST["args"])
    dict_args= dict(json.loads(request.POST["args"]))
    type_check_out =dict_args["type_check_out"] #request.POST["type_check_out"]
    documents=dict_args["documents"]#dict(json.loads(request.GET["documents"]))

    if type_check_out=="stp":
        lock_of_documents_files_whit_extension(documents,[".stp",".step"],request.user,type_check_out) 
        #to avoid weird concurrency events verify all documents were locked by the user
        STP_file=root_document.files.get(models3D.is_stp)
        return {"id" : STP_file.id , "filename" : STP_file.filename , "object" : object_to_dict(controller)}

    elif type_check_out=="catia":                 
        objects=lock_of_documents_files_whit_extension(documents,[".catpart",".catproduct"],request.user,type_check_out)
        roots=possibles_root_catia(root_document)                
        return {"objects" : objects, "roots" : roots ,  "object" : object_to_dict(controller)}  


@transaction.commit_on_success
def lock_of_documents_files_whit_extension(documents, extensions,user,type_check_out):  # para generar bien el commit on succes

    objects=[]
    for elem in documents:
        doc_id=elem["id"] 
        check_out=bool(elem["check-out"])  
        document = models3D.Document3D.objects.get(id=doc_id) 
        controller=models3D.Document3DController(document,user)
        
        try:
            if type_check_out=="stp" and check_out:  
                STP_file=document.files.get(models3D.is_stp)                    
                controller.lock(STP_file)
            elif type_check_out=="catia":
                CATIA_files=document.files.filter(models3D.is_catia)
                for doc_file in CATIA_files:
                    objects.append(dict(id=doc_file.id,check_out=check_out,filename=doc_file.filename))
                    if check_out:  
                        controller.lock(doc_file)     
                                          
        except:
            raise Exception("File related to " + document.__unicode__() + " was locked by other user or it could not be found.Please, restart the process")    

    return objects   
    
    
@login_json
def get_decomposition_documents(request, doc_id ,type_check_out):
    """
    Returns all objects matching a query.

    :param editable_only: if ``"true"`` (the default), returns only editable objects
    :param with_file_only: if ``"true"`` (the default), returns only documents with 
                           at least one file

    :implements: :func:`http_api.search`
    """
    
    #root    
    objects=[]      
    document = models3D.Document3D.objects.get(id=doc_id) 
    ids = set() 
    files , check_out_valide = files_for_decomposition(document,type_check_out)
    ids.add(document.id)   
    
    objects.append(dict(id=document.id, name=document.name, type=document.type,revision=document.revision, reference=document.reference , files=files , check_out_valide=check_out_valide))       
 
    #children
    if files:      
        exploreAroborescense(document,type_check_out,objects,ids)    

    if type_check_out=="stp":
        return {"objects" : objects  } 
    elif type_check_out=="catia": 
        return {"objects" : objects }
        
        
def exploreAroborescense(document,type_check_out,objects,ids):

    doc_related=document.documents_related
    
    for doc in doc_related:
        if doc.id in ids: # avoiding duplicated results
            continue
        files , check_out_valide = files_for_decomposition(doc,type_check_out)
        ids.add(doc.id)
        objects.append(dict(id=doc.id, name=doc.name, type=doc.type,revision=doc.revision, reference=doc.reference , files=files , check_out_valide=check_out_valide))
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

                  
def files_for_decomposition(doc,type_check_out):
    files=[]
    check_out_valide=True
    if type_check_out=="catia":
        doc_fileS=doc.files.filter(models3D.is_catia)
    elif type_check_out=="stp": 
        doc_fileS=doc.files.filter(models3D.is_stp)
    
    for doc_file in doc_fileS:
        files.append(dict(id=doc_file.id , name=doc_file.filename))        
        if not doc_file.checkout_valid or doc_file.locked:
            check_out_valide=False
    return files ,  check_out_valide
    
@login_json    
def add_zip_file(request, doc_id, unlock , thumbnail_extension ="False" ,thumbnail=False ):
    """
    Adds a file to the :class:`.Document` identified by *doc_id*.

    :implements: :func:`http_api.add_file`
    
    :param request: the request
    :param doc_id: id of a :class:`.Document`
    :returned fields: doc_file, the file that has been had,
                      see :ref:`http-api-file`.
    """
    doc = get_obj_by_id(doc_id, request.user)
    form = forms.AddFileForm(request.POST, request.FILES)
    
    zip_file = zipfile.ZipFile(request.FILES["filename"])
    
    for filename in zip_file.namelist(): 
        if not filename.endswith(thumbnail_extension):
            buf = bytearray(zip_file.read(filename))
            tmp_file = io.BytesIO(buf)
            dummy_file = File(tmp_file)   
            dummy_file.name = filename
            dummy_file.size = len(buf)
            dummy_file.file = tmp_file
            df = doc.add_file(dummy_file,thumbnail=True)
            
            if unlock == "False" or unlock == "false":
                df.locked=True
                df.save()    
            if thumbnail:
                buf = bytearray(zip_file.read(filename+"."+thumbnail_extension))
                tmp_file = io.BytesIO(buf)
                dummy_file = File(tmp_file)   
                dummy_file.name = filename
                dummy_file.size = len(buf)
                dummy_file.file = tmp_file 
                doc.add_thumbnail(df, dummy_file)               
    return {"OK" : dict(id=unlock, filename=thumbnail, size=df.size)}

