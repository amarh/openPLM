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

''' This module provides an high level API built on top of BRepMesh and SMESH low level
objects. '''

import random
from math import sqrt as math_sqrt
from OCC.Utils.Topology import *
from OCC.TopoDS import *
from OCC.TopAbs import *
# to determine default precision
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

def mesh_shape(shape,filename,name,shape_nom):
    """ Take a topods_shape instance, returns the tesselated object"""
    ''' Connect a ode.Trimesh to this body. The mesh is generated from the MSH subpackage. vertices lits
    and faces indices are passed to the trimesh.
    The default mesh precision is divided by the quality factor:
    - if quality_factor>1, the mesh will be more precise, i.e. more triangles (more precision, but also
    more memory consumption and time for the mesher,
    - if quality_factor<1, the mesh will be less precise.
    By default, this argument is set to 1 : the default precision of the mesher is used.
    '''
    quality_factor=0.3
    a_mesh = QuickTriangleMesh(shape,quality_factor)

    
    
    directory = os.path.dirname(filename)
    
    if not os.path.exists(directory):
        os.makedirs(directory)

    output = open(filename,"w")
    output.write("//Computation for : %s\n"%shape_nom)
    output.write("var %s = new THREE.Geometry();\n"%name) 


    a_mesh.compute(output,name)
    return a_mesh       



class QuickTriangleMesh(object):
    ''' A mesh based on the BRepMesh OCC classes.
'''
    def __init__(self,shape,quality_factor):
        self._shape = shape
        bbox = Bnd_Box()
        BRepBndLib_Add(self._shape, bbox) 
        x_min,y_min,z_min,x_max,y_max,z_max = bbox.Get()
        diagonal_length = gp_Vec(gp_Pnt(x_min,y_min,z_min),gp_Pnt(x_max,y_max,z_max)).Magnitude()
        self._precision = (diagonal_length / 20.)/quality_factor

    
    def triangle_is_valid(self, P1,P2,P3):
        ''' check wether a triangle is or not valid
'''
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

    def compute(self,output,name):
        init_time = time.time()
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
                        if not _points.has_key(p1_coord):
                            _points.add(p1_coord,index)
                            output.write("%s.vertices.push(new THREE.Vertex(new THREE.Vector3(%.4f,%.4f,%.4f)));\n"%(name,p1_coord[0],p1_coord[1],p1_coord[2]))
                            index+=1
                        if not _points.has_key(p2_coord):
                            _points.add(p2_coord,index)
                            output.write("%s.vertices.push(new THREE.Vertex(new THREE.Vector3(%.4f,%.4f,%.4f)));\n"%(name,p2_coord[0],p2_coord[1],p2_coord[2]))
                            index+=1
                        if not _points.has_key(p3_coord):
                            _points.add(p3_coord,index)
                            output.write("%s.vertices.push(new THREE.Vertex(new THREE.Vector3(%.4f,%.4f,%.4f)));\n"%(name,p3_coord[0],p3_coord[1],p3_coord[2]))
                            index+=1
                        output.write("%s.faces.push( new THREE.Face3( %i, %i, %i, [ new THREE.Vector3( %.4f, %.4f, %.4f ), new THREE.Vector3( %.4f, %.4f, %.4f ), new THREE.Vector3( %.4f, %.4f, %.4f ) ]  ) );\n"%(name,_points.neighbors(p1_coord)[0],_points.neighbors(p2_coord)[0],_points.neighbors(p3_coord)[0],the_normal(index1).X(),the_normal(index1).Y(), the_normal(index1).Z(),the_normal(index2).X(),the_normal(index2).Y(), the_normal(index2).Z(),the_normal(index3).X(),the_normal(index3).Y(), the_normal(index3).Z()))                            


        return True



 

