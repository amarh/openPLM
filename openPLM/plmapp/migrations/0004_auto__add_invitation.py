# encoding: utf-8
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Invitation'
        db.create_table('plmapp_invitation', (
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plmapp.GroupInfo'])),
            ('guest', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invitation_inv_guest', to=orm['auth.User'])),
            ('guest_asked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('validation_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='p', max_length=1)),
            ('token', self.gf('django.db.models.fields.CharField')(default='3031111705822048650998027131156820001126719039497784265494329246307920237300935280947334177736032673784822865744216017846396537104025045540559031430349658', max_length=155, primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invitation_inv_owner', to=orm['auth.User'])),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 10, 4, 17, 33, 36, 558986))),
        ))
        db.send_create_signal('plmapp', ['Invitation'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Invitation'
        db.delete_table('plmapp_invitation')
    
    
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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 4, 17, 33, 36, 961108)'}),
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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 4, 17, 33, 36, 892212)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.GroupInfo']"}),
            'guest': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitation_inv_guest'", 'to': "orm['auth.User']"}),
            'guest_asked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitation_inv_owner'", 'to': "orm['auth.User']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'p'", 'max_length': '1'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "'2772213081172912677954042742095567121446226956798425959021756984071406297921830150929300151162455220471539536247404353061117957401501268945749342486301460'", 'max_length': '155', 'primary_key': 'True'}),
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
            'quantity': ('django.db.models.fields.FloatField', [], {'default': '1'})
        },
        'plmapp.part': {
            'Meta': {'object_name': 'Part', '_ormbases': ['plmapp.PLMObject']},
            'plmobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.PLMObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        'plmapp.plmobject': {
            'Meta': {'unique_together': "(('reference', 'type', 'revision'),)", 'object_name': 'PLMObject'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 10, 4, 17, 33, 36, 969855)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_group'", 'to': "orm['plmapp.GroupInfo']"}),
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
