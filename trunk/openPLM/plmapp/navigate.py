############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
# 
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

"""
This module provides :class:`NavigationGraph` which is used to generate
the navigation's graph in :func:`~plmapp.views.navigate`.
"""

import os
import warnings
import cStringIO as StringIO
import xml.etree.cElementTree as ET

import pygraphviz as pgv

from openPLM.plmapp.controllers import PLMObjectController, PartController,\
                                       DocumentController
from openPLM.plmapp.user_controller import UserController

basedir = os.path.join(os.path.dirname(__file__), "..", "media", "img")

# just a shortcut
OSR = "only_search_results"

class FrozenAGraph(pgv.AGraph):
    '''
    A frozen AGraph

    :param data: representation of the graph in dot format
    '''

    def __init__(self, data):
        pgv.AGraph.__init__(self, data)
        self.data = data

    def write(self, path):
        if hasattr(path, "write"):
            path.write(self.data)
        else:
            with file(path, "w") as f:
                f.write(self.data)

class NavigationGraph(object):
    """
    This object can be used to generate a naviation's graph from an
    object.

    By default, the graph contains one node: the object given as argument.
    You can change this behaviour with :meth`set_options`

    Usage::

        graph = NavigationGraph(a_part_controller)
        graph.set_options({'child' : True, "parents" : True })
        graph.create_edges()
        map_str, picture_url = graph.render()

    :param obj: root of the graph
    :type obj: :class:`.PLMObjectController` or :class:`.UserController`
    :param results: if the option *only_search_results* is set, only objects in
                    results are displayed

    .. warning::
        *results* must not be a QuerySet if it contains users.
    """

    GRAPH_ATTRIBUTES = dict(dpi='96.0', aspect='2', mindist=".5", center='true',
                            ranksep='1.2', pad='0.1', mode="ipsep",
                            overlap="false", splines="false", sep="+.1,.1",
                            nodesep=".2", outputorder="edgesfirst",
                            bgcolor="transparent")
    NODE_ATTRIBUTES = dict(shape='Mrecord', fixedsize='true', fontsize='10',
                           style='filled', width='1.0', height='0.6')
    EDGE_ATTRIBUTES = dict(color='#000000', minlen="1.5", len="1.5", arrowhead='normal')
    TYPE_TO_ATTRIBUTES = {UserController : dict(color='#c7dec5',
                            image=os.path.join(basedir, "user.png")),
                          PartController : dict(color='#b5c5ff',
                            image=os.path.join(basedir, "part.png")),
                          DocumentController : dict(color='#ffffc6',
                            image=os.path.join(basedir, "document.png"))}
                           
    def __init__(self, obj, results=()):
        self.object = obj
        self.results = [r.id for r in results]
        # a PLMObject and an user may have the same id, so we add a variable
        # which tell if results contains users
        self.users_result = False
        if results:
            self.users_result = hasattr(results[0], "username")
        self.options_list = ("child", "parents", "doc", "cad", "owner", "signer",
                             "notified", "part", "owned", "to_sign",
                             "request_notification_from", OSR) 
        self.options = dict.fromkeys(self.options_list, False)
        self.graph = pgv.AGraph()
        self.graph.graph_attr.update(self.GRAPH_ATTRIBUTES)
        self.graph.node_attr.update(self.NODE_ATTRIBUTES)
        self.graph.edge_attr.update(self.EDGE_ATTRIBUTES)

    def set_options(self, options):
        """
        Sets which kind of edges should be inserted.

        Options is a dictionary(*option_name* -> boolean)

        The option *only_search_results* enables results filtering.

        If the root is a :class:`.PartController`, valid options are:

            ========== ======================================================
             Name       Description
            ========== ======================================================
             child      If True, adds recursively all children of the root
             parents    If True, adds recursively all parents of the root
             doc        If True, adds documents attached to the parts
             cad        Not yet implemented
             owner      If True, adds the owner of the root
             signer     If True, adds the signers of the root
             notified   If True, adds the notified of the root
            ========== ======================================================

        If the root is a :class:`.DocumentController`, valid options are:

            ========== ======================================================
             Name       Description
            ========== ======================================================
             parts      If True, adds parts attached to the root
             owner      If True, adds the owner of the root
             signer     If True, adds the signers of the root
             notified   If True, adds the notified of the root
            ========== ======================================================

        If the root is a :class:`.UserController`, valid options are:

            ========================== ======================================
             Name                          Description
            ========================== ======================================
             owned                     If True, adds all plmobjects owned by
                                       the root
             to_sign                   If True, adds all plmobjects signed by
                                       the root
             request_notification_from If True, adds all plmobjects which
                                       notifies the root
            ========================== ======================================

        """
        self.options.update(options)
        
    def _create_child_edges(self, obj, *args):
        if self.options[OSR] and self.users_result:
            return
        for child_l in obj.get_children():
            if self.options[OSR] and child_l.link.child.id not in self.results:
                continue
            child = PartController(child_l.link.child, None)
            self.graph.add_edge(obj.id, child.id)
            self._set_node_attributes(child)
            if self.options['doc']:
               self._create_doc_edges(child)
            self._create_child_edges(child)
    
    def _create_parents_edges(self, obj, *args):
        if self.options[OSR] and self.users_result:
            return
        for parent_l in obj.get_parents():
            if self.options[OSR] and parent_l.link.parent.id not in self.results:
                continue
            parent = PartController(parent_l.link.parent, None)
            self.graph.add_edge(parent.id, obj.id)
            self._set_node_attributes(parent)
            if self.options['doc']:
                self._create_doc_edges(parent)
            self._create_parents_edges(parent)
   
    def _create_part_edges(self, obj, *args):
        if self.options[OSR] and self.users_result:
            return
        for link in obj.get_attached_parts():
            if self.options[OSR] and link.part.id not in self.results:
                continue
            part = PartController(link.part, None)
            self.graph.add_edge(obj.id, part.id)
            self._set_node_attributes(part)
    
    def _create_doc_edges(self, obj, *args):
        if self.options[OSR] and self.users_result:
            return
        for document_item in obj.get_attached_documents():
            if self.options[OSR] and document_item.document.id not in self.results:
                continue
            document = DocumentController(document_item.document, None)
            self.graph.add_edge(obj.id, document.id)
            self._set_node_attributes(document)

    def _create_user_edges(self, obj, role):
        if self.options[OSR] and not self.users_result:
            return
        user_list = obj.plmobjectuserlink_plmobject.filter(role__istartswith=role)
        for user_item in user_list:
            if self.options[OSR] and user_item.user.id not in self.results:
                continue
            user = UserController(user_item.user, None) 
            user_id = user_item.role + str(user_item.user.id)
            self.graph.add_edge(user_id, obj.id)
            self._set_node_attributes(user, user_id, user_item.role)

    def _create_object_edges(self, obj, role):
        if self.options[OSR] and self.users_result:
            return
        part_doc_list = obj.plmobjectuserlink_user.filter(role__istartswith=role)
        for part_doc_item in part_doc_list:
            if self.options[OSR] and part_doc_item.plmobject.id not in self.results:
                continue
            part_doc_id = str(part_doc_item.role) + str(part_doc_item.plmobject_id)
            self.graph.add_edge("User%d" % obj.id, part_doc_id)
            if hasattr(part_doc_item.plmobject, 'document'):
                part_doc = DocumentController(part_doc_item.plmobject, None)
            else:
                part_doc = PartController(part_doc_item.plmobject, None)
            self._set_node_attributes(part_doc, part_doc_id)

    def create_edges(self):
        """
        Builds the graph (adds all edges and nodes that respected the options)
        """
        if isinstance(self.object, UserController):
            id_ = "User%d" % self.object.id
        else:
            id_ = self.object.id
        self.graph.add_node(id_)
        node = self.graph.get_node(id_)
        self._set_node_attributes(self.object, id_)
        color = node.attr["color"]
        node.attr.update(color="#444444", fillcolor=color, shape="box", root="true")
        functions_dic = {'child':(self._create_child_edges, None),
                         'parents':(self._create_parents_edges, None),
                         'doc':(self._create_doc_edges, None),
                         'cad':(self._create_doc_edges, None),
                         'owner':(self._create_user_edges, 'owner'),
                         'signer':(self._create_user_edges, 'sign'),
                         'notified':(self._create_user_edges, 'notified'),
                         'part': (self._create_part_edges, None),
                         'owned':(self._create_object_edges, 'owner'),
                         'to_sign':(self._create_object_edges, 'sign'),
                         'request_notification_from':(self._create_object_edges, 'notified'),
                         OSR : (lambda *args: None, None), }
        for field, value in self.options.items():
            if value:
                function, argument = functions_dic[field]
                function(self.object, argument)

    def _set_node_attributes(self, obj, obj_id=None, extra_label=""):
        node = self.graph.get_node(obj_id or obj.id)
        type_ = type(obj)
        if issubclass(type_, PartController):
            type_ = PartController
        elif issubclass(type_, DocumentController):
            type_ = DocumentController
        node.attr.update(self.TYPE_TO_ATTRIBUTES[type_])
        node.attr["URL"] = obj.plmobject_url + "navigate/"
        if isinstance(obj, PLMObjectController):
            node.attr['label'] = "%s\\n%s\\n%s" % (obj.type.encode('utf-8'),
                                                   obj.reference.encode('utf-8'),
                                                   obj.revision.encode('utf-8'))
        else:
            node.attr["label"] = obj.username.encode("utf-8")
        node.attr["label"] += "\\n" + extra_label.encode("utf-8")
        if type_ == DocumentController:
            path = "/".join((obj.type.encode('utf-8'),                                                   obj.reference.encode('utf-8'), obj.revision.encode('utf-8')))
            node.attr["tooltip"] = "/ajax/thumbnails/" + path
        else:
            node.attr["tooltip"] = "None"

    def convert_map(self, map_string):
        elements = []
        for area in ET.fromstring(map_string).findall("area"):
            left, top, x2, y2 = map(int, area.get("coords").split(","))
            width = x2 - left
            height = y2 - top
            style = "position:absolute;z-index:5;top:%dpx;left:%dpx;width:%dpx;height:%dpx;" % (top, left, width, height)
            id_ = "Nav-%s" % area.get("id")
            div = ET.Element("div", id=id_, style=style)
            div.set("class", "node")
            url = area.get("title")
            if url != "None":
                thumbnails = ET.SubElement(div, "img", src="/media/img/search.png",
                        title="Display thumbnails")
                thumbnails.set("class", "node_thumbnails ui-button ui-widget ui-state-default ui-corner-all")
                thumbnails.set("onclick", "display_thumbnails('%s', '%s');" % (id_, url))
            a = ET.SubElement(div, "a", href=area.get("href")) 
            ET.SubElement(a, "span")
            elements.append(div)

        s = "\n".join(ET.tostring(div) for div in elements)
        return s

    def render(self):
        """
        Renders an image of the graph

        :returns: a tuple (image map data, url of the image)
        """
        warnings.simplefilter('ignore', RuntimeWarning)
        # rebuild a frozen graph with sorted edges to avoid random output
        edges = self.graph.edges()
        self.graph.remove_edges_from(edges)
        s = str(self.graph) 
        s = s[:s.rfind("}")]
        edges.sort()
        s += "\n".join("%s -- %s;" % (a,b) for a, b in edges) + "}\n"
        self.graph.close()
        self.graph = FrozenAGraph(s)

        t = "p" if isinstance(self.object, PLMObjectController) else "u"
        picture_path = "media/navigate/" + t + str(self.object.id) + "-"
        for opt in self.options_list:
            picture_path += str(int(self.options[opt]))
        self.graph.layout(prog="twopi")
        picture_path2 = os.path.join(basedir, "..", "..", picture_path)
        map_path= picture_path2 + ".map"
        picture_path += ".png"
        picture_path2 += ".png"
        s = StringIO.StringIO()
        self.graph.draw(picture_path2, format='png', prog='neato')
        self.graph.draw(s, format='cmapx', prog='neato')
        s.seek(0)
        map_string = s.read()
        self.graph.clear()
        warnings.simplefilter('default', RuntimeWarning)
        return self.convert_map(map_string), picture_path

