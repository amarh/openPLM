import sys
import os
from classes import data_for_product , get_available_name
from STP_converter_WebGL import NEW_STEP_Import , MultiRoot_Error , OCC_ReadingStep_Error 
import logging
import django.utils.simplejson as json
    


def generateGeometrys_Arborescense(doc_file_path,doc_file_id,location):
    """
    
    
    :param doc_file_path: Path of a file **.stp**
    :param doc_file_id: id that is applied for the generation of the tree **.arb** and the geometries **.geo**
    :param location: Path where to store the files **.geo** and **.arb** generated     
    
      
    For a file STEP determined by his path (**doc_file_path**),  it generates his file **.arb** and his files **.geo** having count an **id** determined by **doc_file_id** 
    and return in stdout the list of paths of files generated
    
    """ 
    logging.getLogger("GarbageCollector").setLevel(logging.ERROR)    
    my_step_importer = NEW_STEP_Import(doc_file_path,doc_file_id) 
    product_arbre=my_step_importer.generate_product_arbre()   
    geo=my_step_importer.procesing_geometrys(location)
    print geo
    print write_ArbFile_from_Product(product_arbre,my_step_importer.fileName,location)



def write_ArbFile_from_Product(product,fileName,location):

    """
    
    
    :param product: :class:`.Product` relative to the structure of assamblys of a file **.stp**
    :param fileName: Name of the file **.stp** for which we are going to generate the file **.arb**
    :param location: Path where to store the file **.arb** generated  
    """ 
    
    
       
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

if __name__ == "__main__":    
    try:    
        generateGeometrys_Arborescense(sys.argv[1],sys.argv[2],sys.argv[3])        
    except Exception as excep:
        if type(excep)==MultiRoot_Error:
            sys.exit(-1)
        elif type(excep)==OCC_ReadingStep_Error:
            sys.exit(-2)
        sys.exit(-3)

    
