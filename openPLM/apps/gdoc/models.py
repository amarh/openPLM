

from oauth2client.django_orm import Storage
from oauth2client.django_orm import FlowField
from oauth2client.django_orm import CredentialsField

from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

from south.modelsinspector import add_introspection_rules

import openPLM.plmapp.exceptions as exc
from openPLM.plmapp.models import Document
from openPLM.plmapp.controllers import DocumentController

from openPLM.apps.gdoc.gutils import get_gclient


class FlowModel(models.Model):
    """
    Short live model used by OAuth2 authentication process.
    """
    id = models.ForeignKey(User, primary_key=True)
    flow = FlowField()


class CredentialsModel(models.Model):
    """
    Model that stores an OAuth2 credential.
    """
    id = models.ForeignKey(User, primary_key=True)
    credential = CredentialsField()

add_introspection_rules([], ["^oauth2client\.django_orm\.CredentialsField"])
add_introspection_rules([], ["^oauth2client\.django_orm\.FlowField"])

admin.site.register(CredentialsModel)
admin.site.register(FlowModel)


class GoogleDocument(Document):

    ACCEPT_FILES = False

    resource_id = models.CharField(max_length=200, blank=False, null=False)

    @property
    def attributes(self):
        return super(GoogleDocument, self).attributes + ["resource_id"]

    @classmethod
    def get_creation_fields(cls):
        # remove the "name" field
        return super(GoogleDocument, cls).get_creation_fields()[1:]

    @classmethod
    def excluded_creation_fields(cls):
        return super(GoogleDocument, cls).excluded_creation_fields() + \
                ['name', 'resource_id']

    def is_promotable(self):
        # a GoogleDocument has no files, so we do not checks
        # if it has a locked file
        return self._is_promotable()

admin.site.register(GoogleDocument)

class InvalidCredentialException(StandardError):
    pass

class GoogleDocumentController(DocumentController):

    __slots__ = DocumentController.__slots__ + ("client", )

    def init_gclient(self):
        storage = Storage(CredentialsModel, 'id', self._user, 'credential')
        credential = storage.get()
        if credential is None or credential.invalid == True:
            raise InvalidCredentialException()
        else:
            self.client = get_gclient(credential)

    def revise(self, new_revision, *args, **kwargs):
        rev = super(GoogleDocumentController, self).revise(new_revision, *args, **kwargs)
        # try to copy the document in google docs
        if not hasattr(self, "client"):
            # TODO errors
            try:
                self.init_gclient()
            except InvalidCredentialException:
                return
        entry = self.client.get_resource_by_id(self.resource_id)
        copy = self.client.copy_resource(entry, self.name + " - " + new_revision)
        rev.object.resource_id = copy.resource_id.text
        rev.object.save()

    def lock(self, doc_file):
        raise exc.LockError()

    def unlock(self, doc_file):
        raise exc.UnlockErrot()

    def add_file(self, f, update_attributes=True):
        raise exc.AddFileError()

    def delete_file(self, doc_file):
        raise exc.DeleteFileError()

    def clone(self, *args, **kwargs):
        c = super(GoogleDocumentController, self).clone(*args, **kwargs)
        # try to copy the document in google docs
        if not hasattr(self, "client"):
            # TODO errors
            try:
                self.init_gclient()
            except InvalidCredentialException:
                return
        entry = self.client.get_resource_by_id(self.resource_id)
        copy = self.client.copy_resource(entry, self.name)
        c.object.resource_id = copy.resource_id.text
        c.object.name = self.name
        c.object.save()
        return c


