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

import os
import datetime
from django.conf import settings
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.files.base import ContentFile
from django.core.files import File

from openPLM.plmapp.utils import *
from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.lifecycle import *
from openPLM.computer.models import *
from openPLM.office.models import *
from openPLM.cad.models import *


class ControllerTest(TestCase):
    CONTROLLER = PLMObjectController
    TYPE = "Part"
    DATA = {}

    def setUp(self):
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.save()
        self.user.get_profile().is_contributor = True
        self.user.get_profile().save()

    def test_create(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertEqual(controller.name, "")
        self.assertEqual(controller.type, self.TYPE)
        self.assertEqual(type(controller.object), get_all_plmobjects()[self.TYPE])
        obj = get_all_plmobjects()[self.TYPE].objects.get(reference=controller.reference,
                revision=controller.revision, type=controller.type)
        self.assertEqual(obj.owner, self.user)
        self.assertEqual(obj.creator, self.user)
        PLMObjectUserLink.objects.get(plmobject=obj, user=self.user, role="owner")
        self.failUnless(obj.is_editable)

    def test_create_error1(self):
        # empty reference
        def fail():
            controller = self.CONTROLLER.create("", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)

    def test_create_error2(self):
        # empty revision
        def fail():
            controller = self.CONTROLLER.create("paer", self.TYPE, "",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)

    def test_create_error3(self):
        # empty reference
        def fail():
            controller = self.CONTROLLER.create("zeez", "", "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)

    def test_create_error4(self):
        # bad type
        def fail():
            controller = self.CONTROLLER.create("zee", "__", "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)
    
    def test_create_error5(self):
        # bad type : PLMObject
        def fail():
            controller = self.CONTROLLER.create("zee", "PLMOBject_", "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, fail)
    
    def test_create_error6(self):
        """Create error test : user is not a contributor"""
        self.user.get_profile().is_contributor = False
        self.user.get_profile().save()
        def fail():
            controller = self.CONTROLLER.create("zee", "PLMOBject_", "a",
                                            self.user, self.DATA)
        self.assertRaises(PermissionError, fail)

    def test_keys(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        controller2 = self.CONTROLLER.create("Part2", self.TYPE, "a",
                                             self.user, self.DATA)
        def fail():
            controller3 = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.assertRaises(IntegrityError, fail)

    def test_getattr(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertEqual(controller.name, "")
        self.failUnless("name" in controller.attributes)
        self.assertEqual(controller.state.name, "draft")
        self.assertRaises(AttributeError, lambda: controller.unknown_attr)

    def test_setattr(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertEqual(controller.name, "")
        controller.name = "a name"
        self.assertEqual(controller.name, "a name")
        controller.save()
        self.assertEqual(controller.name, "a name")

    def test_setattr_errors(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertRaises(ValueError, setattr, controller, "owner", "error")
        self.assertRaises(ValueError, setattr, controller, "state", "error")
        self.assertRaises(ValueError, setattr, controller, "state", "draft")

    def test_promote(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertEqual(controller.state.name, "draft")
        controller.promote()
        self.assertEqual(controller.state.name, "official")
        self.failIf(controller.is_editable)
        controller.demote()
        self.assertEqual(controller.state.name, "draft")
        self.failUnless(controller.is_editable)

    def test_revise(self):
        """
        Test :meth:`revise`
        """
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        rev = controller.revise("b")
        self.assertEqual(rev.revision, "b")
        def fail():
            controller.revise("b2")
        self.assertRaises(RevisionError, fail)
        for attr in controller.get_modification_fields():
            self.assertEqual(getattr(controller, attr), getattr(rev, attr))

    def test_revise_error1(self):
        "Revision : error : empty name"
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertRaises(RevisionError, controller.revise, "")
    
    def test_revise_error2(self):
        "Revision : error : same revision name"
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        self.assertRaises(RevisionError, controller.revise, "a")

    def test_set_owner(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        user = User(username="user2")
        user.save()
        user.get_profile().is_contributor = True
        user.get_profile().save()
        controller.set_owner(user)
        self.assertEqual(controller.owner, user)

    def test_set_owner_error(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        user = User(username="user2")
        user.save()
        self.assertRaises(PermissionError, controller.set_owner, user)

    def test_set_sign1(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        user = User(username="user2")
        user.save()
        user.get_profile().is_contributor = True
        user.get_profile().save()
        controller.set_signer(user, level_to_sign_str(0))
        link = PLMObjectUserLink.objects.get(role=level_to_sign_str(0),
                                             plmobject=controller.object)
        self.assertEqual(user, link.user)

    def test_set_sign_error1(self):
        """Test sign error : bad level"""
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        user = User(username="user2")
        user.save()
        user.get_profile().is_contributor = True
        user.get_profile().save()
        self.assertRaises(PermissionError, controller.set_role, user,
                          level_to_sign_str(1664))

    def test_set_sign_error2(self):
        """Test sign error : user is not a contributor"""    
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        user = User(username="user2")
        user.save()
        self.assertRaises(PermissionError, controller.set_role, user,
                          level_to_sign_str(0))

    def test_add_notified(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        user = User(username="user2")
        user.save()
        controller.add_notified(user)
        PLMObjectUserLink.objects.get(user=user, plmobject=controller.object,
                                      role="notified")

    def test_remove_notified(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        controller.add_notified(self.user)
        PLMObjectUserLink.objects.get(user=self.user, plmobject=controller.object,
                                      role="notified")
        controller.remove_notified(self.user)
        self.assertEqual(0, len(PLMObjectUserLink.objects.filter(
            plmobject=controller.object, role="notified")))

    def test_set_role(self):
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        user = User(username="user2")
        user.save()
        user.get_profile().is_contributor = True
        user.get_profile().save()
        controller.set_role(user, "owner")
        self.assertEqual(controller.owner, user)
        controller.set_role(self.user, "notified")
        PLMObjectUserLink.objects.get(user=self.user, plmobject=controller.object,
                                      role="notified")
        controller.set_role(user, level_to_sign_str(0))
        link = PLMObjectUserLink.objects.get(role=level_to_sign_str(0),
                                             plmobject=controller.object)
        self.assertEqual(user, link.user)

    def test_promote_error(self):
        """
        Tests that a :exc:`.PromotionError` is raised when 
        :meth:`.PLMObject.is_promotable` returns False.
        """
        controller = self.CONTROLLER.create("Part1", self.TYPE, "a",
                                            self.user, self.DATA)
        # fake function so that is_promotable returns False
        def always_false():
            return False
        controller.object.is_promotable = always_false
        self.assertRaises(PromotionError, controller.promote)

class PartControllerTest(ControllerTest):
    TYPE = "Part"
    CONTROLLER = PartController
   
    def setUp(self):
        super(PartControllerTest, self).setUp()
        self.controller = self.CONTROLLER.create("aPart1", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.controller2 = self.CONTROLLER.create("aPart2", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.controller3 = self.CONTROLLER.create("aPart3", self.TYPE, "a",
                                                  self.user, self.DATA)
        self.controller4 = self.CONTROLLER.create("aPart4", self.TYPE, "a",
                                                  self.user, self.DATA)

    def test_add_child(self):
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

    def test_add_child_error1(self):
        def fail():
            # bad quantity
            self.controller.add_child(self.controller2, -10, 15)
        self.assertRaises(ValueError, fail)

    def test_add_child_error2(self):
        def fail():
            # bad order
            self.controller.add_child(self.controller2, 10, -15)
        self.assertRaises(ValueError, fail)
    
    def test_add_child_error3(self):
        def fail():
            # bad child : parent
            self.controller2.add_child(self.controller, 10, 15)
            self.controller.add_child(self.controller2, 10, 15)
        self.assertRaises(ValueError, fail)
    
    def test_add_child_error4(self):
        def fail():
            # bad child : already a child
            self.controller.add_child(self.controller2, 10, 15)
            self.controller.add_child(self.controller2, 10, 15)
        self.assertRaises(ValueError, fail)
    
    def test_add_child_error5(self):
        def fail():
            # bad child type
            doc = PLMObjectController.create("e", "PLMObject", "1", self.user)
            self.controller.add_child(doc, 10, 15)
        self.assertRaises(ValueError, fail)

    def test_add_child_error6(self):
        def fail():
            # bad child : add self
            self.controller.add_child(self.controller, 10, 15)
        self.assertRaises(ValueError, fail)

    def test_modify_child(self):
        self.controller.add_child(self.controller2, 10, 15)
        self.controller.modify_child(self.controller2, 3, 5)
        children = self.controller.get_children()
        level, link = children[0]
        self.assertEqual(link.quantity, 3)
        self.assertEqual(link.order, 5)

    def test_delete_child(self):
        self.controller.add_child(self.controller2, 10, 15)
        self.controller.delete_child(self.controller2)
        self.assertEqual(self.controller.get_children(), [])

    def test_get_children(self):
        self.controller.add_child(self.controller2, 10, 15)
        date = datetime.datetime.now()
        self.controller2.add_child(self.controller3, 10, 15)
        self.controller.add_child(self.controller4, 10, 15)
        wanted = [(1, self.controller2.object.pk),
                  (2, self.controller3.object.pk),
                  (1, self.controller4.object.pk)]
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(-1)]
        self.assertEqual(children, wanted)
        wanted = [(1, self.controller2.object.pk),
                  (1, self.controller4.object.pk)]
        # first level
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(1)]
        self.assertEqual(children, wanted)
        # date
        wanted = [(1, self.controller2.object.pk)]
        children = [(lvl, lk.child.pk) for lvl, lk in self.controller.get_children(date=date)]
        self.assertEqual(children, wanted)

    def test_get_parents(self):
        self.controller.add_child(self.controller2, 10, 15)
        date = datetime.datetime.now()
        self.controller2.add_child(self.controller3, 10, 15)
        self.controller.add_child(self.controller4, 10, 15)
        wanted = [(1, self.controller2.object.pk),
                  (2, self.controller.object.pk),]
        parents = [(lvl, lk.parent.pk) for lvl, lk in self.controller3.get_parents(-1)]
        self.assertEqual(parents, wanted)
        wanted = [(1, self.controller2.object.pk)]
        # first level
        parents = [(lvl, lk.parent.pk) for lvl, lk in self.controller3.get_parents(1)]
        self.assertEqual(parents, wanted)
        # date
        parents = [(lvl, lk.parent.pk) for lvl, lk in self.controller3.get_parents(date=date)]
        self.assertEqual(parents, [])

    def test_is_promotable1(self):
        self.failUnless(self.controller.is_promotable())

    def test_is_promotable2(self):
        self.controller.promote()
        self.failUnless(self.controller.is_promotable())
    
    def test_is_promotable3(self):
        self.controller.add_child(self.controller2, 10, 15)
        self.failUnless(self.controller.is_promotable())
        
    def test_is_promotable4(self):
        self.controller2.promote()
        self.controller.add_child(self.controller2, 10, 15)
        self.failUnless(self.controller.is_promotable())

    def test_is_promotable5(self):
        self.controller.add_child(self.controller2, 10, 15)
        self.controller.promote()
        self.failIf(self.controller.is_promotable())


class HardDiskControllerTest(PartControllerTest):
    TYPE = "HardDisk"
    CONTROLLER = SinglePartController
    DATA = {"capacity_in_go" : 500}

class DocumentControllerTest(ControllerTest):
    TYPE = "Document"
    CONTROLLER = DocumentController
    DATA = {}

    def setUp(self):
        super(DocumentControllerTest, self).setUp()
        self.controller = self.CONTROLLER.create("adoc", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.part = PartController.create("mpart", "Part", "a", self.user)
        self.old_files = []

    def tearDown(self):
        for f in list(self.controller.files.all()) + self.old_files:
            os.chmod(f.file.path, 0700)
            os.remove(f.file.path)

    def test_initial_lock(self):
        d = self.controller.add_file(self.get_file())
        self.assertEqual(d.locked, False)
        self.assertEqual(d.locker, None)

    def test_promote(self):
        self.controller.add_file(self.get_file())
        self.assertEqual(self.controller.state.name, "draft")
        self.controller.promote()
        self.assertEqual(self.controller.state.name, "official")
        self.failIf(self.controller.is_editable)
        self.controller.demote()
        self.assertEqual(self.controller.state.name, "draft")
        self.failUnless(self.controller.is_editable)

    def test_lock(self):
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertEqual(d.locked, True)
        self.assertEqual(d.locker, self.user)

    def test_lock_error1(self):
        "Error : already locked"
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertRaises(LockError, self.controller.lock, d)
    
    def test_lock_error2(self):
        "Error : bad file"
        controller = self.CONTROLLER.create("adoc2", self.TYPE, "a",
                                                 self.user, self.DATA)
        d = controller.add_file(self.get_file())
        self.old_files.append(d)
        self.assertRaises(ValueError, self.controller.lock, d)
    
    def test_unlock(self):
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.controller.unlock(d)
        self.assertEqual(d.locked, False)
        self.assertEqual(d.locker, None)
    
    def test_unlock_error1(self):
        d = self.controller.add_file(self.get_file())
        self.assertRaises(UnlockError, self.controller.unlock, d)

    def test_unlock_error2(self):
        user = User(username="baduser")
        user.set_password("password")
        user.save()
        controller = self.CONTROLLER(self.controller.object, user)
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertRaises(UnlockError, controller.unlock, d)
    
    def test_unlock_error3(self):
        "Error : bad file"
        controller = self.CONTROLLER.create("adoc2", self.TYPE, "a",
                                                 self.user, self.DATA)
        d = controller.add_file(self.get_file())
        self.assertRaises(ValueError, self.controller.unlock, d)
        self.old_files.append(d)
    
    def get_file(self, name="temp.txt", data="data"):
        f = ContentFile(data)
        f.name = name
        return f

    def test_add_file(self):
        f = self.get_file()
        self.controller.add_file(f)
        files = self.controller.files.all()
        self.assertEqual(len(files), 1)
        f2 = files[0]
        self.assertEqual(f2.filename, f.name)
        self.assertEqual(f2.size, f.size)
        self.assertEqual(f2.file.read(), "data")
        self.assertEqual(file(f2.file.name).read(), "data")
        self.assertEqual(os.path.splitext(f2.file.name)[1], ".txt")
        self.failIf("temp" in f2.file.path)
        self.failUnless(f2.file.name.startswith(os.path.join(
            settings.DOCUMENTS_DIR, "txt")))
        self.failUnless(os.access(f2.file.path, os.F_OK))
        self.failUnless(os.access(f2.file.path, os.R_OK))
        self.failUnless(not os.access(f2.file.path, os.W_OK))
        self.failUnless(not os.access(f2.file.path, os.X_OK))

    def test_add_several_files(self):
        nb = 5
        for i in xrange(nb):
            f = self.get_file("temp%d.txt" % i, "data%d" % i)
            self.controller.add_file(f)
        files = self.controller.files.all().order_by('filename')
        self.assertEqual(len(files), nb)
        for i, f2 in enumerate(files):
            self.assertEqual(f2.filename, "temp%d.txt" % i)
            self.assertEqual(f2.file.read(), "data%d" % i)
 
    def test_add_file_error1(self):
        """
        test add_file : file too big
        """
        f = self.get_file("temp.txt", "x" * 500)
        old, settings.MAX_FILE_SIZE = settings.MAX_FILE_SIZE, 400
        self.assertRaises(ValueError, self.controller.add_file, f)
        settings.MAX_FILE_SIZE = old

    def test_delete_file(self):
        self.controller.add_file(self.get_file())
        f2 = self.controller.files.all()[0]
        path = f2.file.path
        self.controller.delete_file(f2)
        self.assertEqual([], list(self.controller.files.all()))
        self.failIf(os.path.exists(path))
 
    def test_delete_file_error(self):
        self.controller.add_file(self.get_file())
        f2 = self.controller.files.all()[0]
        self.controller.lock(f2)
        self.assertRaises(DeleteFileError, self.controller.delete_file, f2)

    def test_delete_file_error2(self):
        "Error : bad file"
        controller = self.CONTROLLER.create("adoc2", self.TYPE, "a",
                                                 self.user, self.DATA)
        d = controller.add_file(self.get_file())
        self.assertRaises(ValueError, self.controller.delete_file, d)
        self.old_files.append(d)

    def test_attach_to_part(self):
        self.controller.attach_to_part(self.part)
    
    def test_attach_to_part_error1(self):
        self.assertRaises(ValueError, self.controller.attach_to_part, None)
    
    def test_attach_to_part_error2(self):
        self.assertRaises(ValueError, self.controller.attach_to_part, self)

    def test_attach_to_part_error3(self):
        obj = PLMObject.objects.create(reference="obj", type="PLMObject",
                           revision="a", creator=self.user, owner=self.user)
        self.assertRaises(ValueError, self.controller.attach_to_part, obj)
    
    def test_attach_to_part_error4(self):
        obj = self.CONTROLLER.create("ob", self.TYPE, "a", self.user, self.DATA)
        self.assertRaises(ValueError, self.controller.attach_to_part, obj)
    
    def test_detach_part(self):
        self.controller.attach_to_part(self.part)
        self.controller.detach_part(self.part)
        self.assertEqual(len(self.controller.get_attached_parts()), 0)

    def test_get_attached_parts(self):
        self.controller.attach_to_part(self.part)
        links = list(self.controller.get_attached_parts())
        self.assertEqual([l.part for l in links], [self.part.object])
        
    def test_get_attached_parts_empty(self):
        links = list(self.controller.get_attached_parts())
        self.assertEqual(links, [])

    def test_revise2(self):
        self.controller.attach_to_part(self.part)
        self.controller.add_file(self.get_file())
        f1 = self.controller.files.all()[0]
        rev = self.controller.revise("new_name")
        links = list(rev.get_attached_parts())
        self.assertEqual(links, [])
        self.assertEqual(len(rev.files.all()), 1)
        self.assertEqual(len(self.controller.files.all()), 1)
        f2 = rev.files.all()[0]
        self.assertEqual(f2.locker, None)
        self.assertEqual(f2.locked, False)
        self.assertEqual(f1.filename, f2.filename)
        self.assertEqual(f1.size, f2.size)
        self.assertEqual(f1.file.read(), f2.file.read())
        self.failIf(f1.file.path == f2.file.path)
        self.old_files.append(f2)

    def test_checkin(self):
        d = self.controller.add_file(self.get_file())
        self.controller.checkin(d, self.get_file(data="new_data"))
        self.assertEqual(len(self.controller.files), 1)
        f = self.controller.files.all()[0]
        self.assertEqual(f.file.read(), "new_data")

    def test_checkin_error1(self):
        controller = self.CONTROLLER.create("adoc2", self.TYPE, "a",
                                                 self.user, self.DATA)
        d = controller.add_file(self.get_file())
        self.old_files.append(d)
        self.assertRaises(ValueError, self.controller.checkin, 
                          d, self.get_file(data="new_data"))
        
    def test_checkin_error2(self):
        user = User(username="baduser")
        user.set_password("password")
        user.save()
        controller = self.CONTROLLER(self.controller.object, user)
        PLMObjectUserLink.objects.create(user=user, role="owner",
                                         plmobject=controller.object)
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertRaises(UnlockError, controller.checkin, d,
                          self.get_file())
        
class OfficeTest(DocumentControllerTest):
    TYPE = "OfficeDocument"
    CONTROLLER = OfficeDocumentController
    DATA = {}

    def test_add_odt(self):
        # format a4, 3 pages
        f = file("datatests/office_a4_3p.odt", "rb")
        my_file = File(f)
        self.controller.add_file(my_file)
        self.assertEquals(self.controller.nb_pages, 3)
        self.assertEquals(self.controller.format, "A4")
        f2 = self.controller.files.all()[0]
        self.failUnless(f2.file.path.endswith(".odt"))
        self.controller.delete_file(f2)

    def test_add_odt2(self):
        # fake odt
        # No exceptions should be raised
        self.controller.add_file(self.get_file("plop.odt"))
        f2 = self.controller.files.all()[0]
        self.controller.delete_file(f2)

    def test_add_odt3(self):
        # do not update fields
        f = file("datatests/office_a4_3p.odt", "rb")
        my_file = File(f)
        self.controller.add_file(my_file, False)
        self.assertEquals(self.controller.nb_pages, None)
        f2 = self.controller.files.all()[0]
        self.controller.delete_file(f2)

class DesignTest(DocumentControllerTest):
    TYPE = "Drawing"
    CONTROLLER = DrawingController
    DATA = {}

