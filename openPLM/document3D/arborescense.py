from OCC.TopLoc import TopLoc_Location
from OCC.TDF import *
import os, os.path
from OCC.gp import *
from openPLM.plmapp.controllers.part import PartController
from openPLM.document3D.classes import *
import openPLM.document3D.classes as classes 
from openPLM.document3D.models import Document3D , ArbreFile , Location_link , is_stp , GeometryFile
from openPLM.plmapp.models import *
from openPLM.plmapp.models import DocumentFile
import django.utils.simplejson as json
    
def generate_javascript_for_3D(product):

    if product:
        numeration=[0]
        javascript=['var object3D = new THREE.Object3D();\n']        


        
        javascript_menu=['function menu() {\nelement = document.createElement("div");\nelement.id="root";\nelement.innerHTML ="']


        
        javascript[0]+='var part%s=new THREE.Object3D();\n'%numeration[0]
        javascript_menu[0]+=function_generate_menu(numeration[0],product.name)         

        ok=generate_javascript(product,numeration,javascript,[],javascript_menu,numeration[0])
        
        javascript_menu[0]+='</li></ul>' 
        javascript_menu[0]+='";\ndocument.getElementById("menu_").appendChild(element);\n}\n'

        return javascript_menu[0]+javascript[0]
    else:
        return False
    
       
def generate_javascript(product,numeration,javascript,loc,javascript_menu,old_numeration):
    
    
    numeration[0]+=1     

    javascript_menu[0]+="<ul>"
        
    if product.geometry==None:
        parts_generated=[]
             
        for link in product.links:
        
            
            
            for i in range(link.quantity):

                loc2=loc[:]
                loc2.append(link.locations[i])
                parts_generated.append(numeration[0])
                                 
                javascript_menu[0]+=function_generate_menu(numeration[0],link.names[i])                
                      
                generate_javascript(link.product,numeration,javascript,loc2,javascript_menu,numeration[0]) 
       
                javascript_menu[0]+="</li>"
            
                
        javascript[0]+=generate_functions_visibilty_parts(old_numeration,parts_generated)
    
    else:       
  
        javascript[0]+=generate_functions_visibilty_object(old_numeration,numeration[0],product,loc)
              

    javascript_menu[0]+="</ul>"        
        
                            
            



def generate_functions_visibilty_parts(numeration,parts_generated):


    parts_definition=""
    function=str(function_head % (locals()))
    for part_numeration_child in parts_generated:
        parts_definition+="var part%s=new THREE.Object3D();\n"%part_numeration_child
        function+=str(function_change_part % (locals()))
    function+="}\n"
    return parts_definition+function        



 
def generate_functions_visibilty_object(numeration,object_numeration,product,loc):


            
    reference=product.geometry
    part_id=str(product.doc_id)        
                                           
    function=str(function_head % (locals()))+str(function_change_object % (locals()))+"}\n"
  
    return generate_object(loc,object_numeration,reference,part_id)+function     




def generate_object(loc,numeration,reference,part_id):

    


    locate="var object%s=new THREE.Mesh(_%s_%s,material_for_%s_%s );\n"%(numeration,reference,part_id,reference,part_id)
    locate+="object%s.matrixAutoUpdate = false;\n"%numeration
    if len(loc)>0:
        transformation=gp_Trsf()
        gp=gp_XYZ()
        for g in range(len(loc)):
            if g==0:
                transformation=loc[g].Transformation()
            else:
                transformation.Multiply(loc[g].Transformation())
                
        a ,b =transformation.GetRotation(gp)
        t=transformation.TranslationPart()



        if a:        
            locate+="object%s.matrix.setRotationAxis(new THREE.Vector3( %s, %s, %s ), %s);\n"%(numeration,gp.X(),gp.Y(),gp.Z(),b)
                  
        locate+="object%s.matrix.setPosition(new THREE.Vector3( %s, %s, %s ));\n"%(numeration,t.X(),t.Y(),t.Z())
        
    locate+="object3D.add(object%s);\n"%numeration    
         
        
    
     
    return locate
    
