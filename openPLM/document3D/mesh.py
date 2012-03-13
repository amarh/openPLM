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

def mesh_shape(shape):
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
    a_mesh = QuickTriangleMesh(DISPLAY_LIST=True)
    #a_mesh = QuickTriangleMesh()
    a_mesh.set_shape(shape)
    a_mesh.set_precision(a_mesh.get_precision()/quality_factor)
    a_mesh.compute()
    return a_mesh       



def mesh_to_3js(mesh,filename,name,shape_nom):
    """ Take a mesh, exports to a three.js javascript file"""


    
    try:
        directory = os.path.dirname(filename)
        
        if not os.path.exists(directory):
            os.makedirs(directory)

        output = open(filename,"w")
        output.write("//Computation for : %s"%shape_nom)
        output.write("""
    var %s = function () {

    var scope = this;
    THREE.Geometry.call( this );
        """%name)
        # export vertices
        for vertex in mesh.get_vertices():

           output.write('v(%.4f,%.4f,%.4f);\n'%(vertex[0],vertex[1],vertex[2]))
        # export faces
        index = 0
        
        faces = mesh.get_faces()
        normals = mesh.get_normals()
        while index<len(faces)-2:
            n1 = normals[index]
            n2 = normals[index+1]
            n3 = normals[index+2]
            output.write('f3(%i,%i,%i,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f);\n'%(faces[index],faces[index+1],faces[index+2],n1[0],n1[1],n1[2],n2[0],n2[1],n2[2],n3[0],n3[1],n3[2]))
            
            index += 3
        
        #closing file
        #this.sortFacesByMaterial();
        
        output.write("""
    
    function v( x, y, z ) {
        scope.vertices.push( new THREE.Vertex( new THREE.Vector3( x, y, z )  ) );
        }
    function f3( a, b, c, n1_x,n1_y,n1_z,n2_x,n2_y,n2_z,n3_x,n3_y,n3_z ) {
        scope.faces.push( new THREE.Face3( a, b, c, [ new THREE.Vector3( n1_x, n1_y, n1_z ), new THREE.Vector3( n2_x, n2_y, n2_z ), new THREE.Vector3( n3_x, n3_y, n3_z ) ]  ) );
        }
        }

    %s.prototype = new THREE.Geometry();
    %s.prototype.constructor = %s;
        """%(name,name,name))
        output.close()
        return True
    except IOError as (errno, strerror):
        return False
    



class MeshBase(object):
    ''' This class is an abstract class and gathers common properties/methods for the different types
of available meshes.'''
    def __init__(self,DISPLAY_LIST=False):
        self._shape = None
        self._precision = 0.0 #by default
        self._vertices = []
        self._faces = []
        self._normals = []
        self._uvs = []
        self._DISPLAY_LIST = DISPLAY_LIST  
    #return False si shape est vide
    def set_shape(self,shape):
        ''' @param shape: the TopoDS_Shape to mesh
'''
        self._shape = shape
        self.compute_default_precision()
    
    def get_vertices(self):
        ''' Returns the list of vertices coordinates
'''
        return self._vertices   
    def get_normals(self):
        return self._normals    
    def get_nb_nodes(self):
        return len(self._vertices)
    def get_nb_faces(self):
        return len(self._faces)    
    def get_faces(self):
        ''' Returns the face indices list
'''
        return self._faces    
    def get_precision(self):
        return self._precision    
    def set_precision(self, precision):
        self._precision = precision       
    def compute_default_precision(self):
        ''' The default precision is a float number. It's computed from the bounding box of the shape.
default_precision = bounding_box_diagonal / 10.
This default precision enables to quickly mesh a shape.
'''
        bbox = Bnd_Box()
        BRepBndLib_Add(self._shape, bbox) 
        x_min,y_min,z_min,x_max,y_max,z_max = bbox.Get()
        diagonal_length = gp_Vec(gp_Pnt(x_min,y_min,z_min),gp_Pnt(x_max,y_max,z_max)).Magnitude()
        self._precision = diagonal_length / 20.
        return True
    
    def get_shape(self):
        ''' @return: the TopoDS shape to mesh
'''
        return self._shape

class QuickTriangleMesh(MeshBase):
    ''' A mesh based on the BRepMesh OCC classes.
'''
    def __init__(self,DISPLAY_LIST = False, compute_uv = False):
        MeshBase.__init__(self,DISPLAY_LIST)
        self._compute_uv = compute_uv
    
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

    def compute(self):
        init_time = time.time()
        if self._shape is None:
            raise "Error: first set a shape"
            return False
        BRepMesh_Mesh(self._shape,self.get_precision())
        points = []
        faces = []
        _points = kjDict()
        normals = []
        uv = []
        faces_iterator = Topo(self._shape).faces()  
        index=0      
        for F in faces_iterator:
            face_location = TopLoc_Location()
            triangulation = BRep_Tool_Triangulation(F,face_location)
            if triangulation.IsNull() == False: 
                facing = triangulation.GetObject()
                tab = facing.Nodes()
                if self._compute_uv:
                    uvnodes = facing.UVNodes()
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
                            points.append(p1_coord)
                            index+=1
                        if not _points.has_key(p2_coord):
                            _points.add(p2_coord,index)
                            points.append(p2_coord)
                            index+=1
                        if not _points.has_key(p3_coord):
                            _points.add(p3_coord,index)
                            points.append(p3_coord)
                            index+=1
                        faces.append(_points.neighbors(p1_coord)[0])
                        faces.append(_points.neighbors(p2_coord)[0])
                        faces.append(_points.neighbors(p3_coord)[0])
                        
                        normals.append([the_normal(index1).X(),the_normal(index1).Y(), the_normal(index1).Z()])
                        normals.append([the_normal(index2).X(),the_normal(index2).Y(), the_normal(index2).Z()])
                        normals.append([the_normal(index3).X(),the_normal(index3).Y(), the_normal(index3).Z()])
        self._vertices = points
        self._faces = faces        
        self._normals = normals
        return True



 

