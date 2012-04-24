
import hashlib
import string
import random
import os
import django.utils.simplejson as json
import sys





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
    """
    Class used to represent the **arborescense** contained in a :class:`~django.core.files.File` **.stp**.A :class:`.Product` can be simple or an assembly, if it is an assembly in **links** we will guard the information about other :class:`.Product` that compose it
    
    :model attributes:

    .. attribute:: links
             
        If the product is an assembly, links stores one or more :class:`.openPLM.document3D.classes.Link` references to the products that compose it   


    .. attribute:: label_reference
    
        When we generate an arborescense using pythonOCC, here we will store the label that represents the :class:`.Product` ,if we generate the arborescense reading a file **.geo**, this attribute will be **False**
        
    .. attribute:: name
    
        Name of :class:`.Product` ,if the name is empty and there exists a :class:`.Link` at the :class:`.Product` , we will assign the name of the :class:`.Link` to the :class:`.Product`
        
    .. attribute:: doc_id
    
        Id of the :class:`.DocumentFile` that contains the :class:`.Product` , in the case of :class:`~django.core.files.File` .stp decomposed them **doc_id** maybe different for every :class:`.Product` of the arborescense    
        
    .. attribute:: doc_path
    
        Path of the :class:`~django.core.files.File` represented by the :class:`.DocumentFile` that contains the product   
        
    .. attribute:: part_to_decompose
    
        Used in the decomposition, it indicates the :class:`.Part` where the :class:`.Product` was decomposed

    .. attribute:: geometry
    
        If geometry is True (>=1) then the :class:`.Product` is single (without **links** )  , and his value refers to the index that we will use to recover a :class:`.GeometryFile`          
        
    .. attribute:: deep
    
        Depth in the arborescense  
        
    .. attribute:: visited
    
        Used in the decomposition , indicates if a :class:`.Product`  has been visited in the tour of the arborescense
              
    """
    __slots__ = ("label_reference","name","doc_id","links","geometry","deep","doc_path","visited","part_to_decompose")
    
    
    def __init__(self,name,deep,label_reference,doc_id,doc_path=None,geometry=False):
        #no tiene location
        self.links = []          
        self.label_reference=label_reference
        #if name="":
            #raise "Must we forbid it?"  
        self.name=name
        self.doc_id=doc_id
        self.doc_path=doc_path 
        self.part_to_decompose=False
        self.geometry=geometry 
        self.deep=deep
        self.visited=False
    def set_geometry(self,geometry):
        #0 cant be a valid geometry index , 0==False
        if geometry:
            self.geometry=geometry
        else:
            raise Document3D_generate_Index_Error
    
        
    @property       
    def is_decomposed(self):
        """
        If it is an assembly and the any :class:`.Product` contents in his **links**  are defined (**doc_id**) in another :class:`DocumentFile` (**doc_id**)
        """
        for link in self.links:
            if not link.product.doc_id == self.doc_id:
                return True 
        return False
        
    @property       
    def is_decomposable(self):
        """
        If it is an assembly and any :class:`.Product` contents in his **links** are defined (**doc_id**) in the same :class:`DocumentFile` (**doc_id**)
        """
        for link in self.links:
            if link.product.doc_id == self.doc_id:
                return True 
        return False
    @property  
    def is_assembly(self):
        if self.links:
            return self.name 
        return False
        
 
         
