import lxml.html

from django.contrib.auth.models import User

from openPLM.plmapp import models
from openPLM.plmapp.navigate import NavigationGraph, OSR
from openPLM.plmapp.controllers import PartController, DocumentController,\
        UserController, GroupController

from openPLM.plmapp.tests.base import BaseTestCase


class NavigateTestCase(BaseTestCase):
    TYPE = "Part"
    CONTROLLER = PartController
    DATA = {}
    REFERENCE = "Part1"

    def setUp(self):
        super(NavigateTestCase, self).setUp()
        self.controller = self.CONTROLLER.create(self.REFERENCE, self.TYPE, "a",
                    self.user, self.DATA, True, True)
        self.user.first_name = "robert"
        self.user.last_name = "oooo"
        self.user.save()
        self.root = self.json = None

    def get_graph_data(self, options, results=()):
        graph = NavigationGraph(self.controller, results)
        graph.set_options(options)
        graph.create_edges()
        html, json = graph.render()
        root = lxml.html.fragment_fromstring("<div>%s</div>" % html)
        self.assertNodeIsMain(root)
        self.root = root
        self.json = json
        self.nodes = root.find_class("node")
        self.edges = root.find_class("edge")

    def assertNodeIsMain(self, root):
        """
        Asserts the first div of the root is the main node.
        """
        main = root.find_class("main_node")
        self.assertEqual(1, len(main))
        self.assertEqual(root.getchildren()[0], main[0])

    def assertCount(self, nb_nodes, nb_edges):
        """
        Asserts the graph contains *nb_nodes* nodes and *nb_edges* edges.
        """
        self.assertEqual(nb_nodes, len(self.nodes))
        self.assertEqual(nb_edges, len(self.edges))
        self.assertEqual(nb_edges, len(self.json["edges"]))

    def test_navigate_empty(self):
        """ Tests that a graph with all options set to false contains only
        the main node."""
        self.get_graph_data({})
        self.assertCount(1, 0)