def read_ArbreFile(doc_file,recursif=None):

 
    try:
        new_ArbreFile=ArbreFile.objects.get(stp=doc_file)
    except:
        return False

    product=generateArbre(json.loads(new_ArbreFile.file.read()))
    if recursif:
        add_child_ArbreFile(doc_file,product,product,deep=1)        
            
    return product
    

    
    
def add_child_GeometryFiles(doc_file,files_to_add):
#ahora puede tener 2 veces el mismo recorrido
    stp_related ,list_loc=get_step_related(doc_file)
    for stp in stp_related: 
        files_to_add+=list(GeometryFile.objects.filter(stp=stp))
        add_child_GeometryFiles(stp,files_to_add)
                        
                            
                            
def add_child_ArbreFile(doc_file,product,product_root,deep):


    stp_related,list_loc=get_step_related(doc_file)

    for i,stp in enumerate(stp_related):    
        #try:
        
        new_ArbreFile=ArbreFile.objects.get(stp=stp)
        new_product=generateArbre(json.loads(new_ArbreFile.file.read()),deep,product_root)                                                      
        product.links.append(classes.Link(new_product))                             
        for location in list_loc[i]:
            product.links[-1].add_occurrence(location.name,Matrix_rotation(location.Transforms()))
            
    
        add_child_ArbreFile(stp,new_product,product_root,deep+1)                       
        #except:

            #pass

                             

def get_step_related(doc_file,locations=None):
    stp_related=[]
    list_loc=[]
    Doc3D=Document3D.objects.get(id=doc_file.document.id)
    part=Doc3D.PartDecompose
    
    if part:
        list_link=ParentChildLink.objects.filter(parent=part, end_time=None)
        for i in range(len(list_link)):
            locations=list(Location_link.objects.filter(link=list_link[i]))
            if locations: 
                part_child=list_link[i].child
                part_controller=PartController(part_child,None)
                list_doc=part_controller.get_attached_documents()
                
                for Doc_Part_Link in list_doc:
                    if Doc_Part_Link.document.type=="Document3D":
                        STP_file=Doc_Part_Link.document.files.filter(is_stp)
                        if STP_file.exists():
                            stp_related.append(STP_file[0])
                            list_loc.append(locations)
                        else:
                            pass
                            #raise Document3D_link_Error
                            
                        break

    return stp_related , list_loc
                            
                                                       

    
    

        
def generate_ArbreFile(product,doc_file):



    #delete_ArbreFile(doc_file)
    
    
    data=data_for_product(product)

    fileName, fileExtension = os.path.splitext(doc_file.filename) 
    new_ArbreFile= ArbreFile()
    new_ArbreFile.stp = doc_file
    name = new_ArbreFile.file.storage.get_available_name(fileName+".arb")
    path = os.path.join(new_ArbreFile.file.storage.location, name)
    new_ArbreFile.file = name
    new_ArbreFile.save()
    directory = os.path.dirname(path.encode())        
    if not os.path.exists(directory):
        os.makedirs(directory)
    output = open(path.encode(),"w")
    output.write(json.dumps(data))        
    output.close() 
    return new_ArbreFile.file.path          
   
    
    
                
 
    
   

      
def function_generate_menu(numeration,name):

    onclick="change_part"+str(numeration)+"(\\\"click\\\")" 
    return "<li > <a href='#' onClick='%s'><b onClick='%s'></b>%s </a>"%(onclick,onclick,name)
    
    
         
function_head = """
function change_part%(numeration)s(atribute) {
    if (atribute==\"click\"){
    
        part%(numeration)s.visible=!part%(numeration)s.visible;
        
    }
    else{
        part%(numeration)s.visible=atribute;
    }       
""" 


function_change_part = """
    change_part%(part_numeration_child)s(part%(numeration)s.visible)       
"""
function_change_object = """
    object%(object_numeration)s.visible=part%(numeration)s.visible;   
"""                                    
    




#var NewMaterial=new THREE.MeshFaceMaterial({opacity:0.5,shading:THREE.SmoothShading});
  
    
    
    
    
