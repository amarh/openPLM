###########################
# adapted from https://github.com/mixcloud/django-celery-haystack-SearchIndex/
# by sdcooke

from functools import wraps

from django.db.models.loading import get_model

import openPLM.plmapp.mail
import openPLM.plmapp.thumbnailers

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
    # cls.__class__.__call__ is set by recent versions of celery (2.5)
    def call(self, *args, **kwargs):
        return wrapper(*args, **kwargs)
    cls.__class__.__call__ = call
    return cls


_plmobject_fields = ("owner", "creator", "group", "state", "lifecycle")
_documentfile_fields =  ("document", ) + tuple("document__" + f for f in _plmobject_fields)
def _get_related_fields(model_class):
    from openPLM.plmapp import models
    if issubclass(model_class, models.PLMObject):
        return _plmobject_fields
    elif issubclass(model_class, models.GroupInfo):
        return ("owner", "creator")
    elif issubclass(model_class, models.DocumentFile):
        return _documentfile_fields
    return ()

@synchronized
@task(name="openPLM.plmapp.tasks.update_index",
      default_retry_delay=60, max_retries=10)
def update_index(app_name, model_name, pk, fast_reindex=False, **kwargs):
    from haystack import site
    import openPLM.plmapp.search_indexes

    model_class = get_model(app_name, model_name)
    fields = _get_related_fields(model_class)
    if fields:
        instance = model_class.objects.select_related(*fields).get(pk=pk)
    else:
        instance = model_class.objects.get(pk=pk)
    if fast_reindex:
        instance.fast_reindex = True
    search_index = site.get_index(model_class)
    search_index.update_object(instance)

@task(name="openPLM.plmapp.tasks.update_indexes",
      default_retry_delay=60, max_retries=10)
def update_indexes(instances, fast_reindex=False):
    from haystack import site
    import openPLM.plmapp.search_indexes

    for app_name, model_name, pk in instances:
        model_class = get_model(app_name, model_name)
        fields = _get_related_fields(model_class)
        if fields:
            instance = model_class.objects.select_related(*fields).get(pk=pk)
        else:
            instance = model_class.objects.get(pk=pk)
        if fast_reindex:
            instance.fast_reindex = True
        search_index = site.get_index(model_class)
        search_index.update_object(instance)
update_indexes = synchronized(update_indexes, update_index.lock)


@task(name="openPLM.plmapp.tasks.remove_index",
      default_retry_delay=60, max_retries=10)
def remove_index(app_name, model_name, identifier):
    from haystack import site
    import openPLM.plmapp.search_indexes

    model_class = get_model(app_name, model_name)
    search_index = site.get_index(model_class)
    search_index.remove_object(identifier)
remove_index = synchronized(remove_index, update_index.lock)


@task
def add(a, b):
    u"""Simple task, to test the queue ;-)"""
    return a + b

