import sys
import django.utils.simplejson as json

from OCC.TDF import TDF_LabelSequence
from OCC.XSControl import XSControl_WorkSession
from OCC.STEPControl import STEPControl_AsIs
from OCC.STEPCAFControl import STEPCAFControl_Writer
from OCC.TopLoc import TopLoc_Location
from OCC.gp import gp_Trsf
from STP_converter_WebGL import NEW_STEP_Import , SetLabelNom , colour_chercher
from classes import Product_from_Arb
from OCC.Quantity import Quantity_Color





def composer(temp_file_name):

    """
    
    :param temp_file_name: path of a  :class:`.tempfile` **.arb** that contains the information to generate a :class:`.Product` relative to the arborescense of a **.stp** file

    
    For every node of the :class:`.Product`  the attribute **doc_file_path** indicates where is store the file **.stp** that represents the node
    
    """
    
    output = open(temp_file_name.encode(),"r")
    product =Product_from_Arb(json.loads(output.read()))
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

    if product.links:
        for link in product.links:

        
            if link.product.doc_id!= product.doc_id: # solo los que esten descompuesto, si no esta descompuesto no tiene que anadirlo

                if not link.product.label_reference:

                    my_step_importer = NEW_STEP_Import(link.product.doc_path)
                    lr_2= TDF_LabelSequence()
                    my_step_importer.shape_tool.GetFreeShapes(lr_2)        
                    add_labels(link.product,lr_2.Value(1),my_step_importer.shape_tool)
                    link.product.label_reference=lr_2.Value(1)
                    
                for d in range(link.quantity):

                    transformation=gp_Trsf()
                    
                    transformation.SetValues(link.locations[d].x1,link.locations[d].x2,link.locations[d].x3,link.locations[d].x4,
                    link.locations[d].y1,link.locations[d].y2,link.locations[d].y3,link.locations[d].y4,link.locations[d].z1,link.locations[d].z2,
                    link.locations[d].z3,link.locations[d].z4,1,1) 
                     
                    new_label=st.AddComponent(lr,link.product.label_reference,TopLoc_Location(transformation))
                    SetLabelNom(new_label,link.names[d])

                
            else:
                pass # no hace falta por que ya esta en la geometria
                                         
                
if __name__ == "__main__":    
    composer(sys.argv[1])  
  
    
    
    
    
     
    
