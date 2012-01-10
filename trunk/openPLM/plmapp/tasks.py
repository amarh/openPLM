###########################
# adapted from https://github.com/mixcloud/django-celery-haystack-SearchIndex/
# by sdcooke

from functools import wraps

from django.db.models.loading import get_model

from celery.task import task

def synchronized(cls=None, lock=None):
    """Class decorator to synchronize execution of a task's run method.

    This prevents parallel execution of two instances of the same task within
    the same worker. If an instance of the same task is running in the same
    worker, the second invocation blocks until the first one completes.

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
    cls.lock = lock or Lock()
    cls.unsynchronized_run = cls.run
    @wraps(cls.unsynchronized_run)
    def wrapper(*args, **kwargs):
        with cls.lock:
            cls.unsynchronized_run(*args, **kwargs)
    cls.run = wrapper
    return cls

@synchronized
@task(default_retry_delay = 60, max_retries = 10)
def update_index(app_name, model_name, pk, **kwargs):
    from haystack import site
    import openPLM.plmapp.search_indexes

    model_class = get_model(app_name, model_name)
    instance = model_class.objects.select_related(depth=1).get(pk=pk)
    search_index = site.get_index(model_class)
    search_index.update_object(instance)

@task(default_retry_delay = 60, max_retries = 10)
def update_indexes(instances):
    from haystack import site
    import openPLM.plmapp.search_indexes

    for app_name, model_name, pk in instances:
        model_class = get_model(app_name, model_name)
        instance = model_class.objects.select_related(depth=1).get(pk=pk)
        search_index = site.get_index(model_class)
        search_index.update_object(instance)
update_indexes = synchronized(update_indexes, update_index.lock)

@task
def add(a, b):
    u"""Simple task, to test the queue ;-)"""
    return a + b

