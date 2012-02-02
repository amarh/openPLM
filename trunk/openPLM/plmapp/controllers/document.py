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
"""

import os
import re
import shutil

import Image
from django.conf import settings

import openPLM.plmapp.models as models
from openPLM.plmapp.exceptions import LockError, UnlockError, DeleteFileError
from openPLM.plmapp.controllers.plmobject import PLMObjectController
from openPLM.plmapp.controllers.base import get_controller
from openPLM.plmapp.thumbnailers import generate_thumbnail

class DocumentController(PLMObjectController):
    """
    A :class:`PLMObjectController` which manages 
    :class:`.Document`
    
    It provides methods to add or delete files, (un)lock them and attach a
    :class:`.Document` to a :class:`.Part`.
    """

    def lock(self, doc_file):
        """
        Lock *doc_file* so that it can not be modified or deleted
        
        :exceptions raised:
            * :exc:`ValueError` if *doc_file*.document is not self.object
            * :exc:`.PermissionError` if :attr:`_user` is not the owner of
              :attr:`object`
            * :exc:`.PermissionError` if :attr:`object` is not editable.

        :param doc_file:
        :type doc_file: :class:`.DocumentFile`
        """
        self.check_permission("owner")
        self.check_editable()
        if doc_file.document.pk != self.object.pk:
            raise ValueError("Bad file's document")
        if not doc_file.locked:
            doc_file.locked = True
            doc_file.locker = self._user
            doc_file.save()
            self._save_histo("Locked",
                             "%s locked by %s" % (doc_file.filename, self._user))
        else:
            raise LockError("File already locked")

    def unlock(self, doc_file):
        """
        Unlock *doc_file* so that it can be modified or deleted
        
        :exceptions raised:
            * :exc:`ValueError` if *doc_file*.document is not self.object
            * :exc:`plmapp.exceptions.UnlockError` if *doc_file* is already
              unlocked or *doc_file.locker* is not the current user

        :param doc_file:
        :type doc_file: :class:`.DocumentFile`
        """

        if doc_file.document.pk != self.object.pk:
            raise ValueError("Bad file's document")
        if not doc_file.locked:
            raise UnlockError("File already unlocked")
        if doc_file.locker != self._user:
            raise UnlockError("Bad user")
        doc_file.locked = False
        doc_file.locker = None
        doc_file.save()
        self._save_histo("Locked",
                         "%s unlocked by %s" % (doc_file.filename, self._user))

    def add_file(self, f, update_attributes=True, thumbnail=True):
        """
        Adds file *f* to the document. *f* should be a :class:`~django.core.files.File`
        with an attribute *name* (like an :class:`UploadedFile`).

        If *update_attributes* is True (the default), :meth:`handle_added_file`
        will be called with *f* as parameter.

        :return: the :class:`.DocumentFile` created.
        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
              :attr:`object`
        :raises: :exc:`.PermissionError` if :attr:`object` is not editable.
        :raises: :exc:`ValueError` if the file size is superior to
                 :attr:`settings.MAX_FILE_SIZE`
        """
        self.check_permission("owner")
        self.check_editable()
        if settings.MAX_FILE_SIZE != -1 and f.size > settings.MAX_FILE_SIZE:
            raise ValueError("File too big, max size : %d bytes" % settings.MAX_FILE_SIZE)
        f.name = f.name.encode("utf-8")
        doc_file = models.DocumentFile.objects.create(filename=f.name, size=f.size,
                        file=models.docfs.save(f.name, f), document=self.object)
        self.save(False)
        # set read only file
        os.chmod(doc_file.file.path, 0400)
        self._save_histo("File added", "file : %s" % f.name)
        if update_attributes:
            self.handle_added_file(doc_file)
        if thumbnail:
           generate_thumbnail.delay(doc_file.id) 
        return doc_file

    def add_thumbnail(self, doc_file, thumbnail_file):
        """
        Sets *thumnail_file* as the thumbnail of *doc_file*. *thumbnail_file*
        should be a :class:`~django.core.files.File` with an attribute *name*
        (like an :class:`UploadedFile`).
        
        :exceptions raised:
            * :exc:`ValueError` if *doc_file*.document is not self.objec
            * :exc:`ValueError` if the file size is superior to
              :attr:`settings.MAX_FILE_SIZE`
            * :exc:`.PermissionError` if :attr:`_user` is not the owner of
              :attr:`object`
            * :exc:`.PermissionError` if :attr:`object` is not editable.
        """
        self.check_permission("owner")
        self.check_editable()
        if doc_file.document.pk != self.object.pk:
            raise ValueError("Bad file's document")
        if settings.MAX_FILE_SIZE != -1 and thumbnail_file.size > settings.MAX_FILE_SIZE:
            raise ValueError("File too big, max size : %d bytes" % settings.MAX_FILE_SIZE)
        basename = os.path.basename(thumbnail_file.name)
        name = "%d%s" % (doc_file.id, os.path.splitext(basename)[1])
        if doc_file.thumbnail:
            doc_file.thumbnail.delete(save=False)
        doc_file.thumbnail = models.thumbnailfs.save(name, thumbnail_file)
        doc_file.save()
        image = Image.open(doc_file.thumbnail.path)
        image.thumbnail((150, 150), Image.ANTIALIAS)
        image.save(doc_file.thumbnail.path)

    def delete_file(self, doc_file):
        """
        Deletes *doc_file*, the file attached to *doc_file* is physically
        removed.

        :exceptions raised:
            * :exc:`ValueError` if *doc_file*.document is not self.object
            * :exc:`plmapp.exceptions.DeleteFileError` if *doc_file* is
              locked
            * :exc:`.PermissionError` if :attr:`_user` is not the owner of
              :attr:`object`
            * :exc:`.PermissionError` if :attr:`object` is not editable.

        :param doc_file: the file to be deleted
        :type doc_file: :class:`.DocumentFile`
        """

        self.check_permission("owner")
        self.check_editable()
        if doc_file.document.pk != self.object.pk:
            raise ValueError("Bad file's document")
        if doc_file.locked:
            raise DeleteFileError("File is locked")
        path = os.path.realpath(doc_file.file.path)
        if not path.startswith(settings.DOCUMENTS_DIR):
            raise DeleteFileError("Bad path : %s" % path)
        os.chmod(path, 0700)
        os.remove(path)
        if doc_file.thumbnail:
            doc_file.thumbnail.delete(save=False)
        self._save_histo("File deleted", "file : %s" % doc_file.filename)
        doc_file.delete()

    def handle_added_file(self, doc_file):
        """
        Method called when adding a file (method :meth:`add_file`) with
        *updates_attributes* true.

        This method may be overridden to updates attributes with data from
        *doc_file*. The default implementation does nothing.
        
        :param doc_file:
        :type doc_file: :class:`.DocumentFile`
        """
        pass

    def attach_to_part(self, part):
        """
        Links *part* (a :class:`.Part`) with
        :attr:`~PLMObjectController.object`.
        """

        self.check_attach_part(part)        
        if isinstance(part, PLMObjectController):
            part = part.object
        self.documentpartlink_document.create(part=part)
        self._save_histo(models.DocumentPartLink.ACTION_NAME,
                         "Part : %s - Document : %s" % (part, self.object))

    def detach_part(self, part):
        """
        Delete link between *part* (a :class:`.Part`) and
        :attr:`~PLMObjectController.object`.
        """

        if isinstance(part, PLMObjectController):
            part = part.object
        link = self.documentpartlink_document.get(part=part)
        link.delete()
        self._save_histo(models.DocumentPartLink.ACTION_NAME + " - delete",
                         "Part : %s - Document : %s" % (part, self.object))

    def get_attached_parts(self):
        """
        Returns all :class:`.Part` attached to
        :attr:`~PLMObjectController.object`.
        """
        return self.object.documentpartlink_document.all()

    def is_part_attached(self, part):
        """
        Returns True if *part* is attached to the current document.
        """

        if isinstance(part, PLMObjectController):
            part = part.object
        return bool(self.documentpartlink_document.filter(part=part))

    def check_attach_part(self, part):
        self.check_permission("owner")
        if not (hasattr(part, "is_part") and part.is_part):
            raise TypeError("%s is not a part" % part)

        if isinstance(part, PLMObjectController):
            part.check_readable()
            part = part.object
        else:
            get_controller(part.type)(part, self._user).check_readable()
        if self.is_part_attached(part):
            raise ValueError("part is already attached.")
    
    def can_attach_part(self, part):
        """
        Returns True if *part* can be attached to the current document.
        """
        can_attach = False
        try:
            self.check_attach_part(part)
            can_attach = True
        except StandardError:
            pass
        return can_attach

    def revise(self, new_revision):
        # same as PLMObjectController + duplicate files (and their thumbnails)
        rev = super(DocumentController, self).revise(new_revision)
        for doc_file in self.object.files.all():
            filename = doc_file.filename
            path = models.docfs.get_available_name(filename)
            shutil.copy(doc_file.file.path, models.docfs.path(path))
            new_doc = models.DocumentFile.objects.create(file=path,
                filename=filename, size=doc_file.size, document=rev.object)
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
        return rev

    def checkin(self, doc_file, new_file, update_attributes=True,
            thumbnail=True):
        """
        Updates *doc_file* with data from *new_file*. *doc_file*.thumbnail
        is deleted if it is present.
        
        :exceptions raised:
            * :exc:`ValueError` if *doc_file*.document is not self.object
            * :exc:`ValueError` if the file size is superior to
              :attr:`settings.MAX_FILE_SIZE`
            * :exc:`plmapp.exceptions.UnlockError` if *doc_file* is locked
              but *doc_file.locker* is not the current user
            * :exc:`.PermissionError` if :attr:`_user` is not the owner of
              :attr:`object`
            * :exc:`.PermissionError` if :attr:`object` is not editable.

        :param doc_file:
        :type doc_file: :class:`.DocumentFile`
        :param new_file: file with new data, same parameter as *f*
                         in :meth:`add_file`
        :param update_attributes: True if :meth:`handle_added_file` should be
                                  called
        """
        self.check_permission("owner")
        self.check_editable()
        if doc_file.document.pk != self.object.pk:
            raise ValueError("Bad file's document")
        if doc_file.filename != new_file.name:
            raise ValueError("Checkin document and document already in plm have different names")
        if settings.MAX_FILE_SIZE != -1 and new_file.size > settings.MAX_FILE_SIZE:
            raise ValueError("File too big, max size : %d bytes" % settings.MAX_FILE_SIZE)
        if doc_file.locked:
            self.unlock(doc_file)   
        os.chmod(doc_file.file.path, 0700)
        os.remove(doc_file.file.path)
        doc_file.filename = new_file.name
        doc_file.size = new_file.size
        doc_file.file = models.docfs.save(new_file.name, new_file)
        os.chmod(doc_file.file.path, 0400)
        if doc_file.thumbnail:
            doc_file.thumbnail.delete(save=False)
        doc_file.save()
        self._save_histo("Check-in", doc_file.filename)
        if update_attributes:
            self.handle_added_file(doc_file)
        if thumbnail:
            generate_thumbnail.delay(doc_file.id)
            
    def update_rel_part(self, formset):
        u"""
        Updates related part informations with data from *formset*
        
        :param formset:
        :type formset: a modelfactory_formset of 
                        :class:`~plmapp.forms.ModifyRelPartForm`
        """
        if formset.is_valid():
            for form in formset.forms:
                document = form.cleaned_data["document"]
                if document.pk != self.document.pk:
                    raise ValueError("Bad document %s (%s expected)" % (document, self.object))
                delete = form.cleaned_data["delete"]
                part = form.cleaned_data["part"]
                if delete:
                    self.detach_part(part)

    def update_file(self, formset):
        u"""
        Updates uploaded file informations with data from *formset*
        
        :param formset:
        :type formset: a modelfactory_formset of 
                        :class:`~plmapp.forms.ModifyFileForm`
        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
              :attr:`object`
        :raises: :exc:`.PermissionError` if :attr:`object` is not editable.
        """
        
        self.check_permission("owner")
        self.check_editable()
        if formset.is_valid():
            for form in formset.forms:
                document = form.cleaned_data["document"]
                if document.pk != self.document.pk:
                    raise ValueError("Bad document %s (%s expected)" % (document, self.object))
                delete = form.cleaned_data["delete"]
                filename = form.cleaned_data["id"]
                if delete:
                    self.delete_file(filename)

