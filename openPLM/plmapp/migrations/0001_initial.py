# encoding: utf-8
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'UserProfile'
        db.create_table('plmapp_userprofile', (
            ('is_contributor', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('is_administrator', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal('plmapp', ['UserProfile'])

        # Adding model 'GroupInfo'
        db.create_table('plmapp_groupinfo', (
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 9, 30, 16, 3, 52, 119939))),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('group_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Group'], unique=True, primary_key=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='groupinfo_owner', to=orm['auth.User'])),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('plmapp', ['GroupInfo'])

        # Adding model 'State'
        db.create_table('plmapp_state', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
        ))
        db.send_create_signal('plmapp', ['State'])

        # Adding model 'Lifecycle'
        db.create_table('plmapp_lifecycle', (
            ('official_state', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plmapp.State'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, primary_key=True)),
        ))
        db.send_create_signal('plmapp', ['Lifecycle'])

        # Adding model 'LifecycleStates'
        db.create_table('plmapp_lifecyclestates', (
            ('state', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plmapp.State'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rank', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('lifecycle', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plmapp.Lifecycle'])),
        ))
        db.send_create_signal('plmapp', ['LifecycleStates'])

        # Adding unique constraint on 'LifecycleStates', fields ['lifecycle', 'state']
        db.create_unique('plmapp_lifecyclestates', ['lifecycle_id', 'state_id'])

        # Adding model 'PLMObject'
        db.create_table('plmapp_plmobject', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('reference', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='plmobject_creator', to=orm['auth.User'])),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 9, 30, 16, 3, 52, 229207))),
            ('state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='plmobject_lifecyle', to=orm['plmapp.State'])),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='plmobject_owner', to=orm['auth.User'])),
            ('lifecycle', self.gf('django.db.models.fields.related.ForeignKey')(related_name='plmobject_lifecyle', to=orm['plmapp.Lifecycle'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('revision', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('plmapp', ['PLMObject'])

        # Adding unique constraint on 'PLMObject', fields ['reference', 'type', 'revision']
        db.create_unique('plmapp_plmobject', ['reference', 'type', 'revision'])

        # Adding model 'Part'
        db.create_table('plmapp_part', (
            ('plmobject_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['plmapp.PLMObject'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('plmapp', ['Part'])

        # Adding model 'DocumentFile'
        db.create_table('plmapp_documentfile', (
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plmapp.Document'])),
            ('locked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('locker', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['auth.User'], null=True, blank=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('size', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('plmapp', ['DocumentFile'])

        # Adding model 'Document'
        db.create_table('plmapp_document', (
            ('plmobject_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['plmapp.PLMObject'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('plmapp', ['Document'])

        # Adding model 'History'
        db.create_table('plmapp_history', (
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='history_user', to=orm['auth.User'])),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('plmobject', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plmapp.PLMObject'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('details', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('plmapp', ['History'])

        # Adding model 'UserHistory'
        db.create_table('plmapp_userhistory', (
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='userhistory_user', to=orm['auth.User'])),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('plmobject', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('details', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('plmapp', ['UserHistory'])

        # Adding model 'GroupHistory'
        db.create_table('plmapp_grouphistory', (
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='grouphistory_user', to=orm['auth.User'])),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('plmobject', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('details', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('plmapp', ['GroupHistory'])

        # Adding model 'RevisionLink'
        db.create_table('plmapp_revisionlink', (
            ('new', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisionlink_new', to=orm['plmapp.PLMObject'])),
            ('old', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisionlink_old', to=orm['plmapp.PLMObject'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('plmapp', ['RevisionLink'])

        # Adding unique constraint on 'RevisionLink', fields ['old', 'new']
        db.create_unique('plmapp_revisionlink', ['old_id', 'new_id'])

        # Adding model 'ParentChildLink'
        db.create_table('plmapp_parentchildlink', (
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='parentchildlink_parent', to=orm['plmapp.Part'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('child', self.gf('django.db.models.fields.related.ForeignKey')(related_name='parentchildlink_child', to=orm['plmapp.Part'])),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('quantity', self.gf('django.db.models.fields.FloatField')(default=1)),
        ))
        db.send_create_signal('plmapp', ['ParentChildLink'])

        # Adding unique constraint on 'ParentChildLink', fields ['parent', 'child', 'end_time']
        db.create_unique('plmapp_parentchildlink', ['parent_id', 'child_id', 'end_time'])

        # Adding model 'DocumentPartLink'
        db.create_table('plmapp_documentpartlink', (
            ('part', self.gf('django.db.models.fields.related.ForeignKey')(related_name='documentpartlink_part', to=orm['plmapp.Part'])),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='documentpartlink_document', to=orm['plmapp.Document'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('plmapp', ['DocumentPartLink'])

        # Adding unique constraint on 'DocumentPartLink', fields ['document', 'part']
        db.create_unique('plmapp_documentpartlink', ['document_id', 'part_id'])

        # Adding model 'DelegationLink'
        db.create_table('plmapp_delegationlink', (
            ('delegatee', self.gf('django.db.models.fields.related.ForeignKey')(related_name='delegationlink_delegatee', to=orm['auth.User'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('delegator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='delegationlink_delegator', to=orm['auth.User'])),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('plmapp', ['DelegationLink'])

        # Adding unique constraint on 'DelegationLink', fields ['delegator', 'delegatee', 'role']
        db.create_unique('plmapp_delegationlink', ['delegator_id', 'delegatee_id', 'role'])

        # Adding model 'PLMObjectUserLink'
        db.create_table('plmapp_plmobjectuserlink', (
            ('plmobject', self.gf('django.db.models.fields.related.ForeignKey')(related_name='plmobjectuserlink_plmobject', to=orm['plmapp.PLMObject'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='plmobjectuserlink_user', to=orm['auth.User'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('plmapp', ['PLMObjectUserLink'])

        # Adding unique constraint on 'PLMObjectUserLink', fields ['plmobject', 'user', 'role']
        db.create_unique('plmapp_plmobjectuserlink', ['plmobject_id', 'user_id', 'role'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'UserProfile'
        db.delete_table('plmapp_userprofile')

        # Deleting model 'GroupInfo'
        db.delete_table('plmapp_groupinfo')

        # Deleting model 'State'
        db.delete_table('plmapp_state')

        # Deleting model 'Lifecycle'
        db.delete_table('plmapp_lifecycle')

        # Deleting model 'LifecycleStates'
        db.delete_table('plmapp_lifecyclestates')

        # Removing unique constraint on 'LifecycleStates', fields ['lifecycle', 'state']
        db.delete_unique('plmapp_lifecyclestates', ['lifecycle_id', 'state_id'])

        # Deleting model 'PLMObject'
        db.delete_table('plmapp_plmobject')

        # Removing unique constraint on 'PLMObject', fields ['reference', 'type', 'revision']
        db.delete_unique('plmapp_plmobject', ['reference', 'type', 'revision'])

        # Deleting model 'Part'
        db.delete_table('plmapp_part')

        # Deleting model 'DocumentFile'
        db.delete_table('plmapp_documentfile')

        # Deleting model 'Document'
        db.delete_table('plmapp_document')

        # Deleting model 'History'
        db.delete_table('plmapp_history')

        # Deleting model 'UserHistory'
        db.delete_table('plmapp_userhistory')

        # Deleting model 'GroupHistory'
        db.delete_table('plmapp_grouphistory')

        # Deleting model 'RevisionLink'
        db.delete_table('plmapp_revisionlink')

        # Removing unique constraint on 'RevisionLink', fields ['old', 'new']
        db.delete_unique('plmapp_revisionlink', ['old_id', 'new_id'])

        # Deleting model 'ParentChildLink'
        db.delete_table('plmapp_parentchildlink')

        # Removing unique constraint on 'ParentChildLink', fields ['parent', 'child', 'end_time']
        db.delete_unique('plmapp_parentchildlink', ['parent_id', 'child_id', 'end_time'])

        # Deleting model 'DocumentPartLink'
        db.delete_table('plmapp_documentpartlink')

        # Removing unique constraint on 'DocumentPartLink', fields ['document', 'part']
        db.delete_unique('plmapp_documentpartlink', ['document_id', 'part_id'])

        # Deleting model 'DelegationLink'
        db.delete_table('plmapp_delegationlink')

        # Removing unique constraint on 'DelegationLink', fields ['delegator', 'delegatee', 'role']
        db.delete_unique('plmapp_delegationlink', ['delegator_id', 'delegatee_id', 'role'])

        # Deleting model 'PLMObjectUserLink'
        db.delete_table('plmapp_plmobjectuserlink')

        # Removing unique constraint on 'PLMObjectUserLink', fields ['plmobject', 'user', 'role']
        db.delete_unique('plmapp_plmobjectuserlink', ['plmobject_id', 'user_id', 'role'])
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
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
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'plmapp.document': {
            'Meta': {'object_name': 'Document', '_ormbases': ['plmapp.PLMObject']},
            'plmobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.PLMObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        'plmapp.documentfile': {
            'Meta': {'object_name': 'DocumentFile'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.Document']"}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 30, 16, 3, 52, 298671)'}),
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
            'quantity': ('django.db.models.fields.FloatField', [], {'default': '1'})
        },
        'plmapp.part': {
            'Meta': {'object_name': 'Part', '_ormbases': ['plmapp.PLMObject']},
            'plmobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.PLMObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        'plmapp.plmobject': {
            'Meta': {'unique_together': "(('reference', 'type', 'revision'),)", 'object_name': 'PLMObject'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 30, 16, 3, 52, 437699)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lifecycle': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_lifecyle'", 'to': "orm['plmapp.Lifecycle']"}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_owner'", 'to': "orm['auth.User']"}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'revision': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_lifecyle'", 'to': "orm['plmapp.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'plmapp.plmobjectuserlink': {
            'Meta': {'unique_together': "(('plmobject', 'user', 'role'),)", 'object_name': 'PLMObjectUserLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobjectuserlink_plmobject'", 'to': "orm['plmapp.PLMObject']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
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
            'is_administrator': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_contributor': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }
    
    complete_apps = ['plmapp']
