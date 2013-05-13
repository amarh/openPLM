import sys
import os
import tempfile
from classes import data_for_product , get_available_name
from STP_converter_WebGL import StepImporter , MultiRoot_Error , OCC_ReadingStep_Error 
import logging
import json
    
from pov import create_thumbnail

def generateGeometrys_Arborescense(doc_file_path,doc_file_id,location, thumb_path):
    """
    
    
    :param doc_file_path: Path of a file **.stp**
    :param doc_file_id: id that is applied for the generation of the tree **.arb** and the geometries **.geo**
    :param location: Path where to store the files **.geo** and **.arb** generated     
    
      
    For a file STEP determined by its path (**doc_file_path**),  it generates its file **.arb** and its files **.geo** having count an **id** determined by **doc_file_id** 
    and returns in stdout the list of paths of files generated
    
    """ 
    logging.getLogger("GarbageCollector").setLevel(logging.ERROR)    
    step_importer = StepImporter(doc_file_path,doc_file_id) 
    product = step_importer.generate_product_arbre()   
    pov_dir = tempfile.mkdtemp(suffix="openplm_pov")
    geo = step_importer.compute_geometries(location, pov_dir)
    print geo
    print write_ArbFile_from_Product(product, step_importer.fileName,location)
    if step_importer.thumbnail_valid and product:
        create_thumbnail(product, step_importer, pov_dir, thumb_path)

def write_ArbFile_from_Product(product,fileName,location):
    """
    :param product: :class:`.Product` relative to the structure of assemblies of a file **.stp**
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
        generateGeometrys_Arborescense(*sys.argv[1:])   
    except Exception as excep:
        raise
        if type(excep)==MultiRoot_Error:
            sys.exit(-1)
        elif type(excep)==OCC_ReadingStep_Error:
            sys.exit(-2)
        sys.exit(-3)

