
import cStringIO, StringIO
from collections import defaultdict

from django.core import mail
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from celery.signals import task_prerun

import openPLM.plmapp.models as models
from openPLM.plmapp.models import GroupInfo, PLMObject, ParentChildLink
from openPLM.plmapp.csvimport import PLMObjectsImporter, BOMImporter,\
        CSVImportError, UsersImporter
from openPLM.plmapp.views.base import get_obj
from openPLM.plmapp.utils.unicodecsv import UnicodeWriter
from openPLM.plmapp.forms import CSVForm


class CSVImportTestCase(TransactionTestCase):

    def setUp(self):
        super(CSVImportTestCase, self).setUp()
        self.sent_tasks = defaultdict(list)
        self.cie = User.objects.create(username="company")
        p = self.cie.profile
        p.is_contributor = True
        p.save()
        self.leading_group = GroupInfo.objects.create(name="leading_group",
                owner=self.cie, creator=self.cie)
        self.cie.groups.add(self.leading_group)
        self.user = User(username="user")
        self.user.email = "test@example.net"
        self.user.set_password("password")
        self.user.save()
        self.user.profile.is_contributor = True
        self.user.profile.save()
        self.group = GroupInfo(name="grp", owner=self.user, creator=self.user,
                description="grp")
        self.group.save()
        self.user.groups.add(self.group)
        self.client.post("/login/", {'username' : 'user', 'password' : 'password'})
        task_prerun.connect(self.task_sent_handler)

    def task_sent_handler(self, sender=None, task_id=None, task=None, args=None,
                      kwargs=None, **kwds):
        self.sent_tasks[task.name].append(task)

    def tearDown(self):
        super(CSVImportTestCase, self).tearDown()
        task_prerun.disconnect(self.task_sent_handler)
        from haystack import backend
        backend.SearchBackend.inmemory_db = None

    def get_valid_rows(self):
        return [[u'Type',
              u'reference',
              u'revision',
              u'name',
              u'supplier',
              u'group',
              u'lifecycle'],
             [u'Part',
              u'p1',
              u'a',
              u'Part1',
              u'Moi',
              self.group.name,
              u'draft_official_deprecated'],
             [u'Document',
              u'd1',
              u'2',
              u'Document1',
              u'',
              self.group.name,
              u'draft_official_deprecated'],
             [u'Document',
              u'd2',
              u'7',
              u'Document 2',
              u'',
              self.group.name,
              u'draft_official_deprecated'],
             [u'SinglePart',
              u'sp1',
              u's',
              u'SP1',
              u'Lui',
              self.group.name,
              u'draft_official_deprecated'],
             [u'SinglePart',
              u'sp2',
              u's',
              u'SP2',
              u'Lui',
              self.group.name,
              u'draft_official_deprecated'],
             ]


    def import_csv(self, Importer, rows):
        csv_file = cStringIO.StringIO()
        UnicodeWriter(csv_file).writerows(rows)
        csv_file.seek(0)
        importer = Importer(csv_file, self.user)
        headers = importer.get_preview().guessed_headers
        objects = importer.import_csv(headers)
        return objects

    def test_import_valid(self):
        csv_rows = self.get_valid_rows()
        objects = self.import_csv(PLMObjectsImporter, csv_rows)
        self.assertEquals(len(csv_rows) - 1, len(objects))
        sp1 = get_obj("SinglePart", "sp1", "s", self.user)
        self.assertEquals("SP1", sp1.name)
        self.assertEqual(0, len(mail.outbox))
        self.assertEqual(1, len(self.sent_tasks["openPLM.plmapp.tasks.update_indexes"]))

    def test_import_csv_invalid_last_row(self):
        """
        Tests that an import with an invalid row doest not modify
        the database.
        """
        csv_rows = self.get_valid_rows()
        csv_rows.append(["BadType", "bt", "1", "BT",
            self.group.name, u'draft_official_deprecated'])
        plmobjects = list(PLMObject.objects.all())
        self.assertRaises(CSVImportError, self.import_csv,
                PLMObjectsImporter, csv_rows)
        self.assertEquals(plmobjects, list(PLMObject.objects.all()))
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(self.sent_tasks["openPLM.plmapp.tasks.update_indexes"])

    def get_valid_bom(self):
        return [["parent-type", "parent-reference", "parent-revision",
                 "child-type", "child-reference", "child-revision",
                 "quantity", "order"],
                ["Part", "p1", "a", "SinglePart", "sp1", "s", "10", "15"],
                ["SinglePart", "sp1", "s", "SinglePart", "sp2", "s", "10.5", "16"],
                ]

    def test_import_bom_valid(self):
        """
        Tests an import of a valid bom.
        """
        self.import_csv(PLMObjectsImporter, self.get_valid_rows())
        csv_rows = self.get_valid_bom()
        objects = self.import_csv(BOMImporter, csv_rows)
        # objects should be [parent1, child1, ...]
        self.assertEquals((len(csv_rows) - 1) * 2, len(objects))

        # first row
        parent = get_obj("Part", "p1", "a", self.user)
        child = get_obj("SinglePart", "sp1", "s", self.user)
        c = parent.get_children()[0]
        self.assertEquals(c.link.parent.id, parent.id)
        self.assertEquals(c.link.child.id, child.id)
        self.assertEquals(c.link.quantity, 10)
        self.assertEquals(c.link.order, 15)

        # second row
        parent = get_obj("SinglePart", "sp1", "s", self.user)
        child = get_obj("SinglePart", "sp2", "s", self.user)
        c = parent.get_children()[0]
        self.assertEquals(c.link.parent.id, parent.id)
        self.assertEquals(c.link.child.id, child.id)
        self.assertEquals(c.link.quantity, 10.5)
        self.assertEquals(c.link.order, 16)

    def test_import_bom_invalid_order(self):
        """
        Tests an import of an invalid bom: invalid order.
        """
        self.import_csv(PLMObjectsImporter, self.get_valid_rows())
        csv_rows = self.get_valid_bom()
        csv_rows[-1][-1] = "not an integer"
        self.assertRaises(CSVImportError, self.import_csv,
                          BOMImporter, csv_rows)
        self.assertEquals(0, len(ParentChildLink.objects.all()))

    def test_import_bom_invalid_parent(self):
        """
        Tests an import of an invalid bom: invalid parent.
        """
        self.import_csv(PLMObjectsImporter, self.get_valid_rows())
        csv_rows = self.get_valid_bom()
        csv_rows[1][0] = "not an type"
        self.assertRaises(CSVImportError, self.import_csv,
                          BOMImporter, csv_rows)
        self.assertEquals(0, len(ParentChildLink.objects.all()))

    def test_import_bom_invalid_duplicated_row(self):
        """
        Tests an import of an invalid bom: a row is duplicated.
        """
        self.import_csv(PLMObjectsImporter, self.get_valid_rows())
        csv_rows = self.get_valid_bom()
        csv_rows.append(csv_rows[-1])
        self.assertRaises(CSVImportError, self.import_csv,
                          BOMImporter, csv_rows)
        self.assertEquals(0, len(ParentChildLink.objects.all()))

    def test_view_init_get(self):
        response = self.client.get("/import/csv/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.context["step"])
        self.assertEqual("csv", response.context["target"])
        form = response.context["csv_form"]
        self.assertTrue(isinstance(form, CSVForm))

    def test_view_csv_all(self):
        """
        Complex test that simulate an upload of a csv file (complete process).
        """
        # upload a csv file
        csv_file = StringIO.StringIO()
        csv_file.name = "data.csv"
        UnicodeWriter(csv_file).writerows(self.get_valid_rows())
        csv_file.seek(0)
        response = self.client.post("/import/csv/", {"encoding":"utf_8",
            "filename":"data.csv", "file":csv_file}, follow=True)
        csv_file.close()

        # load the second page
        url = response.redirect_chain[0][0]
        response2 = self.client.get(url)
        self.assertEquals(2, response2.context["step"])
        preview = response2.context["preview"]
        self.assertFalse(None in preview.guessed_headers)
        formset = response2.context["headers_formset"]

        # validate and import the file
        data = {}
        for key, value in formset.management_form.initial.iteritems():
            data["form-" + key] = value or ""
        for i, d in enumerate(formset.initial):
            for key, value in d.iteritems():
                data["form-%d-%s" % (i, key)] = value
            data['form-%d-ORDER' % i] = str(i)
        response3 = self.client.post(url, data, follow=True)
        url_done = response3.redirect_chain[-1][0]
        self.assertEquals("http://testserver/import/done/", url_done)
        # check an item
        sp1 = get_obj("SinglePart", "sp1", "s", self.user)
        self.assertEquals("SP1", sp1.name)

    def get_users_rows(self):
        return [['username', 'first_name', 'last_name', 'email', 'groups', 'language'],
                ['user_1', 'fn1', 'ln1', 'user_1@example.net', 'grp', 'en'],
                ['user_2', 'fn2', 'ln2', 'user_2@example.net', 'grp', 'en'],
                ['user_3', 'fn3', 'ln3', 'user_3@example.net', 'grp', 'en'],
                ['user_4', 'fn4', 'ln4', 'user_4@example.net', 'grp', 'en'],
                ['user_5', 'fn5', 'ln5', 'user_5@example.net', 'grp', 'en'],
               ]

    def test_users_valid(self):
        csv_rows = self.get_users_rows()
        objects = self.import_csv(UsersImporter, csv_rows)
        self.assertEquals(len(csv_rows) - 1, len(objects))
        users = models.User.objects.filter(username__startswith="user_")
        self.assertEquals(5, users.count())
        sponsor_links = self.user.delegationlink_delegator.filter(role="sponsor")
        self.assertEquals(5, sponsor_links.count())
        self.assertEquals(set(users.values_list("id", flat=True)),
                set(sponsor_links.values_list("delegatee", flat=True)))

    def test_users_invalid_duplicated_users(self):
        csv_rows = self.get_users_rows()
        csv_rows.append(csv_rows[1])
        self.assertRaises(CSVImportError, self.import_csv,
                          UsersImporter, csv_rows)
        # 2 : company + test
        self.assertEquals(2, User.objects.count())
        sponsor_links = self.user.delegationlink_delegator.filter(role="sponsor")
        self.assertFalse(bool(sponsor_links))
        self.assertEqual(len(mail.outbox), 0)

    def test_users_invalid_missing_first_name(self):
        csv_rows = self.get_users_rows()
        csv_rows[1][1] = ""
        self.assertRaises(CSVImportError, self.import_csv,
                          UsersImporter, csv_rows)
        # 2 : company + test
        self.assertEquals(2, User.objects.count())
        sponsor_links = self.user.delegationlink_delegator.filter(role="sponsor")
        self.assertFalse(bool(sponsor_links))
        self.assertEqual(len(mail.outbox), 0)

