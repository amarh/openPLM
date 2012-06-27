# TODO: refactor this code

def generate_javascript_for_3D(product):
    """
    
    :param product: :class:`.Product` that represents the arborescense of the :class:`.DocumentFile` that we want to show
    
    From a :class:`.Product`  generates the code javascript necessarily to locate and to show the different geometries that compose the visualization 3D
    
    """
    if product:
        numeration=[0]
        javascript=['var object3D = new THREE.Object3D(); var part_to_object = {}; var part_to_parts = {};\n']        
        javascript_menu=['function menu() {\nelement = document.createElement("div");\nelement.id="root";\nelement.innerHTML ="']
        
        javascript[0]+='var part%s=new THREE.Object3D();\n'%numeration[0]
        javascript_menu[0]+=function_generate_menu(numeration[0],product.name)         

        generate_javascript(product,numeration,javascript,[],javascript_menu,numeration[0])
        
        javascript_menu[0]+='</li></ul>' 
        javascript_menu[0]+='";\ndocument.getElementById("menu_").appendChild(element);\n}\n'

        return javascript_menu[0]+javascript[0]
    else:
        return False
    
       
def generate_javascript(product,numeration,javascript,loc,javascript_menu,old_numeration):
    numeration[0]+=1     

    javascript_menu[0]+="<ul>"
        
    if product.geometry==False:
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
    parts_definition = []
    function = [function_head % locals()]
    part_to_parts = ['part_to_parts["part%s"] = [' % numeration]
    for part_numeration_child in parts_generated:
        parts_definition.append( "var part%s=new THREE.Object3D();\n"%part_numeration_child)
        function.append(function_change_part % locals())
        part_to_parts.append('"part%s", ' % part_numeration_child)
    part_to_parts.append("];\n")
    function.append("}\n")
    return ''.join(parts_definition) + ''.join(function) + ''.join(part_to_parts)
 
def generate_functions_visibilty_object(numeration,object_numeration,product,loc):
    reference=product.geometry
    part_id=str(product.doc_id)        
                                           
    function= function_head % locals() + function_change_object % locals() + "}\n"
    function += "part_to_object['part%(numeration)s'] = object%(object_numeration)s;" % locals()
  
    return generate_object(loc,object_numeration,reference,part_id)+function     


def generate_object(loc,numeration,reference,part_id):

    locate="var object%s=new THREE.Mesh(_%s_%s,material_for_%s_%s );\n"%(numeration,reference,part_id,reference,part_id)
    locate+="object%s.matrixAutoUpdate = false;\n"%numeration
    if len(loc)>0:
        for g in range(len(loc)):
            locate+="object%s.matrix.multiplySelf(new THREE.Matrix4(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,0,0,1));\n"%(numeration,loc[g].x1,loc[g].x2,loc[g].x3,loc[g].x4,loc[g].y1,
            loc[g].y2,loc[g].y3,loc[g].y4,loc[g].z1,loc[g].z2,loc[g].z3,loc[g].z4)

    locate+="object3D.add(object%s);\n"%numeration    
    return locate
    
       
def function_generate_menu(numeration,name):

    onclick="change_part"+str(numeration)+"(\\\"click\\\")" 
    return "<li > <a href='#' id='li-part-%s' onClick='%s'><b onClick='%s'></b>%s </a>" % (numeration, onclick,onclick,name)
    
    
         
function_head = """
function change_part%(numeration)s(attr) {
    if (attr == "click"){
    
        part%(numeration)s.visible=!part%(numeration)s.visible;
        
    }
    else{
        part%(numeration)s.visible=attr;
    }       
""" 


function_change_part = """
    change_part%(part_numeration_child)s(part%(numeration)s.visible); 
"""
function_change_object = """
    object%(object_numeration)s.visible=part%(numeration)s.visible;   
"""                                    

