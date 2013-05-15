###########################
# adapted from https://github.com/mixcloud/django-celery-haystack-SearchIndex/
# by sdcooke

from functools import wraps

from django.db.models.loading import get_model

import openPLM.plmapp.mail
import openPLM.plmapp.thumbnailers

from djcelery_transactions import task

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


_plmobject_fields = ("owner__username", "creator__username", "group__name", "state", "lifecycle")
_documentfile_fields =  ("document", ) + tuple("document__" + f for f in _plmobject_fields)
_deffered_user_fields = [
 'owner__password', 'owner__last_login', 'owner__is_superuser',
 'owner__first_name', 'owner__last_name', 'owner__email', 'owner__is_staff', 'owner__is_active',
 'owner__date_joined',
 'creator__password', 'creator__last_login', 'creator__is_superuser', 'creator__first_name',
 'creator__last_name', 'creator__email', 'creator__is_staff', 'creator__is_active',
 'creator__date_joined']

def _get_manager(model_class):
    from openPLM.plmapp import models
    manager = model_class.objects
    if issubclass(model_class, models.PLMObject):
        return manager.select_related(*_plmobject_fields).defer(*_deffered_user_fields)
    elif issubclass(model_class, models.GroupInfo):
        return manager.select_related(*("owner", "creator")).defer(*_deffered_user_fields)
    elif issubclass(model_class, models.DocumentFile):
        return manager.select_related(*_documentfile_fields)
    return manager


@synchronized
@task(name="openPLM.plmapp.tasks.update_index",
      default_retry_delay=60, max_retries=10)
def update_index(app_name, model_name, pk, fast_reindex=False, **kwargs):
    from haystack import site
    import openPLM.plmapp.search_indexes

    model_class = get_model(app_name, model_name)
    manager = _get_manager(model_class)
    instance = manager.get(pk=pk)
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
        manager = _get_manager(model_class)
        instance = manager.get(pk=pk)
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

