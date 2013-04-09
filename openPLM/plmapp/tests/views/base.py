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


from django.contrib.auth.models import User

from openPLM.plmapp.controllers import DocumentController, PartController

from openPLM.plmapp.tests.base import BaseTestCase

class CommonViewTest(BaseTestCase):
    TYPE = "Part"
    CONTROLLER = PartController
    DATA = {}
    REFERENCE = "Part1"
    LANGUAGE = "en"

    def setUp(self):
        super(CommonViewTest, self).setUp()
        self.client.post("/login/", {'username' : self.user.username, 'password' : 'password'})
        self.client.post("/i18n/setlang/", {"language" : self.LANGUAGE})
        # block initial mails
        controller = self.CONTROLLER.create(self.REFERENCE, self.TYPE, "a",
                                            self.user, self.DATA, True)
        self.controller = self.CONTROLLER(controller.object, self.user)
        self.base_url = self.controller.plmobject_url
        self._brian = None

    @property
    def brian(self):
        if self._brian is None:
            brian = User.objects.create_user(username="Brian", password="life",
                    email="brian@example.net")
            brian.profile.is_contributor = True
            brian.profile.save()
            self._brian = brian
        return self._brian

    def post(self, url, data=None, follow=True, status_code=200,
            link=False, page=""):
        return self.get_or_post(self.client.post, url, data, follow, status_code,
                link, page)

    def get(self, url, data=None, follow=True, status_code=200,
            link=False, page=""):
        return self.get_or_post(self.client.get, url, data, follow, status_code,
                link, page)

    def get_or_post(self, func, url, data=None, follow=True, status_code=200,
            link=False, page=""):
        response = func(url, data or {}, follow=follow)
        self.assertEqual(response.status_code, status_code)
        if status_code == 200:
            self.assertEqual(link, response.context["link_creation"])
            if page:
                self.assertEqual(page, response.context["current_page"])
        return response

    def attach_to_official_document(self):
        u""" If :attr:`controller`` is a PartController, this method attachs
        an official document to it, so that it becomes promotable.

        Does nothing if :attr:`controller` is a DocumentController.

        Returns the created document (a controller) or None.
        """
        if self.controller.is_part:
            document = DocumentController.create("doc_1", "Document", "a",
                    self.user, self.DATA)
            document.add_file(self.get_file())
            document.promote()
            self.controller.attach_to_document(document)
            return document
        return None

