##Copyright 2010 Thomas Paviot (tpaviot@gmail.com)
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
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
##GNU Lesser General Public License for more details.
##
##You should have received a copy of the GNU Lesser General Public License
##along with pythonOCC. If not, see <http://www.gnu.org/licenses/>.



import random
from math import sqrt as math_sqrt
from OCC.Utils.Topology import *
from OCC.TopoDS import *
from OCC.TopAbs import *
from OCC.Bnd import *
from OCC.BRepBndLib import *
from OCC.gp import *
from OCC.BRepMesh import *
from OCC.BRep import *
from OCC.BRepTools import *
from OCC.TopLoc import *
from OCC.Poly import *
from OCC.BRepBuilderAPI import *
from OCC.StdPrs import *
from OCC.TColgp import *
from OCC.Poly import *
import time
import os, os.path
from kjbuckets import  kjDict
import time
from OCC.GarbageCollector import garbage
def mesh_shape(shape,filename,_index_id, pov_dir):
    """ 

    :param shape: :class:`.simple_shape` of which we are going to generate the file **.geo**  
    :param filename: name of the :class:`.DocumentFile` of which we are going to generate the file **.geo**  
    :param _index_id: id to to differentiate the content between the diverse files **.geo** generated .Composed of the id of the :class:`.DocumentFile` and by one index that will be diferent for each file **.geo** generated for the same :class:`.DocumentFile`
 
 
 
    The files **.geo** are a series of judgments javascript that turn the geometry of the object into representable triangles by means of Webgl

    We can select the **opacity** and the **quality_factor** of the representation
    
    
    """

    quality_factor=0.3
    opacity=0.8
    a_mesh = QuickTriangleMesh(shape.shape,quality_factor)

    
    
    directory = os.path.dirname(filename)
    
    if not os.path.exists(directory):
        os.makedirs(directory)

    output = open(filename,"w")
    output.write("//Computation for : %s\n"%shape.name)
    output.write("var %s = new THREE.Geometry();\n"%_index_id) 
    output.write("var material_for%s = new THREE.MeshBasicMaterial({opacity:%s,shading:THREE.SmoothShading});\n"%(_index_id,opacity))
    pov_file = open(os.path.join(pov_dir, os.path.basename(filename + ".inc")), "w")
    pov_file.write("""
#declare m%s = mesh {
""" % _index_id)
    
    if shape.color:
        output.write("material_for%s.color.setRGB(%f,%f,%f);\n"%(_index_id,shape.color.Red(),shape.color.Green(),shape.color.Blue()))
     
    a_mesh.compute(output, pov_file, _index_id)
    if shape.color:
        color = shape.color.Red(),shape.color.Green(),shape.color.Blue()
    else:
        color = 1, 1, 0
    pov_file.write("""  
};

#declare t%s = texture {
    pigment {
        color <%f,%f, %f, 0.9>
    }
     finish {ambient 0.1
         diffuse 0.9
         phong 1}
  }
""" % ((_index_id, ) + color))
    
    output.close()
    pov_file.close()

    return a_mesh       

triangle_fmt = """ smooth_triangle {
        <%f, %f, %f>, <%f, %f, %f>,
        <%f, %f, %f>, <%f, %f, %f>, 
        <%f, %f, %f>, <%f, %f, %f>
      }
    """
vertice_fmt = "%s.vertices.push(new THREE.Vector3(%.4f,%.4f,%.4f));\n"
face_fmt = "%s.faces.push( new THREE.Face3( %i, %i, %i, [ new THREE.Vector3( %.4f, %.4f, %.4f ), new THREE.Vector3( %.4f, %.4f, %.4f ), new THREE.Vector3( %.4f, %.4f, %.4f ) ]  ) );\n"

def get_mesh_precision(shape, quality_factor):
    bbox = Bnd_Box()
    BRepBndLib_Add(shape, bbox) 
    x_min,y_min,z_min,x_max,y_max,z_max = bbox.Get()
    diagonal_length = gp_Vec(gp_Pnt(x_min, y_min, z_min),
                             gp_Pnt(x_max, y_max, z_max)).Magnitude()
    return (diagonal_length / 20.) / quality_factor

