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
This module contains some tests for openPLM.
"""

from django.db import models as djmodels

from openPLM.plmapp.controllers import PartController, DocumentController
import openPLM.plmapp.models as models
import openPLM.plmapp.forms as forms

from openPLM.plmapp.tests.base import BaseTestCase

class MockExtension(models.ParentChildLinkExtension):

    custom_attribute = djmodels.CharField(max_length=20, blank=True)

    @classmethod
    def get_visible_fields(cls):
        return ("custom_attribute", )

    @classmethod
    def apply_to(cls, parent):
        return parent.name == u"mockextension"
   
    def clone(self, link, save=False, **data):
        ca = data.get("custom_attribute", self.custom_attribute)
        clone = MockExtension(link=link, custom_attribute=ca)
        if save:
            clone.save()
        return clone

mockext = MockExtension._meta.module_name

class InvisibleMockExtension(models.ParentChildLinkExtension):

    attr1 = djmodels.CharField(max_length=20, blank=True)
    attr2 = djmodels.IntegerField(blank=True)

    @classmethod
    def apply_to(cls, parent):
        return parent.name == u"imockextension"
   
    def clone(self, link, save=False, **data):
        attr1 = data.get("attr1", self.attr1)
        attr2 = data.get("attr2", self.attr2)
        clone = InvisibleMockExtension(link=link, attr1=attr1, attr2=attr2)
        if save:
            clone.save()
        return clone


imockext = InvisibleMockExtension._meta.module_name

class ParentChildLinkExtensionTestCase(BaseTestCase):
    TYPE = "Part"
    CONTROLLER = PartController
   
    def setUp(self):
        self.registered_PCLEs = list(models.registered_PCLEs)
        models.register_PCLE(MockExtension)
        models.register_PCLE(InvisibleMockExtension)
        super(ParentChildLinkExtensionTestCase, self).setUp()
        self.controller = self.CONTROLLER.create("aPart1", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.controller.name = u"mockextension"
        self.controller.save()
        self.controller2 = self.CONTROLLER.create("aPart2", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.controller2.name = u"imockextension"
        self.controller2.save()
        self.controller3 = self.CONTROLLER.create("aPart3", self.TYPE, "a",
                                                  self.user, self.DATA)

    def tearDown(self):
        models.registered_PCLEs = self.registered_PCLEs
        super(ParentChildLinkExtensionTestCase, self).tearDown()
   
    def test_clone_PCLE(self):
        link = models.ParentChildLink.objects.create(parent=self.controller.object,
                child=self.controller2.object, quantity=3, order=4, unit="m")
        self.assertFalse(bool(link.extensions))
        ext = MockExtension.objects.create(link=link, custom_attribute="slt")
        self.assertEqual([ext.id], [e.id for e in link.extensions])
        clone = ext.clone(link)
        self.assertEqual(clone.custom_attribute, ext.custom_attribute)
        self.assertEqual(link.id, clone.link.id)
        clone = ext.clone(link, custom_attribute="'")
        self.assertEqual(clone.custom_attribute, "'")
        self.assertEqual(link.id, clone.link.id)

        clone = ext.clone(link, save=True, custom_attribute="'")
        self.assertEqual(clone.custom_attribute, "'")
        self.assertEqual(link.id, clone.link.id)
        self.assertEqual(2, MockExtension.objects.count()) 

    def get_link_and_ext(self):

        link = models.ParentChildLink.objects.create(parent=self.controller.object,
                child=self.controller2.object, quantity=3, order=4, unit="m")
        ext = MockExtension.objects.create(link=link, custom_attribute="slt")
        return link, ext

    def test_clone_link(self):
        # clone a link without saving it
        link, ext = self.get_link_and_ext()
        clone, exts = link.clone()
        self.assertEqual(1, len(exts))
        self.assertNotEqual(link.id, clone.id)
        self.assertEqual(3, clone.quantity)
        self.assertEqual(4, clone.order)
        self.assertEqual(self.controller.object, clone.parent)
        self.assertEqual("slt", exts[0].custom_attribute)
        self.assertEqual(1, MockExtension.objects.count())

    def test_clone_link_invisible_ext(self):
        link = models.ParentChildLink.objects.create(parent=self.controller2.object,
                child=self.controller3.object, quantity=3, order=4, unit="m")
        ext1 = InvisibleMockExtension.objects.create(link=link, attr1="slt", attr2=5)
        ext2 = InvisibleMockExtension.objects.create(link=link, attr1="st", attr2=6)
        clone, exts = link.clone(save=True)
        self.assertEqual(2, len(exts))
        e1 = InvisibleMockExtension.objects.filter(link=clone, attr1="slt")[0]
        e2 = InvisibleMockExtension.objects.filter(link=clone, attr1="st")[0]
        self.assertNotEqual(link.id, clone.id)
        self.assertNotEqual(e1.id, ext1.id)
        self.assertNotEqual(e2.id, ext2.id)
        self.assertEqual(4, InvisibleMockExtension.objects.count())
    
    def test_clone_link_with_saving(self):
        # clone a link with saving
        link, ext = self.get_link_and_ext()
        clone, exts = link.clone(save=True, order=8)
        self.assertNotEqual(link.id, clone.id)
        self.assertEqual(1, len(exts))
        self.assertEqual(3, clone.quantity)
        self.assertEqual(8, clone.order)
        self.assertEqual(self.controller.object, clone.parent)
        self.assertEqual("slt", exts[0].custom_attribute)
        self.assertEqual(2, MockExtension.objects.count())
        self.assertEqual(tuple(exts), tuple(clone.extensions))

    def test_clone_with_extension_modification(self):
        # clone a link and modify its extension
        link, ext = self.get_link_and_ext()
        clone, exts = link.clone(save=True,
                extension_data={mockext:{"custom_attribute":"yo"}})
        self.assertNotEqual(link.id, clone.id)
        self.assertEqual(1, len(exts))
        self.assertEqual(3, clone.quantity)
        self.assertEqual(4, clone.order)
        self.assertEqual(self.controller.object, clone.parent)
        self.assertEqual("yo", exts[0].custom_attribute)
        self.assertEqual(2, MockExtension.objects.count())
        self.assertEqual(tuple(exts), tuple(clone.extensions))

    def test_add_child_no_extension(self):
        children = self.controller.get_children()
        self.assertEqual(len(children), 0)
        self.controller.add_child(self.controller2, 10, 15)
        children = self.controller.get_children()
        self.assertEqual(len(children), 1)
        level, link = children[0]
        self.assertEqual(level, 1)
        self.assertEqual(link.child.pk, self.controller2.object.pk)
        self.assertEqual(link.parent.pk, self.controller.object.pk)
        self.assertEqual(link.quantity, 10)
        self.assertEqual(link.order, 15)
        self.assertFalse(bool(link.extensions))
        
    def test_modify_child(self):
        self.controller.add_child(self.controller2, 10, 15, "-")
        self.controller.modify_child(self.controller2, 3, 5, "kg",
                **{mockext:{"custom_attribute":"val"}})
        children = self.controller.get_children()
        level, link = children[0]
        self.assertEqual(link.quantity, 3)
        self.assertEqual(link.order, 5)
        self.assertEqual(link.unit, "kg")
        # checks the extension
        extensions = link.extensions
        self.assertEqual(1, len(extensions))
        ext = extensions[0]
        self.assertEqual(MockExtension, type(ext))
        self.assertEqual("val", ext.custom_attribute)

    def test_modify_child_invisible_ext(self):
        self.controller2.add_child(self.controller3, 10, 15, "-")
        link = self.controller2.get_children()[0].link
        ext1 = InvisibleMockExtension.objects.create(link=link, attr1="slt", attr2=6)
        ext2 = InvisibleMockExtension.objects.create(link=link, attr1="st", attr2=6)
        self.controller2.modify_child(self.controller3, 3, 5, "kg")
        children = self.controller2.get_children()
        level, link = children[0]
        self.assertEqual(link.quantity, 3)
        self.assertEqual(link.order, 5)
        self.assertEqual(link.unit, "kg")
        # checks the extension
        extensions = link.extensions
        self.assertEqual(2, len(extensions))
        ext = extensions[0]
        self.assertEqual(InvisibleMockExtension, type(ext))
        self.assertEqual(6, ext.attr2)
        self.assertEqual(4, InvisibleMockExtension.objects.count())
    
    def test_modify_only_extension(self):
        self.controller.add_child(self.controller2, 10, 15, "-",
                **{mockext:{"custom_attribute":"val1"}})
        self.controller.modify_child(self.controller2, 10, 15, "-",
                **{mockext:{"custom_attribute":"val2"}})
        children = self.controller.get_children()
        level, link = children[0]
        self.assertEqual(link.quantity, 10)
        self.assertEqual(link.order, 15)
        self.assertEqual(link.unit, "-")
        extensions = link.extensions
        self.assertEqual(1, len(extensions))
        ext = extensions[0]
        self.assertEqual(MockExtension, type(ext))
        self.assertEqual("val2", ext.custom_attribute)
        self.assertEqual(2, models.ParentChildLink.objects.
                filter(parent=self.controller.object).count())

    def test_modify_nothing(self):
        self.controller.add_child(self.controller2, 10, 15, "-",
                **{mockext:{"custom_attribute":"val1"}})
        self.controller.modify_child(self.controller2, 10, 15, "-",
                **{mockext:{"custom_attribute":"val1"}})
        self.assertEqual(1, models.ParentChildLink.objects.
                filter(parent=self.controller.object).count())
        self.assertEqual(1, MockExtension.objects.count())

    def test_delete_child(self):
        self.assertEqual(0, MockExtension.objects.count())
        self.controller.add_child(self.controller2, 10, 15,
                **{mockext:{"custom_attribute":"val1"}})
        self.controller.delete_child(self.controller2)
        self.assertEqual(self.controller.get_children(), [])
        # the extension must not be deleted
        self.assertEqual(1, MockExtension.objects.count())

    def test_revise(self):

        self.controller.add_child(self.controller2, 10, 15, "-",
                **{mockext:{"custom_attribute":"val1"}})
        self.controller.add_child(self.controller3, 10, 35, "-")
        rev = self.controller.revise("b")
        self.assertEqual(2, MockExtension.objects.count())
        child1, child2 = rev.get_children()
        exts = child1.link.extensions
        self.assertFalse(bool(child2.link.extensions))
        self.assertEqual(1, len(exts))
        ext = exts[0]
        self.assertEqual("val1", ext.custom_attribute)
                
    def test_add_child_form(self):
        fname = mockext + "_custom_attribute"
        # create a form and check that it has a custom_attribute field
        form = forms.AddChildForm(self.controller.object)
        field = form[fname]
        self.assertRaises(KeyError, lambda: form[imockext + "_attr1"])
        self.assertRaises(KeyError, lambda: form[imockext + "_attr2"])
        # create another form that must not have a custom_attribute field 
        form = forms.AddChildForm(self.controller2.object)
        self.assertRaises(KeyError, lambda: form[fname])
        self.assertRaises(KeyError, lambda: form[imockext + "_attr1"])
        self.assertRaises(KeyError, lambda: form[imockext + "_attr2"])

        data = {"type" : "Part",
                "reference" : self.controller2.reference,
                "revision" : self.controller2.revision,
                "quantity" : 3,
                "order" : 4,
                "unit" : "g",
                fname : "plop",
                }
        form = forms.AddChildForm(self.controller.object, data)
        self.assertTrue(form.is_valid())
        self.assertEqual({mockext : {"custom_attribute" : u"plop"}},
                form.extensions)
        
    def test_children_formset(self):
        fname = mockext + "_custom_attribute"
        self.controller.add_child(self.controller2, 10, 15, "-",
                **{mockext:{"custom_attribute":"val1"}})
        self.controller.add_child(self.controller3, 10, 35, "-")
        # create an initial formset
        formset = forms.get_children_formset(self.controller)
        f1, f2 = formset.forms
        field = f1[fname].field
        self.assertEqual("val1", field.initial)
        self.assertEqual(None, f2[fname].field.initial)
        self.assertRaises(KeyError, lambda: f1[imockext + "_attr1"])
        self.assertRaises(KeyError, lambda: f1[imockext + "_attr2"])
        
        # create a valid formset
        data = {}
        for key, value in formset.management_form.initial.iteritems():
            data["form-" + key] = value or ""
        for i, form in enumerate(formset.forms):
            for field in form:
                value = field.field.initial or form.initial.get(field.name, "")
                if callable(value):
                    value = value()
                data["form-%d-%s" % (i, field.name)] = value 
            data['form-%d-ORDER' % i] = str(i)
        data["form-1-" + fname] = "beer"
        formset = forms.get_children_formset(self.controller, data)
        self.assertTrue(formset.is_valid())

        # update the controller
        self.controller.update_children(formset)
        child1, child2 = self.controller.get_children()
        self.assertEqual(1, child1.link.extensions.count())
        self.assertEqual(1, child2.link.extensions.count())
        self.assertEqual("beer", child2.link.extensions[0].custom_attribute)
        self.assertEqual(3, models.ParentChildLink.objects.count())
        self.assertEqual(2, MockExtension.objects.count())