class Link(object):
    """
    
    Class used to represent a :class:`Link` between a :class:`.Product`, a :class:`Link` can have several references, each one with his own name and matrix of transformation. Every :class:`Link` points at a :class:`.Product`

    
    
    
    :model attributes:
        
        
    .. attribute:: names
    
        Name of each instances of the :class:`Link` , if the instance does not have name, he get the name of his :class:`.Product` child 

    .. attribute:: locations
    
        :class:`Matrix_rotation` of each instances of the :class:`Link` 
               
    .. attribute:: product
    
        :class:`.Product` child of the :class:`Link`
        
    .. attribute:: quantity
    
        Number of instances of the :class:`Link`  (Every instance have a **name** and **location**)
        
    .. attribute:: visited
    
        Used in the decomposition , indicates if a :class:`Link` has been visited in the tour of the arborescense  
    
    """    
    __slots__ = ("names","locations","product","quantity","visited")
    

    def __init__(self,product):
  
        self.names=[]           
        self.locations=[]
        self.product=product
        self.quantity=0
        self.visited=False#used only in multi-level decomposition


    def add_occurrence(self,name,Matrix_rotation):
        if name==u' ' or name==u'':
            self.names.append(self.product.name)    
        else:
            self.names.append(name)
            
            
        if self.product.name=="":
            self.product.name=name
               
        self.locations.append(Matrix_rotation)
        self.quantity=self.quantity+1

        
class Matrix_rotation(object):
    """
    
    Defines a non-persistent transformation in 3D space
         
     == == == == == = ==
     x1 x2 x3 x4  x = x'    
     y1 y2 y3 y4  y = y'    
     z1 z2 z3 z4  z = z'    
     0  0  0  1   1 = 1  
     == == == == == = ==
     
    
    """
    __slots__ = ("x1","x2","x3","x4","y1","y2","y3","y4","z1","z2","z3","z4")

    
    def __init__(self,list_coord):
    
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

   
    def to_array(self):    
        return [self.x1,self.x2,self.x3,self.x4,self.y1,self.y2,self.y3,self.y4,self.z1,self.z2,self.z3,self.z4] 
        


def Product_from_Arb(arbre,product=False,product_root=False,deep=0,to_update_product_root=False):   

    """ 
    
    :param arbre: chain of characters formatted (following the criteria of the function :class:`.data_for_product`) that represents an arborescense,It contains necessary information to construct :class:`.Product` and :class:`Link` 

    :param product: Product that represents a arborescense , **ONLY** used in successive recursive calls of the function
    :type plmobject: :class:`.Product`
    :param product_root: Product that represents a root arborescense , used to determine if the product to generating is already present in the tree 
    :type plmobject: :class:`.Product`
    :param deep: depth of **product** in the arborescense
    :param to_update_product_root: Product that represents a node of an arborescense  (sub-brach of arborescense referenced by **product_root**)
    :type plmobject: :class:`.Product`
        
    
   
    
    From the information contained in a file **.arb** (**arbre**), it generates the corresponding :class:`Product`
    In case of files STEP decomposed, this information can be distributed in several files **.arb** and due to the 
    nature of the decomposition, a **product** could be generated more than once , to avoid this we use the **product_root**.
    Whenever we generate a new product we verify that it is not already present in **product_root**,we use **to_update_product_root** 
    to support updated **product_root**(**to_update_product_root** is a branch of **product_root**)
    
    Example:
        -If we want to generate a **product** of a single file **.arb**
            tree =Product_from_Arb(json.loads(new_ArbreFile.file.read()))
            
            
        -If we want to generate a **product** of a single file .arb and link this one like a branch of a certain **product_root_node** of an already existing **product_root**
         
            product=Product_from_Arb(json.loads(new_ArbreFile.file.read()),product=False, product_root=product_root, deep=xxx, to_update_product_root=product_root_node)
             
            This method generates the :class:`Link` between **product_root_node** and  **product** ,**BUT** it does not add the occurrences, generally this occurrences are stored in the 
            existing  :class:`Location_link` between :class:`Part`
            
                After generating the **product** and the :class:`Link`, we will have to refill the :class:`Link` calling the function :meth:`.add_occurrence` for the :class:`Link`:
                
                
                    for location in locations:
                        product_root_node.links[-1].add_occurrence(location.name,location)
    
    
    """
    label_reference=False
                 
    if not product_root: 
        product=generateProduct(arbre,deep)
        product_root=product
        
        
    elif to_update_product_root: #Important, in case of generation of a tree contained in several files, it supports updated product_root
        product=generateProduct(arbre,deep)
        product_assembly=search_assembly(product.name,label_reference,product.doc_id,product_root,product.geometry)
        if product_assembly: 
            to_update_product_root.links.append(Link(product_assembly))
            return False 
        else:
            to_update_product_root.links.append(Link(product)) 
              
                    
    for i in range(len(arbre)-1):
        
        product_child=generateProduct(arbre[i+1][1],deep+1)
        product_assembly=search_assembly(product_child.name,label_reference,product_child.doc_id,product_root,product_child.geometry)

           
        if product_assembly:
            product_child=product_assembly 
            
           
                                    
        generateLink(arbre[i+1],product,product_child) 
               
        if not product_assembly:
            Product_from_Arb(arbre[i+1][1],product_child,product_root,deep+1)  
            
           
    return product 


        
