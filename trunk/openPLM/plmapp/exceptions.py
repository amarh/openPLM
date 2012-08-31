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
This modules contains exceptions that may be raised by a controller
:class:`.PLMObjectController` and :class:`.UserController`.

All exceptions defined here derive from :exc:`ControllerError`
(except of course :exc:`ControllerError`)
"""

class ControllerError(StandardError):
    """
    Base class of exceptions raised by a
    :class:`~plmapp.controllers.PLMObjectController`.
    """

class RevisionError(ControllerError):
    """
    Exception raised when :meth:`~PLMObjectController.revise` is called but
    making a revision is not allowed.
    """

class LockError(ControllerError):
    """
    Exception raised when :meth:`~Document.lock` is called but the document
    is already locked.
    """

class UnlockError(ControllerError):
    """
    Exception raised when :meth:`~Document.unlock` is called but the document
    is unlocked or the user is not allowed to unlock the document.
    """

class AddFileError(ControllerError):
    """
    Exception raised when an error occurs while adding a file to a document
    """

class DeleteFileError(ControllerError):
    """
    Exception raised when an error occurs while deleting a file from a document
    """

class PermissionError(ControllerError):
    """
    Exception raised when a user attempt to made an unauthorized action
    """

class PromotionError(ControllerError):
    """
    Exception raised when a user attempt to promote a non-promotable object
    """

