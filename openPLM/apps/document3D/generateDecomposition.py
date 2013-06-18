import sys
import json
import itertools

from OCC.TDF import *
from OCC.XSControl import XSControl_WorkSession
from OCC.STEPCAFControl import *
from OCC.STEPControl import *
from STP_converter_WebGL import StepImporter
from classes import Product
from OCC.GarbageCollector import garbage

def new_collect_object(self, obj_deleted):
    self._kill_pointed()

garbage.collect_object=new_collect_object


def decompose(path, temp_file_name):
    """
    Decomposes a STEP file into several STEP files (one per unique assembly/part)

    :param path: Path of a file **.stp**
    :param temp_file_name: path of a  :class:`.tempfile` **.arb** that contains the data required
          to generate a :class:`.Product` relative to the arborescense of a **.stp** file
    """
    output = open(temp_file_name.encode(),"r")
    old_product = Product.from_list(json.loads(output.read()))
    step_importer = StepImporter(path)
    shape_tool = step_importer.shape_tool
    product = step_importer.generate_product_arbre()
    decompose_children(product, old_product, shape_tool)
    write_step(product, old_product, shape_tool)


def decompose_children(product, old_product, shape_tool):

    for old_link, link in itertools.izip(old_product.links, product.links):
        if not link.product.visited:
            link.product.visited = True
            decompose_children(link.product, old_link.product, shape_tool)
            write_step(link.product, old_link.product, shape_tool)

def write_step(product, old_product, shape_tool):

    if shape_tool.IsAssembly(product.label_reference):
        l_c = TDF_LabelSequence()
        shape_tool.GetComponents(product.label_reference,l_c)
        for e in range(l_c.Length()):
            shape_tool.RemoveComponent(l_c.Value(e+1))

    WS = XSControl_WorkSession()
    writer = STEPCAFControl_Writer( WS.GetHandle(), False )
    writer.Transfer(product.label_reference, STEPControl_AsIs)
    writer.Write(old_product.doc_path.encode("utf-8"))


if __name__ == "__main__":
    decompose(sys.argv[1], sys.argv[2])

