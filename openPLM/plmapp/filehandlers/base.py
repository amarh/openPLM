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

class HandlersManager(object):
    """
    The HandlersManager has methods to register a :class:`FileHandler` with a
    type of file (an extension with the dot, like ``".pdf"``) and to get a
    :class:`FileHandler` from a typename.

    In all methods, *typename* should be in lowercase and start with a dot.
    """
    #: internal dict(typename->FileHanfler)
    _handlers = {}

    @classmethod
    def register(cls, typename, handler):
        """
        Registers the subclass of :class:`FileHandler` *handler* for *typename*.
        """
        l = cls._handlers.get(typename, [])
        l.append(handler)
        cls._handlers[typename] = l

    @classmethod
    def get_best_handler(cls, typename):
        """
        Gets the best :class:`FileHandler` associated to *typename*. The best
        handler is the first registered handler for *typename*.
        """
        return cls._handlers[typename][0]

    @classmethod
    def get_all_handlers(cls, typename):
        """
        Returns a list of all :class:`FileHander` associated to *typename*.
        """
        return list(cls._handlers[typename])

    @classmethod
    def get_all_supported_types(cls):
        """
        Returns all supported types (a list of string).
        """
        return cls._handlers.keys()

class FileHandler(object):
    """
    A FileHandler is an object which retrieves informations from a file and 
    exposes this informations through its attributes.

    :param path: path of the file that should be parsed
    :param filename: original filename of the file (with its extension).

    .. admonition:: Tips for developpers

        A FileHandler has the following protected attributes:

            .. attribute:: _path
                
                equals to *path*
            .. attribute:: _filename

                equals to *filename*
            .. attribute:: _is_valid

                True if the file has been successfully parsed. Set by default
                to False. You can use the methods :meth:`_set_valid` and
                :meth:`_set_invalid` to modify this attribute.

            .. automethod:: _set_valid
            .. automethod:: _set_invalid
    """

    def __init__(self, path, filename):
        self._path = path
        self._filename = filename
        self._is_valid = False

    def _set_valid(self):
        """ Sets the file as valid """
        self._is_valid = True

    def _set_invalid(self):
        """ Sets the file as invalid """
        self._is_valid = False
    
    def is_valid(self):
        """
        Returns True if the file has been successfully parsed.
        """
        return self._is_valid

    @property
    def attributes(self):
        """
        List of the attributes which have been successfully set.
        """
        return []

