u"""
Tools to import data from a CSV file.
"""

import re
from abc import ABCMeta, abstractmethod
from functools import partial
from itertools import islice
from collections import defaultdict

from django.db import transaction
from django.forms.util import ErrorList
from django.utils.safestring import mark_safe

from openPLM.plmapp import models
from openPLM.plmapp.utils.unicodecsv import UnicodeReader
from openPLM.plmapp.controllers import PLMObjectController, UserController
from openPLM.plmapp.tasks import update_indexes


# function that replace spaces by an underscore
_to_underscore = partial(re.compile(r"\s+").sub, "_")

class CSVImportError(StandardError):
    """
    Exception raised when an import of a CSV file fails.

    .. attribute: errors

        dictionary (line -> :class:`~django.forms.util.ErrorList`) of all
        detected errors.
    """

    def __init__(self, errors):
        self.errors = errors

    def __unicode__(self):
        details = self.errors.as_text()
        return u"CSVImportError:\n\t" + details

class Preview(object):
    u"""
    Preview of a CSV file.

    :param csv_file: the csv file being parsed
    :type csv_file: a file like object
    :param encoding: encoding of the file (`utf-8`, `ascii`, etc.)
    :param known_headers: collection of headers that may be valid

    .. attribute:: headers

        headers of the CSV file
    .. attribute:: guessed_headers

        headers translated according to *known_headers*, an header that can
        not be translated is replaced by `None`
    .. attribute:: rows

        first non-headers rows of the file (at most two rows)
    """

    def __init__(self, csv_file, encoding, known_headers):
        reader = UnicodeReader(csv_file, encoding=encoding)
        self.headers = reader.next()
        self.guessed_headers = self._guess_headers(known_headers)
        self.rows = tuple(islice(reader, 2))

    def _guess_headers(self, known_headers):
        headers = []
        for header in self.headers:
            h = _to_underscore(header.lower().strip())
            if h in known_headers:
                headers.append(h)
            else:
                headers.append(None)
        return headers

