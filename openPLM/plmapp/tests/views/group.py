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

import openPLM.plmapp.models as m
from openPLM.plmapp.controllers import PartController, GroupController


from .base import CommonViewTest

class GroupViewTestCase(CommonViewTest):

    def setUp(self):
        super(GroupViewTestCase, self).setUp()
        self.part_controller = self.controller
        self.group_url = "/group/%s/" % self.group.name
        self.controller = GroupController(self.group, self.user)
        self.brian # populate field

    def test_group_attributes(self):
        response = self.get(self.group_url + "attributes/", page="attributes")
        attributes = dict((x.capitalize(), y) for (x, y, z) in
                          response.context["object_attributes"])
        self.assertEqual(attributes["Description"], self.group.description)
        self.assertTrue(response.context["is_owner"])

    def test_users(self):
        response = self.get(self.group_url + "users/", page="users")
        user_formset = response.context["user_formset"]
        self.assertEqual(0, user_formset.total_form_count())
        self.assertTrue(response.context["in_group"])

    def test_users_get(self):
        self.brian.groups.add(self.group)
        response = self.get(self.group_url + "users/", page="users")
        user_formset = response.context["user_formset"]
        self.assertEqual(1, user_formset.total_form_count())
        form = user_formset.forms[0]
        self.assertFalse(form.fields["delete"].initial)
        self.assertEqual(self.brian, form.initial["user"])
        self.assertEqual(self.group, form.initial["group"])

    def test_users_post(self):
        self.brian.groups.add(self.group)
        data = {
            'form-TOTAL_FORMS' : '1',
            'form-INITIAL_FORMS' : '1',
            'form-MAX_NUM_FORMS' : 1,
            'form-0-group' : self.group.id,
            'form-0-user' : self.brian.id,
            'form-0-delete' : 'on',
            }
        response = self.post(self.group_url + "users/", data)
        self.assertEqual([], list(self.brian.groups.all()))

    def test_users_post_nodeletetion(self):
        self.brian.groups.add(self.group)
        data = {
            'form-TOTAL_FORMS' : '1',
            'form-INITIAL_FORMS' : '1',
            'form-MAX_NUM_FORMS' : 1,
            'form-0-group' : self.group.id,
            'form-0-user' : self.brian.id,
            'form-0-delete' : '',
            }
        response = self.post(self.group_url + "users/", data)
        self.assertTrue(self.brian.groups.filter(id=self.group.id).exists())
        user_formset = response.context["user_formset"]
        self.assertEqual(1, user_formset.total_form_count())
        form = user_formset.forms[0]
        self.assertFalse(form.fields["delete"].initial)
        self.assertEqual(self.brian, form.initial["user"])
        self.assertEqual(self.group, form.initial["group"])

    def test_plmobjects(self):
        response = self.get(self.group_url + "objects/", page="objects")
        objects = response.context["objects"]
        self.assertEqual([self.part_controller.plmobject_ptr], list(objects.object_list))
        # create a new group
        group = m.GroupInfo(name="grp2", owner=self.user, creator=self.user,
                description="grp")
        group.save()
        self.user.groups.add(group)
        # create another part which bellows to another group
        p2 = PartController.create("Part2", "Part", "a", self.user,
                dict(group=group))
        response = self.get(self.group_url + "objects/", page="objects")
        objects = response.context["objects"]
        self.assertEqual([self.part_controller.plmobject_ptr], list(objects.object_list))

    def test_history(self):
        response = self.get(self.group_url + "history/", page="history")

    def test_navigate(self):
        response = self.get(self.group_url + "navigate/")

    def test_user_add_get(self):
        """
        Tests the page to add a user to the group, get version.
        """
        response = self.get(self.group_url + "users/add/", page="users",
                link=True)
        form = response.context["add_user_form"]

    def test_user_add_post(self):
        """
        Tests the page to add a user to the group, post version.
        """
        mail.outbox = []
        data = {"type" : "User", "username" : self.brian.username}
        response = self.post(self.group_url + "users/add/", data=data)
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertFalse(inv.guest_asked)
        self.assertEqual(m.Invitation.PENDING, inv.state)
        self.assertFalse(self.brian.groups.count())
        # get the users page
        response = self.get(self.group_url + "users/")
        pending = response.context["pending_invitations"]
        self.assertEqual([inv], list(pending))
        # check a mail has been sent to brian
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].bcc, [self.brian.email])

    def test_user_join_get(self):
        """
        Tests the page to ask to join the group, get version.
        """
        authenticated = self.client.login(username="Brian", password="life")
        self.assertTrue(authenticated)
        response = self.get(self.group_url + "users/join/", page="users")
        self.assertFalse(response.context["in_group"])

    def test_user_join_post(self):
        """
        Tests the page to ask to join the group, post version.
        """
        mail.outbox = []
        self.client.login(username="Brian", password="life")
        data = {"type" : "User", "username" : self.brian.username}
        response = self.post(self.group_url + "users/join/", data=data)
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertTrue(inv.guest_asked)
        self.assertEqual(m.Invitation.PENDING, inv.state)
        self.assertFalse(self.brian.groups.count())
        # get the users page
        response = self.get(self.group_url + "users/")
        pending = response.context["pending_invitations"]
        self.assertEqual([inv], list(pending))
        # check a mail has been sent to brian
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].bcc, [self.user.email])

    def _do_test_accept_invitation_get(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        response = self.get(self.group_url + "invitation/accept/%s/" % inv.token,
                page="users")
        self.assertEqual(inv, response.context["invitation"])
        form = response.context["invitation_form"]
        self.assertEqual(form.initial["invitation"], inv)
        # check that brian does not belong to the group
        self.assertFalse(self.brian.groups.count())
        self.assertFalse(mail.outbox)

    def test_accept_invitation_from_guest_get(self):
        """
        Tests the page to accept an invitation, get version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_accept_invitation_get()

    def _do_test_accept_invitation_post_error(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        data = {"invitation" : inv.pk }
        response = self.client.post(self.group_url + "invitation/accept/%s/" % inv.token,
                data=data)
        self.assertTemplateUsed(response, "error.html")
        # checks that brian does not belong to the group
        self.assertFalse(self.brian.groups.filter(id=self.group.id).exists())
        self.assertEqual(0, len(mail.outbox))
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertEqual(m.Invitation.PENDING, inv.state)

    def test_accept_invitation_from_guest_post_error(self):
        """
        Tests the page to accept an invitation, post version,
        Error: not the guest asks and accepts.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self.client.login(username="Brian", password="life")
        self._do_test_accept_invitation_post_error()

    def test_accept_invitation_from_owner_post_error(self):
        """
        Tests the page to accept an invitation, post version.
        Error: the owner adds and accepts.
        """
        self.controller.add_user(self.brian)
        self._do_test_accept_invitation_post_error()

    def _do_test_accept_invitation_post(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        data = {"invitation" : inv.pk }
        response = self.post(self.group_url + "invitation/accept/%s/" % inv.token,
                page="users", data=data)
        # checks that brian belongs to the group
        self.assertFalse(response.context["pending_invitations"])
        form = response.context["user_formset"].forms[0]
        self.assertEqual(self.brian, form.initial["user"])
        self.assertTrue(self.brian.groups.filter(id=self.group.id).exists())
        user = response.context["request"].user
        if self.LANGUAGE == "en" or user == self.user:
            self.assertEqual(1, len(mail.outbox))
        else:
            # two languages -> two messages
            self.assertEqual(2, len(mail.outbox))
        # a notification is sent to the owner and to the guest
        recipients = set()
        for msg in mail.outbox:
            recipients.update(msg.bcc)
        if user == self.user:
            self.assertEqual(recipients, set([self.brian.email]))
        else:
            self.assertEqual(recipients, set([self.user.email, self.brian.email]))
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertEqual(m.Invitation.ACCEPTED, inv.state)

    def test_accept_invitation_from_guest_post(self):
        """
        Tests the page to accept an invitation, post version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_accept_invitation_post()

    def test_accept_invitation_from_owner_get(self):
        """
        Tests the page to accept an invitation, get version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_accept_invitation_get()

    def test_accept_invitation_from_owner_post(self):
        """
        Tests the page to accept an invitation, post version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_accept_invitation_post()

    def _do_test_refuse_invitation_get(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        response = self.get(self.group_url + "invitation/refuse/%s/" % inv.token,
                page="users")
        self.assertEqual(inv, response.context["invitation"])
        form = response.context["invitation_form"]
        self.assertEqual(form.initial["invitation"], inv)
        # check that brian does not belong to the group
        self.assertFalse(self.brian.groups.count())
        self.assertFalse(mail.outbox)

    def test_refuse_invitation_from_guest_get(self):
        """
        Tests the page to refuse an invitation, get version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_refuse_invitation_get()

    def _do_test_refuse_invitation_post(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        data = {"invitation" : inv.pk }
        response = self.post(self.group_url + "invitation/refuse/%s/" % inv.token,
                page="users", data=data)
        # checks that brian does not belong to the group
        self.assertFalse(response.context["pending_invitations"])
        self.assertFalse(response.context["user_formset"].forms)
        self.assertFalse(self.brian.groups.filter(id=self.group.id).exists())
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertEqual(m.Invitation.REFUSED, inv.state)

    def test_refuse_invitation_from_guest_post(self):
        """
        Tests the page to refuse an invitation, post version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_refuse_invitation_post()

    def test_refuse_invitation_from_owner_get(self):
        """
        Tests the page to refuse an invitation, get version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_refuse_invitation_get()

    def test_refuse_invitation_from_owner_post(self):
        """
        Tests the page to refuse an invitation, post version.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_refuse_invitation_post()

    def _do_test_refuse_invitation_post_error(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        data = {"invitation" : inv.pk }
        response = self.client.post(self.group_url + "invitation/refuse/%s/" % inv.token,
                data=data)
        self.assertTemplateUsed(response, "error.html")
        # checks that brian does not belong to the group
        self.assertFalse(self.brian.groups.filter(id=self.group.id).exists())
        self.assertEqual(0, len(mail.outbox))
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertEqual(m.Invitation.PENDING, inv.state)

    def test_refuse_invitation_from_guest_post_error(self):
        """
        Tests the page to refuse an invitation, post version,
        Error: not the guest asks and refuses.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self.client.login(username="Brian", password="life")
        self._do_test_refuse_invitation_post_error()

    def test_refuse_invitation_from_owner_post_error(self):
        """
        Tests the page to refuse an invitation, post version.
        Error: the owner adds and refuses.
        """
        self.controller.add_user(self.brian)
        self._do_test_refuse_invitation_post_error()

    def _do_test_send_invitation_post_error(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        data = {"invitation" : inv.pk }
        response = self.client.post(self.group_url + "invitation/send/%s/" % inv.token,
                data=data)
        self.assertTemplateUsed(response, "error.html")
        # checks that brian does not belong to the group
        self.assertFalse(self.brian.groups.filter(id=self.group.id).exists())
        self.assertEqual(0, len(mail.outbox))
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertEqual(m.Invitation.PENDING, inv.state)

    def test_send_invitation_from_guest_post_error(self):
        """
        Tests the page to send an invitation, post version,
        Error: not the guest asks and sends.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self._do_test_send_invitation_post_error()

    def test_send_invitation_from_owner_post_error(self):
        """
        Tests the page to send an invitation, post version.
        Error: the owner adds and sends.
        """
        self.controller.add_user(self.brian)
        self.client.login(username="Brian", password="life")
        self._do_test_send_invitation_post_error()

    def _do_test_send_invitation_get(self):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        response = self.get(self.group_url + "invitation/send/%s/" % inv.token,
                page="users")
        # check that brian does not belong to the group
        self.assertFalse(self.brian.groups.count())
        self.assertFalse(mail.outbox)

    def test_send_invitation_from_guest_get(self):
        """
        Tests the page to send an invitation, get version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self.client.login(username="Brian", password="life")
        self._do_test_send_invitation_get()

    def _do_test_send_invitation_post(self, from_owner):
        mail.outbox = []
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        data = {"invitation" : inv.pk }
        response = self.post(self.group_url + "invitation/send/%s/" % inv.token,
                page="users", data=data)
        # checks that brian does not belong to the group
        self.assertEqual([inv], list(response.context["pending_invitations"]))
        self.assertFalse(response.context["user_formset"].forms)
        self.assertFalse(self.brian.groups.filter(id=self.group.id).exists())
        inv = m.Invitation.objects.get(group=self.group,
                guest=self.brian, owner=self.user)
        self.assertEqual(m.Invitation.PENDING, inv.state)
        # check a mail has been sent to the right user
        self.assertEqual(1, len(mail.outbox))
        email = self.brian.email if from_owner else self.user.email
        self.assertEqual(mail.outbox[0].bcc, [email])

    def test_send_invitation_from_guest_post(self):
        """
        Tests the page to send an invitation, post version.
        """
        GroupController(self.group, self.brian).ask_to_join()
        self.client.login(username="Brian", password="life")
        self._do_test_send_invitation_post(False)

    def test_send_invitation_from_owner_get(self):
        """
        Tests the page to send an invitation, get version.
        """
        self.controller.add_user(self.brian)
        self._do_test_send_invitation_get()

    def test_send_invitation_from_owner_post(self):
        """
        Tests the page to send an invitation, post version.
        """
        self.controller.add_user(self.brian)
        self._do_test_send_invitation_post(True)
