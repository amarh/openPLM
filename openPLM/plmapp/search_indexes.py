from django.conf import settings
from django.db.models import signals
from django.db.models.loading import get_model

from haystack import site
from haystack import indexes
from haystack.indexes import *
from haystack.models import SearchResult

import openPLM.plmapp.models as models
from openPLM.plmapp.tasks import update_index

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

def remove_instance_from_index(instance):
    model_class = get_model(instance._meta.app_label, instance._meta.module_name)
    search_index = site.get_index(model_class)
    search_index.remove_object(instance)

class QueuedSearchIndex(indexes.SearchIndex):
    """
A ``SearchIndex`` subclass that enqueues updates for later processing.

Deletes are handled instantly since a reference, not the instance, is put on the queue. It would not be hard
to update this to handle deletes as well (with a delete task).
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
        remove_instance_from_index(instance)

##################

def set_template_name(index):
    for name, field in index.fields.iteritems():
        field.template_name = "search/indexes_%s.txt" % name


class QueuedModelSearchIndex(ModelSearchIndex, QueuedSearchIndex):
    pass

class UserIndex(ModelSearchIndex):
    class Meta:
        pass
    
    rendered = CharField(use_template=True, indexed=False)
    rendered_add = CharField(use_template=True, indexed=False)

set_template_name(UserIndex)
site.register(models.User, UserIndex)

class GroupIndex(ModelSearchIndex):
    class Meta:
        pass
    
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
       
        owner = CharField(model_attr="owner")
        creator = CharField(model_attr="creator")
        state = CharField(model_attr="state__name")
        lifecycle = CharField(model_attr="lifecycle__name")

        rendered = CharField(use_template=True, indexed=False)
        rendered_add = CharField(use_template=True, indexed=False)
       
        def prepare_owner(self, obj):
            return obj.owner.username

        def prepare_creator(self, obj):
            return obj.creator.username

        def index_queryset(self):
            if "type" in self.model.get_creation_fields():
                return self.model.objects.filter(type=self.key)
            else:
                return self.model.objects.all()
    set_template_name(ModelIndex)
    site.register(model, ModelIndex)

from subprocess import Popen, PIPE
import codecs
import os.path
text_files = set((".txt", ".test", ))

class DocumentFileIndex(QueuedModelSearchIndex):
    text = CharField(document=True, use_template=True)
    filename = CharField(model_attr='filename')
    file = CharField(model_attr='file')
    
    rendered = CharField(use_template=True, indexed=False)
    rendered_add = CharField(use_template=True, indexed=False)

    def prepare_file(self, obj):
        # if it is a text file, we can dump it
        # it's faster than launching a new process 
        path = obj.file.path
        name, ext = os.path.splitext(path)
        if ext.lower() in text_files:
            return codecs.open(path, encoding="utf-8", errors="ignore").read()
        else:
            p = Popen([settings.EXTRACTOR, path], stdout=PIPE, close_fds=True)
            return p.stdout.read()

site.register(models.DocumentFile, DocumentFileIndex)

