##Copyright 2008-2011 Thomas Paviot (tpaviot@gmail.com)
##
##This file is part of pythonOCC.
##
##pythonOCC is free software: you can redistribute it and/or modify
##it under the terms of the GNU Lesser General Public License as published by
##the Free Software Foundation, either version 3 of the License, or
##(at your option) any later version.
##
##pythonOCC is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU Lesser General Public License for more details.
##
##You should have received a copy of the GNU Lesser General Public License
##along with pythonOCC.  If not, see <http://www.gnu.org/licenses/>.



import os, os.path
from OCC.STEPCAFControl import STEPCAFControl_Reader
from OCC import XCAFApp, TDocStd , XCAFDoc
from OCC.TCollection import TCollection_ExtendedString , TCollection_AsciiString
from OCC.TDF import TDF_LabelSequence , TDF_Tool , TDF_Label 
from OCC.Utils.Topology import Topo
from OCC.TDataStd import Handle_TDataStd_Name ,TDataStd_Name_GetID
from OCC.Quantity import Quantity_Color
from mesh import *
from classes import *
from OCC.GarbageCollector import garbage

"""
l_SubShapes = TDF_LabelSequence()
shape_tool.GetSubShapes(label,l_SubShapes)
if(l_SubShapes.Length()>0):
    print "SubShapeDetectado ###################"#tengo un ejemplo en shapes con color
"""




def new_collect_object(self, obj_deleted):
        self._kill_pointed()

garbage.collect_object=new_collect_object

    
class NEW_STEP_Import(object):

    """
    
    :param file_path: Path of the file **.stp** to analyzing
    :param id: For the generation of the :class:`.Product`, **id** is assigned like product.doc_id for every node of :class:`.Product`. For the generation of the files of geometry **.geo**, **id** , together with an index generated by the class, is used for identify the content of every file
    
    

    Generates from a path of :class:`~django.core.files.File` **.stp**: 
    
      
    -A set of files **.geo** that represents the geometry of the different simple products that are useful to realize the visualization 3D across the web browser. 
    
    -A structure of information that represents the arborescencse of the different assemblys,represented in a  :class:`.Product` . (Including his spatial location and orientation and his label of reference (**OCC.TDF.TDF_Label**))
    
    
    This class is invoked from three different subprocesses related to the functionality of pythonOCC(generate3D.py , generateComposition.py , generateDecomposition.py).
    
   """
    
    def __init__(self, file_path,id=None):

        self.file =file_path.encode("utf-8")
        self.id =id
        self.shapes_simples = [] #an empty string
        self.product_relationship_arbre=None
        self.shapes_simples=[]
        basefile=os.path.basename(self.file)
        fileName, fileExtension = os.path.splitext(basefile)
        self.fileName=fileName

       
        self.STEPReader = STEPCAFControl_Reader()  

        if not self.STEPReader.ReadFile(self.file) == 1:
            raise OCC_ReadingStep_Error
               
        self.h_doc = TDocStd.Handle_TDocStd_Document()
        self.app = XCAFApp.GetApplication().GetObject()
        self.app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"),self.h_doc) #  "XmlXCAF" "XmlOcaf" "MDTV-Standard"



        self.STEPReader.Transfer(self.h_doc)

        self.doc = self.h_doc.GetObject()
        self.h_shape_tool = XCAFDoc.XCAFDoc_DocumentTool_ShapeTool(self.doc.Main())
        self.h_colors_tool = XCAFDoc.XCAFDoc_DocumentTool_ColorTool(self.doc.Main())
        self.shape_tool = self.h_shape_tool.GetObject()
        self.color_tool=self.h_colors_tool.GetObject()

        self.shapes = TDF_LabelSequence()
        self.shape_tool.GetShapes(self.shapes)        
        for i in range(self.shapes.Length()):
            if self.shape_tool.IsSimpleShape(self.shapes.Value(i+1)):
                compShape=self.shape_tool.GetShape(self.shapes.Value(i+1))
                t=Topo(compShape)
                if t.number_of_vertices() > 0:
                    self.shapes_simples.append(simple_shape(GetLabelNom(self.shapes.Value(i+1)),compShape,colour_chercher(self.shapes.Value(i+1),self.color_tool,self.shape_tool)))
                else:
                    pass
                    #print "Not information found for shape : ", GetLabelNom(shapes.Value(i+1))        

        ws=self.STEPReader.Reader().WS().GetObject()
        model=ws.Model().GetObject()
        model.Clear()          
    def procesing_geometrys(self,location):
        """
        :param location: Path where to store the files **.geo** generated      
        
        For every simple shape it generates a file **.geo** representatively of his geometry,the content of the file is identified by an index and **self.id**
        Returns the list of the path of the generated **.geo** files
        """
        files_index=""
        
        for index, shape in enumerate(self.shapes_simples):
                name=get_available_name(location,self.fileName+".geo")
                path=os.path.join(location, name)
                mesh_shape(shape,path,"_"+str(index+1)+"_"+str(self.id)) #index+1
                files_index+="GEO:"+name+" , "+str(index+1)+"\n" #index+1
             
     
        return files_index        

    def generate_product_arbre(self):
    
        """    
        
        Generates a :class:`.Product` relative to the assemblys of the file **.stp**, for every node of the :class:`.Product` it includes a label (**OCC.TDF.TDF_Label**) that represents and identifies the node
        
        """    
    
        roots = TDF_LabelSequence()
        self.shape_tool.GetFreeShapes(roots)
        if not roots.Length()==1:
            raise MultiRoot_Error

        deep=0            
        self.product_relationship_arbre=Product(GetLabelNom(roots.Value(1)),deep,roots.Value(1),self.id,self.file) 
        parcour_product_relationship_arbre(roots.Value(1),self.shape_tool,self.product_relationship_arbre,self.shapes_simples,
        (deep+1),self.id,self.product_relationship_arbre)
       
        return self.product_relationship_arbre
        


      


         
