
import os
import string
import random
import hashlib
from django.utils import timezone

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.utils.functional import memoize

from openPLM.plmapp.files.formats import native_to_standards
from openPLM.plmapp.utils import memoize_noarg


from .plmobject import (PLMObject, get_all_subclasses,
        get_all_subclasses_with_level)

# document stuff
class DocumentStorage(FileSystemStorage):
    """
    File system storage which stores files with a specific name
    """
    def get_available_name(self, name):
        """
        Returns a path for a file *name*, the path always refers to a file
        which does not already exist.

        The path is computed as follow:
            #. a directory which name is the last extension of *name*.
               For example, it is :file:`.gz` if *name* is :file:`.a.tar.gz`.
               If *name* does not have an extension, the directory is
               :file:`.no_ext/`.
            #. a file name with 4 parts:
                #. the md5 sum of *name*
                #. a dash separator: ``-``
                #. a random part with 7 characters in ``[a-z0-9]``
                #. the extension, like :file:`.gz`

            For example, if *name* is :file:`.my_file.tar.gz`,
            a possible output is:

                :file:`.gz/c7bfe8d00ea6e7138215ebfafff187af-jj6789g.gz`

            If *name* is :file:`.my_file`, a possible output is:

                :file:`.no_ext/59c211e8fc0f14b21c78c87eafe1ab72-dhh5555`
        """

        def rand():
            r = ""
            for i in xrange(7):
                r += random.choice(string.ascii_lowercase + string.digits)
            return r
        basename = os.path.basename(name)
        base, ext = os.path.splitext(basename)
        ext2 = ext.lstrip(".").lower() or "no_ext"
        md5 = hashlib.md5()
        md5.update(basename)
        md5_value = md5.hexdigest() + "-%s" + ext
        path = os.path.join(ext2, md5_value % rand())
        while os.path.exists(os.path.join(self.location, path)):
            path = os.path.join(ext2, md5_value % rand())
        return path


#: :class:`.DocumentStorage` instance which stores files in :const:`.settings.DOCUMENTS_DIR`
docfs = DocumentStorage(location=settings.DOCUMENTS_DIR)
#: :class:`.FileSystemStorage` instance which stores thumbnails in :const:`.settings.THUMBNAILS_DIR`
thumbnailfs = FileSystemStorage(location=settings.THUMBNAILS_DIR,
        base_url=settings.THUMBNAILS_URL)

class DocumentFile(models.Model):
    """
    .. versionchanged:: 1.2
        New attributes: :attr:`.ctime`, :attr:`.end_time`, :attr:`.deleted`,
        :attr:`.revision`, :attr:`.previous_revision`, :attr:`.last_revision`

    Model which stores informations of a file bounded to a :class:`.Document`

    :model attributes:
        .. attribute:: filename

            original filename
        .. attribute:: file

            file stored in :obj:`.docfs`
        .. attribute:: size

            size of the file in Byte
        .. attribute:: locked

            True if the file is locked
        .. attribute:: locker

            :class:`~django.contrib.auth.models.User` who locked the file,
            None, if the file is not locked
        .. attribute:: document

            :class:`.Document` bounded to the file (required)
        .. attribute:: ctime

            date of creation of the document file
        .. attribute:: end_time

            date of creation of the next revision or None if it is
            the last revision
        .. attribute:: revision

            revision number (starts at 1)
        .. attribute:: previous_revision

            :class:`.DocumentFile` or None if it's the first revision
        .. attribute:: last_revision

            foreign key to the last revision (:class:`.DocumentFile`)
            or None it it'is the last_revision
        .. attribute:: deleted

            True if the file has been physically removed

    """

    class Meta:
        app_label = "plmapp"

    filename = models.CharField(max_length=200)
    file = models.FileField(upload_to=".", storage=docfs)
    size = models.PositiveIntegerField()
    thumbnail = models.ImageField(upload_to=".", storage=thumbnailfs,
                                 blank=True, null=True)
    locked = models.BooleanField(default=lambda: False)
    locker = models.ForeignKey(User, null=True, blank=True,
                               default=lambda: None)
    document = models.ForeignKey('Document')
    deprecated = models.BooleanField(default=lambda: False)

    ctime = models.DateTimeField(auto_now_add=False, default=timezone.now)
    end_time = models.DateTimeField(blank=True, null=True, default=lambda: None)
    deleted = models.BooleanField(default=False)
    revision = models.IntegerField(default=1)
    previous_revision = models.OneToOneField('self',
            related_name="next_revision", default=None, null=True)
    last_revision = models.ForeignKey('self',
            related_name="older_files", default=None, null=True)

    @property
    def native_related(self):
        """
        Returns the native DocumentFile related to this DocumentFile
        if :const:`.settings.ENABLE_NATIVE_FILE_MANAGEMENT` is True.

        Returns False if there are no native DocumentFile related.
        """

        if getattr(settings, 'ENABLE_NATIVE_FILE_MANAGEMENT', False):
            name, ext = os.path.splitext(self.filename)
            ext = ext.lower()
            doc_files = DocumentFile.objects.filter(document__id=self.document_id)\
                    .exclude(deprecated=True, id=self.id)
            for doc in doc_files:
                native, native_ext = os.path.splitext(doc.filename)
                if native == name and ext in native_to_standards[native_ext.lower()]:
                    return doc
        return None

    @property
    def checkout_valid(self):
        """
        Returns False if DocumentFile has a native related *locked* file
        and :const:`.settings.ENABLE_NATIVE_FILE_MANAGEMENT` is True.
        """
        if getattr(settings, 'ENABLE_NATIVE_FILE_MANAGEMENT', False):
            name, ext = os.path.splitext(self.filename)
            ext = ext.lower()
            doc_files = DocumentFile.objects.filter(document__id=self.document_id, locked=True)\
                    .exclude(deprecated=True, id=self.id).values_list("filename", flat=True)
            for filename in doc_files:
                native, native_ext = os.path.splitext(filename)
                if native == name and ext in native_to_standards[native_ext.lower()]:
                    return False

        return True

    def __unicode__(self):
        return u"DocumentFile<%s, %s>" % (self.filename, self.document)


