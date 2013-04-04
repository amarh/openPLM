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

from django.core import mail
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils import translation

import lxml.html

from openPLM.plmapp import forms
from openPLM.plmapp.utils import level_to_sign_str
import openPLM.plmapp.models as m
from openPLM.plmapp.controllers import UserController

from .base import CommonViewTest

class UserViewTestCase(CommonViewTest):

    def setUp(self):
        super(UserViewTestCase, self).setUp()
        self.user_url = "/user/%s/" % self.user.username
        self.controller = UserController(self.user, self.user)

    def test_user_attribute(self):
        response = self.get(self.user_url + "attributes/", page="attributes")
        attributes = dict((x.capitalize(), y) for (x, y, z) in
                          response.context["object_attributes"])

        old_lang = translation.get_language()
        translation.activate(self.LANGUAGE)
        key = _("email address")
        translation.activate(old_lang)
        del old_lang

        self.assertEqual(attributes[key.capitalize()], self.user.email)
        self.assertTrue(response.context["is_owner"])

    def test_groups(self):
        response = self.get(self.user_url + "groups/")
        # TODO

    def test_part_doc_cads(self):
        response = self.get(self.user_url + "parts-doc-cad/")
        # TODO

    def test_history(self):
        response = self.get(self.user_url + "history/")

    def test_navigate(self):
        response = self.get(self.user_url + "navigate/")

    def test_sponsor_get(self):
        response = self.get(self.user_url + "delegation/sponsor/")
        form = response.context["sponsor_form"]
        self.assertEquals(set(g.id for g in self.user.groupinfo_owner.all()),
                set(g.id for g in form.fields["groups"].queryset.all()))

    def test_sponsor_post(self):
        data = dict(sponsor=self.user.id,
                    username="loser", first_name="You", last_name="Lost",
                    email="you.lost@example.com", groups=[self.group.pk],
                    language=self.user.profile.language)
        response = self.post(self.user_url + "delegation/sponsor/", data)
        user = User.objects.get(username=data["username"])
        for attr in ("first_name", "last_name", "email"):
            self.assertEquals(data[attr], getattr(user, attr))
        self.assertTrue(user.profile.is_contributor)
        self.assertFalse(user.profile.is_administrator)
        self.assertTrue(user.groups.filter(id=self.group.id))

    def test_modify_get(self):
        response = self.get(self.user_url + "modify/")
        form = response.context["modification_form"]
        self.assertEqual(self.user.first_name, form.initial["first_name"])
        self.assertEqual(self.user.email, form.initial["email"])

    def test_modify_post(self):
        data = {"last_name":"Snow", "email":"user@test.com", "first_name":"John",
                "avatar": "",}
        response = self.post(self.user_url + "modify/", data)
        user = User.objects.get(username=self.user.username)
        self.assertEqual("Snow", user.last_name)

    def test_modify_sponsored_user(self):
        data0 = dict(sponsor=self.user.id,
                    username="loser", first_name="You", last_name="Lost",
                    email="you.lost@example.com", groups=[self.group.pk],
                    language=self.user.profile.language)
        response = self.post(self.user_url + "delegation/sponsor/", data0)
        data = {"last_name":"Snow", "email":"user@test.com", "first_name":"John",
                "avatar":None,}
         # brian can not edit these data
        self.client.login(username=self.brian.username, password="life")
        response = self.client.post("/user/loser/modify/", data)
        user = User.objects.get(username="loser")
        self.assertEqual(user.email, data0["email"])
        self.assertEqual(user.first_name, data0["first_name"])
        self.assertEqual(user.last_name, data0["last_name"])

        # self.user can edit these data
        self.client.login(username=self.user.username, password="password")
        response = self.client.post("/user/loser/modify/", data)
        user = User.objects.get(username="loser")
        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.first_name, data["first_name"])
        self.assertEqual(user.last_name, data["last_name"])

        # it should not be possible to edit data once loser has logged in
        user.set_password("pwd")
        user.save()
        self.client.login(username=user.username, password="pwd")
        self.client.get("/home/")
        self.client.login(username=self.user.username, password="password")
        data2 = {"last_name":"Snow2", "email":"user2@test.com", "first_name":"John2"}
        response = self.client.post("/user/loser/modify/", data2)
        user = User.objects.get(username="loser")
        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.first_name, data["first_name"])
        self.assertEqual(user.last_name, data["last_name"])

    def test_password_get(self):
        response = self.get(self.user_url + "password/")
        self.assertTrue(response.context["modification_form"])

    def test_password_post(self):
        data = dict(old_password="password", new_password1="pw",
                new_password2="pw")
        response = self.post(self.user_url + "password/", data)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.check_password("pw"))

    def test_password_error(self):
        data = dict(old_password="error", new_password1="pw",
                new_password2="pw")
        response = self.post(self.user_url + "password/", data)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.check_password("password"))
        self.assertFalse(self.user.check_password("pw"))

    def test_delegation_get(self):
        response = self.get(self.user_url + "delegation/")

    def test_delegation_remove(self):
        self.controller.delegate(self.brian, m.ROLE_OWNER)
        link = self.controller.get_user_delegation_links()[0]
        data = {"link_id" : link.id }
        response = self.post(self.user_url + "delegation/delete/", data)
        self.assertFalse(self.controller.get_user_delegation_links())

    def test_delegate_get(self):
        for role in ("owner", "notified"):
            url = self.user_url + "delegation/delegate/%s/" % role
            response = self.get(url, link=True, page="delegation")
            self.assertEqual(role, unicode(response.context["role"]))

    def test_delegate_sign_get(self):
        for level in ("all", "1", "2"):
            url = self.user_url + "delegation/delegate/sign/%s/" % str(level)
            response = self.get(url, link=True, page="delegation")
            if self.LANGUAGE == "en":
                role = unicode(response.context["role"])
                self.assertTrue(role.startswith("signer"))
                self.assertTrue(level in role)

    def test_delegate_post(self):
        data = { "type" : "User", "username": self.brian.username }
        for role in ("owner", "notified"):
            url = self.user_url + "delegation/delegate/%s/" % role
            response = self.post(url, data)
            m.DelegationLink.objects.get(role=role, delegator=self.user,
                    delegatee=self.brian)

    def test_delegate_sign_post(self):
        data = { "type" : "User", "username": self.brian.username }
        for level in xrange(1, 4):
            url = self.user_url + "delegation/delegate/sign/%d/" % level
            response = self.post(url, data)
            role = level_to_sign_str(level - 1)
            m.DelegationLink.objects.get(role=role,
                delegator=self.user, delegatee=self.brian)

    def test_delegate_sign_all_post(self):
        # sign all level
        data = { "type" : "User", "username": self.brian.username }
        url = self.user_url + "delegation/delegate/sign/all/"
        response = self.post(url, data)
        for level in xrange(2):
            role = level_to_sign_str(level)
            m.DelegationLink.objects.get(role=role, delegator=self.user,
                    delegatee=self.brian)

    def test_resend_sponsor_mail(self):
        user = User(username="dede", email="dede@example.net")
        self.controller.sponsor(user)
        link = m.DelegationLink.objects.get(role="sponsor", delegatee=user)
        pwd = user.password
        mail.outbox = []
        self.post(self.user_url + 'delegation/sponsor/mail/',
                {"link_id" : link.id})
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].bcc, [user.email])
        user = User.objects.get(username="dede")
        self.assertNotEqual(user.password, pwd)

    def test_resend_sponsor_error_user_connected(self):
        user = User(username="dede", email="dede@example.net")
        self.controller.sponsor(user)
        user.last_login = timezone.now()
        user.save()
        link = m.DelegationLink.objects.get(role="sponsor", delegatee=user)
        pwd = user.password
        mail.outbox = []
        self.post(self.user_url + 'delegation/sponsor/mail/',
                {"link_id" : link.id}, status_code=403)
        self.assertEqual(0, len(mail.outbox))
        user = User.objects.get(username="dede")
        self.assertEqual(user.password, pwd)

    def test_resend_sponsor_error_not_sponsor(self):
        user = User(username="dede", email="dede@example.net")
        UserController(self.cie, self.cie).sponsor(user)
        link = m.DelegationLink.objects.get(role="sponsor", delegatee=user)
        pwd = user.password
        mail.outbox = []
        self.post(self.user_url + 'delegation/sponsor/mail/',
                {"link_id" : link.id}, status_code=403)
        self.assertEqual(0, len(mail.outbox))
        user = User.objects.get(username="dede")
        self.assertEqual(user.password, pwd)

    def test_upload_file_get(self):
        response = self.get(self.user_url + "files/add/")
        self.assertTrue(isinstance(response.context["add_file_form"],
                                   forms.AddFileForm))

    def test_upload_file_post(self):
        fname = u"toti\xe8o_t.txt"
        name = u"toti\xe8o t"
        f = self.get_file(name=fname, data="crumble")
        data = { "filename" : f }
        response = self.post(self.user_url + "files/add/", data)
        df = list(self.controller.files.all())[0]
        self.assertEquals(df.filename, f.name)
        self.assertEquals("crumble", df.file.read())
        url = "/object/create/?type=Document&pfiles=%d" % df.id
        self.assertRedirects(response, url)
        # post the form as previously returned by "files/add/"
        cform = response.context["creation_form"]
        self.assertEquals(name, cform.initial["name"])
        form = lxml.html.fromstring(response.content).xpath("//form[@id='creation_form']")[0]
        data = dict(form.fields)
        r2 = self.post(url, data)
        obj = r2.context["obj"]
        self.assertEquals(name, obj.name)
        self.assertEquals(list(obj.files.values_list("filename", flat=True)), [fname])
        self.assertFalse(self.controller.files.all())
        self.assertEquals(obj.files.all()[0].file.read(), "crumble")