class CSVImporter(object):
    """
    Abstract class to import data from a CSV file.

    :param csv_file: file being imported
    :type csv_file: a file like object
    :param user: user who imports the file
    :type user: :class:`~django.contrib.auth.models.User`
    :param encoding: encoding of the file (`utf-8`, `ascii`, etc.)

    For "end users", this class has two useful methods:

        * :meth:`get_preview` to generate a :class:`Preview` of the file
        * :meth:`import_csv` to import the csv file

    An implementation must overwrite the methods :meth:`get_headers_set` and
    :meth:`parse_row` and redefine the attribute :attr:`REQUIRED_HEADERS`.
    """

    __metaclass__ = ABCMeta

    #: Headers that must be present in the csv file
    REQUIRED_HEADERS = ()

    def __init__(self, csv_file, user, encoding="utf-8"):
        self.csv_file = csv_file
        self.user = user
        self.encoding = encoding
        self.inbulk_cache = {}

    @classmethod
    @abstractmethod
    def get_headers_set(cls):
        """
        Returns a set of all possible headers.

        .. note::

            This method is abstract and must be implemented.
        """
        return set()

    @classmethod
    def get_headers(cls):
        """
        Returns a sorted list of all possible headers.
        """
        headers = [None]
        headers.extend(sorted(cls.get_headers_set()))
        return headers

    @classmethod
    def get_missing_headers_msg(cls):
        """
        Returns a message explaining which headers are required.
        """
        headers = ", ".join(cls.REQUIRED_HEADERS)
        return u"Missing headers: %s are required." % headers

    def get_preview(self):
        """
        Returns a :class:`Preview` of the csv file.
        """
        self.csv_file.seek(0)
        return Preview(self.csv_file, self.encoding, self.get_headers_set())

    @transaction.commit_on_success
    def __do_import_csv(self, headers):
        self.csv_file.seek(0)
        reader = UnicodeReader(self.csv_file, encoding=self.encoding)
        self.headers_dict = dict((h, i) for i, h in enumerate(headers))
        # checks that required columns are presents
        for field in self.REQUIRED_HEADERS:
            if field not in self.headers_dict:
                raise CSVImportError({1: self.get_missing_headers_msg()})
        # read the header
        reader.next()
        self._errors = defaultdict(ErrorList)
        self.objects = []
        # parse each row
        for line, row in enumerate(reader):
            try:
                self.parse_row(line + 2, row)
            except Exception, e:
                self.store_errors(line + 2, e)
        if self._errors:
            raise CSVImportError(self._errors)

    def import_csv(self, headers):
        """
        Imports the csv file. *headers* is the list of headers as given by the
        user. Columns whose header is `None` are ignored.
        *headers* must contains all values of :attr:`REQUIRED_HEADERS`.

        If one or several errors occur (missing headers, row which can not be
        parsed), a :exc:`CSVImportError` is raised with all detected errors.

        :return: A list of :class:`.PLMObjectController` of all created objects.
        """
        # puts all stuff in a private method so we call tear_down only after
        # after a database commit
        self.__do_import_csv(headers)
        self.tear_down()
        return self.objects

    def tear_down(self):
        """
        Method called once *all* rows have been successfully parsed.

        By default, this method sends all blocked mails.
        """
        for obj in self.objects:
            obj.unblock_mails()

    def store_errors(self, line, *errors):
        """
        Appends *errors* to the list of errors which occured at the line *line*.
        """
        for e in errors:
            if isinstance(e, Exception):
                e = unicode(e)
            self._errors[line].append(e)

    def get_value(self, row, header):
        return row[self.headers_dict[header]].strip()

    def get_values(self, row, *headers):
        return [self.get_value(row, h) for h in headers]

    @abstractmethod
    def parse_row(self, line, row):
        """
        Method called by :meth:`import_csv` for each row.

        :param line: line number of current row, useful to store a list of
                     errors
        :type line: int
        :param row: row being parsed.
        :type row: list of unicode strings.

        This method must be overwritten. Implementation can use the methods
        :meth:`get_value`, :meth:`get_values`, and :meth:`store_errors` to
        retrieve values and store detected errors.

        .. warning::

            All :class:`.Controller` created should not send emails since an
            error may occur and thus, all modifications would be cancelled.
            To block mails, call :meth:`.Controller.block_mails`. You can
            released all blocked mails by appending the controller to
            :attr:`objects`. :meth:`import_csv` will send mails if no errors
            occurred.

            Example::

                ctrl = get_obj(type, reference, revision, user)
                ctrl.block_mails()
                ...
                if ok:
                    self.objects.append(ctrl)
        """
        pass

class PLMObjectsImporter(CSVImporter):
    """
    An :class:`CSVImporter` that creates :class:`PLMObject` from
    a csv file.

    The CSV must contain the following columns:

        * type
        * reference
        * revision
        * name
        * group (name of the group, not its id)
        * lifecycle (name of the lifecycle, not its id)

    Moreover, it must have a column for each required field of defined types.
    """

    #: Headers that must be present in the csv file
    REQUIRED_HEADERS = ("type", "reference", "revision", "name", "group", "lifecycle")

    @classmethod
    def get_headers_set(cls):
        """
        Returns a set of all possible headers.
        """
        return set().union(*(cls.get_creation_fields()
            for cls in models.get_all_plmobjects().itervalues()))

    def tear_down(self):
        super(PLMObjectsImporter, self).tear_down()
        instances = []
        for obj in self.objects:
            instance = obj.object
            instances.append((instance._meta.app_label,
                    instance._meta.module_name, instance._get_pk_val()))
        update_indexes.delay(instances)

    def parse_row(self, line, row):
        """
        Method called by :meth:`import_csv` for each row.
        """
        from openPLM.plmapp.forms import get_creation_form
        type_, reference, revision = self.get_values(row, "type", "reference",
            "revision")
        cls = models.get_all_plmobjects()[type_]
        group = models.GroupInfo.objects.get(name=self.get_value(row, "group"))
        lifecycle = models.Lifecycle.objects.get(name=self.get_value(row, "lifecycle"))
        form = get_creation_form(self.user, cls, inbulk_cache=self.inbulk_cache)
        data = {
                "type" : type_,
                "group" : str(group.id),
                "reference" : reference,
                "revision" : revision,
                "auto" : False,
                }
        for field in form.fields:
            if field not in data and field in self.headers_dict:
                data[field] = self.get_value(row, field)
        form = get_creation_form(self.user, cls, data, inbulk_cache=self.inbulk_cache)
        if not form.is_valid():
            items = (mark_safe(u"%s: %s" % item) for item
                    in form.errors.iteritems())
            self.store_errors(line, *items)
        else:
            obj = PLMObjectController.create_from_form(form, self.user, True, True)
            self.objects.append(obj)


