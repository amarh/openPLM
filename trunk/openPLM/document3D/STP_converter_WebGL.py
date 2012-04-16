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
#from openPLM.document3D.models import media3DGeometryFile
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
            print "False"
               
        self.h_doc = TDocStd.Handle_TDocStd_Document()
        self.app = XCAFApp.GetApplication().GetObject()
        self.app.NewDocument(TCollection_ExtendedString("XmlXCAF"),self.h_doc)
        """
          Formats.Append(TCollection_ExtendedString ("MDTV-XCAF"));  
          Formats.Append(TCollection_ExtendedString ("XmlXCAF"));
          Formats.Append(TCollection_ExtendedString ("XmlOcaf"));
          Formats.Append(TCollection_ExtendedString ("MDTV-Standard"));
        """

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

        files_index=""

        for index, shape in enumerate(self.shapes_simples):
                name=get_available_name(location,self.fileName+".geo")
                path=os.path.join(location, name)
                mesh_shape(shape,path,"_"+str(index)+"_"+str(self.id))
                files_index+="GEO:"+name+" , "+str(index)+"\n"
             
     
        return files_index        

    def generate_product_arbre(self):
    
        roots = TDF_LabelSequence()
        self.shape_tool.GetFreeShapes(roots)
        #prohibir step conj 2 ROOTS
        deep=0
        for i in range(roots.Length()):
            
            self.product_relationship_arbre=Product(GetLabelNom(roots.Value(i+1)),deep,roots.Value(i+1),self.id,self.file) 
            parcour_product_relationship_arbre(roots.Value(i+1),self.shape_tool,self.product_relationship_arbre,self.shapes_simples,
            (deep+1),self.id,self.product_relationship_arbre)
       
        return self.product_relationship_arbre
        


      


         
class simple_shape():

    def __init__(self, name,TopoDS_Shape,color):
        self.name = name
        self.shape = TopoDS_Shape
        self.color = color




     


    
    
    
def parcour_product_relationship_arbre(label,shape_tool,product,shapes_simples,deep,doc_id,product_root):
    #un parcour para ver si existen 2 nodos con el mismo nombre o algun nodo sin nombre al principio antes de empezar

    #colour_chercher(label,color_tool,shape_tool)
    if shape_tool.IsAssembly(label):
        # si no tiene nombre lanzar excepcion
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

                    product_assembly=search_assembly(GetLabelNom(label_reference),label_reference,doc_id,product_root)
                             
                    if product_assembly:  
                        product.links.append(Link(product_assembly))
         
                    else:      
                        product.links.append(Link(Product(GetLabelNom(label_reference),deep,label_reference,doc_id)))                               
                        parcour_product_relationship_arbre(label_reference,shape_tool,product.links[-1].product,shapes_simples,deep+1,doc_id,product_root)
                        
                        
                    
                    product.links[-1].add_occurrence(GetLabelNom(l_c.Value(i+1)),Matrix_rotation(getMatrixFromLocation(shape_tool.GetLocation(l_c.Value(i+1)).Transformation())))  
    else:            
        compShape=shape_tool.GetShape(label)

        #nous cherchons sa correspondance dans la liste de shapes simples / si le shape n avais pas de vertices on ne trouvera aucun shape 
                      
        for index in range(len(shapes_simples)):
            if compShape.IsPartner(shapes_simples[index].shape):
                product.set_geometry(index) # to evade product.geometry=0
                   

               
         
    

        
        
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
    return True
 
  
def colour_chercher(label,color_tool,shape_tool):
    c=Quantity_Color()
    if( color_tool.GetInstanceColor(shape_tool.GetShape(label),0,c) or  color_tool.GetInstanceColor(shape_tool.GetShape(label),1,c) or color_tool.GetInstanceColor(shape_tool.GetShape(label),2,c)):
        color_tool.SetColor(label,c,0)
        color_tool.SetColor(label,c,1)
        color_tool.SetColor(label,c,2) #para no tener problemas a la hora de componer y no perder informacion del color
        #print "Color encontrado manera 1(",c.Red(),",",c.Green() ,"," ,c.Blue() ,    ") encontrado para : " , GetLabelNom(label) 
        return c
    
    if( color_tool.GetColor(label,0,c) or  color_tool.GetColor(label,1,c) or color_tool.GetColor(label,2,c) ):
        color_tool.SetInstanceColor(shape_tool.GetShape(label),0,c)
        color_tool.SetInstanceColor(shape_tool.GetShape(label),1,c)
        color_tool.SetInstanceColor(shape_tool.GetShape(label),2,c)
        #print "Color encontrado manera 2 (",c.Red(),",",c.Green() ,"," ,c.Blue() ,    ") encontrado para : " , GetLabelNom(label) 
        return c

    return False

