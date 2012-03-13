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


def decomposer_all(doc_file,list_document_controller,links,user):
    
    try:	
	    my_step_importer = NEW_STEP_Import(doc_file) 
	    product=my_step_importer.generate_product_arbre()
	    to_delete=[]
	    for i,link in enumerate(product.links):
		    diviser(link.product,list_document_controller[i],doc_file,to_delete)
	    decomposer_product(my_step_importer,doc_file,user,to_delete)                                
    except:
        raise  Document3D_decomposer_Error(to_delete)


def diviser(product,Doc_controller,doc_file,to_delete):



    new_doc_file=generate_DocumentFile(product,Doc_controller,product.label_reference,product.name+".stp".encode("utf-8"),to_delete)
  
    index_reference=[0]
    assigned_index=[]
    update_product(product,new_doc_file,doc_file,index_reference,assigned_index,to_delete)
    to_delete.append(write_ArbreFile(product,new_doc_file))
               

    
        
       


def is_decomposable(Document3D):

    
    STP_file=Document3D.files.filter(is_stp)
    if STP_file.exists() and elements_decomposable(STP_file[0]) and STP_file[0].checkout_valid and not STP_file[0].locked:
        return STP_file[0]      
    return False



         
def elements_decomposable(fileSTP):

    product=read_ArbreFile(fileSTP)               
    if product:
        return product.links
    return False 



def update_product(product,new_doc_file,old_doc_file,index_reference,assigned_index,to_delete):

    product.doc_id=new_doc_file.id
   
    if product.geometry:
        copy_js(product,old_doc_file,new_doc_file,index_reference,assigned_index,to_delete)           
      
    else:            
        for link in product.links:
            update_product(link.product,new_doc_file,old_doc_file,index_reference,assigned_index,to_delete)  
    return True


def copy_js(product,old_doc_file,new_doc_file,index_reference,assigned_index,to_delete):
    



    if not assigned_index.count(product.geometry.reference):

        old_GeometryFile=GeometryFile.objects.get(stp=old_doc_file,index=product.geometry.reference)
        new_GeometryFile= GeometryFile()           

        fileName, fileExtension = os.path.splitext(new_doc_file.filename)
        
           
        new_GeometryFile.file = new_GeometryFile.file.storage.get_available_name(fileName+".geo")
        new_GeometryFile.stp = new_doc_file
        new_GeometryFile.index = index_reference[0]
        new_GeometryFile.save() 
        to_delete.append(new_GeometryFile.file.path) 
        
        
                       
        infile = open(old_GeometryFile.file.path,"r")
        outfile = open(new_GeometryFile.file.path,"w")
        
        for line in infile.readlines(): 
            new_line=line.replace("_%s_%s"%(product.geometry.reference,old_doc_file.id),"_%s_%s"%(index_reference[0],new_doc_file.id))
            outfile.write(new_line)
            
            
        assigned_index.append(product.geometry.reference)
        product.geometry.reference=index_reference[0]
        index_reference[0]+=1

    else:
        product.geometry.reference=assigned_index.index(product.geometry.reference)
            



def decomposer_product(my_step_importer,stp_file,user,to_delete):

    product=my_step_importer.generate_product_arbre()
    shape_tool=my_step_importer.shape_tool
    labels_roots = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels_roots)
    
    
    Doc_controller=get_controller(stp_file.document.type)
    Doc_controller=Doc_controller(stp_file.document,user)




       
    
    for i in range(labels_roots.Length()):
        if shape_tool.IsAssembly(labels_roots.Value(i+1)):
            l_c = TDF_LabelSequence()
            shape_tool.GetComponents(labels_roots.Value(i+1),l_c)
            for e in range(l_c.Length()):
                shape_tool.RemoveComponent(l_c.Value(e+1))


    new_doc_file=generate_DocumentFile(product,Doc_controller,labels_roots.Value(1),stp_file.filename,to_delete)
    product.links=[]
    product.doc_id=new_doc_file.id
    to_delete.append(write_ArbreFile(product,new_doc_file))    
    



    
    
def generate_DocumentFile(product,Doc_controller,label,new_name,to_delete):

    new_doc_file=DocumentFile()
    name = new_doc_file.file.storage.get_available_name(product.name+".stp")
    path = os.path.join(new_doc_file.file.storage.location, name)

    WS = XSControl_WorkSession()
    writer = STEPCAFControl_Writer( WS.GetHandle(), False )
        
    writer.Transfer(label, STEPControl_AsIs) 


    f = File(open(path.encode(), 'w'))   
    status = writer.Write(f.name)
    f = File(open(path.encode(), 'r'))
    
     
    Doc_controller.check_permission("owner")
    Doc_controller.check_editable()
    
    if settings.MAX_FILE_SIZE != -1 and f.size > settings.MAX_FILE_SIZE:
        raise ValueError("File too big, max size : %d bytes" % settings.MAX_FILE_SIZE)
            
    if Doc_controller.has_standard_related_locked(f.name):
        raise ValueError("Native file has a standard related locked file.") 
   
             
    new_doc_file.filename=new_name
    new_doc_file.size=f.size
    new_doc_file.file=name
    new_doc_file.document=Doc_controller.object
    new_doc_file.save()
    to_delete.append(new_doc_file.file.path)       
    os.chmod(new_doc_file.file.path, 0400)

    Doc_controller._save_histo("File added", "file : %s" % new_doc_file.filename)


    return new_doc_file 
    
    
   

    


    

