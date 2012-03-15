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


from OCC.TDataStd import *
from OCC.STEPCAFControl import *

from OCC import XCAFApp, TDocStd, XCAFDoc, gp
from OCC.Utils.Topology import Topo
from OCC.Quantity import *


from OCC.TCollection import *
from OCC.TopoDS import *
from OCC.XSControl import *
from OCC.STEPControl import *
from OCC.TopLoc import TopLoc_Location
from OCC.TDF import *
from openPLM.document3D.mesh import *
from openPLM.document3D.models import *
"""
l_SubShapes = TDF_LabelSequence()
shape_tool.GetSubShapes(label,l_SubShapes)
if(l_SubShapes.Length()>0):
    print "SubShapeDetectado ###################"#tengo un ejemplo en shapes con color
"""    
class NEW_STEP_Import(object):


   
    
    def __init__(self, doc_file):
        self.doc_file = doc_file
        self.shapes_simples = [] #an empty string
        self.product_relationship_arbre=None
        self.shapes_simples=[]

       
        STEPReader = STEPCAFControl_Reader()        
        
        if not STEPReader.ReadFile(self.doc_file.file.path.encode()) is 1:
            return False
               
        h_doc = TDocStd.Handle_TDocStd_Document()
        app = XCAFApp.GetApplication().GetObject()
        app.NewDocument(TCollection_ExtendedString("MDTV-CAF"),h_doc)

        
        STEPReader.Transfer(h_doc)

        doc = h_doc.GetObject()
        h_shape_tool = XCAFDoc.XCAFDoc_DocumentTool_ShapeTool(doc.Main())
        h_colors_tool = XCAFDoc.XCAFDoc_DocumentTool_ColorTool(doc.Main())
        self.shape_tool = h_shape_tool.GetObject()
        self.color_tool=h_colors_tool.GetObject()

        shapes = TDF_LabelSequence()
        self.shape_tool.GetShapes(shapes)        
        for i in range(shapes.Length()):
            if self.shape_tool.IsSimpleShape(shapes.Value(i+1)):
                compShape=self.shape_tool.GetShape(shapes.Value(i+1))
                t=Topo(compShape)
                if t.number_of_vertices() > 0:
                    self.shapes_simples.append(simple_shape(GetLabelNom(shapes.Value(i+1)),compShape))
                else:
                    pass
                    #print "Not information found for shape : ", GetLabelNom(shapes.Value(i+1))        

           
    def procesing_geometrys(self):
        from openPLM.document3D.models import GeometryFile
        
        


        fileName, fileExtension = os.path.splitext(self.doc_file.filename)   
        for i, shape in enumerate(self.shapes_simples):
                new_GeometryFile= GeometryFile()
                new_GeometryFile.stp = self.doc_file
                my_mesh = mesh_shape(shape.shape)
                name = new_GeometryFile.file.storage.get_available_name(fileName+".geo")
                path = os.path.join(new_GeometryFile.file.storage.location, name)
                if(not mesh_to_3js(my_mesh,path.encode(),"_"+str(i+1)+"_"+str(self.doc_file.id),shape.nom)):
                    return False    
                else:

                    new_GeometryFile.file = name
                    new_GeometryFile.index = i+1 # to evade product.geometry=0
                    new_GeometryFile.save()
                    
     


    def generate_product_arbre(self):
    
        roots = TDF_LabelSequence()
        self.shape_tool.GetFreeShapes(roots)
            
        for i in range(roots.Length()):
            self.product_relationship_arbre=Product(GetLabelNom(roots.Value(i+1)),self.doc_file.id,roots.Value(i+1)) 
            parcour_product_relationship_arbre(roots.Value(i+1),self.shape_tool,self.product_relationship_arbre,self.color_tool,self.shapes_simples,self.doc_file.id)
       
        return self.product_relationship_arbre
        


      


         
class simple_shape():

    def __init__(self, nom,TopoDS_Shape):
        self.nom = nom
        self.shape = TopoDS_Shape





     


    
    
    
def parcour_product_relationship_arbre(label,shape_tool,product,color_tool,shapes_simples,doc_id):



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
                        link.add_occurrence(GetLabelNom(l_c.Value(i+1)),Matrix_rotation(shape_tool.GetLocation(l_c.Value(i+1)).Transformation()))
                else:
                        
                    product.links.append(Link(Product(GetLabelNom(label_reference),doc_id,label_reference)))
                    product.links[-1].add_occurrence(GetLabelNom(l_c.Value(i+1)),Matrix_rotation(shape_tool.GetLocation(l_c.Value(i+1)).Transformation()))
                                
                    parcour_product_relationship_arbre(label_reference,shape_tool,product.links[-1].product,color_tool,shapes_simples,doc_id)

    else:            
        compShape=shape_tool.GetShape(label)
        #nous cherchons sa correspondance dans la liste de shapes simples / si le shape navais pas de vertices on ne trouvera aucun shape                         
        for index in range(len(shapes_simples)):
            if compShape.IsPartner(shapes_simples[index].shape):
                product.set_shape_geometry_related(index+1,colour_chercher(label,color_tool,shape_tool)) # to evade product.geometry=0
                 
                   

               


        
        
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
                   


            
            
           

