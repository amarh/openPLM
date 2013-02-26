# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
        model = "ecr.ECRUserLink"
        orm[model].objects.filter(role="sign_3rd_level").update(role="sign_4th_level")
        orm[model].objects.filter(role="sign_3th_level").update(role="sign_3rd_level")
        orm["ECR.ECRHistory"].objects.filter(action="New sign_3rd_level").update(action="New sign_4th_level")
        orm["ECR.ECRHistory"].objects.filter(action="New sign_3th_level").update(action="New sign_3rd_level")
        orm["ECR.ECRHistory"].objects.filter(action="sign_3rd_level removed").update(action="sign_4th_level removed")
        orm["ECR.ECRHistory"].objects.filter(action="sign_3th_level removed").update(action="sign_3rd_level removed")


    def backwards(self, orm):
        "Write your backwards methods here."
        model = "ecr.ECRUserLink"
        orm[model].objects.filter(role="sign_3rd_level").update(role="sign_3th_level")
        orm[model].objects.filter(role="sign_4th_level").update(role="sign_3rd_level")
        orm["ECR.ECRHistory"].objects.filter(action="New sign_3rd_level").update(action="New sign_3th_level")
        orm["ECR.ECRHistory"].objects.filter(action="New sign_4th_level").update(action="New sign_3rd_level")
        orm["ECR.ECRHistory"].objects.filter(action="sign_3rd_level removed").update(action="sign_3th_level removed")
        orm["ECR.ECRHistory"].objects.filter(action="sign_4th_level removed").update(action="sign_3rd_level removed")

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
        'ecr.ecr': {
            'Meta': {'ordering': "['reference']", 'object_name': 'ECR'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ecr_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 1, 15, 0, 0)'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lifecycle': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['plmapp.Lifecycle']"}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ecr_owner'", 'to': "orm['auth.User']"}),
            'reference': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'reference_number': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['plmapp.State']"})
        },
        'ecr.ecrhistory': {
            'Meta': {'object_name': 'ECRHistory'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ecr.ECR']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ecrhistory_user'", 'to': "orm['auth.User']"})
        },
        'ecr.ecrplmobjectlink': {
            'Meta': {'unique_together': "(('ecr', 'plmobject', 'end_time'),)", 'object_name': 'ECRPLMObjectLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ecr': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobjects'", 'to': "orm['ecr.ECR']"}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plmobject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ecrs'", 'to': "orm['plmapp.PLMObject']"})
        },
        'ecr.ecrpromotionapproval': {
            'Meta': {'unique_together': "(('ecr', 'user', 'current_state', 'next_state', 'end_time'),)", 'object_name': 'ECRPromotionApproval'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['plmapp.State']"}),
            'ecr': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'approvals'", 'to': "orm['ecr.ECR']"}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['plmapp.State']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ecr_approvals'", 'to': "orm['auth.User']"})
        },
        'ecr.ecruserlink': {
            'Meta': {'ordering': "['user', 'role', 'ecr__reference']", 'unique_together': "(('ecr', 'user', 'role', 'end_time'),)", 'object_name': 'ECRUserLink'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ecr': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'users'", 'to': "orm['ecr.ECR']"}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ecrs'", 'to': "orm['auth.User']"})
        },
        'plmapp.groupinfo': {
            'Meta': {'object_name': 'GroupInfo', '_ormbases': ['auth.Group']},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groupinfo_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 1, 15, 0, 0)'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groupinfo_owner'", 'to': "orm['auth.User']"})
        },
        'plmapp.lifecycle': {
            'Meta': {'object_name': 'Lifecycle'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'official_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.State']"}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        'plmapp.plmobject': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'unique_together': "(('reference', 'type', 'revision'),)", 'object_name': 'PLMObject'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 1, 15, 0, 0)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_group'", 'to': "orm['plmapp.GroupInfo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lifecycle': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['plmapp.Lifecycle']"}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_owner'", 'to': "orm['auth.User']"}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'reference_number': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'revision': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['plmapp.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'plmapp.state': {
            'Meta': {'object_name': 'State'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'})
        }
    }

    complete_apps = ['ecr']
    symmetrical = True
