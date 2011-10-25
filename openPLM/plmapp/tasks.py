###########################
# adapted from https://github.com/mixcloud/django-celery-haystack-SearchIndex/
# by sdcooke

from django.db.models.loading import get_model

from haystack import site

from celery.task import task

@task(default_retry_delay = 5 * 60, max_retries = 1)
def update_index(app_name, model_name, pk, **kwargs):
    logger = update_index.get_logger(**kwargs)
    try:
        model_class = get_model(app_name, model_name)
        instance = model_class.objects.get(pk=pk)
        search_index = site.get_index(model_class)
        search_index.update_object(instance)
    except Exception, exc:
        logger.error(exc)
        update_index.retry([app_name, model_name, pk], kwargs, exc=exc)

@task
def add(a, b):
    u"""Simple task, to test the queue ;-)"""
    return a + b

