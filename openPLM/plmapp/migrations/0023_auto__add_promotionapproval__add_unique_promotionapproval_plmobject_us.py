# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PromotionApproval'
        db.create_table('plmapp_promotionapproval', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('plmobject', self.gf('django.db.models.fields.related.ForeignKey')(related_name='approvals', to=orm['plmapp.PLMObject'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='approvals', to=orm['auth.User'])),
            ('current_state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='promotionapproval_current_state', to=orm['plmapp.State'])),
            ('next_state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='promotionapproval_next_state', to=orm['plmapp.State'])),
        ))
        db.send_create_signal('plmapp', ['PromotionApproval'])

        # Adding unique constraint on 'PromotionApproval', fields ['plmobject', 'user', 'current_state', 'next_state', 'end_time']
        db.create_unique('plmapp_promotionapproval', ['plmobject_id', 'user_id', 'current_state_id', 'next_state_id', 'end_time'])


    def backwards(self, orm):
        # Removing unique constraint on 'PromotionApproval', fields ['plmobject', 'user', 'current_state', 'next_state', 'end_time']
        db.delete_unique('plmapp_promotionapproval', ['plmobject_id', 'user_id', 'current_state_id', 'next_state_id', 'end_time'])

        # Deleting model 'PromotionApproval'
        db.delete_table('plmapp_promotionapproval')


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
            'Meta': {'unique_together': "(('delegator', 'delegatee', 'role', 'end_time'),)", 'object_name': 'DelegationLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delegatee': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'delegationlink_delegatee'", 'to': "orm['auth.User']"}),
            'delegator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'delegationlink_delegator'", 'to': "orm['auth.User']"}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'})
        },
        'plmapp.document': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'Document', '_ormbases': ['plmapp.PLMObject']},
            'plmobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.PLMObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        'plmapp.documentfile': {
            'Meta': {'object_name': 'DocumentFile'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'timezone.now'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'deprecated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.Document']"}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_revision': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'older_files'", 'null': 'True', 'to': "orm['plmapp.DocumentFile']"}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'locker': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'previous_revision': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'related_name': "'next_revision'", 'unique': 'True', 'null': 'True', 'to': "orm['plmapp.DocumentFile']"}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'size': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'plmapp.documentpartlink': {
            'Meta': {'unique_together': "(('document', 'part', 'end_time'),)", 'object_name': 'DocumentPartLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documentpartlink_document'", 'to': "orm['plmapp.Document']"}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 10, 9, 0, 0)'}),
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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 10, 9, 0, 0)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.GroupInfo']"}),
            'guest': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitation_inv_guest'", 'to': "orm['auth.User']"}),
            'guest_asked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitation_inv_owner'", 'to': "orm['auth.User']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'p'", 'max_length': '1'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "'8976931342509920382872290747688353011246276762195635580705100407361392380698489115191374921810452320190738587419439233602898757200987268865583968298860710'", 'max_length': '155', 'primary_key': 'True'}),
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
            'Meta': {'object_name': 'Part', '_ormbases': ['plmapp.PLMObject']},
            'plmobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.PLMObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        'plmapp.plmobject': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'unique_together': "(('reference', 'type', 'revision'),)", 'object_name': 'PLMObject'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 10, 9, 0, 0)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_group'", 'to': "orm['plmapp.GroupInfo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lifecycle': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_lifecyle'", 'to': "orm['plmapp.Lifecycle']"}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_owner'", 'to': "orm['auth.User']"}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'reference_number': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'revision': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_lifecyle'", 'to': "orm['plmapp.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'plmapp.plmobjectuserlink': {
            'Meta': {'ordering': "['user', 'role', 'plmobject__type', 'plmobject__reference', 'plmobject__revision']", 'unique_together': "(('plmobject', 'user', 'role', 'end_time'),)", 'object_name': 'PLMObjectUserLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobjectuserlink_plmobject'", 'to': "orm['plmapp.PLMObject']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobjectuserlink_user'", 'to': "orm['auth.User']"})
        },
        'plmapp.promotionapproval': {
            'Meta': {'unique_together': "(('plmobject', 'user', 'current_state', 'next_state', 'end_time'),)", 'object_name': 'PromotionApproval'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'promotionapproval_current_state'", 'to': "orm['plmapp.State']"}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'promotionapproval_next_state'", 'to': "orm['plmapp.State']"}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'approvals'", 'to': "orm['plmapp.PLMObject']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'approvals'", 'to': "orm['auth.User']"})
        },
        'plmapp.revisionlink': {
            'Meta': {'unique_together': "(('old', 'new', 'end_time'),)", 'object_name': 'RevisionLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
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
            'start_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 10, 9, 0, 0)'}),
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
            'can_publish': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_administrator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_contributor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '5'}),
            'restricted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['plmapp']
