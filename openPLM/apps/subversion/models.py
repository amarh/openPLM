from django.db import models
from django.contrib import admin
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_noop
from django.utils.translation import ugettext_lazy as _

import pysvn

import openPLM.plmapp.exceptions as exc
from openPLM.plmapp.models import Document
from openPLM.plmapp.controllers import DocumentController

# Regular expression from pysiso8601
date_rx = (r"(?P<year>[0-9]{4})(-(?P<month>[0-9]{1,2})(-(?P<day>[0-9]{1,2})"
    r"((?P<separator>.)(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2})(:(?P<second>[0-9]{2})(\.(?P<fraction>[0-9]+))?)?"
    r"(?P<timezone>Z|(([-+])([0-9]{2}):([0-9]{2})))?)?)?)?")

revision_rx = r'^\d+|HEAD|\{(?:%s)\}$' % date_rx
revision_validator = RegexValidator(revision_rx,
        message=ugettext_noop(u"Valid value are HEAD, a number or a date between brackets"))

class SubversionRepository(Document):

    ACCEPT_FILES = False

    repository_uri = models.CharField(verbose_name=_("repository uri"),max_length=250, blank=False, null=False)
    svn_revision = models.CharField(verbose_name=_("svn revision"),max_length=50, blank=False, null=False,
            default="HEAD", validators=[revision_validator])
    issue_tracking_system = models.CharField(verbose_name=_("issue tracking system"),max_length=250, blank=True,
            null=False)

    @property
    def attributes(self):
        attrs = ["repository_uri", "svn_revision", "issue_tracking_system"]
        return super(SubversionRepository, self).attributes + attrs

    def is_promotable(self):
        # a SubversionRepository has no files, so we do not checks
        # if it has a locked file
        return self._is_promotable()

    @property
    def menu_items(self):
        return super(SubversionRepository, self).menu_items + ["logs"]

    @property
    def checkout_cmd(self):
        return u"svn co -r '%s' '%s'"  % (self.svn_revision.strip(),
                self.repository_uri.strip())

    @property
    def export_cmd(self):
        return u"svn export -r '%s' '%s'"  % (self.svn_revision.strip(),
                self.repository_uri.strip())

admin.site.register(SubversionRepository)


def parse_revision(rev_string):
    """Convert *rev_string* into a :class:`pysvn.Revision` object."""

    if rev_string.lower() == 'head':
        return pysvn.Revision( pysvn.opt_revision_kind.head )
    if rev_string[0] == '{' and rev_string[-1] == '}':
        # does not support date conversion
        raise ValueError()
    try:
        return pysvn.Revision( pysvn.opt_revision_kind.number, int(rev_string) )
    except ValueError:
        raise


class SubversionRepositoryController(DocumentController):

    def lock(self, doc_file):
        raise exc.LockError()

    def unlock(self, doc_file):
        raise exc.UnlockErrot()

    def add_file(self, f, update_attributes=True):
        raise exc.AddFileError()

    def delete_file(self, doc_file):
        raise exc.DeleteFileError()

    def promote(self, *args, **kwargs):
        r = super(SubversionRepositoryController, self).promote(*args, **kwargs)
        if self.state == self.lifecycle.official_state and\
                self.svn_revision == "HEAD":
            # try to retreive the revision number and replace svn_revision
            # by it
            obj = self.object
            try:
                revision = parse_revision(obj.svn_revision)
                uri = obj.repository_uri
                if uri.startswith("file://") or uri.startswith("/"):
                    raise ValueError()
                client = pysvn.Client()
                if not client.is_url(uri):
                    raise ValueError()
                infos = client.info2(uri, revision=revision, recurse=False)
                rev = str(infos[0][1]["rev"].number)
                self.object.svn_revision = rev
                self.object.save()
            except (StandardError, pysvn.ClientError):
                pass
        return r