class PrivateFile(models.Model):
    """
    .. versionadded:: 1.2

    Model which stores informations of a private file only readable by its
    creator.

    There are no revision, locker, deleted or similar attributes.
    A private file is not shared, and it is temporary. It is created to
    store a file before a document creation.

    Private files are created when a user uploads files and *then* creates
    a document containing these files.

    :model attributes:
        .. attribute:: filename

            original filename
        .. attribute:: file

            file stored in :obj:`.docfs`
        .. attribute:: size

            size of the file in Byte
        .. attribute:: creator

            :class:`~django.contrib.auth.models.User` who created the file,
        .. attribute:: ctime
            date of creation of the file
    """

    class Meta:
        app_label = "plmapp"

    filename = models.CharField(max_length=200)
    file = models.FileField(upload_to=".", storage=docfs)
    size = models.PositiveIntegerField()
    creator = models.ForeignKey(User, related_name="files")
    ctime = models.DateTimeField(auto_now_add=False, default=timezone.now)

    def __unicode__(self):
        return u"PrivateFile<%s, %s>" % (self.filename, self.creator)


class Document(PLMObject):
    """
    Model for documents
    """

    class Meta:
        app_label = "plmapp"

    ACCEPT_FILES = True

    @property
    def files(self):
        "Queryset of all non deprecated :class:`.DocumentFile` linked to self"
        return self.documentfile_set.exclude(deprecated=True)

    @property
    def deprecated_files(self):
        "Queryset of all deprecated :class:`.DocumentFile` linked to self"
        return self.documentfile_set.filter(deprecated=True)

    def get_content_and_size(self, doc_file):
        return open(doc_file.file.path, "rb"), doc_file.file.size

    def is_promotable(self):
        """
        Returns True if the object is promotable. A document is promotable
        if there is a next state in its lifecycle and if it has at least
        one file and if none of its files are locked.
        """
        if not self._is_promotable():
            return False
        if not self.files.exists():
            self._promotion_errors.append(_("This document has no files."))
            return False
        if self.files.filter(locked=True).exists():
            self._promotion_errors.append(_("Some files are locked."))
            return False
        return True

    @property
    def menu_items(self):
        items = list(super(Document, self).menu_items)
        items.insert(0, ugettext_noop("files"))
        items.append(ugettext_noop("parts"))
        return items

    @property
    def is_part(self):
        return False

    @property
    def is_document(self):
        return True

    @classmethod
    def get_creation_score(cls, files):
        """
        .. versionadded:: 2.0

        Returns a score (an integer) computed from *files*.
        *files* is a list of :class:`PrivateFile` uploaded by a user
        who wants to create a document with all files.

        The class which returns the highest score is chosen has the
        default type after an upload.

        The default implementation returns 10 if the current class is *Document*
        and 0 otherwise.

        For example, :class:`~Document3D` returns 50 if a CAD file has been
        uploaded. Document3D is so preferred when a STEP file is uploaded.

        .. seealso::
            :func:`get_best_document_type`
        """
        if cls == Document:
            return 10
        return 0


@memoize_noarg
def get_all_documents():
    u"""
    Returns a dict<doc_name, doc_class> of all available :class:`.Document` classes
    """
    res = {}
    get_all_subclasses(Document, res)
    return res


def get_all_subtype_documents(subtype):
    u"""
    Returns a dict<doc_name, doc_class> of all available **subtype** classes
    """
    res = {}
    get_all_subclasses(subtype, res)
    return res


def get_all_documents_with_level(only_accept_files=False):
    lst = []
    level="=>"
    get_all_subclasses_with_level(Document, lst, level)
    classes = get_all_documents()
    if only_accept_files:
        return [(n, l) for n, l in lst if classes[n].ACCEPT_FILES]
    return lst

get_all_documents_with_level = memoize(get_all_documents_with_level, {}, 1)


def get_best_document_type(files):
    """
    .. versionadded:: 2.0

    Returns the document type (str) which returns the highest
    creation score for the uploaded files (list of :class:`PrivateFile`).

    .. seealso::
        :meth:`Document.get_creation_score`
    """
    dtype = "Document"
    max_score = 0
    for name, cls in get_all_documents().iteritems():
        score = cls.get_creation_score(files)
        if score > max_score:
            max_score = score
            dtype = name
    return dtype
