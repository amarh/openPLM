import os
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.test import TestCase

from openPLM.plmapp.models import GroupInfo, DocumentFile
from openPLM.plmapp.controllers import PLMObjectController

class BaseTestCase(TestCase):
    CONTROLLER = PLMObjectController
    TYPE = "Part"
    DATA = {}

    def setUp(self):
        self.cie = User.objects.create(username="company")
        p = self.cie.profile
        p.is_contributor = True
        p.save()
        self.leading_group = GroupInfo.objects.create(name="leading_group",
                owner=self.cie, creator=self.cie)
        self.cie.groups.add(self.leading_group)
        self.user = User(username="John")
        self.user.set_password("password")
        self.user.email = "test@example.net"
        self.user.save()
        self.user.profile.is_contributor = True
        self.user.profile.save()
        self.group = GroupInfo(name="grp", owner=self.user, creator=self.user,
                description="grp")
        self.group.save()
        self.user.groups.add(self.group)
        self.DATA["group"] = self.group

    def get_contributor(self, username="user2"):
        """ Returns a new contributor"""
        user = User(username=username)
        user.save()
        user.profile.is_contributor = True
        user.profile.save()
        user.groups.add(self.group)
        return user

    def get_publisher(self, username="publisher"):
        """ Returns a new contributor"""
        user = User(username=username)
        user.save()
        user.profile.can_publish = True
        user.profile.save()
        user.groups.add(self.group)
        return user

    def create(self, ref="Part1", type=None):
        return self.CONTROLLER.create(ref, type or self.TYPE, "a", self.user, self.DATA)

    def get_file(self, name="temp.test", data="data"):
        f = ContentFile(data)
        f.name = name
        return f

    def tearDown(self):
        cache.clear()
        from haystack import backend
        backend.SearchBackend.inmemory_db = None
        super(BaseTestCase, self).tearDown()
        for df in DocumentFile.objects.all():
            try:
                os.remove(df.file.path)
            except (IOError, OSError):
                pass


