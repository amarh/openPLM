import sys
import os
from classes import data_for_product , get_available_name
from STP_converter_WebGL import NEW_STEP_Import , MultiRoot_Error , OCC_ReadingStep_Error 
import logging
import django.utils.simplejson as json
    


def generateGeometrys_Arborescense(doc_file_path,doc_file_id,location):
    """
    For a file STEP determined by his path, it generates his file .arb and his files .geo
    """ 
    logging.getLogger("GarbageCollector").setLevel(logging.ERROR)    
    my_step_importer = NEW_STEP_Import(doc_file_path,doc_file_id) 
    product_arbre=my_step_importer.generate_product_arbre()   
    geo=my_step_importer.procesing_geometrys(location)
    print geo
    print write_ArbreFile(product_arbre,my_step_importer.fileName,location)



def write_ArbreFile(product,fileName,location):


    
    
       
    data=data_for_product(product)
    name=get_available_name(location,fileName+".arb")
    path=os.path.join(location, name)
    directory = os.path.dirname(path.encode())        
    if not os.path.exists(directory):
        os.makedirs(directory)
    output = open(path.encode(),"w")
    output.write(json.dumps(data))        
    output.close() 
    decomposable = "true" if product.links and product.is_decomposable else "false"
    return "ARB:%s\nDecomposable:%s\n" % (name, decomposable) 
    
try:    
    generateGeometrys_Arborescense(sys.argv[1],sys.argv[2],sys.argv[3])        
except Exception as excep:
    if type(excep)==MultiRoot_Error:
        sys.exit(-1)
    elif type(excep)==OCC_ReadingStep_Error:
        sys.exit(-2)
    sys.exit(-3)

    
