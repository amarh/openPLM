import sys

from OCC.TDF import *
from OCC.XSControl import XSControl_WorkSession
from OCC.STEPCAFControl import * 
from OCC.STEPControl import *
from OCC.Utils.DataExchange.STEP import StepOCAF_Export
from STP_converter_WebGL import NEW_STEP_Import
import django.utils.simplejson as json
from classes import generateArbre
  
def decomposer(path,temp_file_name,new_root_path):


    output = open(temp_file_name.encode(),"r")
    old_product=generateArbre(json.loads(output.read()))
    my_step_importer = NEW_STEP_Import(path) 
    product=my_step_importer.generate_product_arbre()

    
    for index,link in enumerate(product.links):
        WS = XSControl_WorkSession()
        writer = STEPCAFControl_Writer( WS.GetHandle(), False )
        writer.Transfer(link.product.label_reference, STEPControl_AsIs) 
        status = writer.Write(old_product.links[index].product.doc_path.encode("utf-8"))
           
    decomposer_root(my_step_importer,new_root_path)    
    

def decomposer_root(my_step_importer,new_root_path):

    shape_tool=my_step_importer.shape_tool
    labels_roots = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels_roots)
   
    for i in range(labels_roots.Length()):
        if shape_tool.IsAssembly(labels_roots.Value(i+1)):
            l_c = TDF_LabelSequence()
            shape_tool.GetComponents(labels_roots.Value(i+1),l_c)
            for e in range(l_c.Length()):
                shape_tool.RemoveComponent(l_c.Value(e+1))

    WS = XSControl_WorkSession()
    writer = STEPCAFControl_Writer( WS.GetHandle(), False )     
    writer.Transfer(labels_roots.Value(1), STEPControl_AsIs) 

    status = writer.Write(new_root_path.encode("utf-8"))
    
    
decomposer(sys.argv[1],sys.argv[2],sys.argv[3]) 

