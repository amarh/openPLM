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
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Ce fichier fait parti d' openPLM.
#
#    Ce programme est un logiciel libre ; vous pouvez le redistribuer ou le
#    modifier suivant les termes de la “GNU General Public License” telle que
#    publiée par la Free Software Foundation : soit la version 3 de cette
#    licence, soit (à votre gré) toute version ultérieure.
#
#    Ce programme est distribué dans l’espoir qu’il vous sera utile, mais SANS
#    AUCUNE GARANTIE : sans même la garantie implicite de COMMERCIALISABILITÉ
#    ni d’ADÉQUATION À UN OBJECTIF PARTICULIER. Consultez la Licence Générale
#    Publique GNU pour plus de détails.
#
#    Vous devriez avoir reçu une copie de la Licence Générale Publique GNU avec
#    ce programme ; si ce n’est pas le cas, consultez :
#    <http://www.gnu.org/licenses/>.
#    
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

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

