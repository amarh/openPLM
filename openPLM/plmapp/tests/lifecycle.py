"""
This module contains test for lifecycle stuff.
"""

from django.test import TestCase

from openPLM.plmapp.utils import *
from openPLM.plmapp.models import *

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
        cycle = LifecycleList("cycle_name", "a", "b", "c")
        lifecycle = Lifecycle.from_lifecyclelist(cycle)
        self.assertEqual(cycle.name, lifecycle.name)

    def test_iteration(self):
        cycle = LifecycleList("cycle_name", "a", "b", "c")
        lifecycle = Lifecycle.from_lifecyclelist(cycle)
        for i, state in enumerate(lifecycle):
            self.assertEqual(state, cycle[i])

    def test_get_default_state(self):
        state = get_default_state()
        self.assertEqual(state.name, "draft")

