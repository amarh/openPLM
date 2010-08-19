"""
This module contains tests to measure the performances of
:func:`.rebuild_closure`.
"""

import time
import random
from django.test import TestCase

from openPLM.plmapp.models import *

class ClosureTest(TestCase):
    def go(self, nb_users, nb_links):
        users = []
        for i in xrange(nb_users):
            user = User(username=str(i))
            user.save()
            users.append(user)
        for role, r in [("owner", "owner")]:
            for i in xrange(nb_links):
                u1 = random.choice(users)
                u2 = random.choice(users)
                if u1 != u2:
                    DelegationLink.objects.get_or_create(delegator=u1, delegatee=u2,
                                          role=role)
        t = time.clock()
        for user in users:
            delegators = DelegationLink.get_delegators(user, "owner")
            print len(delegators), delegators[:10]
        print time.clock() - t
        print DelegationLink.objects.all().count(), "links"
        t = time.clock()
        rebuild_closure()
        print time.clock() - t
        print ClosureDelegationLink.objects.all().count(), "links"

    def test_performance(self):
        self.go(1000, 1000)
