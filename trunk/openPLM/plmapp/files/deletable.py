"""
.. versionadded:: 1.2

Module to select which files should be deleted (physically removed) after:

    * a checkin of a :class:`.DocumentFile`
    * a deletion of a :class:`.DocumentFile`
    * a cancellation of a :class:`.Document`
    * a deprecation of a :class:`.Document`

Each case can have a different behaviour specified by:

    * :const:`ON_CHECKIN_SELECTORS`
    * :const:`ON_DELETE_SELECTORS`
    * :const:`ON_CANCEL_SELECTORS`
    * :const:`ON_DEPRECATE_SELECTORS`

These constants are lists of tuples (*test*, *selector*) where:

    * *test* is a function that takes a :class:`.DocumentFile` and
      returns True if *selector* applies to the given file
    * *selector* is an instance of :class:`Selector` which returns
      a list of :class:`.DocumentFile` to be deleted.

They can be given to :func:`get_deletable_files` to retrieve the list of
:class:`.DocumentFile` to delete.
"""

import fnmatch

from django.conf import settings
from django.db.models import Q, Sum

class Selector(object):

    def get_deletable_files(self, doc_file):
        """
        Returns the list of :class:`.DocumentFile` to delete.

        :param doc_file: the last revision of the file
        """
        return []

class KeepLastNFiles(Selector):
    """
    A selector which keeps only the last *count* revisions
    (last one include).
    """

    def __init__(self, count):
        self.count = count

    def get_deletable_files(self, doc_file):
        rev = doc_file.revision - self.count
        return doc_file.older_files.filter(deleted=False, revision__lte=rev)

class KeepAllFiles(Selector):
    """
    A selector which keeps all files: :meth:`~KeepAllFiles.get_deletable_files`
    always returns an empty list.
    """

    def get_deletable_files(self, doc_file):
        return []

class DeleteAllFiles(Selector):
    """
    A selector which returns all undeleted files.
    
    If *include_last_revision* is True, the given document file is also
    included in the returned list.
    """

    def __init__(self, include_last_revision=False):
        self.include_last_revision = include_last_revision

    def get_deletable_files(self, doc_file):
        if self.include_last_revision:
            files = [doc_file]
        else:
            files = []
        return files + list(doc_file.older_files.filter(deleted=False))

class MaximumTotalSize(Selector):
    """
    A selector which ensures that the size of files related to a revision 
    does not exceed *max_size*.

    :param max_size: maximum size in bytes
    :param order: ordering field used to select which files must be deleted
                  if the total size exceeds *max_size*

    Possible values for *order* are:

        ``revision``
            first deletes the most recent revisions
        ``-revision``
            first deletes the oldest revisions
        ``size``
            first deletes the biggest files
        ``-size``
            first deletes the smallest files
    """

    def __init__(self, max_size, order="revision"):
        self.max_size = max_size
        self.order = order

    def get_deletable_files(self, doc_file):
        available_size = self.max_size - doc_file.size
        older_files = doc_file.older_files.filter(deleted=False).order_by(self.order)
        if available_size <= 0:
            return older_files
        total = older_files.aggregate(Sum("size"))["size__sum"]
        if total and total > available_size:
            for i, df in enumerate(older_files):
                total -= df.size
                if total <= available_size:
                    return older_files[:i+1]
        return []

class MaxPerDate(Selector):
    """
    A selector which keeps at most *maximum* per *frequency*
    (``day``, ``month``, ``year``).

    If the number of revisions exceeds *maximum*, most recent revisions
    are first deleted.
    """

    def __init__(self, frequency, maximum):
        self.frequency = frequency
        self.maximum = maximum

    def get_deletable_files(self, doc_file):
        query = Q(ctime__year=doc_file.ctime.year, deleted=False)
        if self.frequency in ("day", "month"):
            query &= Q(ctime__month=doc_file.ctime.month)
        if self.frequency == "day":
            query &= Q(ctime__day=doc_file.ctime.day)
        # delete most recent files
        return doc_file.older_files.filter(query).order_by("revision")[self.maximum-1:]

class Modulo(Selector):
    """
    A selector which only keeps revisions if the revision modulo *number* equals to
    *modulo*.

    For example, ``Modulo(4, 1)`` keeps a revision of four, and the intial revision is
    kept.
    """

    def __init__(self, number, modulo=1):
        self._extra = ["revision %% %d != %d" % (number, modulo)]

    def get_deletable_files(self, doc_file):
        return doc_file.older_files.filter(deleted=False).extra(where=self._extra)

class YoungerThan(Selector):
    """
    A selector which deletes too frequent updates.

    A revision is deleted if the difference between the date of creation of
    the last revision and its creation time is lesser than *timedelta*
    (a :class:`.datetime.timedelta` object).

    If *incremental* is True (the default), only the previous revision is tested.
    This behaviour should be used after a checkin.
    """

    def __init__(self, timedelta, incremental=True):
        self.timedelta = timedelta
        self.incremental = incremental

    def get_deletable_files(self, doc_file):
        time = doc_file.ctime - self.timedelta
        if self.incremental:
            if doc_file.previous_revision.ctime > time:
                return [doc_file.previous_revision]
            else:
                return []
        else:
            return doc_file.older_files.filter(ctime__gt=time)

def pattern(*patterns):
    """
    Returns a function which takes a :class:`.DocumentFile` and returns
    True if its filename matches one of the given patterns (like ``*.txt``).
    patterns are not case sensitive.
    """
    return lambda df: any(fnmatch.fnmatch(df.filename.lower(), pat) for pat in patterns)

def yes(x):
    "A simple function that always returns True"
    return True

def get_deletable_files(doc_file, selectors):
    """
    Returns the list of :class:`.DocumentFile` to delete.

    Returns an empty list if :const:`settings.KEEP_ALL_FILES` is True.
    
    :param doc_file: the last revision of the file
    :param selectors: list of tuples (*test*, *selector*) to determine which
        selectors should be called
    """
    if getattr(settings, "KEEP_ALL_FILES", False):
        return []
    for test, selector in selectors:
        if test(doc_file):
            return selector.get_deletable_files(doc_file)
    return []

#: default selectors called after a checkin
ON_CHECKIN_SELECTORS = [
    #(pattern("*.txt"), KeepAllFiles()),
    (yes, KeepLastNFiles(10)),
]

#: default selectors called after a deletion
ON_DELETE_SELECTORS = [
    (yes, DeleteAllFiles(True)),
]

#: default selectors called after a deprecation
ON_DEPRECATE_SELECTORS = [
    (yes, DeleteAllFiles(False)),
]

#: default selectors called after a cancellation
ON_CANCEL_SELECTORS = [
    (yes, DeleteAllFiles(False)),
]

