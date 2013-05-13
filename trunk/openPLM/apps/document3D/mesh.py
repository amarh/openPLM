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

import os, os.path
from kjbuckets import  kjDict

from OCC.Utils.Topology import Topo
from OCC.TopAbs import TopAbs_REVERSED
from OCC.Bnd import Bnd_Box
from OCC.BRepBndLib import BRepBndLib_Add
from OCC.gp import gp_Vec, gp_Pnt
from OCC.BRepMesh import BRepMesh_Mesh
from OCC.BRep import BRep_Tool_Triangulation
from OCC.TopLoc import TopLoc_Location
from OCC.Poly import Poly_Connect
from OCC.StdPrs import StdPrs_ToolShadedShape_Normal
from OCC.TColgp import TColgp_Array1OfDir


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


class GeometryWriter(object):
    """
    Tool to convert an OpenCascade shape into a javascript file.

    :model attributes:

    .. attribute:: shape

        :class:`.SimpleShape` that contains the geometry

    .. attribute:: quality_factor

        quality of applied to the geometry
    """
    def __init__(self, shape, quality_factor):
        self.shape = shape
        self.topo_shape = shape.shape
        self._precision = get_mesh_precision(self.topo_shape, quality_factor)
        self.triangle_count = 0

    def _triangle_is_valid(self, P1,P2,P3):

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

    def write_geometries(self, identifier, filename, pov_filename):
        """
        Write the geometry to *filename* (javascript) * and *pov_filename* (POVRay)
        *identifier* is the name of the generated variable describing the whole geometry.
        """

        opacity = 0.8

        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        shape = self.shape

        output = open(filename, "w")
        with open(filename, "w") as output:
            output.write("//Computation for : %s\n"%shape.name)
            output.write("var %s = new THREE.Geometry();\n"%identifier)
            output.write("var material_for%s = new THREE.MeshBasicMaterial({opacity:%s,shading:THREE.SmoothShading});\n"%(identifier,opacity))

            with open(pov_filename, "w") as pov_file:
                pov_file.write("""
                #declare m%s = mesh {
                    """ % identifier)
                if shape.color:
                    output.write("material_for%s.color.setRGB(%f,%f,%f);\n"%(identifier,shape.color.Red(),shape.color.Green(),shape.color.Blue()))

                self._write_faces(output, pov_file, identifier)
                if shape.color:
                    color = shape.color.Red(), shape.color.Green(), shape.color.Blue()
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
            """ % ((identifier, ) + color))

    def _write_faces(self, output, pov_file, identifier):
        """
        Triangulates all faces and writes them to *output* (javascript) and *pov_file* (POVRay).
        """
        BRepMesh_Mesh(self.topo_shape, self._precision)

        _points = kjDict()

        faces_iterator = Topo(self.topo_shape).faces()
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

                for i in range(1, facing.NbTriangles()+1):

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
                    if self._triangle_is_valid(P1, P2, P3):
                        for point in (p1_coord, p2_coord, p3_coord):
                            if not _points.has_key(point):
                                _points.add(point, index)
                                output.write(vertice_fmt % (identifier, point[0], point[1], point[2]))
                                index+=1

                        n1 = the_normal(index1)
                        n2 = the_normal(index2)
                        n3 = the_normal(index2)
                        output.write(face_fmt %
                                (identifier, _points.neighbors(p1_coord)[0],
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

