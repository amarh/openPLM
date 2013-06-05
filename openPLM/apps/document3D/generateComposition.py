import gc
import re
import sys
import json

import os
os.environ["MMGT_OPT"] = "0"

from OCC.TDF import TDF_LabelSequence
from OCC.XSControl import XSControl_WorkSession
from OCC.STEPControl import STEPControl_AsIs
from OCC.STEPCAFControl import STEPCAFControl_Writer
from OCC.TopLoc import TopLoc_Location
from OCC.gp import gp_Trsf
from STP_converter_WebGL import set_label_name

from OCC.STEPCAFControl import STEPCAFControl_Reader
from OCC import XCAFApp, TDocStd , XCAFDoc
from OCC.TCollection import TCollection_ExtendedString

from classes import Product

class StepImporter(object):
    def __init__(self, file_path):
        self.h_doc = TDocStd.Handle_TDocStd_Document()
        self.app = XCAFApp.GetApplication().GetObject()
        self.app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"),self.h_doc)

        self.STEPReader = STEPCAFControl_Reader()
        if not self.STEPReader.ReadFile(file_path.encode("utf-8")):
            raise Exception()
        self.STEPReader.Transfer(self.h_doc)
        self.doc = self.h_doc.GetObject()
        self.h_shape_tool = XCAFDoc.XCAFDoc_DocumentTool_ShapeTool(self.doc.Main())
        self.h_colors_tool = XCAFDoc.XCAFDoc_DocumentTool_ColorTool(self.doc.Main())
        self.shape_tool = self.h_shape_tool.GetObject()
        self.color_tool=self.h_colors_tool.GetObject()
        self.shapes = TDF_LabelSequence()
        self.shape_tool.GetShapes(self.shapes)
        roots = TDF_LabelSequence()
        self.shape_tool.GetFreeShapes(roots)
        ws=self.STEPReader.Reader().WS().GetObject()
        model=ws.Model().GetObject()
        model.Clear()
        ws.ClearData(7)


def composer(temp_file_name):
    """
    :param temp_file_name: path of a  :class:`.tempfile` **.arb** that contains the information to generate a :class:`.Product` relative to the arborescense of a **.stp** file


    For every node of the :class:`.Product`  the attribute **doc_file_path** indicates where is store the file **.stp** that represents the node

    """
    output = open(temp_file_name.encode(),"r")
    product =Product.from_list(json.loads(output.read()))
    output.close()
    output = open(temp_file_name.encode(),"w+")# erase old data
    output.close()
    my_step_importer = StepImporter(product.doc_path)

    st= my_step_importer.shape_tool
    lr= TDF_LabelSequence()
    st.GetFreeShapes(lr)

    add_labels(product,lr.Value(1), st)
    WS = XSControl_WorkSession()
    writer = STEPCAFControl_Writer( WS.GetHandle(), False )
    for i in range(lr.Length()):
        writer.Transfer(lr.Value(i+1), STEPControl_AsIs)

    writer.Write(temp_file_name)


def add_labels(product,lr,st):

    if product.links:
        for link in product.links:

            if link.product.doc_id!= product.doc_id: # solo los que esten descompuesto, si no esta descompuesto no tiene que anadirlo

                if not link.product.label_reference:

                    lr_2= TDF_LabelSequence()
                    si = StepImporter(link.product.doc_path)
                    shape_tool = si.shape_tool
                    shape_tool.GetFreeShapes(lr_2)
                    add_labels(link.product,lr_2.Value(1),shape_tool)
                    link.product.label_reference=lr_2.Value(1)
                    # FIXME: free memory
                    del si
                    gc.collect()
                for d in range(link.quantity):

                    transformation=gp_Trsf()

                    transformation.SetValues(link.locations[d].x1,link.locations[d].x2,link.locations[d].x3,link.locations[d].x4,
                    link.locations[d].y1,link.locations[d].y2,link.locations[d].y3,link.locations[d].y4,link.locations[d].z1,link.locations[d].z2,
                    link.locations[d].z3,link.locations[d].z4,1,1)

                    new_label=st.AddComponent(lr,link.product.label_reference,TopLoc_Location(transformation))
                    set_label_name(new_label,link.names[d])


if __name__ == "__main__":
    composer(sys.argv[1])

