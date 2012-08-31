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
