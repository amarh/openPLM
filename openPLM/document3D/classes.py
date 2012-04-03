from OCC.gp import gp_Trsf
import hashlib
import string
import random
import os
import django.utils.simplejson as json


def get_available_name(location, name):

   
    def rand():
        r = ""
        for i in xrange(7):
            r += random.choice(string.ascii_lowercase + string.digits)
        return r
    basename = os.path.basename(name)
    base, ext = os.path.splitext(basename)
    ext2 = ext.lstrip(".").lower() or "no_ext"
    md5 = hashlib.md5()
    md5.update(basename)
    md5_value = md5.hexdigest() + "-%s" + ext
    path = os.path.join(ext2, md5_value % rand())
    while os.path.exists(os.path.join(location, path)):
        path = os.path.join(ext2, md5_value % rand())
    return path   

class Product(object):

    __slots__ = ("label_reference","name","doc_id","links","geometry","deep","doc_path")
    
    
    def __init__(self,name,deep,label_reference,doc_id,doc_path=None,geometry=None):
        #no tiene location
        self.links = []
        self.label_reference=label_reference
        self.name=name
        self.doc_id=doc_id
        self.doc_path=doc_path
        self.geometry=geometry
        self.deep=deep
    def set_geometry(self,geometry):
        self.geometry=geometry
    
        
    @property       
    def is_decomposed(self):
        for link in self.links:
            if not link.product.doc_id == self.doc_id:
                return True 
        return False    
class Link(object):

    __slots__ = ("names","locations","product","quantity")
    
    
    def __init__(self,product):
  
        self.names=[]           
        self.locations=[]
        self.product=product
        self.quantity=0


    def add_occurrence(self,name,Matrix_rotation):
        if name==u' ' or name==u'':
            self.names.append(self.product.name)    
        else:
            self.names.append(name)
        self.locations.append(Matrix_rotation)
        self.quantity=self.quantity+1

        
class Matrix_rotation(object):

    __slots__ = ("x1","x2","x3","x4","y1","y2","y3","y4","z1","z2","z3","z4")
    
    
    def __init__(self,transformation,list_coord=False):
    
        if list_coord:
            self.x1=list_coord[0]           
            self.x2=list_coord[1] 
            self.x3=list_coord[2] 
            self.x4=list_coord[3] 
            self.y1=list_coord[4]         
            self.y2=list_coord[5] 
            self.y3=list_coord[6] 
            self.y4=list_coord[7] 
            self.z1=list_coord[8]         
            self.z2=list_coord[9] 
            self.z3=list_coord[10] 
            self.z4=list_coord[11]    

        else:   

            m=transformation.VectorialPart()
            gp=m.Row(1)
            self.x1=gp.X()           
            self.x2=gp.Y()
            self.x3=gp.Z()
            self.x4=transformation.Transforms()[0]
            gp=m.Row(2)
            self.y1=gp.X()          
            self.y2=gp.Y()
            self.y3=gp.Z()
            self.y4=transformation.Transforms()[1]
            gp=m.Row(3)
            self.z1=gp.X()         
            self.z2=gp.Y()
            self.z3=gp.Z()
            self.z4=transformation.Transforms()[2]   
    def Transformation(self):
        transformation=gp_Trsf()
        transformation.SetValues(self.x1,self.x2,self.x3,self.x4,self.y1,self.y2,self.y3,self.y4,self.z1,self.z2,self.z3,self.z4,1,1)
        return transformation     
        
    def to_array(self):    
        return [self.x1,self.x2,self.x3,self.x4,self.y1,self.y2,self.y3,self.y4,self.z1,self.z2,self.z3,self.z4] 
        





def generateArbre(arbre,deep=0,product_root=None):   
    label_reference=False
    product_assembly=search_assembly(arbre[0][0],label_reference,arbre[0][1],product_root)            
    if product_assembly:
        return product_assembly 
    else:    
        product=Product(arbre[0][0],deep,label_reference,arbre[0][1],arbre[0][3],arbre[0][2])
        if not product_root:
            product_root=product    
        for i in range(len(arbre)-1):
            product.links.append(generate_link(arbre[i+1],deep,product_root))
                 
    return product


        
def generate_link(arbre,deep,product_root):
  
    product=generateArbre(arbre[1],(deep+1),product_root)
    link=Link(product)
    for i in range(len(arbre[0])):
        link.add_occurrence(arbre[0][i][0],Matrix_rotation(False,arbre[0][i][1]))     
    return link


  

def search_assembly(name,label,id,product_root):
    if product_root: 
        for link in product_root.links:
            if name and link.product.name==name: # puede haber asembly sin nombre!
                if link.product.label_reference==label and id==link.product.doc_id: 
                    return link.product
                else:
                    pass
                    #raise "FATAL ERROR , 2 assembly diferente shape , FATAL FATALTALTALTALTATLA"
                
            else:
                product=search_assembly(name,label,id,link.product)
                if product:
                    return product


    
        
def data_for_product(product):
    output=[]

    output.append([product.name,product.doc_id,product.geometry,product.doc_path])  
    
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
 
