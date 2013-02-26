# encoding: utf-8
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'CAE'
        db.create_table('cae_cae', (
            ('document_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['plmapp.Document'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cae', ['CAE'])

        # Adding model 'Geometry'
        db.create_table('cae_geometry', (
            ('cae_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cae.CAE'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cae', ['Geometry'])

        # Adding model 'BoundaryConditions'
        db.create_table('cae_boundaryconditions', (
            ('cae_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cae.CAE'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cae', ['BoundaryConditions'])

        # Adding model 'Mesh'
        db.create_table('cae_mesh', (
            ('cae_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cae.CAE'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cae', ['Mesh'])

        # Adding model 'Results'
        db.create_table('cae_results', (
            ('cae_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cae.CAE'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cae', ['Results'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'CAE'
        db.delete_table('cae_cae')

        # Deleting model 'Geometry'
        db.delete_table('cae_geometry')

        # Deleting model 'BoundaryConditions'
        db.delete_table('cae_boundaryconditions')

        # Deleting model 'Mesh'
        db.delete_table('cae_mesh')

        # Deleting model 'Results'
        db.delete_table('cae_results')
    
    
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
        'cae.boundaryconditions': {
            'Meta': {'object_name': 'BoundaryConditions', '_ormbases': ['cae.CAE']},
            'cae_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cae.CAE']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cae.cae': {
            'Meta': {'object_name': 'CAE', '_ormbases': ['plmapp.Document']},
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cae.geometry': {
            'Meta': {'object_name': 'Geometry', '_ormbases': ['cae.CAE']},
            'cae_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cae.CAE']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cae.mesh': {
            'Meta': {'object_name': 'Mesh', '_ormbases': ['cae.CAE']},
            'cae_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cae.CAE']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cae.results': {
            'Meta': {'object_name': 'Results', '_ormbases': ['cae.CAE']},
            'cae_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cae.CAE']", 'unique': 'True', 'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'plmapp.document': {
            'Meta': {'object_name': 'Document', '_ormbases': ['plmapp.PLMObject']},
            'plmobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.PLMObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        'plmapp.lifecycle': {
            'Meta': {'object_name': 'Lifecycle'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'official_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.State']"})
        },
        'plmapp.plmobject': {
            'Meta': {'unique_together': "(('reference', 'type', 'revision'),)", 'object_name': 'PLMObject'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 30, 16, 9, 19, 856763)'}),
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
        'plmapp.state': {
            'Meta': {'object_name': 'State'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'})
        }
    }
    
    complete_apps = ['cae']