def generateLink(arbre,product,product_child):
    """ 
    :param arbre: chain of characters formatted (following the criteria of the function :class:`.data_for_product`) that represents the different occurrences of a :class:`Link`
    :param product: :class:`Product` root of the assembly 
    :param product_child: :class:`Product` child of the assembly 
    
    """
    product.links.append(Link(product_child))
    for i in range(len(arbre[0])):
        product.links[-1].add_occurrence(arbre[0][i][0],Matrix_rotation(arbre[0][i][1]))
        
                 
def generateProduct(arbre,deep):
    """ 
    :param arbre: chain of characters formatted (following the criteria of the function :class:`.data_for_product`) that represents a :class:`Product` 
    :param deep: depth of :class:`Product`
    
    """
    label_reference=False
    return Product(arbre[0][0],deep,label_reference,arbre[0][1],arbre[0][3],arbre[0][2])   




def search_assembly(name,label,doc_id,product_root,geometry): 
    """
    
    :param product_root: :class:`Product` that represents a root arborescense  
    :type plmobject: :class:`.Product`
    :param geometry: indicates if the :class:`Product` for that we look is a Assembly (**product.geometry** is False )or a simple :class:`Product` (**product.geometry** >=1)
    :param name: name of :class:`Product` for that we look
    :param doc_id: id of :class:`.DocumentFile` that contains the :class:`Product` for that we look
    :param label: label generated by pythonOCC that represent the :class:`Product` for that we look
         
    Function that it checks if a :class:`Product` (determined by **name** , **id** and **geometry** or by **name** and **label**)is already present in a arborescense :class:`Product` (**product_root**)
    There are two manners of comparison, across **name** and **label_referencia**, generated for pythonOCC for every product, or across **name**, **doc_id** and **geometry** ,extracted of a file **.geo**
    """
  
    if product_root: 
        for link in product_root.links:

            if (name and link.product.name==name and  
            ((geometry and link.product.geometry) or (not geometry and not link.product.geometry))):# 2 assemblys or 2 geometrys wtih same name       
                                
                if label:
                    
                    if link.product.label_reference==label:
                        return link.product
                    
                    
                elif doc_id==link.product.doc_id and geometry==link.product.geometry:
                    return link.product                                        
                    
        
                #raise "2 diferent assembly or geometrys with same name" #is not recomndable to had 2 product or 2 assembly whit same name

                    

     
            product=search_assembly(name,label,doc_id,link.product,geometry)
            if product:
                return product

    
   
    
            
def data_for_product(product):
    """
    :param product: :class:`Product` for which the chain was generated
    
    generate a chain of characters formatted that contains information about a :class:`Product`
    
    """
    output=[]

    output.append([product.name,product.doc_id,product.geometry,product.doc_path])  
    
    for link in product.links:
        output.append(data_for_link(link))    
    return output            

               
def data_for_link(link):
    """
    :param product: :class:`Link` for which the chain was generated
    
    generate a chain of characters formatted that contains information about a :class:`Link`
    
    """    
    output=[]    
    name_loc=[]
    for i in range(link.quantity):             
        name_loc.append([link.names[i],link.locations[i].to_array()]) 
               
    output.append(name_loc)        
    output.append(data_for_product(link.product))
        
    return output
 
