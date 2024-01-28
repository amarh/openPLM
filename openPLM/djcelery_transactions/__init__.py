from celery import Celery
#from celery.signals import after_commit, after_rollback
from functools import partial
import threading
from django.db import transaction
from celery.signals import task_postrun, task_prerun

# Celery configuration
app = Celery('djcelery_transactions')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Thread-local data (task queue).
_thread_data = threading.local()


def _get_task_queue():
    """Returns the calling thread's task queue."""
    return _thread_data.__dict__.setdefault("task_queue", [])


class PostTransactionTask(app.Task):
    """A task whose execution is delayed until after the current transaction.

    The task's fate depends on the outcome of the current transaction. If it's
    committed or no changes are made in the transaction block, the task is sent
    as normal. If it's rolled back, the task is discarded.

    If transactions aren't being managed when ``apply_async()`` is called (if
    you're in the Django shell, for example) or the ``after_transaction``
    keyword argument is ``False``, the task will be sent immediately.

    A replacement decorator is provided:

    .. code-block:: python

        from djcelery_transactions import task

        @task
        def example(pk):
            print("Hooray, the transaction has been committed!")
    """

    abstract = True

    @classmethod
    def original_apply_async(cls, *args, **kwargs):
        """Shortcut method to reach the real implementation
        of celery.Task.apply_async
        """
        return super(PostTransactionTask, cls).apply_async(*args, **kwargs)

    @classmethod
    def apply_async(cls, *args, **kwargs):
        # Delay the task unless the client requested otherwise or transactions
        # aren't being managed (i.e. the signal handlers won't send the task).
        if not app.conf.CELERY_ALWAYS_EAGER:
            if not getattr(transaction, 'in_transaction', False):
                # Always mark the transaction as dirty
                # because we push tasks in the queue that must be fired or discarded
                if 'using' in kwargs:
                    setattr(transaction, 'in_transaction', True)
                    after_rollback.connect(_discard_tasks)
                else:
                    setattr(transaction, 'in_transaction', True)
                    after_commit.connect(_send_tasks)
            _get_task_queue().append((cls, args, kwargs))
        else:
            return cls.original_apply_async(*args, **kwargs)


def _discard_tasks(**kwargs):
    """Discards all delayed Celery tasks.

    Called after a transaction is rolled back."""
    _get_task_queue()[:] = []


def _send_tasks(**kwargs):
    """Sends all delayed Celery tasks.

    Called after a transaction is committed or we leave a transaction
    management block in which no changes were made (effectively a commit).
    """
    queue = _get_task_queue()
    while queue:
        cls, args, kwargs = queue.pop(0)
        cls.original_apply_async(*args, **kwargs)


# A replacement decorator.
task = partial(app.task, base=PostTransactionTask)
