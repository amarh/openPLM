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
This module contains a class that can be used to simplify the usage of
:class:`.Lifecycle` and :class:`.LifecycleStates`.

.. seealso::

    :meth:`.Lifecycle.to_states_list`
        Method to convert a :class:`.Lifecycle` into a :class:`LifecycleList`

    :meth:`.Lifecycle.from_lifecyclelist`.
        Method to convert a :class:`LifecycleList` into a :class:`.Lifecycle` 

Example::

    _lifecycles_list = [
        ("draft", "official", "deprecated"),
        ("draft", "official"),
    ]

    lifecycles = dict()
    for cycles in _lifecycles_list:
        name = "->".join(cycles) 
        lifecycles[name] = LifecycleList(name, "official", *cycles)
"""

try:
    import pygraphviz as pgv
except ImportError:
    print "ImportError : Please install pygraphviz."
    print "It's used to generate graphes from lifecycle"


class LifecycleList(list):
    u"""
    Object which represents a lifecycle as a list of string.

    This class inherits from list, so you can use all list methods.

    For example::

        >>> cycle = LifecycleList("MyCycle", "b")
        >>> cycle.extend(["a", "b", "c"])
        >>> cycle[0]
        'a'

    .. attribute:: name

        name of the lifecycle
    .. attribute:: official_state
        
        name of the official state (must be in the list of states)
    """
    def __init__(self, name, official_state, *args):
        super(LifecycleList, self).__init__(self)
        self.name = name
        self.official_state = official_state
        self.extend(args)

    def next_state(self, state):
        u"""
        Returns the next state of *state*

        Raises :exc:`ValueError` if *state* is not in the list and :exc:`IndexError`
        if *state* is the last state.
        
        Example::

            >>> cycle = LifecycleList("MyCycle", "b", "a", "b", "c", "d")
            >>> cycle.next_state("b")
            'c'
            >>> cycle.next_state("d")
            Traceback (most recent call last):
                ...
            IndexError: list index out of range

            >>> cycle.next_state("z")
            Traceback (most recent call last):
                ...
            ValueError: list.index(x): x not in list

        """
        index = self.index(state)
        return self[index + 1]
    
    def previous_state(self, state):
        u"""
        Returns the previous state of *state*

        Raises :exc:`ValueError` if *state* is not in the list and :exc:`IndexError`
        if *state* is the first state.

        Example::

            >>> cycle = LifecycleList("MyCycle", "b", "a", "b", "c", "d")
            >>> cycle.previous_state("b")
            'a'
            >>> cycle.previous_state("a")
            Traceback (most recent call last):
                ...
            IndexError

            >>> cycle.previous_state("z")
            Traceback (most recent call last):
                ...
            ValueError: list.index(x): x not in list


        """
        index = self.index(state)
        if index - 1 < 0:
            raise IndexError()
        return self[index - 1]

    def draw_graph(self, current_state, output_path,
                   normal_color="#7a7af8", current_color="#0808fa"):
        u"""
        Draws a graph (with pygraphviz) of the lifecycle. 

        :param current_state: current state to highlight, may be empty
        :type cuurent_state: str
        :param output_path: pathname of the generated png
        :type output_path: str
        :param normal_color: fill color of normal states
        :type normal_color: an html color (like ``cyan`` or ``#110011``)
        :param current_color: fill color of current state
        :type current_color: an html color (like ``cyan`` or ``#110011``)

        """
        graph = pgv.AGraph(directed=True)
        graph.graph_attr["rankdir"] = "LR"
        graph.graph_attr["bgcolor"] = "#00000000" # transparent
        graph.node_attr["style"] = "filled"
        graph.node_attr["fillcolor"] = normal_color
        graph.add_edges_from(zip(self, self[1:]))
        if current_state:
            node = graph.get_node(current_state)
            node.attr["fillcolor"] = current_color
        graph.draw(path=output_path, format="png", prog="dot")

if __name__ == "__main__":
    import doctest
    doctest.testmod()