class PLMObjectNavigateTestCase(NavigateTestCase):
    """
    Tests common to part and document.
    """

    def test_navigate_owner(self):
        """
        Tests a navigate with the "owner" option set.
        """
        for osr, results in ((False, ()), (True, (self.user,))):
            self.get_graph_data({"owner" : True, OSR : osr }, results)
            self.assertCount(2, 1)
            main, owner = self.nodes
            self.assertEqual("owner", self.edges[0].text_content())
            text = owner.text_content().strip()
            self.assertTrue(self.user.first_name in text)
            self.assertTrue(self.user.last_name in text)
        for result in (self.cie, self.group, self.controller.object):
            self.get_graph_data({"owner" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_signer(self):
        """
        Tests a navigate with the "signer" option set.
        """
        for osr, results in ((False, ()), (True, (self.user,))):
            self.get_graph_data({"signer" : True, OSR : osr }, results)
            self.assertCount(3, 2)
            main, signer1, signer2 = self.nodes
            for edge in self.edges:
                self.assertTrue("sign" in edge.text_content())
            for node in (signer1, signer2):
                text = node.text_content().strip()
                self.assertTrue(self.user.first_name in text)
                self.assertTrue(self.user.last_name in text)
            self.assertNotEqual(signer1.attrib["id"], signer2.attrib["id"])
        for result in (self.cie, self.group, self.controller.object):
            self.get_graph_data({"signer" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_notified(self):
        """
        Tests a navigate with the "notified" option set.
        """
        self.controller.set_role(self.cie, "notified")
        for osr, results in ((False, ()), (True, (self.cie,))):
            self.get_graph_data({"notified" : True })
            self.assertCount(2, 1)
            main, owner = self.nodes
            self.assertEqual("notified", self.edges[0].text_content())
            text = owner.text_content().strip()
            self.assertTrue(self.cie.username in text)
        for result in (self.user, self.group, self.controller.object):
            self.get_graph_data({"notified" : True, OSR : True }, (result,))
            self.assertCount(1, 0)


class PartNavigateTestCase(NavigateTestCase):

    def test_navigate_children(self):
        """
        Tests a navigate with the "child" option set.
        """
        data = self.DATA.copy()
        data["name"] = "Coffee"
        child1 = PartController.create("c1", "Part", "k",
                self.user, data, True, True)
        self.controller.add_child(child1, 15, 789, "kg")
        for osr, results in ((False, ()), (True, (child1.object,))):
            self.get_graph_data({"child" : True, OSR : osr }, results)
            self.assertCount(2, 1)
            main, child_node = self.nodes
            # check the edge
            self.assertTrue("15" in self.edges[0].text_content())
            self.assertTrue("kg" in self.edges[0].text_content())
            text = child_node.text_content().strip()
            self.assertTrue(data["name"] in text)
        # add another child to child1
        child2 = PartController.create("c2", "Part", "k",
                self.user, data, True, True)
        child1.add_child(child2, 15, 789, "kg")
        for osr, results in ((False, ()), (True, (child1.object, child2.object))):
            self.get_graph_data({"child" : True, OSR : osr }, results)
            self.assertCount(3, 2)
        # empty graph is child1 is not found
        self.get_graph_data({"child" : True, OSR : True }, (child2.object,))
        self.assertCount(1, 0)
        # add child2 to the controller
        # we should have 3 nodes (controller, child1, child2)
        # and 3 edges (controller -> child1, controller -> child2 and
        # child1 -> child2)
        self.controller.add_child(child2, 15, 789, "kg")
        for osr, results in ((False, ()), (True, (child1.object, child2.object))):
            self.get_graph_data({"child" : True, OSR : osr }, results)
            self.assertCount(3, 3)
        for result in (self.cie, self.group, self.user, self.controller.object):
            self.get_graph_data({"child" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_parents(self):
        """
        Tests a navigate with the "parents" option set.
        """
        data = self.DATA.copy()
        data["name"] = "Coffee"
        parent1 = PartController.create("c1", "Part", "k",
                self.user, data, True, True)
        parent1.add_child(self.controller, 15, 789, "kg")
        for osr, results in ((False, ()), (True, (parent1.object, ))):
            self.get_graph_data({"parents" : True, OSR : osr }, results)
            self.assertCount(2, 1)
            main, parent_node = self.nodes
            self.assertTrue("789" in self.edges[0].text_content())
            self.assertTrue("15" in self.edges[0].text_content())
            self.assertTrue("kg" in self.edges[0].text_content())
            text = parent_node.text_content().strip()
            self.assertTrue(data["name"] in text)
        # add another parent to parent1
        parent2 = PartController.create("c2", "Part", "k",
                self.user, data, True, True)
        parent2.add_child(parent1, 15, 789, "kg")
        for osr, results in ((False, ()), (True, (parent1.object, parent2.object))):
            self.get_graph_data({"parents" : True, OSR : osr }, results)
            self.assertCount(3, 2)
        self.get_graph_data({"parents" : True, OSR : True }, (parent2.object,))
        self.assertCount(1, 0)
        # add the controller to parent2
        parent2.add_child(self.controller, 5, 79, "kg")
        for osr, results in ((False, ()), (True, (parent1.object, parent2.object))):
            self.get_graph_data({"parents" : True, OSR : osr }, results)
            self.assertCount(3, 3)
        for result in (self.cie, self.group, self.user, self.controller.object):
            self.get_graph_data({"parents" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_documents(self):
        """
        Tests a navigate with the "doc" option set.
        """
        data = self.DATA.copy()
        data["name"] = "Coffee"
        doc = DocumentController.create("doc", "Document", "d",
                self.user, data, True, True)
        self.controller.attach_to_document(doc)
        for osr, results in ((False, ()), (True, (doc.object,))):
            self.get_graph_data({"doc" : True, OSR : osr }, results)
            self.assertCount(2, 1)
            main, doc_node = self.nodes
            text = doc_node.text_content().strip()
            self.assertTrue(data["name"] in text)
        for result in (self.cie, self.group, self.user, self.controller.object):
            self.get_graph_data({"doc" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_doc_parts(self):
        """
        Tests a navigate with the "doc_parts" option set.
        """
        data = self.DATA.copy()
        data["name"] = "Coffee"
        doc = DocumentController.create("doc", "Document", "d",
                self.user, data, True, True)
        self.controller.attach_to_document(doc)
        for osr, results in ((False, ()), (True, (doc.object,))):
            self.get_graph_data({"doc" : False, OSR : osr,
                "doc_parts" : [self.controller.id] }, results)
            self.assertCount(2, 1)
            main, doc_node = self.nodes
            text = doc_node.text_content().strip()
            self.assertTrue(data["name"] in text)

    def test_navigate_documents2(self):
        """
        Tests a navigate with the "doc" and "child" options set, both
        parts are attached to the same document.
        """
        data = self.DATA.copy()
        data["name"] = "Coffee"
        child1 = PartController.create("c1", "Part", "k",
                self.user, data, True, True)
        self.controller.add_child(child1, 4, 8, "m")
        doc = DocumentController.create("doc", "Document", "d",
                self.user, data, True, True)
        self.controller.attach_to_document(doc)
        child1.attach_to_document(doc)
        for osr, results in ((False, ()), (True, (doc.object, child1.object))):
            self.get_graph_data({"doc" : True, "child" : True})
            self.assertCount(3, 3)


class DocumentNavigateTestCase(NavigateTestCase):
    TYPE = "Document"
    CONTROLLER = DocumentController

    def test_navigate_part(self):
        """
        Tests a navigate with the "doc" option set.
        """
        data = self.DATA.copy()
        data["name"] = "Coffee"
        part = PartController.create("part", "Part", "d",
                self.user, data, True, True)
        self.controller.attach_to_part(part)
        for osr, results in ((False, ()), (True, (part.object,))):
            self.get_graph_data({"part" : True, OSR: osr}, results)
            self.assertCount(2, 1)
            main, part_node = self.nodes
            text = part_node.text_content().strip()
            self.assertTrue(data["name"] in text)
        for result in (self.cie, self.group, self.user, self.controller.object):
            self.get_graph_data({"part" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

class GroupNavigateTestCase(NavigateTestCase):

    def setUp(self):
        super(GroupNavigateTestCase, self).setUp()
        self.part = self.controller.object
        self.controller = GroupController(self.group, self.user)

    def test_navigate_owner(self):
        """
        Tests a navigate with the "owner" option set.
        """
        for osr, results in ((False, ()), (True, (self.user,))):
            self.get_graph_data({"owner" : True, OSR : osr }, results)
            self.assertCount(2, 1)
            main, owner = self.nodes
            self.assertEqual("owner", self.edges[0].text_content())
            text = owner.text_content().strip()
            self.assertTrue(self.user.first_name in text)
            self.assertTrue(self.user.last_name in text)
        for result in (self.cie, self.group, self.part):
            self.get_graph_data({"owner" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_member(self):
        """
        Tests a navigate with the "member" option set.
        """
        for osr, results in ((False, ()), (True, (self.user,))):
            self.get_graph_data({"user" : True, OSR : osr }, results)
            self.assertCount(2, 1)
            main, owner = self.nodes
            self.assertEqual("member", self.edges[0].text_content())
            text = owner.text_content().strip()
            self.assertTrue(self.user.first_name in text)
            self.assertTrue(self.user.last_name in text)
        for result in (self.cie, self.group, self.part):
            self.get_graph_data({"member" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_two_members(self):
        """
        Tests a navigate with the "member" option set.
        The group has two members.
        """
        # add another user
        brian = User.objects.create(username="Brian", password="life")
        brian.profile.is_contributor = True
        brian.profile.save()
        brian.groups.add(self.group)
        brian.save()
        for osr, results in ((False, ()), (True, (self.user, brian))):
            self.get_graph_data({"user" : True, OSR : osr }, results)
            self.assertCount(3, 2)
            for edge in self.edges:
                self.assertEqual("member", edge.text_content())
            for node in self.nodes[1:]:
                text = node.text_content().strip()
                self.assertTrue(self.user.first_name in text or brian.username in text)
        # only brian
        self.get_graph_data({"user" : True, OSR : True }, (brian,))
        self.assertCount(2, 1)
        self.assertEqual("member", self.edges[0].text_content())
        text = self.nodes[1].text_content().strip()
        self.assertTrue(brian.username in text)
        for result in (self.cie, self.group, self.part):
            self.get_graph_data({"member" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_part(self):
        """
        Tests a navigate with the "part" option set.
        """
        # we already have one part
        for osr, results in ((False, ()), (True, (self.part,))):
            self.get_graph_data({"part" : True, OSR : osr }, results)
            self.assertCount(2, 1)
            main, part_node = self.nodes
            self.assertEqual([part_node], self.root.find_class("n_part"))
        doc = DocumentController.create("d", "Document", "doc",
                self.user, self.DATA, True, True)
        for result in (self.cie, self.group, self.user, doc.object):
            self.get_graph_data({"part" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_doc(self):
        """
        Tests a navigate with the "doc" option set.
        """
        doc = DocumentController.create("d", "Document", "doc",
                self.user, self.DATA, True, True)
        for osr, results in ((False, ()), (True, (doc.object,))):
            self.get_graph_data({"doc" : True, OSR : osr }, results)
            self.assertCount(2, 1)
            main, doc_node = self.nodes
            self.assertEqual([doc_node], self.root.find_class("n_document"))
        for result in (self.cie, self.group, self.part, self.user):
            self.get_graph_data({"doc" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

class UserNavigateTestCase(NavigateTestCase):

    def setUp(self):
        super(UserNavigateTestCase, self).setUp()
        self.part = self.controller
        self.controller = UserController(self.user, self.user)

    def test_navigate_owned(self):
        """
        Tests a navigate with the "owned" option set.
        """
        # we already own self.part
        for osr, results in ((False, ()), (True, (self.part.object,))):
            self.get_graph_data({"owned" : True, OSR : osr }, results)
            self.assertCount(2, 1)
        doc = DocumentController.create("d", "Document", "doc",
                self.user, self.DATA, True, True)
        for osr, results in ((False, ()), (True, (self.part.object, doc.object))):
            self.get_graph_data({"owned" : True, OSR : osr }, results)
            self.assertCount(3, 2)
        for result in (self.cie, self.group, self.user):
            self.get_graph_data({"owned" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

    def test_navigate_doc_parts(self):
        """
        Tests a navigate with the "doc_parts" option set.
        """
        data = self.DATA.copy()
        data["name"] = "Coffee"
        # the company owns doc so that it does not appear if only
        # the "owned" option is set
        doc = DocumentController.create("doc", "Document", "d",
                self.cie, data, True, True)
        self.part.attach_to_document(doc)
        for osr, results in ((False, ()), (True, (doc.object,))):
            self.get_graph_data({"owned" : True, OSR : osr,
                "doc_parts" : [self.part.id] }, results)
            self.assertTrue(3, 2)
        for result in (self.cie, self.group, self.user):
            self.get_graph_data({"owned" : True, OSR : True,
                "doc_parts" : [self.part.id]  }, (result,))
            self.assertCount(1, 0)

    def test_navigate_notified(self):
        """
        Tests a navigate with the "request_notification_from" option set.
        """
        self.get_graph_data({"request_notification_from" : True })
        self.assertCount(1, 0)
        self.part.set_role(self.user, "notified")
        for osr, results in ((False, ()), (True, (self.part.object,))):
            self.get_graph_data({"request_notification_from" : True, OSR : osr },
                    results)
            self.assertCount(2, 1)

    def test_navigate_signer(self):
        """
        Tests a navigate with the "to_sign" option set.
        """
        for osr, results in ((False, ()), (True, (self.part.object,))):
            self.get_graph_data({"to_sign" : True, OSR : osr }, results)
            self.assertCount(3, 2)
            roles = set(e.text_content().strip() for e in self.edges)
            self.assertEqual(set(("sign1stlevel", "sign2ndlevel")), roles)
        for result in (self.cie, self.group, self.user):
            self.get_graph_data({"to_sign" : True, OSR : True }, (result,))
            self.assertCount(1, 0)

