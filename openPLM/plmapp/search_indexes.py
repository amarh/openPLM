import datetime
import codecs
import os.path
from subprocess import Popen, PIPE

from django.conf import settings
from django.db.models import signals

from haystack import site
from haystack import indexes
from haystack.indexes import *
from haystack.models import SearchResult
from haystack.query import SearchQuerySet
from haystack.utils import get_identifier

import openPLM.plmapp.models as models
from openPLM.plmapp.tasks import update_index, remove_index
from openPLM.plmapp.filters import plaintext

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

    def prepare_description(self, obj):
        return plaintext(obj.description, obj)

    rendered = CharField(use_template=True, indexed=False)
    rendered_add = CharField(use_template=True, indexed=False)

set_template_name(GroupIndex)
site.register(models.GroupInfo, GroupIndex)

indexed = site.get_indexed_models()

def get_state_class(obj):
    if obj.is_cancelled:
        cls = "cancelled"
    elif obj.is_official:
        cls = "official"
    elif obj.is_draft:
        cls = "draft"
    elif obj.is_deprecated:
        cls = "deprecated"
    else:
        cls = "proposed"
    return "state-" + cls

for key, model in models.get_all_plmobjects().iteritems():
    if model in indexed:
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
        state_class = CharField()
        if "group" in Meta.fields:
            group= CharField(model_attr="group__name")

        ctime = DateTimeField(model_attr="ctime")
        mtime = DateTimeField(model_attr="mtime")

        rendered = CharField(use_template=True, indexed=False)
        rendered_add = CharField(use_template=True, indexed=False)

        def prepare(self, object):
            self.prepared_data = QueuedSearchIndex.prepare(self, object)
            meta_fields = object._meta.get_all_field_names()
            for f in self.Meta.fields:
                if f in meta_fields and f in self.prepared_data:
                    if getattr(object._meta.get_field(f), "richtext", False):
                        self.prepared_data[f] = plaintext(self.prepared_data[f], object)
            return self.prepared_data

        def prepare_ctime(self, obj):
            return prepare_date(obj.ctime)

        def prepare_mtime(self, obj):
            return prepare_date(obj.mtime)

        def prepare_state_class(self, obj):
            return get_state_class(obj)

        def index_queryset(self):
            if "type" in self.model._meta.get_all_field_names():
                return self.model.objects.filter(type=self.key)
            else:
                return self.model.objects.all()

    set_template_name(ModelIndex)
    site.register(model, ModelIndex)

text_files = set((".txt", ".test", ))

class DocumentFileIndex(QueuedModelSearchIndex):
    text = CharField(document=True, use_template=True)
    filename = CharField(model_attr='filename')
    file = CharField(model_attr='file', stored=False)
    group = CharField(model_attr="document__group__name")
    document_id = IntegerField(model_attr="document__id", indexed=False)
    state = CharField(model_attr="document__state__name")
    lifecycle = CharField(model_attr="document__lifecycle__name")
    state_class = CharField()

    rendered = CharField(use_template=True, indexed=False)
    rendered_add = CharField(use_template=True, indexed=False)

    def prepare_state_class(self, obj):
        return get_state_class(obj.document)

    def prepare_file(self, obj):
        if getattr(obj, "fast_reindex", False):
            rset = SearchQuerySet().filter(id=get_identifier(obj))
            if rset:
                return rset[0].file

        # if it is a text file, we can dump it
        # it's faster than launching a new process
        path = obj.file.path
        name, ext = os.path.splitext(path)
        size = 1024*1024 # 1Mo
        if ext.lower() in text_files:
            content = codecs.open(path, encoding="utf-8", errors="ignore").read(size)
        else:
            p = Popen([settings.EXTRACTOR, path], stdout=PIPE, close_fds=True)
            content = p.stdout.read(size).decode("utf-8", "ignore")
        return content

    def index_queryset(self):
        return models.DocumentFile.objects.filter(deprecated=False)

    def should_update(self, instance, **kwargs):
        if instance.deprecated:
            # this method is called by a task, so we should not acquire a lock
            # or delay this deletion
            self.remove_object(instance)
        return not instance.deprecated

site.register(models.DocumentFile, DocumentFileIndex)

