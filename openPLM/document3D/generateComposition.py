import sys
import django.utils.simplejson as json

from OCC.TDF import TDF_LabelSequence
from OCC.XSControl import XSControl_WorkSession
from OCC.STEPControl import STEPControl_AsIs
from OCC.STEPCAFControl import STEPCAFControl_Writer
from OCC.TopLoc import TopLoc_Location

from STP_converter_WebGL import NEW_STEP_Import , SetLabelNom , colour_chercher
from classes import generateArbre






def composer(temp_file_name):


    
    output = open(temp_file_name.encode(),"r")
    product=generateArbre(json.loads(output.read()))
    output.close()
    output = open(temp_file_name.encode(),"w+")# erase old data
    output.close()
    my_step_importer = NEW_STEP_Import(product.doc_path)

  
    st=my_step_importer.shape_tool
    lr= TDF_LabelSequence()
    st.GetFreeShapes(lr)
    
    add_labels(product,lr.Value(1),st)

    
    WS = XSControl_WorkSession()
    writer = STEPCAFControl_Writer( WS.GetHandle(), False )
    for i in range(lr.Length()):
        writer.Transfer(lr.Value(i+1), STEPControl_AsIs)
        
    #f = NamedTemporaryFile(delete=False)
        
    status = writer.Write(temp_file_name) 
    #f.seek(0)
    #return f
    
    
   
    
def add_labels(product,lr,st):

    
    for link in product.links:

    
        if link.product.doc_id!= product.doc_id:

            my_step_importer = NEW_STEP_Import(link.product.doc_path)
            
            lr_2= TDF_LabelSequence()

            my_step_importer.shape_tool.GetFreeShapes(lr_2)
            
            add_labels(link.product,lr_2.Value(1),my_step_importer.shape_tool)
              
            for d in range(link.quantity):

                new_label=st.AddComponent(lr,lr_2.Value(1),TopLoc_Location(link.locations[d].Transformation()))
                SetLabelNom(new_label,link.names[d])
                                            
                
    
composer(sys.argv[1])    
    
    
    
    
     
    
