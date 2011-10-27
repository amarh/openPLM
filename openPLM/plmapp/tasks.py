###########################
# adapted from https://github.com/mixcloud/django-celery-haystack-SearchIndex/
# by sdcooke

from functools import wraps

from django.db.models.loading import get_model

from haystack import site

from celery.task import task

def synchronized(cls):
    """Class decorator to synchronize execution of a task's run method.

    This prevents parallel execution of two instances of the same task within
    the same worker. If an instance of the same task is running in the same
    worker, the second invocation calls :meth:`~celery.task.base.Task.retry`
    is called instead of running the task.

    Note that this applies to the task class, so `@synchronized` should
    appear before `@task` or `@periodic_task` when tasks are defined with
    decorators.

    .. code-block:: python

        @synchronized
        @task
        def cleanup_database(**kwargs):
            logger = cleanup_database.get_logger(**kwargs)
            logger.warn("Task running...")
    """
    from multiprocessing import Lock
    cls.lock = Lock()
    cls.unsynchronized_run = cls.run
    @wraps(cls.unsynchronized_run)
    def wrapper(*args, **kwargs):
        if cls.lock.acquire(False):
            try:
                cls.unsynchronized_run(*args, **kwargs)
            finally:
                cls.lock.release()
        else:
            cls.retry(args=args, kwargs=kwargs)
    cls.run = wrapper
    return cls

@synchronized
@task(default_retry_delay = 5 * 60, max_retries = 1)
def update_index(app_name, model_name, pk, **kwargs):
    logger = update_index.get_logger(**kwargs)
    model_class = get_model(app_name, model_name)
    instance = model_class.objects.get(pk=pk)
    search_index = site.get_index(model_class)
    search_index.update_object(instance)

@task
def add(a, b):
    u"""Simple task, to test the queue ;-)"""
    return a + b

