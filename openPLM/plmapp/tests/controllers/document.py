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
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

"""
This module contains some tests for openPLM.
"""

import os
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

import openPLM.plmapp.exceptions as exc
import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PartController, DocumentController
from openPLM.plmapp.lifecycle import LifecycleList

from openPLM.plmapp.tests.controllers.plmobject import ControllerTest

class DocumentControllerTest(ControllerTest):
    TYPE = "Document"
    CONTROLLER = DocumentController
    DATA = {}

    def setUp(self):
        super(DocumentControllerTest, self).setUp()
        self.controller = self.CONTROLLER.create("adoc", self.TYPE, "a",
                                                 self.user, self.DATA)
        self.old_files = []

    def get_part(self):
        return PartController.create("mpart", "Part", "a", self.user,
                self.DATA, True, True)

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
        self.assertFalse(self.controller.is_editable)
        lcl = LifecycleList("diop", "official", "draft",
                "issue1", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.controller.lifecycle = lc
        self.controller.state = models.State.objects.get(name="draft")
        self.controller.save()
        self.controller.promote()
        self.assertEqual(self.controller.state.name, "issue1")
        self.controller.demote()
        self.assertEqual(self.controller.state.name, "draft")
        self.assertTrue(self.controller.is_editable)

    def test_is_promotable_no_file(self):
        """ Tests that a document without a file is not promotable."""
        self.assertFalse(self.controller.files)
        self.assertFalse(self.controller.is_promotable())

    def test_is_promotable_one_locked_file(self):
        """ Tests that a document with one locked file is not promotable."""
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertFalse(self.controller.is_promotable())

    def test_is_promotable_one_unlocked_file(self):
        """ Tests that a document with one unlocked file is promotable."""
        d = self.controller.add_file(self.get_file())
        self.assertTrue(self.controller.is_promotable())

    def test_is_promotable_two_unlocked_files(self):
        """ Tests that a document with two unlocked files is promotable."""
        self.controller.add_file(self.get_file("plop.txt"))
        self.controller.add_file(self.get_file("plap.txt"))
        self.assertTrue(self.controller.is_promotable())

    def test_lock(self):
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertEqual(d.locked, True)
        self.assertEqual(d.locker, self.user)

    def test_lock_error1(self):
        "Error : already locked"
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertRaises(exc.LockError, self.controller.lock, d)

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
        self.assertRaises(exc.UnlockError, self.controller.unlock, d)

    def test_unlock_error2(self):
        user = User(username="baduser")
        user.set_password("password")
        user.save()
        controller = self.CONTROLLER(self.controller.object, user)
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertRaises(exc.UnlockError, controller.unlock, d)

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
        self.assertEqual(os.path.splitext(f2.file.name)[1], ".test")
        self.assertFalse("temp" in f2.file.path)
        self.assertTrue(f2.file.path.startswith(settings.DOCUMENTS_DIR))
        self.assertTrue(os.access(f2.file.path, os.F_OK))
        self.assertTrue(os.access(f2.file.path, os.R_OK))
        self.assertTrue(not os.access(f2.file.path, os.W_OK))
        self.assertTrue(not os.access(f2.file.path, os.X_OK))

    def test_add_several_files(self):
        nb = 5
        for i in xrange(nb):
            f = self.get_file("temp%d.test" % i, "data%d" % i)
            self.controller.add_file(f)
        files = self.controller.files.all().order_by('filename')
        self.assertEqual(len(files), nb)
        for i, f2 in enumerate(files):
            self.assertEqual(f2.filename, "temp%d.test" % i)
            self.assertEqual(f2.file.read(), "data%d" % i)

    def test_add_file_error1(self):
        """
        test add_file : file too big
        """
        f = self.get_file("temp.test", "x" * 500)
        old, settings.MAX_FILE_SIZE = settings.MAX_FILE_SIZE, 400
        self.assertRaises(ValueError, self.controller.add_file, f)
        settings.MAX_FILE_SIZE = old

    def test_delete_file(self):
        self.controller.add_file(self.get_file())
        f2 = self.controller.files.all()[0]
        path = f2.file.path
        self.controller.delete_file(f2)
        self.assertEqual([], list(self.controller.files.all()))
        self.assertFalse(os.path.exists(path))

    def test_delete_file_error(self):
        self.controller.add_file(self.get_file())
        f2 = self.controller.files.all()[0]
        self.controller.lock(f2)
        self.assertRaises(exc.DeleteFileError, self.controller.delete_file, f2)

    def test_delete_file_error2(self):
        "Error : bad file"
        controller = self.CONTROLLER.create("adoc2", self.TYPE, "a",
                                                 self.user, self.DATA)
        d = controller.add_file(self.get_file())
        self.assertRaises(ValueError, self.controller.delete_file, d)
        self.old_files.append(d)

    def test_attach_to_part(self):
        part = self.get_part()
        self.controller.attach_to_part(part)
        attached = self.controller.get_attached_parts()[0].part
        self.assertEqual(part.id, attached.id)

    def test_attach_to_part_error1(self):
        self.assertRaises(TypeError, self.controller.attach_to_part, None)

    def test_attach_to_part_error2(self):
        self.assertRaises(TypeError, self.controller.attach_to_part, self)

    def test_attach_to_part_error3(self):
        obj = models.PLMObject.objects.create(reference="obj", type="PLMObject",
                           revision="a", creator=self.user, owner=self.user,
                           group=self.group)
        self.assertRaises(TypeError, self.controller.attach_to_part, obj)

    def test_attach_to_part_error4(self):
        obj = self.CONTROLLER.create("ob", self.TYPE, "a", self.user, self.DATA)
        self.assertRaises(TypeError, self.controller.attach_to_part, obj)

    def test_detach_part(self):
        part = self.get_part()
        self.controller.attach_to_part(part)
        t = timezone.now()
        self.controller.detach_part(part)
        self.assertEqual(self.controller.get_attached_parts().count(), 0)
        self.assertEqual([part.object], [l.part for l in self.controller.get_attached_parts(t)])

    def test_get_attached_parts(self):
        part = self.get_part()
        self.controller.attach_to_part(part)
        links = list(self.controller.get_attached_parts())
        self.assertEqual([l.part for l in links], [part.object])

    def test_get_attached_parts_empty(self):
        links = list(self.controller.get_attached_parts())
        self.assertEqual(links, [])

    def test_revise2(self):
        part = self.get_part()
        self.controller.attach_to_part(part)
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
        self.assertFalse(f1.file.path == f2.file.path)
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

    def test_checkin_error_not_in_group(self):
        user = User(username="baduser")
        user.set_password("password")
        user.save()
        p = user.profile
        p.is_contributor = True
        p.save()
        controller = self.CONTROLLER(self.controller.object, user)
        models.PLMObjectUserLink.objects.create(user=user, role="owner",
                                         plmobject=controller.object)
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertRaises(exc.PermissionError, controller.checkin, d,
                          self.get_file())

    def test_checkin_error_not_contributor(self):
        user = User(username="baduser")
        user.set_password("password")
        user.save()
        user.groups.add(self.group)
        controller = self.CONTROLLER(self.controller.object, user)
        models.PLMObjectUserLink.objects.create(user=user, role="owner",
                                         plmobject=controller.object)
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertRaises(exc.PermissionError, controller.checkin, d,
                          self.get_file())


    def test_checkin_errors3(self):
        """ Tests that only the user who locked a file can check-in it."""
        user = User(username="baduser")
        user.set_password("password")
        user.save()
        user.groups.add(self.group)
        p = user.profile
        p.is_contributor = True
        p.save()
        models.DelegationLink.objects.create(delegator=self.user, delegatee=user,
                role=models.ROLE_OWNER)
        controller = self.CONTROLLER(self.controller.object, user)
        d = self.controller.add_file(self.get_file())
        self.controller.lock(d)
        self.assertRaises(exc.UnlockError, controller.checkin, d,
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

    def test_cancel(self):
        """
        Tests :meth:`.Document.cancel`.
        """
        self.assertFalse(self.controller.is_cancelled)
        part = self.get_part()
        self.controller.attach_to_part(part)
        self.assertEqual(1, self.controller.get_attached_parts().count())
        # cancels the object
        self.controller.cancel()
        self.check_cancelled_object(self.controller)
        # tests the links
        self.assertEqual(0, self.controller.get_attached_parts().count())

    def assertCancelError(self, ctrl):
        res = super(DocumentControllerTest, self).assertCancelError(ctrl)
        res = res or bool(ctrl.get_attached_parts())
        self.assertTrue(res)

    def test_cancel_has_part_related(self):
        """ Tests that a document linked to a part can *not* be cancelled. """
        part = self.get_part()
        self.controller.attach_to_part(part)
        self.assertEqual(1, self.controller.get_attached_parts().count())
        self.assertCancelError(self.controller)

    #clone test

    def assertClone(self, ctrl, data, parts):
        new_ctrl = super(DocumentControllerTest, self).assertClone(ctrl, data)

        import shutil
        for doc_file in ctrl.files.all():
            filename = doc_file.filename
            path = models.docfs.get_available_name(filename)
            shutil.copy(doc_file.file.path, models.docfs.path(path))
            new_doc = models.DocumentFile.objects.create(file=path,
                filename=filename, size=doc_file.size, document=new_ctrl.object)
            new_doc.thumbnail = doc_file.thumbnail
            if doc_file.thumbnail:
                ext = os.path.splitext(doc_file.thumbnail.path)[1]
                thumb = "%d%s" %(new_doc.id, ext)
                dirname = os.path.dirname(doc_file.thumbnail.path)
                thumb_path = os.path.join(dirname, thumb)
                shutil.copy(doc_file.thumbnail.path, thumb_path)
                new_doc.thumbnail = os.path.basename(thumb_path)
            new_doc.locked = False
            new_doc.locker = None
            new_doc.save()

        for part in parts:
            models.DocumentPartLink.objects.create(part=part,
                document=new_ctrl.object)

        # check that all files from the original are cloned
        same_qtity = len(ctrl.files.all()) == len(new_ctrl.files.all())
        files_cloned = True
        files_cloned = files_cloned and same_qtity
        for f in ctrl.files.all():
            new_f = models.DocumentFile.objects.filter(filename=f.filename,
                size=f.size, document = new_ctrl.object)[0]
            files_cloned = files_cloned and bool(new_f)
            files_cloned = files_cloned and new_f.locker == None and not new_f.locked
            files_cloned = files_cloned and new_f.file.read() == f.file.read()
            files_cloned = files_cloned and new_f.file.path != f.file.path
        self.assertTrue(files_cloned)

        # check that all attached parts are attached to the original document
        part_cloned = True
        for part in new_ctrl.get_suggested_parts():
            part_cloned = part_cloned and part in ctrl.get_suggested_parts()
        self.assertTrue(part_cloned)

    def test_clone_files(self):
        """
        Tests that a document with files can be cloned, and that
        all its files are cloned too.
        """
        ctrl = self.controller
        ctrl.add_file(self.get_file())
        self.assertEqual(len(ctrl.files.all()), 1)
        data = self.getDataCloning(ctrl)
        self.assertClone(ctrl, data, [])

    def test_clone_attached_parts(self):
        """
        Tests that a document attached to a part can be cloned.
        """
        ctrl = self.controller
        ctrl.attach_to_part(self.get_part())
        parts = ctrl.get_suggested_parts()
        self.assertEqual(len(parts),1)
        data = self.getDataCloning(ctrl)
        self.assertClone(ctrl, data, parts)
