
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.test import TestCase

from openPLM.plmapp.models import GroupInfo
from openPLM.plmapp.controllers import PLMObjectController

class BaseTestCase(TestCase):
    CONTROLLER = PLMObjectController
    TYPE = "Part"
    DATA = {}

    def setUp(self):
        self.cie = User.objects.create(username="company")
        p = self.cie.get_profile()
        p.is_contributor = True
        p.save()
        self.leading_group = GroupInfo.objects.create(name="leading_group",
                owner=self.cie, creator=self.cie)
        self.cie.groups.add(self.leading_group)
        self.user = User(username="user")
        self.user.set_password("password")
        self.user.email = "test@example.net"
        self.user.save()
        self.user.get_profile().is_contributor = True
        self.user.get_profile().save()
        self.group = GroupInfo(name="grp", owner=self.user, creator=self.user,
                description="grp")
        self.group.save()
        self.user.groups.add(self.group)
        self.DATA["group"] = self.group

    def create(self, ref="Part1"):
        return self.CONTROLLER.create(ref, self.TYPE, "a", self.user, self.DATA)

    def get_file(self, name="temp.test", data="data"):
        f = ContentFile(data)
        f.name = name
        return f

    def tearDown(self):
        from haystack import backend
        backend.SearchBackend.inmemory_db = None
        super(BaseTestCase, self).tearDown()

