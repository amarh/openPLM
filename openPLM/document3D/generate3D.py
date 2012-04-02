import sys
import os
from classes import data_for_product , get_available_name
from STP_converter_WebGL import NEW_STEP_Import
import logging
import django.utils.simplejson as json
    



def generateGeometry(doc_file_path,doc_file_id,location):

    logging.getLogger("GarbageCollector").setLevel(logging.ERROR)
    my_step_importer = NEW_STEP_Import(doc_file_path,doc_file_id)
    print my_step_importer.procesing_geometrys(location)
    product_arbre=my_step_importer.generate_product_arbre()
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
    
    
    return "ARB:"+name+"\n" 
    
    
generateGeometry(sys.argv[1],sys.argv[2],sys.argv[3])            

