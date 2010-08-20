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
    is unlocked or the user is not allowed to unlocked the document.
    """

class AddFileError(ControllerError):
    """
    Exception raised when an error occurs while adding a file to a document
    """

class DeleteFileError(ControllerError):
    """
    Exception raised when an error occurs while deleting a file to a document
    """

class PermissionError(ControllerError):
    """
    Exception raised when an user attempt to made an unauthorized action
    """

class PromotionError(ControllerError):
    """
    Exception raised when an user attempt to promote anon-promotable object
    """

