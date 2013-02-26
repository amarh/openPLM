# encoding: utf-8
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import DataMigration
from django.db import models

@property
def is_proposed(self):
    """
    True if the object is in a state prior to the official state
    but not draft.
    """
    if self.is_cancelled or self.is_draft:
        return False
    lcs = self.lifecycle.lifecyclestates_set.only("rank")
    current_rank = lcs.get(state=self.state).rank
    official_rank = lcs.get(state=self.lifecycle.official_state).rank
    return current_rank < official_rank

@property
def is_cancelled(self):
    """ True if the object is cancelled. """
    return self.lifecycle.name == "cancelled"

@property
def is_deprecated(self):
    """ True if the object is deprecated. """
    return not self.is_cancelled and self.state == self.lifecyle.lifecyclestates_set.order_by('-rank')[0].state


@property
def is_official(self):
    u"Returns True if object is official."""
    return not self.is_cancelled and self.state == self.lifecycle.official_state

@property
def is_draft(self):
    u""" Returns True if the object is a draft. """
    return not self.is_cancelled and self.state == self.lifecycle.lifecyclestates_set.order_by('rank')[0].state

class Migration(DataMigration):

    def forwards(self, orm):
        # creating a statehistory for each plmobject
        # the value is not really correct, but it is difficult to get valid data
        # if it was easy, we would not need this new table
        orm.PLMObject.is_draft = is_draft
        orm.PLMObject.is_proposed = is_proposed
        orm.PLMObject.is_cancelled = is_cancelled
        orm.PLMObject.is_official = is_official
        orm.PLMObject.is_deprecated = is_deprecated
        DRAFT, PROPOSED, OFFICIAL, DEPRECATED, CANCELLED = range(5)
        for obj in orm.PLMobject.objects.all():
            if obj.is_draft:
                category = DRAFT
            elif obj.is_proposed:
                category = PROPOSED
            elif obj.is_official:
                category = OFFICIAL
            elif obj.is_proposed:
                category = DEPRECATED
            else:
                category = CANCELLED
            orm.StateHistory.objects.create(start_time=obj.ctime, end_time=None,
                    state=obj.state, lifecycle=obj.lifecycle, plmobject=obj,
                    state_category=category)


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'plmapp.delegationlink': {
            'Meta': {'unique_together': "(('delegator', 'delegatee', 'role'),)", 'object_name': 'DelegationLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delegatee': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'delegationlink_delegatee'", 'to': "orm['auth.User']"}),
            'delegator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'delegationlink_delegator'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'})
        },
        'plmapp.document': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'Document', '_ormbases': ['plmapp.PLMObject']},
            'plmobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.PLMObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        'plmapp.documentfile': {
            'Meta': {'object_name': 'DocumentFile'},
            'deprecated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.Document']"}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'locker': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'size': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'plmapp.documentpartlink': {
            'Meta': {'unique_together': "(('document', 'part'),)", 'object_name': 'DocumentPartLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documentpartlink_document'", 'to': "orm['plmapp.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'part': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documentpartlink_part'", 'to': "orm['plmapp.Part']"})
        },
        'plmapp.grouphistory': {
            'Meta': {'object_name': 'GroupHistory'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'grouphistory_user'", 'to': "orm['auth.User']"})
        },
        'plmapp.groupinfo': {
            'Meta': {'object_name': 'GroupInfo', '_ormbases': ['auth.Group']},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groupinfo_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 19, 15, 31, 46, 663508)'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groupinfo_owner'", 'to': "orm['auth.User']"})
        },
        'plmapp.history': {
            'Meta': {'object_name': 'History'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.PLMObject']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'history_user'", 'to': "orm['auth.User']"})
        },
        'plmapp.invitation': {
            'Meta': {'object_name': 'Invitation'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 19, 15, 31, 46, 665182)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.GroupInfo']"}),
            'guest': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitation_inv_guest'", 'to': "orm['auth.User']"}),
            'guest_asked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitation_inv_owner'", 'to': "orm['auth.User']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'p'", 'max_length': '1'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "'8442370746686488521499004199393593321507535216009169941507190211002885903957861553752913676005616603486237740069824229228998452166221149338349945862795467'", 'max_length': '155', 'primary_key': 'True'}),
            'validation_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        'plmapp.lifecycle': {
            'Meta': {'object_name': 'Lifecycle'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'official_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.State']"})
        },
        'plmapp.lifecyclestates': {
            'Meta': {'unique_together': "(('lifecycle', 'state'),)", 'object_name': 'LifecycleStates'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lifecycle': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.Lifecycle']"}),
            'rank': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.State']"})
        },
        'plmapp.parentchildlink': {
            'Meta': {'unique_together': "(('parent', 'child', 'end_time'),)", 'object_name': 'ParentChildLink'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parentchildlink_child'", 'to': "orm['plmapp.Part']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parentchildlink_parent'", 'to': "orm['plmapp.Part']"}),
            'quantity': ('django.db.models.fields.FloatField', [], {'default': '1'}),
            'unit': ('django.db.models.fields.CharField', [], {'default': "'-'", 'max_length': '4'})
        },
        'plmapp.parentchildlinkextension': {
            'Meta': {'object_name': 'ParentChildLinkExtension'},
            '_child_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parentchildlinkextension_link'", 'to': "orm['plmapp.ParentChildLink']"})
        },
        'plmapp.part': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'Part', '_ormbases': ['plmapp.PLMObject']},
            'plmobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.PLMObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        'plmapp.plmobject': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'unique_together': "(('reference', 'type', 'revision'),)", 'object_name': 'PLMObject'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 19, 15, 31, 46, 686441)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_group'", 'to': "orm['plmapp.GroupInfo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lifecycle': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_lifecyle'", 'to': "orm['plmapp.Lifecycle']"}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_owner'", 'to': "orm['auth.User']"}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'revision': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_lifecyle'", 'to': "orm['plmapp.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'plmapp.plmobjectuserlink': {
            'Meta': {'ordering': "['user', 'role', 'plmobject__type', 'plmobject__reference', 'plmobject__revision']", 'unique_together': "(('plmobject', 'user', 'role'),)", 'object_name': 'PLMObjectUserLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobjectuserlink_plmobject'", 'to': "orm['plmapp.PLMObject']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobjectuserlink_user'", 'to': "orm['auth.User']"})
        },
        'plmapp.revisionlink': {
            'Meta': {'unique_together': "(('old', 'new'),)", 'object_name': 'RevisionLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisionlink_new'", 'to': "orm['plmapp.PLMObject']"}),
            'old': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisionlink_old'", 'to': "orm['plmapp.PLMObject']"})
        },
        'plmapp.state': {
            'Meta': {'object_name': 'State'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'})
        },
        'plmapp.statehistory': {
            'Meta': {'object_name': 'StateHistory'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lifecycle': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.Lifecycle']"}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.PLMObject']"}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 19, 15, 31, 46, 666297)'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.State']"}),
            'state_category': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'plmapp.userhistory': {
            'Meta': {'object_name': 'UserHistory'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userhistory_user'", 'to': "orm['auth.User']"})
        },
        'plmapp.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_administrator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_contributor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '5'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['plmapp']