class BOMImporter(CSVImporter):
    """
    A :class:`CSVImporter` that builds a bom from a CSV file.

    The CSV must contain the following columns:

        * parent-type
        * parent-reference
        * parent-revision
        * child-type
        * child-reference
        * child-revision
        * quantity
        * order
    """

    REQUIRED_HEADERS = ("parent-type", "parent-reference", "parent-revision",
                        "child-type", "child-reference", "child-revision",
                        "quantity", "order")

    HEADERS_SET = set(REQUIRED_HEADERS)

    @classmethod
    def get_headers_set(cls):
        return cls.HEADERS_SET

    def parse_row(self, line, row):
        from openPLM.plmapp.views.base import get_obj
        ptype, preference, prevision = self.get_values(row,
                *["parent-" + h for h in ("type", "reference", "revision")])
        parent = get_obj(ptype, preference, prevision, self.user)

        ctype, creference, crevision = self.get_values(row,
                *["child-" + h for h in ("type", "reference", "revision")])
        child = get_obj(ctype, creference, crevision, self.user)

        parent.block_mails()
        parent.object.no_index = True
        child.block_mails()
        child.object.no_index = True
        self.objects.append(parent)
        self.objects.append(child)

        qty = self.get_value(row, "quantity").replace(",", ".").replace(" ", "")
        quantity = float(qty)
        order = int(self.get_value(row, "order").replace(" ", ""))

        parent.add_child(child, quantity, order)

class UsersImporter(CSVImporter):
    """
    A :class:`CSVImporter` that sponsors users from a CSV file.

    The CSV must contain the following columns:

        * username
        * first_name
        * last_name
        * email
        * groups (multiple groups can be separeted by a "/")
        * language

    """

    REQUIRED_HEADERS = ('username', 'first_name', 'last_name', 'email', 'groups','language')

    HEADERS_SET = set(REQUIRED_HEADERS)

    def __init__(self, csv_file, user, encoding="utf-8"):
        self.ctrl = UserController(user, user)
        self.ctrl.block_mails()
        super(UsersImporter, self).__init__(csv_file, user)
        self.groups = dict(user.groups.values_list("name", "id"))

    @classmethod
    def get_headers_set(cls):
        return cls.HEADERS_SET

    def tear_down(self):
        self.ctrl.unblock_mails()

    def parse_row(self, line, row):
        from openPLM.plmapp.forms import SponsorForm
        un, fn, ln, em, grps,la = self.get_values(row, *self.REQUIRED_HEADERS)
        groups = []
        for grp in grps.split("/"):
            try:
                groups.append(self.groups[grp])
            except KeyError:
                self.store_errors(line, u"Invalid group:%s" % grp)
                return
        data = {
                "sponsor" : self.user.id,
                "username": un,
                "last_name": ln,
                "first_name": fn,
                "email" : em,
                "groups" : groups,
                "language" : la,
                "warned" : True,
                }
        form = SponsorForm(data, sponsor=self.user.id)
        if form.is_valid():
            new_user = form.save()
            new_user.profile.language = form.cleaned_data["language"]
            self.ctrl.sponsor(new_user)
            self.objects.append(new_user)
        else:
            items = (mark_safe(u"%s: %s" % item) for item
                    in form.errors.iteritems())
            self.store_errors(line, *items)


#: Dictionary (name -> CSVImporter's subclass) of known :class:`CSVImporter`
IMPORTERS = {"csv" : PLMObjectsImporter, "bom" : BOMImporter,
        "users" : UsersImporter}

