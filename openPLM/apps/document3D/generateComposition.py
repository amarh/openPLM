import gc
import sys
import json
import os
import re

# set to True to enable the dummy composer which consumes less memory
# and should be faster
# Currently it generates invalid STEP file, so you should not use it
# unless you want to fix it

DUMMY_COMPOSER = False

if DUMMY_COMPOSER:
    from part21_preparse import readStepFile, parse_entities
else:
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
        self.app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"), self.h_doc)

        self.STEPReader = STEPCAFControl_Reader()
        if not self.STEPReader.ReadFile(file_path.encode("utf-8")):
            raise Exception("OpenCascade could not read STEP file")
        self.STEPReader.Transfer(self.h_doc)
        self.doc = self.h_doc.GetObject()
        self.h_shape_tool = XCAFDoc.XCAFDoc_DocumentTool_ShapeTool(self.doc.Main())
        self.h_colors_tool = XCAFDoc.XCAFDoc_DocumentTool_ColorTool(self.doc.Main())
        self.shape_tool = self.h_shape_tool.GetObject()
        self.color_tool = self.h_colors_tool.GetObject()
        self.shapes = TDF_LabelSequence()
        self.shape_tool.GetShapes(self.shapes)
        roots = TDF_LabelSequence()
        self.shape_tool.GetFreeShapes(roots)
        ws = self.STEPReader.Reader().WS().GetObject()
        model = ws.Model().GetObject()
        model.Clear()
        for i in range(1, 8):
            ws.ClearData(i)
        ws.ClearFile()

    def __del__(self):
        self.app.Close(self.h_doc)
        del self.h_doc, self.app


def composer(temp_file_name):
    """
    :param temp_file_name: path of a  :class:`.tempfile` **.arb** that contains the information to generate a :class:`.Product` relative to the arborescense of a **.stp** file


    For every node of the :class:`.Product`  the attribute **doc_file_path** indicates where is store the file **.stp** that represents the node

    """
    output = open(temp_file_name.encode(),"r")
    product = Product.from_list(json.loads(output.read()))
    output.close()
    output = open(temp_file_name.encode(),"w+")# erase old data
    output.close()

    WS = XSControl_WorkSession()
    my_step_importer = StepImporter(product.doc_path)

    st = my_step_importer.shape_tool
    lr = TDF_LabelSequence()
    st.GetFreeShapes(lr)

    add_labels(product, lr.Value(1), st)
    writer = STEPCAFControl_Writer(WS.GetHandle(), False)
    for i in range(lr.Length()):
        writer.Transfer(lr.Value(i+1), STEPControl_AsIs)

    writer.Write(temp_file_name)


def add_labels(product,lr,st):

    if product.links:
        for link in product.links:

            if link.product.doc_id != product.doc_id:

                if not link.product.label_reference:

                    lr_2 = TDF_LabelSequence()
                    si = StepImporter(link.product.doc_path)
                    shape_tool = si.shape_tool
                    shape_tool.GetFreeShapes(lr_2)
                    add_labels(link.product, lr_2.Value(1), shape_tool)
                    link.product.label_reference = lr_2.Value(1)
                    # FIXME: free memory
                    del si
                    gc.collect()
                for d in range(link.quantity):
                    transformation = gp_Trsf()
                    loc = link.locations[d]
                    transformation.SetValues(loc.x1, loc.x2, loc.x3, loc.x4,
                        loc.y1, loc.y2, loc.y3, loc.y4,
                        loc.z1, loc.z2, loc.z3, loc.z4,
                        1, 1)

                    new_label = st.AddComponent(lr, link.product.label_reference,
                            TopLoc_Location(transformation))
                    set_label_name(new_label, link.names[d])


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

    def increment_ids(self, line):
        def inc(m):
            val = int(m.group(1))
            return "#%d" % (val + self.item_count)
        new_line = re.sub(r"\#(\d+)", inc, line)
        return new_line

    def add_step_file(self, product):
        path = product.doc_path
        if path in self.added_files:
            return

        step = readStepFile(path)
        max_id = max(step["insttype"].keys())
        for iname, content in step["contents"].iteritems():
            type_ = step["insttype"][iname]
            if product != self.product and type_.startswith("APPLICATION"):
                # there are certainly more lines to skip
                continue
            iname2 = iname + self.item_count
            if type_ == "complex_type":
                line = "#%d=(%s)\n" % (iname2, self.increment_ids(content))
            else:
                line = "#%d=%s(%s)\n" % (iname2, type_, self.increment_ids(content))
            self.output.write(line)

        if 'NEXT_ASSEMBLY_USAGE_OCCURRENCE' in step['typeinst']:
            # find the root of an assembly
            parents = set()
            children = set()
            for n in step['typeinst']['NEXT_ASSEMBLY_USAGE_OCCURRENCE']:
                parent, child = [x.strip(" \n\r#'")
                                 for x in step['contents'][n].split(',')[3:5]]
                parents.add(int(parent))
                children.add(int(child))
            roots = parents / children
            if len(roots) > 1:
                raise ValueError("Too many roots in %s" % path)
            root = roots.pop()
        else:
            # a single product
            root = step['typeinst']['PRODUCT_DEFINITION'][0]
        product.label_reference = self.item_count + root
        del step
        gc.collect()

        self.item_count += max_id
        self.added_files.add(path)

    def add_occurences(self, product):

        if product.links:
            for link in product.links:
                if link.product.doc_id!= product.doc_id:
                    if not link.product.label_reference:
                        self.add_step_file(link.product)
                        self.add_occurences(link.product)
                    for d in range(link.quantity):
                        self.occurences.append((product.label_reference, link.product.label_reference,
                            link.names[d], link.locations[d]))

    def write_occurences(self):

        for ref1, ref2, name, loc in self.occurences:
            self.item_count += 1
            e1 = self.item_count
            self.item_count += 1
            e2 = self.item_count
            self.item_count += 1
            e3 = self.item_count
            self.item_count += 1
            e4 = self.item_count
            self.item_count += 1
            e5 = self.item_count
            self.item_count += 1
            e6 = self.item_count

            self.output.write("""#{e1} = CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(#{e2},#{e4});
#{e2} = ( REPRESENTATION_RELATIONSHIP('','',#33,#10)
REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION(#{e3})
SHAPE_REPRESENTATION_RELATIONSHIP() );
#{e3} = ITEM_DEFINED_TRANSFORMATION('','',#11,#15);
#{e4} = PRODUCT_DEFINITION_SHAPE('Placement','Placement of an item',#{e5}
  );
#{e6} = NEXT_ASSEMBLY_USAGE_OCCURRENCE('1','{name}','',#{ref1},#{ref2},$);
""".format(**locals()))
            # TODO: add locations and replaces #33, #10, #11, #15 entities


def dummy_compose(temp_file_name):

    output = open(temp_file_name.encode(),"r")
    product = Product.from_list(json.loads(output.read()))
    output.close()
    output = open(temp_file_name.encode(),"w+")# erase old data
    output.close()
    with open(temp_file_name, "w") as output:
        c = Composer(product, output)
        c.compose()


if __name__ == "__main__":
    if DUMMY_COMPOSER:
        dummy_compose(sys.argv[1])
    else:
        composer(sys.argv[1])

