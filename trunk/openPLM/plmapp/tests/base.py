
from django.contrib.auth.models import User
from django.test import TestCase

from openPLM.plmapp.utils import *
from openPLM.plmapp.exceptions import *
from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.lifecycle import *
from openPLM.computer.models import *
from openPLM.office.models import *
from openPLM.cad.models import *


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
        self.user.save()
        self.user.get_profile().is_contributor = True
        self.user.get_profile().save()
        self.group = GroupInfo(name="grp", owner=self.user, creator=self.user,
                description="grp")
        self.group.save()
        self.user.groups.add(self.group)
        self.DATA["group"] = self.group

