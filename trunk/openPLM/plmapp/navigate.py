import os
import warnings
import cStringIO as StringIO

import pygraphviz as pgv

from openPLM.plmapp.controllers import PLMObjectController, PartController,\
                                       DocumentController
from openPLM.plmapp.user_controller import UserController

basedir = os.path.join(os.path.dirname(__file__), "..", "media", "img")

class NavigationGraph(object):

    GRAPH_ATTRIBUTES = dict(dpi='96.0', aspect='2', size='16.28, 8.88',
                            center='true', ranksep='1.2', pad='0.1')
    NODE_ATTRIBUTES = dict(shape='none', fixedsize='true', fontsize='10',
                           style='filled', width='1.0', height='0.6')
    EDGE_ATTRIBUTES = dict(color='#000000', len='1.5', arrowhead='normal')
    TYPE_TO_ATTRIBUTES = {UserController : dict(color='#94bd5e',
                            image=os.path.join(basedir, "user.png")),
                          PartController : dict(color='#99ccff',
                            image=os.path.join(basedir, "part.png")),
                          DocumentController : dict(color='#fef176',
                            image=os.path.join(basedir, "document.png"))}
                           
    def __init__(self, obj):
        self.object = obj
        self.options_list = ("child", "parents", "doc", "cad", "owner", "signer",
                             "notified", "part", "owned", "to_sign",
                              "request_notification_from")
        self.options = dict.fromkeys(self.options_list, False)
    
        self.graph = pgv.AGraph()
        self.graph.clear()
        self.graph.graph_attr.update(self.GRAPH_ATTRIBUTES)
        self.graph.node_attr.update(self.NODE_ATTRIBUTES)
        self.graph.edge_attr.update(self.EDGE_ATTRIBUTES)
    
    def set_options(self, options):
        self.options.update(options)
        
    def create_child_edges(self, obj, *args):
        for child_l in obj.get_children():
            child = PartController(child_l.link.child, None)
            self.graph.add_edge(obj.id, child.id)
            self.set_node_attributes(child)
            if self.options['doc']:
               self.create_doc_edges(child)
            self.create_child_edges(child)
    
    def create_parents_edges(self, obj, *args):
        for parent_l in obj.get_parents():
            parent = PartController(parent_l.link.parent, None)
            self.graph.add_edge(parent.id, obj.id)
            self.set_node_attributes(parent)
            if self.options['doc']:
                self.create_doc_edges(parent)
            self.create_parents_edges(parent)
   
    def create_part_edges(self, obj, *args):
        for link in obj.get_attached_parts():
            part = PartController(link.part, None)
            self.graph.add_edge(obj.id, part.id)
            self.set_node_attributes(part)
    
    def create_doc_edges(self, obj, *args):
        for document_item in obj.get_attached_documents():
            document = DocumentController(document_item.document, None)
            self.graph.add_edge(obj.id, document.id)
            self.set_node_attributes(document)

    def create_user_edges(self, obj, role):
        user_list = obj.plmobjectuserlink_plmobject.filter(role__istartswith=role)
        for user_item in user_list:
            user = UserController(user_item.user, None) 
            user_id = user_item.role + str(user_item.user.id)
            self.graph.add_edge(user_id, obj.id)
            self.set_node_attributes(user, user_id, user_item.role)

    def create_object_edges(self, obj, role):
        part_doc_list = obj.plmobjectuserlink_user.filter(role__istartswith=role)
        for part_doc_item in part_doc_list:
            part_doc_id = part_doc_item.role + str(part_doc_item.plmobject_id)
            self.graph.add_edge("User%d" % obj.id, part_doc_id)
            if hasattr(part_doc_item.plmobject, 'document'):
                part_doc = DocumentController(part_doc_item.plmobject, None)
            else:
                part_doc = PartController(part_doc_item.plmobject, None)
            self.set_node_attributes(part_doc, part_doc_id)

    def create_edges(self):
        if isinstance(self.object, UserController):
            id_ = "User%d" % self.object.id
        else:
            id_ = self.object.id
        self.graph.add_node(id_)
        node = self.graph.get_node(id_)
        self.set_node_attributes(self.object, id_)
        color = node.attr["color"]
        node.attr.update(color="#444444", fillcolor=color, shape="box", root="true")
        functions_dic = {'child':(self.create_child_edges, None),
                         'parents':(self.create_parents_edges, None),
                         'doc':(self.create_doc_edges, None),
                         'cad':(self.create_doc_edges, None),
                         'owner':(self.create_user_edges, 'owner'),
                         'signer':(self.create_user_edges, 'sign'),
                         'notified':(self.create_user_edges, 'notified'),
                         'part': (self.create_part_edges, None),
                         'owned':(self.create_object_edges, 'owner'),
                         'to_sign':(self.create_object_edges, 'sign'),
                         'request_notification_from':(self.create_object_edges, 'notified'),}
        for field, value in self.options.items():
            if value: 
                function, argument = functions_dic[field]
                function(self.object, argument)

    def set_node_attributes(self, obj, obj_id=None, extra_label=""):
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
       
    def render(self):
        warnings.simplefilter('ignore', RuntimeWarning)
        picture_path = "media/navigate/" + str(self.object.id) + "-"
        for opt in self.options_list:
            picture_path += str(int(self.options[opt]))
        self.graph.layout()
        picture_path2 = os.path.join(basedir, "..", "..", picture_path)
        map_path= picture_path2 + ".map"
        picture_path += ".gif"
        picture_path2 += ".gif"
        s = StringIO.StringIO()
        self.graph.draw(picture_path2, format='gif', prog='neato')
        self.graph.draw(s, format='cmapx', prog='neato')
        s.seek(0)
        map_string = s.read()
        self.graph.clear()
        warnings.simplefilter('default', RuntimeWarning)
        return map_string, picture_path

