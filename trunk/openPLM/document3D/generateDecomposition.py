import sys

from OCC.TDF import *
from OCC.XSControl import XSControl_WorkSession
from OCC.STEPCAFControl import * 
from OCC.STEPControl import *
from OCC.Utils.DataExchange.STEP import StepOCAF_Export
from STP_converter_WebGL import NEW_STEP_Import
import django.utils.simplejson as json
from classes import generateArbre
from OCC.GarbageCollector import garbage

def new_collect_object(self, obj_deleted):
        self._kill_pointed()

garbage.collect_object=new_collect_object


  
def decomposer(path,temp_file_name):


    output = open(temp_file_name.encode(),"r")
    old_product=generateArbre(json.loads(output.read()))
    my_step_importer = NEW_STEP_Import(path)
    shape_tool=my_step_importer.shape_tool 
    product=my_step_importer.generate_product_arbre()
    decomposer_links(product,old_product,shape_tool)
    cascade_decompose(product,old_product,shape_tool)


def decomposer_links(product,old_product,shape_tool): 


    
           
    for index,link in enumerate(product.links):
        if not link.product.visited:
            link.product.visited=True
            decomposer_links(link.product,old_product.links[index].product,shape_tool)
            
            cascade_decompose(link.product,old_product.links[index].product,shape_tool)

            





def cascade_decompose(product,old_product,shape_tool):

    if shape_tool.IsAssembly(product.label_reference):
        l_c = TDF_LabelSequence()
        shape_tool.GetComponents(product.label_reference,l_c)
        for e in range(l_c.Length()):
            shape_tool.RemoveComponent(l_c.Value(e+1)) 
            
    WS = XSControl_WorkSession()
    writer = STEPCAFControl_Writer( WS.GetHandle(), False )     
    writer.Transfer(product.label_reference, STEPControl_AsIs) 
    status = writer.Write(old_product.doc_path.encode("utf-8"))                      
 
    



    
    
decomposer(sys.argv[1],sys.argv[2]) 

