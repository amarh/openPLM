from openPLM.document3D.models import *
from openPLM.document3D.arborescense import *
from openPLM.document3D.STP_converter_WebGL import *
from OCC.TDF import *
from OCC.STEPCAFControl import *
from OCC.Utils.DataExchange.STEP import StepOCAF_Export
#from OCC import XCAFApp, STEPCAFControl, TDocStd, TCollection, XCAFDoc,  STEPControl
from tempfile import NamedTemporaryFile


def composer(doc_file,user):


    my_step_importer = NEW_STEP_Import(doc_file)
    product=read_ArbreFile(doc_file,user)

    

    st=my_step_importer.shape_tool
    lr= TDF_LabelSequence()
    st.GetFreeShapes(lr)
    
    add_labels(product,lr.Value(1),st)


    WS = XSControl_WorkSession()
    writer = STEPCAFControl_Writer( WS.GetHandle(), False )
    for i in range(lr.Length()):
        writer.Transfer(lr.Value(i+1), STEPControl_AsIs)
        
    f = NamedTemporaryFile(delete=False)
        
    status = writer.Write(f.name) 
    f.seek(0)
    return f
    
   
    
def add_labels(product,lr,st):

    for link in product.links:
        if link.product.doc_id!= product.doc_id:
            q1=DocumentFile.objects.get(id=link.product.doc_id)
            my_step_importer = NEW_STEP_Import(q1)

            lr_2= TDF_LabelSequence()

            my_step_importer.shape_tool.GetFreeShapes(lr_2)
            add_labels(link.product,lr_2.Value(1),my_step_importer.shape_tool)
               
            for d in range(link.quantity):
 

                new_label=st.AddComponent(lr,lr_2.Value(1),TopLoc_Location(link.locations[d].Transformation()))
                SetLabelNom(new_label,link.names[d])
                            
                
    
    
    
    
    
    
     
    
