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



_to_underscore = partial(re.compile(r"\s+").sub, "_")

class CSVImportError(StandardError):

    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        details = self.errors.as_text()
        return "CSVImportError:\n\t" + details 

class Preview(object):

    def __init__(self, csv_file, encoding, known_headers):
        reader = UnicodeReader(csv_file, encoding=encoding)
        self.headers = reader.next()
        self.guessed_headers = self.guess_headers(self.headers,
                known_headers)
        self.rows = tuple(islice(reader, 2))

    def guess_headers(self, csv_headers, known_headers):
        headers = []
        for header in csv_headers:
            h = _to_underscore(header.lower())
            if h in known_headers:
                headers.append(h)
            else:
                headers.append(None)
        return headers

class CSVImporter(object):
    HEADERS_SET = set().union(*(cls.get_creation_fields()
            for cls in models.get_all_plmobjects().itervalues()))
    HEADERS_SET.add(None)
    HEADERS = sorted(HEADERS_SET)

    REQUIRED_FIELDS = ("type", "reference", "revision", "name", "group", "lifecycle")
    
    @classmethod
    def MISSING_HEADERS_MSG(cls):
        fields = ", ".join(cls.REQUIRED_FIELDS)
        return "Missing headers: %s are required." % fields

    def __init__(self, csv_file, user, encoding="utf-8"):
        self.csv_file = csv_file
        self.user = user
        self.encoding = encoding

    def get_preview(self):
        self.csv_file.seek(0)
        return Preview(self.csv_file, self.encoding, self.HEADERS_SET)

    @transaction.commit_on_success
    def import_csv(self, headers):
        self.csv_file.seek(0)
        reader = UnicodeReader(self.csv_file, encoding=self.encoding)
        self.headers_dict = dict((h, i) for i, h in enumerate(headers))
        # checks that required columns are presents
        for field in self.REQUIRED_FIELDS:
            if field not in self.headers_dict:
                raise CSVImportError({1: self.MISSING_HEADERS_MSG()})
        # read the header
        reader.next()
        self.errors = defaultdict(ErrorList)
        self.objects = []
        # parse each row
        for line, row in enumerate(reader):
            try:
                self.parse_row(line, row)
            except Exception, e:
                self.errors[line + 2].append(unicode(e))
        if self.errors:
            raise CSVImportError(self.errors)
        for obj in self.objects:
            obj.unblock_mails()
        return self.objects

    def parse_row(self, line, row):
        from openPLM.plmapp.forms import get_creation_form
        type_ = row[self.headers_dict["type"]]
        reference = row[self.headers_dict["reference"]]
        revision = row[self.headers_dict["revision"]]
        cls = models.get_all_plmobjects()[type_]
        group = models.GroupInfo.objects.get(name=row[self.headers_dict["group"]])
        lifecycle = models.Lifecycle.objects.get(name=row[self.headers_dict["lifecycle"]])
        form = get_creation_form(self.user, cls)
        data = {
                "type" :type_,
                "group" : str(group.id),
                "reference" : reference,
                "revision" : revision,
                }
        for field in form.fields:
            if field not in data and field in self.headers_dict:
                data[field] = row[self.headers_dict[field]]
        form = get_creation_form(self.user, cls, data)
        if not form.is_valid():
            items = (mark_safe(u"%s: %s" % item) for item 
                    in form.errors.iteritems())
            self.errors[line + 2].extend(items)
        else:
            obj = PLMObjectController.create_from_form(form, self.user, True)
            self.objects.append(obj)


class BOMImporter(CSVImporter):
    
    REQUIRED_FIELDS = ("parent-type", "parent-reference", "parent-revision",
                       "child-type", "child-reference", "child-revision",
                       "quantity", "order") 

    HEADERS_SET = set(REQUIRED_FIELDS) 
    HEADERS_SET.add(None)
    HEADERS = sorted(HEADERS_SET)
    
    def parse_row(self, line, row): 
        from openPLM.plmapp.base_views import get_obj
        ptype = row[self.headers_dict["parent-type"]]
        preference = row[self.headers_dict["parent-reference"]]
        prevision = row[self.headers_dict["parent-revision"]]
        parent = get_obj(ptype, preference, prevision, self.user)

        ctype = row[self.headers_dict["child-type"]]
        creference = row[self.headers_dict["child-reference"]]
        crevision = row[self.headers_dict["child-revision"]]
        child = get_obj(ctype, creference, crevision, self.user)

        parent.block_mails()
        child.block_mails()
        self.objects.append(parent)
        self.objects.append(child)

        quantity = float(row[self.headers_dict["quantity"]])
        order = float(row[self.headers_dict["order"]])

        parent.add_child(child, quantity, order)
   

IMPORTERS = {"csv" : CSVImporter, "bom" : BOMImporter }

