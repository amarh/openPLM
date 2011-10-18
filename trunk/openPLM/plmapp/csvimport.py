import re
from functools import partial
from itertools import islice
from collections import defaultdict

from django.db import transaction
from django.forms.util import ErrorList
from django.utils.safestring import mark_safe

from openPLM.plmapp import models
from openPLM.plmapp.unicodecsv import UnicodeReader
from openPLM.plmapp.controllers.plmobject import PLMObjectController

HEADERS_SET = set().union(*(cls.get_creation_fields()
        for cls in models.get_all_plmobjects().itervalues()))
HEADERS = sorted(HEADERS_SET)

_to_underscore = partial(re.compile(r"[\s-]+").sub, "_")

def guess_headers(csv_headers):
    headers = []
    for header in csv_headers:
        h = _to_underscore(header.lower())
        if h in HEADERS_SET:
            headers.append(h)
        else:
            headers.append(None)
    return headers

class CSVPreview(object):

    def __init__(self, csv_file, encoding="utf-8"):
        reader = UnicodeReader(csv_file, encoding=encoding)
        self.headers = reader.next()
        self.guessed_headers = guess_headers(self.headers)
        self.rows = tuple(islice(reader, 2))

class CSVImportError(StandardError):

    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        details = self.errors.as_text()
        return "CSVImportError:\n\t" + details 

REQUIRED_FIELDS = ("type", "reference", "revision", "name", "group", "lifecycle")
REQUIRED_FIELDS_STR = ", ".join(REQUIRED_FIELDS)
MISSING_HEARDERS_MSG = "Missing headers: %s are required." % REQUIRED_FIELDS_STR

@transaction.commit_on_success
def import_csv(csv_file, headers, user, encoding="utf-8"):
    from openPLM.plmapp.forms import get_creation_form
    reader = UnicodeReader(csv_file, encoding=encoding)
    headers_dict = dict((h, i) for i, h in enumerate(headers))
    # checks that required columns are presents
    for field in REQUIRED_FIELDS:
        if field not in headers_dict:
            raise CSVImportError({1: MISSING_HEARDERS_MSG})
    # read the header
    reader.next()
    errors = defaultdict(ErrorList)
    objects = []
    # parse each row
    for line, row in enumerate(reader):
        try:
            type_ = row[headers_dict["type"]]
            reference = row[headers_dict["reference"]]
            revision = row[headers_dict["revision"]]
            cls = models.get_all_plmobjects()[type_]
            group = models.GroupInfo.objects.get(name=row[headers_dict["group"]])
            lifecycle = models.Lifecycle.objects.get(name=row[headers_dict["lifecycle"]])
            form = get_creation_form(user, cls)
            data = {
                    "type" :type_,
                    "group" : str(group.id),
                    "reference" : reference,
                    "revision" : revision,
                    }
            for field in form.fields:
                if field not in data and field in headers_dict:
                    data[field] = row[headers_dict[field]]
            form = get_creation_form(user, cls, data)
            if not form.is_valid():
                items = (mark_safe(u"%s: %s" % item) for item 
                        in form.errors.iteritems())
                errors[line + 2].extend(items)
            else:
                obj = PLMObjectController.create_from_form(form, user, True)
                objects.append(obj)
        except Exception, e:
            errors[line + 2].append(unicode(e))
    if errors:
        raise CSVImportError(errors)
    for obj in objects:
        obj.unblock_mails()
    return objects