class simple_shape():

    """
    Class used to represent a simple geometry ,(not assembly) 
   
    
    
    :model attributes:
        
        
    .. attribute:: name
    
        Name of geometry 

    .. attribute:: locations
    
        :class:`Matrix_rotation` of each instances of the :class:`Link` 
               
    .. attribute:: product
    """    

    def __init__(self, name,TopoDS_Shape,color):
        self.name = name
        self.shape = TopoDS_Shape
        self.color = color




     


    
    
    
def parcour_product_relationship_arbre(label,shape_tool,product,shapes_simples,deep,doc_id,product_root):

    if shape_tool.IsAssembly(label):
        l_c = TDF_LabelSequence()
        shape_tool.GetComponents(label,l_c)
        for i in range(l_c.Length()):
            if shape_tool.IsReference(l_c.Value(i+1)):
                label_reference=TDF_Label()            
                shape_tool.GetReferredShape(l_c.Value(i+1),label_reference)         
                reference_found=False
                for link in product.links:
                    if shape_tool.GetShape(link.product.label_reference).IsPartner(shape_tool.GetShape(label_reference)):                      
                        reference_found=True
                        break
                if reference_found:
                        link.add_occurrence(GetLabelNom(l_c.Value(i+1)),Matrix_rotation(getMatrixFromLocation(shape_tool.GetLocation(l_c.Value(i+1)).Transformation())))
                else:

                    product_assembly=search_assembly(GetLabelNom(label_reference),label_reference,doc_id,product_root,shape_tool.IsSimpleShape(label_reference))
                             
                    if product_assembly:  
                        product.links.append(Link(product_assembly))
         
                    else:      
                        product.links.append(Link(Product(GetLabelNom(label_reference),deep,label_reference,doc_id)))                               
                        parcour_product_relationship_arbre(label_reference,shape_tool,product.links[-1].product,shapes_simples,deep+1,doc_id,product_root)
                        
                        
                    
                    product.links[-1].add_occurrence(GetLabelNom(l_c.Value(i+1)),Matrix_rotation(getMatrixFromLocation(shape_tool.GetLocation(l_c.Value(i+1)).Transformation())))  
    else:            
        compShape=shape_tool.GetShape(label)

        
                      
        for index in range(len(shapes_simples)):
            if compShape.IsPartner(shapes_simples[index].shape):
                product.set_geometry(index+1) #to avoid index==0
                   

               
         
    

def getMatrixFromLocation(Location):


    m=Location.VectorialPart()
    gp=m.Row(1)
    x1=gp.X()           
    x2=gp.Y()
    x3=gp.Z()
    x4=Location.Transforms()[0]
    gp=m.Row(2)
    y1=gp.X()          
    y2=gp.Y()
    y3=gp.Z()
    y4=Location.Transforms()[1]
    gp=m.Row(3)
    z1=gp.X()         
    z2=gp.Y()
    z3=gp.Z()
    z4=Location.Transforms()[2]   
    return [x1,x2,x3,x4,y1,y2,y3,y4,z1,z2,z3,z4]          
        
def GetLabelNom(lab):

            entry = TCollection_AsciiString()
            TDF_Tool.Entry(lab,entry)
            N = Handle_TDataStd_Name()
            lab.FindAttribute(TDataStd_Name_GetID(),N)
            n=N.GetObject()
            return unicode(n.Get().PrintToString(),errors='ignore')#.decode("latin-1")
            
            
def SetLabelNom(lab,nom):

    entry = TCollection_AsciiString()
    TDF_Tool.Entry(lab,entry)
    N = Handle_TDataStd_Name()
    lab.FindAttribute(TDataStd_Name_GetID(),N)
    n=N.GetObject()
    n.Set(TCollection_ExtendedString(nom.encode("latin-1")))

 
  
def colour_chercher(label,color_tool,shape_tool):
    c=Quantity_Color()
    if( color_tool.GetInstanceColor(shape_tool.GetShape(label),0,c) or  color_tool.GetInstanceColor(shape_tool.GetShape(label),1,c) or color_tool.GetInstanceColor(shape_tool.GetShape(label),2,c)):
        color_tool.SetColor(label,c,0)
        color_tool.SetColor(label,c,1)
        color_tool.SetColor(label,c,2) 

        return c
    
    if( color_tool.GetColor(label,0,c) or  color_tool.GetColor(label,1,c) or color_tool.GetColor(label,2,c) ):
        color_tool.SetInstanceColor(shape_tool.GetShape(label),0,c)
        color_tool.SetInstanceColor(shape_tool.GetShape(label),1,c)
        color_tool.SetInstanceColor(shape_tool.GetShape(label),2,c)
       
        return c

    return False

 
   
class MultiRoot_Error(Exception):
    def __unicode__(self):
        return u"OpenPLM does not support files step with multiple roots"    
class OCC_ReadingStep_Error(Exception):
    def __unicode__(self):
        return u"PythonOCC could not read the file"

