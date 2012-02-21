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
import string
import random
import warnings
import cStringIO as StringIO
import xml.etree.cElementTree as ET

from django.contrib.auth.models import User
from django.template.loader import render_to_string

import pygraphviz as pgv

from openPLM.plmapp import models
from openPLM.plmapp.controllers import PLMObjectController, PartController,\
                                       DocumentController
from openPLM.plmapp.controllers.user import UserController

basedir = os.path.join(os.path.dirname(__file__), "..", "media", "img") 

icondir = os.path.join(basedir, "navigate")

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
            path.write(self.data.encode("utf-8"))
        else:
            with file(path, "w") as f:
                f.write(self.data)

def get_path(obj):
    if hasattr(obj, "type"):
        return u"/".join((obj.type, obj.reference, obj.revision))
    elif hasattr(obj, 'name'):
        return u"Group/%s/-/" % obj.name
    else:
        return u"User/%s/-/" % obj.username

_attrs = ("id", "type", "reference", "revision", "name")
_plmobjects_attrs = ["plmobject__" + x for x in _attrs]
_parts_attrs = ["part__" + x for x in _attrs]
_documents_attrs = ["document__" + x for x in _attrs]

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

    GRAPH_ATTRIBUTES = dict(dpi='96.0',
                            mindist=".5",
                            center='true',
                            pad='0.1',
                            mode="ipsep",
                            overlap="false",
                            splines="false",
                            sep="+.1,.1",
                            outputorder="edgesfirst",
                            bgcolor="transparent")
    NODE_ATTRIBUTES = dict(shape='none',
                           fixedsize='true',
                           bgcolor="transparent",
                           width=100./96,
                           height=70./96)
    EDGE_ATTRIBUTES = dict(color='#373434',
                           minlen="1.5",
                           len="1.5",
                           arrowhead='normal',
                           fontname="Sans bold",
                           fontcolor="#373434",
                           fontsize="9")
    TYPE_TO_IMAGE = {
            "user" : os.path.join(icondir, "user.png"),
            "group" : os.path.join(icondir, "user.png"),
            "part" : os.path.join(icondir, "part.png"),
            "document" : os.path.join(icondir, "document.png")}

    def __init__(self, obj, results=()):
        self.object = obj
        self.results = [r.id for r in results]
        # a PLMObject and an user may have the same id, so we add a variable
        # which tells if results contains users
        self.users_result = False
        if results:
            self.users_result = hasattr(results[0], "username")
        self.options_list = ("child", "parents", "doc", "cad", "owner", "signer",
                             "notified", "part", "owned", "to_sign",
                             "request_notification_from", OSR) 
        self.options = dict.fromkeys(self.options_list, False)
        self.options["prog"] = "dot"
        self.options["doc_parts"] = []
        self.graph = pgv.AGraph(directed=True)
        self.graph.graph_attr.update(self.GRAPH_ATTRIBUTES)
        self.graph.node_attr.update(self.NODE_ATTRIBUTES)
        self.graph.edge_attr.update(self.EDGE_ATTRIBUTES)
        self.title_to_nodes = {}
        self._part_to_node = {}

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
        if self.options["prog"] == "twopi":
            self.graph.graph_attr["ranksep"] = "1.2"
       
    def _create_child_edges(self, obj, *args):
        if self.options[OSR] and self.users_result:
            return
        for child_l in obj.get_children():
            link = child_l.link
            if self.options[OSR] and link.child.id not in self.results:
                continue
            child = PartController(link.child, None)
            label = "Qty: %.2f %s\\nOrder: %d" % (link.quantity,
                    link.get_shortened_unit(), link.order) 
            self.graph.add_edge(obj.id, child.id, label)
            self._set_node_attributes(child)
            if self.options['doc'] or child.id in self.options["doc_parts"]:
               self._create_doc_edges(child)
            self._create_child_edges(child)
    
    def _create_parents_edges(self, obj, *args):
        if self.options[OSR] and self.users_result:
            return
        for parent_l in obj.get_parents():
            link = parent_l.link
            if self.options[OSR] and link.parent.id not in self.results:
                continue
            parent = PartController(link.parent, None)
            label = "Qty: %.2f %s\\nOrder: %d" % (link.quantity,
                    link.get_shortened_unit(), link.order) 
            self.graph.add_edge(parent.id, obj.id, label)
            self._set_node_attributes(parent)
            if self.options['doc'] or parent.id in self.options["doc_parts"]:
                self._create_doc_edges(parent)
            self._create_parents_edges(parent)
   
    def _create_part_edges(self, obj, *args):
        if self.options[OSR] and self.users_result:
            return
        for link in obj.get_attached_parts().select_related("part").only(*_parts_attrs):
            if self.options[OSR] and link.part.id not in self.results:
                continue
            part = PartController(link.part, None)
            # create a link part -> document:
            # if layout is dot, the part is on top of the document
            # cf. tickets #82 and #83
            self.graph.add_edge(part.id, obj.id, " ")
            self._set_node_attributes(part)
    
    def _create_doc_edges(self, obj, obj_id=None, *args):
        if self.options[OSR] and self.users_result:
            return
        for document_item in obj.get_attached_documents().select_related("document").only(*_documents_attrs):
            if self.options[OSR] and document_item.document.id not in self.results:
                continue
            document = DocumentController(document_item.document, None)
            self.graph.add_edge(obj_id or obj.id, document.id, " ")
            self._set_node_attributes(document)

    def _create_user_edges(self, obj, role):
        if self.options[OSR] and not self.users_result:
            return
        if hasattr(obj, 'user_set'):
            if role == "owner":
                users = ((obj.owner, role),)
            else:
                users = ((u, role) for u in obj.user_set.all())
        else:
            users = obj.plmobjectuserlink_plmobject.filter(role__istartswith=role)
            users = ((u.user, u.role) for u in users.all())
        for user, role in users:
            if self.options[OSR] and user.id not in self.results:
                continue
            user.plmobject_url = "/user/%s/" % user.username
            user_id = role + str(user.id)
            self.graph.add_edge(user_id, obj.id, role.replace("_", "\\n"))
            self._set_node_attributes(user, user_id, role)

    def _create_object_edges(self, obj, role):
        if self.options[OSR] and self.users_result:
            return
        node = "User%d" % obj.id
        if role in ("owner", "notified"):
            qs = obj.plmobjectuserlink_user.filter(role=role)
            for link in qs.select_related("plmobject").only(*_plmobjects_attrs):
                if self.options[OSR] and link.plmobject_id not in self.results:
                    continue
                part_doc_id = role + str(link.plmobject_id)
                self.graph.add_edge(node, part_doc_id, role)
                part_doc = link.plmobject
                if part_doc.is_part:
                    if part_doc.id in self.options["doc_parts"]:
                        part_doc = PartController(link.plmobject.part, None)
                        self._create_doc_edges(part_doc, part_doc_id)
                self._set_node_attributes(part_doc, part_doc_id)

        else:
            # signer roles
            qs = obj.plmobjectuserlink_user.filter(role__istartswith=role)
            for link in qs.select_related("plmobject").only("role", *_plmobjects_attrs):
                if self.options[OSR] and link.plmobject_id not in self.results:
                    continue
                part_doc_id = link.role + str(link.plmobject_id)
                self.graph.add_edge(node, part_doc_id, link.role.replace("_", "\\n"))
                part_doc = link.plmobject
                if part_doc.is_part:
                    if part_doc.id in self.options["doc_parts"]:
                        part_doc = PartController(link.plmobject.part, None)
                        self._create_doc_edges(part_doc, part_doc_id)
                self._set_node_attributes(part_doc, part_doc_id)

    def create_edges(self):
        """
        Builds the graph (adds all edges and nodes that respected the options)
        """
        self.options["doc_parts"] = set(self.options["doc_parts"])
        self.doc_parts = "#".join(str(o) for o in self.options["doc_parts"])
        if isinstance(self.object, UserController):
            id_ = "User%d" % self.object.id
        else:
            id_ = self.object.id
        self.graph.add_node(id_)
        node = self.graph.get_node(id_)
        self._set_node_attributes(self.object, id_)
        self.main_node = node.attr["id"]
        node.attr["image"] = node.attr["image"].replace(".png", "_main.png")
        node.attr["width"] = 110. / 96 
        node.attr["height"] = 80. / 96 
        functions_dic = {'child':(self._create_child_edges, None),
                         'parents':(self._create_parents_edges, None),
                         'doc':(self._create_doc_edges, None),
                         'cad':(self._create_doc_edges, None),
                         'owner':(self._create_user_edges, 'owner'),
                         'signer':(self._create_user_edges, 'sign'),
                         'notified':(self._create_user_edges, 'notified'),
                         'user':(self._create_user_edges, 'member'),
                         'part': (self._create_part_edges, None),
                         'owned':(self._create_object_edges, 'owner'),
                         'to_sign':(self._create_object_edges, 'sign'),
                         'request_notification_from':(self._create_object_edges, 'notified'),
                         }
        for field, value in self.options.iteritems():
            if value and field in functions_dic:
                function, argument = functions_dic[field]
                function(self.object, argument)
        if not self.options["doc"] and self.object.id in self.options["doc_parts"]:
            if isinstance(self.object, PartController):
                self._create_doc_edges(self.object, None)

        # treats the parts to see if they have an attached document
        if not self.options["doc"]:
            parts = models.DocumentPartLink.objects.\
                    filter(part__in=self._part_to_node.keys()).\
                    values_list("part_id", flat=True)
            for id_ in parts:
                data = self._part_to_node[id_]
                data["show_documents"] = True
                if id_ not in self.options["doc_parts"]:
                    data["parts"] = self.doc_parts + "#" + str(id_)
                    data["doc_img_add"] = True
                else:
                    data["doc_img_add"] = False
                    data["parts"] = "#".join(str(x) for x in self.options["doc_parts"] if x != id_)

    def _set_node_attributes(self, obj, obj_id=None, extra_label=""):
        obj_id = obj_id or obj.id
        
        # data and title_to_nodes are used to retrieve usefull data (url, tooltip)
        # in convert_map
        data = {}
        node = self.graph.get_node(obj_id)
        
        # set node attributes according to its type
        if isinstance(obj, (PLMObjectController, models.PLMObject)):
            # display the object's name if it is not empty
            ref = (obj.type, obj.reference, obj.revision)
            label = obj.name.strip() or u"\n".join(ref)
            data["title_"] = u" - ".join(ref)
            # add data to show/hide thumbnails and attached documents
            if obj.is_document:
                data["path"] = get_path(obj)
                data["thumbnails"] = True
                type_ = "document"
            else:
                type_ = "part"
                # this will be used later to see if it has an attached document
                self._part_to_node[obj.id] = data
        elif isinstance(obj, (User, UserController)):
            full_name = u'%s\n%s' % (obj.first_name, obj.last_name)
            label = full_name.strip() or obj.username
            data["title_"] = obj.username
            type_ = "user"
        else:
            label = obj.name
            type_ = "group"
        id_ = "%s_%s_%d" % (obj_id, type_.capitalize(), obj.id)

        data["label"] = label + "\n" + extra_label if extra_label else label
        node.attr.update(
                URL=obj.plmobject_url + "navigate/",
                label="",
                image=NavigationGraph.TYPE_TO_IMAGE[type_],
                id=id_,
                )
        self.title_to_nodes[id_] = data

    def convert_map(self, map_string):
        elements = []
        ajax_navigate = "/ajax/navigate/" + get_path(self.object)
        for area in ET.fromstring(map_string).findall("area"):
            data = self.title_to_nodes.get(area.get("id"), {})
            
            # compute css position of the div
            left, top, x2, y2 = map(int, area.get("coords").split(","))
            width = x2 - left
            height = y2 - top
            style = "position:absolute;z-index:5;top:%dpx;left:%dpx;width:%dpx;height:%dpx;" % (top, left, width, height)

            # create a div with a title, and an <a> element
            id_ = "Nav-%s" % area.get("id")
            ctx = data.copy()
            ctx["style"] = style
            ctx["id"] = id_
            ctx["main"] = self.main_node == area.get("id")
            ctx["href"] = area.get("href")
            ctx["documents_url"] = ajax_navigate

            elements.append(render_to_string("navigate/node.htm", ctx))
        return u"\n".join(elements)

    def render(self):
        """
        Renders an image of the graph

        :returns: a tuple (image map data, url of the image, path of the image)
        """
        warnings.simplefilter('ignore', RuntimeWarning)
        # rebuild a graph with sorted edges to avoid random output
        edges = self.graph.edges(keys=True)
        self.graph.remove_edges_from((a, b) for a, b, k in edges)
        s = unicode(self.graph)
        s = s[:s.rfind("}")]
        edges.sort()
        s += "\n".join(u'%s -> %s [label="%s"];' % edge for edge in edges) + "}\n"
        self.graph.close()
        self.graph = FrozenAGraph(s)

        rand = "".join(random.choice(string.ascii_lowercase) for x in xrange(40))
        picture_path = "media/navigate/" + rand
        prog = self.options.get("prog", "dot")
        self.graph.layout(prog=prog)
        picture_path2 = os.path.join(basedir, "..", "..", picture_path)
        map_path= picture_path2 + ".map"
        picture_path += ".png"
        picture_path2 += ".png"
        s = StringIO.StringIO()
        self.graph.draw(picture_path2, format='png', prog=prog)
        self.graph.draw(s, format='cmapx', prog=prog)
        s.seek(0)
        map_string = s.read()
        self.graph.clear()
        return self.convert_map(map_string), picture_path, picture_path2
