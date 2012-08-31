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


if __name__ == "__main__":
    import doctest
    doctest.testmod()
