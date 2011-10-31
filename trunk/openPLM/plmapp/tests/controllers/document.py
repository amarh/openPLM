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
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files import File

from openPLM.plmapp.utils import *
from openPLM.plmapp.exceptions import *
from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.lifecycle import *
from openPLM.computer.models import *
from openPLM.office.models import *
from openPLM.cad.models import *

from openPLM.plmapp.tests.controllers.plmobject import ControllerTest

class DocumentControllerTest(ControllerTest):
    TYPE = "Document"
    CONTROLLER = DocumentController
    DATA = {}

    def setUp(self):
        super(DocumentControllerTest, self).setUp()
        self.controller = self.CONTROLLER.create("adoc", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.part = PartController.create("mpart", "Part", "a", self.user,
                self.DATA)
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
        lcl = LifecycleList("diop", "official", "draft", 
                "issue1", "official", "deprecated")
        lc = Lifecycle.from_lifecyclelist(lcl)
        self.controller.lifecycle = lc
        self.controller.state = State.objects.get(name="draft")
        self.controller.save()
        self.controller.promote()
        self.assertEqual(self.controller.state.name, "issue1")
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
    
    def test_add_file(self):
        f = self.get_file()
        self.controller.add_file(f)
        files = self.controller.files.all()
        self.assertEqual(len(files), 1)
        f2 = files[0]
        self.assertEqual(f2.filename, f.name)
        self.assertEqual(f2.size, f.size)
        self.assertEqual(f2.file.read(), "data")
        self.assertEqual(file(f2.file.path).read(), "data")
        self.assertEqual(os.path.splitext(f2.file.name)[1], ".txt")
        self.failIf("temp" in f2.file.path)
        self.failUnless(f2.file.path.startswith(settings.DOCUMENTS_DIR))
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
        self.assertRaises(TypeError, self.controller.attach_to_part, None)
    
    def test_attach_to_part_error2(self):
        self.assertRaises(TypeError, self.controller.attach_to_part, self)

    def test_attach_to_part_error3(self):
        obj = PLMObject.objects.create(reference="obj", type="PLMObject",
                           revision="a", creator=self.user, owner=self.user,
                           group=self.group)
        self.assertRaises(TypeError, self.controller.attach_to_part, obj)
    
    def test_attach_to_part_error4(self):
        obj = self.CONTROLLER.create("ob", self.TYPE, "a", self.user, self.DATA)
        self.assertRaises(TypeError, self.controller.attach_to_part, obj)
    
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
        user.groups.add(self.group)
        controller = self.CONTROLLER(self.controller.object, user)
        PLMObjectUserLink.objects.create(user=user, role="owner",
                                         plmobject=controller.object)
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertRaises(UnlockError, controller.checkin, d,
                          self.get_file())
    
    def test_checkin_errors3(self):
        user = User(username="baduser")
        user.set_password("password")
        user.save()
        DelegationLink.objects.create(delegator=self.user, delegatee=user,
                role=ROLE_OWNER)
        controller = self.CONTROLLER(self.controller.object, user)
        d = self.controller.add_file(self.get_file())
        self.assertRaises(PermissionError, controller.checkin, d,
                          self.get_file())

    def test_add_thumbnail(self):
        thumbnail = ContentFile(file("datatests/thumbnail.png").read())
        thumbnail.name = "Thumbnail.png"
        self.controller.add_file(self.get_file())
        f2 = self.controller.files.all()[0]
        self.controller.add_thumbnail(f2, thumbnail)
        self.assertNotEquals(None, f2.thumbnail)

    def test_revise_with_thumbnail(self):
        thumbnail = ContentFile(file("datatests/thumbnail.png").read())
        thumbnail.name = "Thumbnail.png"
        self.controller.add_file(self.get_file())
        f2 = self.controller.files.all()[0]
        self.controller.add_thumbnail(f2, thumbnail)

        revb = self.controller.revise("b")
        f3 = revb.files.all()[0]
        self.assertNotEquals(f2.thumbnail.path, f3.thumbnail.path)


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

