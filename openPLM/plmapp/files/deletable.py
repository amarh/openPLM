import fnmatch
import datetime

from django.conf import settings
from django.db.models import Q, Sum

class Selector(object):

    def get_deletable_files(self, doc_file):
        return []

class KeepLastNFiles(Selector):

    def __init__(self, count):
        self.count = count

    def get_deletable_files(self, doc_file):
        rev = doc_file.revision - self.count
        return doc_file.older_files.filter(deleted=False, revision__lte=rev)

class KeepAllFiles(Selector):

    def get_deletable_files(self, doc_file):
        return []

class DeleteAllFiles(Selector):

    def __init__(self, include_last_revision=False):
        self.include_last_revision = include_last_revision

    def get_deletable_files(self, doc_file):
        if self.include_last_revision:
            files = [doc_file]
        else:
            files = []
        return files + list(doc_file.older_files.filter(deleted=False))

class MaximumTotalSize(Selector):

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

    def __init__(self, number, modulo=1):
        self._extra = ["revision %% %d != %d" % (number, modulo)]

    def get_deletable_files(self, doc_file):
        return doc_file.older_files.filter(deleted=False).extra(where=self._extra)

class YoungerThan(Selector):

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
    return lambda df: any(fnmatch.fnmatch(df.filename.lower(), pat) for pat in patterns)

def yes(x):
    return True

def get_deletable_files(doc_file, selectors):
    if getattr(settings, "KEEP_ALL_FILES", False):
        return []
    for test, selector in selectors:
        if test(doc_file):
            return selector.get_deletable_files(doc_file)
    return []

ON_CHECKIN_SELECTORS = [
    #(pattern("*.txt"), KeepAllFiles()),
    (yes, KeepLastNFiles(10)),
]

ON_DELETE_SELECTORS = [
    (yes, DeleteAllFiles(True)),
]

ON_DEPRECATE_SELECTORS = [
    (yes, DeleteAllFiles(False)),
]

ON_CANCEL_SELECTORS = [
    (yes, DeleteAllFiles(False)),
]

