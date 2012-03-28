from openPLM.document3D.STP_converter_WebGL import *
from django.core.files import File
from OCC.Utils.DataExchange.STEP import StepOCAF_Export
from kjbuckets import kjGraph
from openPLM.document3D.models import *
from openPLM.document3D.arborescense import *
from OCC.TDF import *
from django.db.models import Q
import os, os.path
import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import get_controller


def decomposer_all(doc_file,list_document_controller,user):
    #atencion , no va a depreciar el objeto doc_file, esto tendra que ser realizado despues
    #tampoco indexa los documentfile , hacerlo a mano despues
    #normalmente vamos a llamar desde un commit on succes , para eso el to_delete
    try:	
        my_step_importer = NEW_STEP_Import(doc_file) 
        product=my_step_importer.generate_product_arbre()
        to_delete=[]
        to_index=[]
        for i,link in enumerate(product.links):
            diviser(link.product,list_document_controller[i],to_delete,to_index)
        decomposer_product(product,my_step_importer,doc_file,user,to_delete,to_index)
        return to_index                                 
    except:
        raise  Document3D_decomposer_Error(to_delete)


def diviser(product,Doc_controller,to_delete,to_index):


    doc_file=generate_DocumentFile(product,Doc_controller,product.label_reference,product.name+".stp".encode("utf-8"),to_delete,to_index)
  
    index_reference=[0] # to evade product.geometry=0
    assigned_index=[]
    update_product(product,doc_file,index_reference,assigned_index,to_delete)
    to_delete.append(write_ArbreFile(product,doc_file))
               

    
        
       


def is_decomposable(doc3d):

    try:
        stp_file=doc3d.files.get(is_stp, locked=False) #solo abra uno pero por si las moscas
    except:
        return False
    if not stp_file.checkout_valid:
        return False
    # TODO: store in a table decomposable step files
    # to not read its content
    product=read_ArbreFile(stp_file)   
    if product and product.links:
        return stp_file      
    return False



         


def update_product(product,doc_file,index_reference,assigned_index,to_delete):

    
   
    if not product.geometry==None:
        copy_js(product,doc_file,index_reference,assigned_index,to_delete)           
      
    else:            
        for link in product.links:
            update_product(link.product,doc_file,index_reference,assigned_index,to_delete)
            
    product.doc_id=doc_file.id
      
    return True


def copy_js(product,doc_file,index_reference,assigned_index,to_delete):
    



    if not assigned_index.count(product.geometry):

        old_GeometryFile=GeometryFile.objects.get(stp__id=product.doc_id,index=product.geometry)
        new_GeometryFile= GeometryFile()           

        fileName, fileExtension = os.path.splitext(doc_file.filename)
        
           
        new_GeometryFile.file = new_GeometryFile.file.storage.get_available_name(fileName+".geo")
        new_GeometryFile.stp = doc_file
        new_GeometryFile.index = index_reference[0]
        new_GeometryFile.save() 
        to_delete.append(new_GeometryFile.file.path) 
        
        
                       
        infile = open(old_GeometryFile.file.path,"r")
        outfile = open(new_GeometryFile.file.path,"w")
        
        for line in infile.readlines(): 
            new_line=line.replace("_%s_%s"%(product.geometry,product.doc_id),"_%s_%s"%(index_reference[0],doc_file.id))
            outfile.write(new_line)
            
            
        assigned_index.append(product.geometry)
        product.geometry=index_reference[0]
        index_reference[0]+=1

    else:
        product.geometry=assigned_index.index(product.geometry)
            



def decomposer_product(product,my_step_importer,doc_file,user,to_delete,to_index):

    shape_tool=my_step_importer.shape_tool
    labels_roots = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels_roots)
    
    
    Doc_controller=get_controller(doc_file.document.type)
    Doc_controller=Doc_controller(doc_file.document,user)




       
    
    for i in range(labels_roots.Length()):
        if shape_tool.IsAssembly(labels_roots.Value(i+1)):
            l_c = TDF_LabelSequence()
            shape_tool.GetComponents(labels_roots.Value(i+1),l_c)
            for e in range(l_c.Length()):
                shape_tool.RemoveComponent(l_c.Value(e+1))


    doc_file=generate_DocumentFile(product,Doc_controller,labels_roots.Value(1),doc_file.filename,to_delete,to_index)
    product.links=[]
    product.doc_id=doc_file.id
    to_delete.append(write_ArbreFile(product,doc_file))    
    return doc_file



    
    
def generate_DocumentFile(product,Doc_controller,label,new_name,to_delete,to_index):
    #no actualiza el historial ni indexa
    doc_file=DocumentFile()
    name = doc_file.file.storage.get_available_name(product.name+".stp")
    path = os.path.join(doc_file.file.storage.location, name)

    WS = XSControl_WorkSession()
    writer = STEPCAFControl_Writer( WS.GetHandle(), False )
        
    writer.Transfer(label, STEPControl_AsIs) 


    f = File(open(path.encode(), 'w'))   
    status = writer.Write(f.name)
    to_delete.append(f.name) 
    f = File(open(path.encode(), 'r'))
    
     
    Doc_controller.check_permission("owner")
    Doc_controller.check_editable()
    
    if settings.MAX_FILE_SIZE != -1 and f.size > settings.MAX_FILE_SIZE:
        raise ValueError("File too big, max size : %d bytes" % settings.MAX_FILE_SIZE)
            
    if Doc_controller.has_standard_related_locked(f.name):
        raise ValueError("Native file has a standard related locked file.") 
   
    doc_file.no_index=True        
    doc_file.filename=new_name
    doc_file.size=f.size
    doc_file.file=name
    doc_file.document=Doc_controller.object
    doc_file.save()
    
    to_index.append((doc_file._meta.app_label,doc_file._meta.module_name, doc_file._get_pk_val()))
    
    os.chmod(doc_file.file.path, 0400)
    
    #sacarlo fuera, por que si falla no abra anadido
    Doc_controller._save_histo("File added", "file : %s" % doc_file.filename)


    return doc_file 
    
    
   

    


    

