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


class Composer(object):

    def __init__(self, product, output):

        self.product = product
        self.output = output
        self.item_count = 0
        self.max_id = 0
        self.added_files = set()
        self.occurences = []
        self.line_completed = True
        self.line_skipped = False

    def compose(self):
        self.init_step_file()
        self.add_step_file(self.product)
        self.add_occurences(self.product)
        self.write_occurences()
        self.close_step_file()

    def init_step_file(self):
        self.output.write("""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Open CASCADE Model'),'2;1');
FILE_NAME('Open CASCADE Shape Model','2013-06-03T13:14:01',('Author'),(
    'Open CASCADE'),'Open CASCADE STEP processor 6.3','Open CASCADE 6.3'
  ,'Unknown');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN_CC2 { 1 2 10303 214 -1 1 5 4 }'));
ENDSEC;
DATA;
 """)

    def close_step_file(self):
        self.output.write("ENDSEC;\nEND-ISO-10303-21;")

    def skip_header(self, f):
        for line in f:
            if line.startswith("DATA;"):
                return

    def skip_line(self, line):
        if not self.line_completed:
            skipped = self.line_skipped
        elif len(self.added_files) > 0:
            skipped = "APPLICATION" in line
        else:
            skipped = False
        self.line_completed = line.rstrip().endswith(";")
        self.line_skipped = skipped
        return skipped

    def increment_ids(self, line):
        def inc(m):
            val = int(m.group(1))
            self.max_id = max(val, self.max_id)
            return "#%d" % (val + self.item_count)
        new_line = re.sub(r"\#(\d+)", inc, line)
        return new_line

    def add_step_file(self, product):
        path = product.doc_path
        if path in self.added_files:
            return
        with open(path) as input_file:
            self.skip_header(input_file)
            for line in input_file:
                if self.skip_line(line):
                    continue
                new_line = self.increment_ids(line)
                m = re.search(r"#(\d+)\s?=\sPRODUCT_DEFINTION\(", new_line)
                if m:
                    product.label_reference = m.group(1)

                self.output.write(new_line)
        self.item_count += self.max_id
        self.max_id = 0
        self.added_files.add(path)

    def add_occurences(self, product):

        if product.links:
            for link in product.links:

                if link.product.doc_id!= product.doc_id: # solo los que esten descompuesto, si no esta descompuesto no tiene que anadirlo

                    if not link.product.label_reference:
                        self.add_step_file(link.product.doc_path)
                        self.add_occurences(link.product)
                    for d in range(link.quantity):
                        self.occurences.append((product.label_reference, link.product.label_reference, link.names[d], link.locations[d]))

    def write_occurences(self):

        for ref1, ref2, name, loc in self.occurences:
            self.output.write("""#632 = CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(#633,#635);
#633 = ( REPRESENTATION_RELATIONSHIP('','',#33,#10)
REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION(#634)
SHAPE_REPRESENTATION_RELATIONSHIP() );
#634 = ITEM_DEFINED_TRANSFORMATION('','',#11,#15);
#635 = PRODUCT_DEFINITION_SHAPE('Placement','Placement of an item',#636
  );
#636 = NEXT_ASSEMBLY_USAGE_OCCURRENCE('1','{name}','',#{ref1},#{ref2},$);
""" % locals())


if __name__ == "__main__":
    composer(sys.argv[1])