class QuickTriangleMesh(object):

    """


    :model attributes:
        
        
    .. attribute:: shape
    
        :class:`.OCC.TopoDS.TopoDS_Shape` that contains the geometry 

    .. attribute:: quality_factor
    
        quality of applied to the geometry
               

    """
    def __init__(self,shape,quality_factor):

        self._shape = shape
        self._precision = get_mesh_precision(shape, quality_factor)
        self.triangle_count = 0
            
    def triangle_is_valid(self, P1,P2,P3):

        V1 = gp_Vec(P1,P2)
        V2 = gp_Vec(P2,P3)
        V3 = gp_Vec(P3,P1)
        if V1.SquareMagnitude()>1e-10 and V2.SquareMagnitude()>1e-10 and V3.SquareMagnitude()>1e-10:
            V1.Cross(V2)
            if V1.SquareMagnitude()>1e-10:
                return True
            else:
                return False
        else:
            return False

    def compute(self,output, pov_file, _index_id):
    
        """
        
        :param _index_id: id to differentiate the content between the diverse files **.geo** generated .Composed of the id of the :class:`.DocumentFile` and by one index that will be diferent for each file **.geo** generated for the same :class:`.DocumentFile` 
        :param output: :class:`~django.core.files.File` **.geo**       
               
        Divides the geometry in triangles and generates the code javascript of each of these writing in **output** 
        
        """
        if self._shape is None:
            raise "Error: first set a shape"
            return False
        BRepMesh_Mesh(self._shape,self._precision)
        
        _points = kjDict()

        uv = []
        faces_iterator = Topo(self._shape).faces()  
        index=0
              
        for F in faces_iterator:
            face_location = TopLoc_Location()
            triangulation = BRep_Tool_Triangulation(F,face_location)
        
            if triangulation.IsNull() == False: 
                facing = triangulation.GetObject()
                tab = facing.Nodes()
                tri = facing.Triangles()
                the_normal = TColgp_Array1OfDir(tab.Lower(), tab.Upper()) 
                StdPrs_ToolShadedShape_Normal(F, Poly_Connect(facing.GetHandle()), the_normal)
                
                for i in range(1,facing.NbTriangles()+1):
                    
                    trian = tri.Value(i)
                    
                    if F.Orientation() == TopAbs_REVERSED:
                        index1, index3, index2 = trian.Get()
                    else:
                        index1, index2, index3 = trian.Get()
                    
                    P1 = tab.Value(index1).Transformed(face_location.Transformation())
                    P2 = tab.Value(index2).Transformed(face_location.Transformation())
                    P3 = tab.Value(index3).Transformed(face_location.Transformation())     
                    p1_coord = P1.XYZ().Coord()
                    p2_coord = P2.XYZ().Coord()
                    p3_coord = P3.XYZ().Coord()
                    if self.triangle_is_valid(P1, P2, P3):                
                        for point in (p1_coord, p2_coord, p3_coord):
                            if not _points.has_key(point):
                                _points.add(point, index)
                                output.write(vertice_fmt % (_index_id, point[0], point[1], point[2]))
                                index+=1

                        n1 = the_normal(index1)
                        n2 = the_normal(index2)
                        n3 = the_normal(index2)
                        output.write(face_fmt % 
                                (_index_id, _points.neighbors(p1_coord)[0],
                                            _points.neighbors(p2_coord)[0],
                                            _points.neighbors(p3_coord)[0],
                                            n1.X(), n1.Y(), n1.Z(),
                                            n2.X(), n2.Y(), n2.Z(),
                                            n3.X(), n3.Y(), n3.Z(),
                                    ))                           
                        pov_file.write(triangle_fmt % (
                            p1_coord[0], p1_coord[1], p1_coord[2],
                            n1.X(), n1.Y(), n1.Z(),
                            p2_coord[0], p2_coord[1], p2_coord[2],
                            n2.X(), n2.Y(), n2.Z(),
                            p3_coord[0], p3_coord[1], p3_coord[2],
                            n3.X(), n3.Y(), n3.Z(),
                            ))
                        self.triangle_count += 1

         
        return True




