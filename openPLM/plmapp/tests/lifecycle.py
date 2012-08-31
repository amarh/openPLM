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
This module contains test for lifecycle stuff.
"""

from django.test import TestCase

from openPLM.plmapp.models import Lifecycle, get_default_lifecycle, \
        get_default_state, LifecycleStates
from openPLM.plmapp.lifecycle import LifecycleList

class LifecycleTest(TestCase):
    def test_get_default(self):
        lifecycle = get_default_lifecycle()
    
    def test_to_list(self):
        lifecycle = get_default_lifecycle()
        lc_list = lifecycle.to_states_list()
        self.assertEqual(lc_list.name, lifecycle.name)
        lcs = LifecycleStates.objects.filter(lifecycle=lifecycle).order_by("rank")
        self.assertEqual(len(lcs), len(lc_list))

    def test_from_list(self):
        cycle = LifecycleList("cycle_name", "b", "a", "b", "c")
        lifecycle = Lifecycle.from_lifecyclelist(cycle)
        self.assertEqual(cycle.name, lifecycle.name)

    def test_iteration(self):
        cycle = LifecycleList("cycle_name", "b", "a", "b", "c")
        lifecycle = Lifecycle.from_lifecyclelist(cycle)
        for i, state in enumerate(lifecycle):
            self.assertEqual(state, cycle[i])

    def test_get_default_state(self):
        state = get_default_state()
        self.assertEqual(state.name, "draft")

