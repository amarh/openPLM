# encoding: utf-8
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Design'
        db.create_table('cad_design', (
            ('document_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['plmapp.Document'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cad', ['Design'])

        # Adding model 'Drawing'
        db.create_table('cad_drawing', (
            ('format', self.gf('django.db.models.fields.CharField')(default='A4', max_length=10)),
            ('nb_pages', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('design_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cad.Design'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cad', ['Drawing'])

        # Adding model 'CustomerDrawing'
        db.create_table('cad_customerdrawing', (
            ('customer', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('drawing_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cad.Drawing'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cad', ['CustomerDrawing'])

        # Adding model 'SupplierDrawing'
        db.create_table('cad_supplierdrawing', (
            ('supplier', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('drawing_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cad.Drawing'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cad', ['SupplierDrawing'])

        # Adding model 'FMEA'
        db.create_table('cad_fmea', (
            ('design_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cad.Design'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cad', ['FMEA'])

        # Adding model 'Sketch'
        db.create_table('cad_sketch', (
            ('design_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cad.Design'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cad', ['Sketch'])

        # Adding model 'FreeCAD'
        db.create_table('cad_freecad', (
            ('design_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cad.Design'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cad', ['FreeCAD'])

        # Adding model 'Patent'
        db.create_table('cad_patent', (
            ('expiration_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('inventor', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('design_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cad.Design'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('cad', ['Patent'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Design'
        db.delete_table('cad_design')

        # Deleting model 'Drawing'
        db.delete_table('cad_drawing')

        # Deleting model 'CustomerDrawing'
        db.delete_table('cad_customerdrawing')

        # Deleting model 'SupplierDrawing'
        db.delete_table('cad_supplierdrawing')

        # Deleting model 'FMEA'
        db.delete_table('cad_fmea')

        # Deleting model 'Sketch'
        db.delete_table('cad_sketch')

        # Deleting model 'FreeCAD'
        db.delete_table('cad_freecad')

        # Deleting model 'Patent'
        db.delete_table('cad_patent')
    
    
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
        'cad.customerdrawing': {
            'Meta': {'object_name': 'CustomerDrawing', '_ormbases': ['cad.Drawing']},
            'customer': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'drawing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cad.Drawing']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cad.design': {
            'Meta': {'object_name': 'Design', '_ormbases': ['plmapp.Document']},
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cad.drawing': {
            'Meta': {'object_name': 'Drawing', '_ormbases': ['cad.Design']},
            'design_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cad.Design']", 'unique': 'True', 'primary_key': 'True'}),
            'format': ('django.db.models.fields.CharField', [], {'default': "'A4'", 'max_length': '10'}),
            'nb_pages': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cad.fmea': {
            'Meta': {'object_name': 'FMEA', '_ormbases': ['cad.Design']},
            'design_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cad.Design']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cad.freecad': {
            'Meta': {'object_name': 'FreeCAD', '_ormbases': ['cad.Design']},
            'design_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cad.Design']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cad.patent': {
            'Meta': {'object_name': 'Patent', '_ormbases': ['cad.Design']},
            'design_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cad.Design']", 'unique': 'True', 'primary_key': 'True'}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'inventor': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'cad.sketch': {
            'Meta': {'object_name': 'Sketch', '_ormbases': ['cad.Design']},
            'design_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cad.Design']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cad.supplierdrawing': {
            'Meta': {'object_name': 'SupplierDrawing', '_ormbases': ['cad.Drawing']},
            'drawing_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cad.Drawing']", 'unique': 'True', 'primary_key': 'True'}),
            'supplier': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 30, 16, 9, 0, 173081)'}),
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
    
    complete_apps = ['cad']
