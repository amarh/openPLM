############################################################################
# openPLM - open source PLM
# Copyright 2012 LinObject SAS
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
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

class DecomposersManager(object):
    """
    The DecomposersManager has methods to register a :class:`Decomposer`
    (a class helping to decompose a part) and to get a decomposition
    message that is displayed on the BOM page of a part.
    """
    _decomposers = []

    @classmethod
    def register(cls, decomposer):
        """
        Registers *decomposer*.
        """
        cls._decomposers.append(decomposer)
    
    @classmethod
    def count(cls):
        """
        Returns the number of registered decomposers.
        """
        return len(cls._decomposers)

    @classmethod
    def get_decomposition_message(cls, part):
        """
        Returns a decomposition message to decompose *part*.

        Returns an empty string if no decomposer can decompose *part*.
        """
        for decomposer in cls._decomposers:
            d = decomposer(part)
            if d.is_decomposable():
                return d.get_message()
        return ""

    @classmethod
    def is_decomposable(cls, part, msg=False):
        """
        Returns True if *part* is decomposable.
        """
        for decomposer in cls._decomposers:
            d = decomposer(part)
            if d.is_decomposable(msg):
                return True
        return False
   
    @classmethod
    def get_decomposable_parts(cls, part_ids):
        """
        Returns all part of *part_ids* (an iterable of part ids) that
        are decomposable by the registered decomposers.
        """
        decomposable = set()
        not_decomposable = set(part_ids)
        for decomposer in cls._decomposers:
            if not not_decomposable:
                break
            d = decomposer(None)
            s = d.get_decomposable_parts(not_decomposable)
            decomposable.update(s)
            not_decomposable.difference_update(s)
        return decomposable


class Decomposer(object):
    """
    Interface of a decomposer. A decomposer is initialized with a part
    and has two methods: :meth:`is_decomposable` and :meth:`get_message`

    The default constructor sets the ``part`` attribute with the given part.
    """

    def __init__(self, part):
        self.part = part

    def is_decomposable(self, msg=True):
        """
        Returns True if the part is decomposable.
        """
        return False

    def get_message(self):
        """
        Returns a message (in html) that is displayed if the part is decomposable.

        The returned message should contains a link to decompose the part and should
        be explicit.
        """
        return ""

    def get_decomposable_parts(self, part_ids):
        """
        Returns all part of *part_ids* (an iterable of part ids) that
        are decomposable by this decomposer.
        """
        return [p for p in part_ids if type(self)(p).is_decomposable(False)]

