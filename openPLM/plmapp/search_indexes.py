import datetime

from django.conf import settings
from django.db.models import signals

from haystack import site
from haystack import indexes
from haystack.indexes import *
from haystack.models import SearchResult
from haystack.utils import get_identifier

import openPLM.plmapp.models as models
from openPLM.plmapp.tasks import update_index, remove_index

# just a hack to prevent a KeyError
def get_state(self):
    ret_dict = self.__dict__.copy()
    if 'searchsite' in ret_dict:
        del(ret_dict['searchsite'])
    del(ret_dict['log'])
    return ret_dict
SearchResult.__getstate__ = get_state

###########################
# from https://github.com/mixcloud/django-celery-haystack-SearchIndex/
# by sdcooke

class QueuedSearchIndex(indexes.SearchIndex):
    """
    A ``SearchIndex`` subclass that enqueues updates for later processing.
    """
    # We override the built-in _setup_* methods to connect the enqueuing operation.
    def _setup_save(self, model):
        signals.post_save.connect(self.enqueue_save, sender=model)

    def _setup_delete(self, model):
        signals.post_delete.connect(self.enqueue_delete, sender=model)

    def _teardown_save(self, model):
        signals.post_save.disconnect(self.enqueue_save, sender=model)

    def _teardown_delete(self, model):
        signals.post_delete.disconnect(self.enqueue_delete, sender=model)

    def enqueue_save(self, instance, **kwargs):
        if not getattr(instance, "no_index", False):
            update_index.delay(instance._meta.app_label,
                    instance._meta.module_name, instance._get_pk_val())

    def enqueue_delete(self, instance, **kwargs):
        remove_index.delay(instance._meta.app_label,
                instance._meta.module_name, get_identifier(instance))

##################

def set_template_name(index):
    for name, field in index.fields.iteritems():
        field.template_name = "search/indexes_%s.txt" % name


class QueuedModelSearchIndex(ModelSearchIndex, QueuedSearchIndex):
    pass


def prepare_date(date):
    """
    Returns a date rounded to the day.
    """
    return datetime.datetime(date.year, date.month, date.day)

class UserIndex(ModelSearchIndex):
    class Meta:
        fields = ("username", "last_name", "first_name", "email")

    ctime = DateTimeField(model_attr="date_joined")
    
    rendered = CharField(use_template=True, indexed=False)
    rendered_add = CharField(use_template=True, indexed=False)
    
    def prepare_ctime(self, obj):
        return prepare_date(obj.date_joined)


set_template_name(UserIndex)
site.register(models.User, UserIndex)

class GroupIndex(ModelSearchIndex):
    class Meta:
        fields = ("name", "description", "owner", "creator")

    owner = CharField(model_attr="owner__username")
    creator = CharField(model_attr="creator__username")

    ctime = DateTimeField(model_attr="ctime")
    mtime = DateTimeField(model_attr="mtime")

    def prepare_ctime(self, obj):
        return prepare_date(obj.ctime)

    def prepare_mtime(self, obj):
        return prepare_date(obj.mtime)


    rendered = CharField(use_template=True, indexed=False)
    rendered_add = CharField(use_template=True, indexed=False)

set_template_name(GroupIndex)
site.register(models.GroupInfo, GroupIndex)



for key, model in models.get_all_plmobjects().iteritems():
    if model == models.GroupInfo:
        continue
    class ModelIndex(QueuedModelSearchIndex):
        model = model
        key = key
        class Meta:
            fields = set(model.get_creation_fields())
            fields.update(model.get_modification_fields())

        owner = CharField(model_attr="owner__username")
        creator = CharField(model_attr="creator__username")
        state = CharField(model_attr="state__name")
        lifecycle = CharField(model_attr="lifecycle__name")

        ctime = DateTimeField(model_attr="ctime")
        mtime = DateTimeField(model_attr="mtime")

        rendered = CharField(use_template=True, indexed=False)
        rendered_add = CharField(use_template=True, indexed=False)
       
        def prepare_ctime(self, obj):
            return prepare_date(obj.ctime)

        def prepare_mtime(self, obj):
            return prepare_date(obj.mtime)

        def index_queryset(self):
            return self.model.objects.filter(type=self.key)

    set_template_name(ModelIndex)
    site.register(model, ModelIndex)

from subprocess import Popen, PIPE
import codecs
import os.path
text_files = set((".txt", ".test", ))

class DocumentFileIndex(QueuedModelSearchIndex):
    text = CharField(document=True, use_template=True)
    filename = CharField(model_attr='filename')
    file = CharField(model_attr='file', stored=False)
    
    rendered = CharField(use_template=True, indexed=False)
    rendered_add = CharField(use_template=True, indexed=False)

    def prepare_file(self, obj):
        # if it is a text file, we can dump it
        # it's faster than launching a new process 
        path = obj.file.path
        name, ext = os.path.splitext(path)
        if ext.lower() in text_files:
            content = codecs.open(path, encoding="utf-8", errors="ignore").read()
        else:
            p = Popen([settings.EXTRACTOR, path], stdout=PIPE, close_fds=True)
            content = p.stdout.read()
        return content

site.register(models.DocumentFile, DocumentFileIndex)

