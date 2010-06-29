class ControllerError(StandardError):
    """
    Base class of exceptions raised by a
    :class:`~plmapp.controllers.PLMObjectController`.
    """
    pass

class RevisionError(ControllerError):
    """
    Exception raised when :meth:`~PLMObjectController.revise` is called but
    making a revision is not allowed.
    """
    pass

class LockError(ControllerError):
    """
    Exception raised when :meth:`~Document.lock` is called but the document
    is already locked.
    """
    pass

class UnlockError(ControllerError):
    """
    Exception raised when :meth:`~Document.unlock` is called but the document
    is unlocked or the user is not allowed to unlocked the document.
    """
    pass

class AddFileError(ControllerError):
    """
    Exception raised when an error occurs while adding a file to a document
    """
    pass

class DeleteFileError(ControllerError):
    """
    Exception raised when an error occurs while deleting a file to a document
    """

