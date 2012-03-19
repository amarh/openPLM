from OCC.TopLoc import TopLoc_Location
from OCC.TDF import *
import os, os.path
import django.utils.simplejson as json
from OCC.gp import *
from openPLM.plmapp.controllers.part import PartController
from openPLM.document3D.models import * 
   
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
        #javascript[0]+="object3D.matrixAutoUpdate = false;\n" 
        #javascript[0]+="object3D.updateMatrix();\n"
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


        red=1
        green=1
        blue=1
        reference=product.geometry
        part_id=str(product.doc_id)        
                                               
        function=str(function_head % (locals()))+str(function_change_object % (locals()))+"}\n"
      
        return generate_object(loc,object_numeration,reference,part_id)+function     




def generate_object(loc,numeration,reference,part_id):

    
    locate=""
    locate+="var NewMaterial=new THREE.MeshBasicMaterial({opacity:0.5,shading:THREE.SmoothShading});\n"
    locate+="var object%s=new THREE.Mesh(_%s_%s,NewMaterial );\n"%(numeration,reference,part_id)
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
    
def read_ArbreFile(doc_file,user=None):

 
    try:     
        new_ArbreFile=ArbreFile.objects.get(stp=doc_file)
    except:
        return False
    product=generate_product(json.loads(new_ArbreFile.file.read()))
    if user:
        add_child_ArbreFile(user,doc_file,product)        
            
        
    return product
    
     
def add_child_GeometryFiles(user,doc_file,files_to_add):

    stp_related ,list_loc=get_step_related(user,doc_file)
    for stp in stp_related: 
        files_to_add+=list(GeometryFile.objects.filter(stp=stp))
        add_child_GeometryFiles(user,stp,files_to_add)
                        
                            
                            
def add_child_ArbreFile(user,doc_file,product):


    stp_related,list_loc=get_step_related(user,doc_file)

    for i,stp in enumerate(stp_related):    
        try:
            new_ArbreFile=ArbreFile.objects.get(stp=stp)
            new_product=generate_product(json.loads(new_ArbreFile.file.read()))                                                      
            product.links.append(Link(new_product))                           
            for location in list_loc[i]:
                product.links[-1].add_occurrence(location.name,Matrix_rotation(location.Transforms()))
            add_child_ArbreFile(user,stp,new_product)                       
        except:
            pass

                                

def get_step_related(user,doc_file,locations=None):
    stp_related=[]
    list_loc=[]
    Doc3D=Document3D.objects.get(id=doc_file.document.id)
    part=Doc3D.PartDecompose
    
    if part:
        list_link=ParentChildLink.objects.filter(parent=part)
        for i in range(len(list_link)):
            locations=list(Location_link.objects.filter(link=list_link[i]))
            if locations: 
                part_child=list_link[i].child
                part_controller=PartController(part_child,user)
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
                            
                                                       
def generate_product(arbre):
    # no vamos a coger label cuando leemos de la bd    
    label_reference=False
    product=Product(arbre[0][0],arbre[0][1],label_reference,arbre[0][2])
    for i in range(len(arbre)-1):
        product.links.append(generate_link(arbre[i+1]))     
    return product

        
def generate_link(arbre):
  
    product=generate_product(arbre[1])
    link=Link(product)
    for i in range(len(arbre[0])):
        link.add_occurrence(arbre[0][i][0],Matrix_rotation(False,arbre[0][i][1]))     
    return link
    
    
    
def write_ArbreFile(product,doc_file):



    delete_ArbreFile(doc_file)
    
    
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
   
    
    
                
def data_for_product(product):
    output=[]

    output.append([product.name,product.doc_id,product.geometry])        

        
    for link in product.links:
        output.append(data_for_link(link))    
    return output            

               
def data_for_link(link):

    
    output=[]    
    name_loc=[]
    for i in range(link.quantity):             
        name_loc.append([link.names[i],link.locations[i].to_array()]) 
               
    output.append(name_loc)        
    output.append(data_for_product(link.product))
        
    return output    
    
   

      
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
  
    
    
    
    
