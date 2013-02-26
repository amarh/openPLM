# encoding: utf-8
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ReferenceDesignator'
        db.create_table('computer_referencedesignator', (
            ('parentchildlinkextension_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['plmapp.ParentChildLinkExtension'], unique=True, primary_key=True)),
            ('reference_designator', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('computer', ['ReferenceDesignator'])


    def backwards(self, orm):
        
        # Deleting model 'ReferenceDesignator'
        db.delete_table('computer_referencedesignator')


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
        'computer.assembly': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'Assembly', '_ormbases': ['plmapp.Part']},
            'manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'part_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Part']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.biosos': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'BiosOs', '_ormbases': ['plmapp.Part']},
            'part_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Part']", 'unique': 'True', 'primary_key': 'True'}),
            'size_in_mo': ('django.db.models.fields.IntegerField', [], {})
        },
        'computer.centralunit': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'CentralUnit', '_ormbases': ['computer.Assembly']},
            'assembly_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.Assembly']", 'unique': 'True', 'primary_key': 'True'}),
            'tech_characteristics': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'computer.computerset': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'ComputerSet', '_ormbases': ['computer.Assembly']},
            'assembly_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.Assembly']", 'unique': 'True', 'primary_key': 'True'}),
            'customer': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'computer.electronicpart': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'ElectronicPart', '_ormbases': ['computer.SinglePart']},
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.harddisk': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'HardDisk', '_ormbases': ['computer.SinglePart']},
            'capacity_in_go': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.keyboard': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'KeyBoard', '_ormbases': ['computer.SinglePart']},
            'keymap': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.mechanicalpart': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'MechanicalPart', '_ormbases': ['computer.SinglePart']},
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.motherboard': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'MotherBoard', '_ormbases': ['computer.SinglePart']},
            'motherboard_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.mouse': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'Mouse', '_ormbases': ['computer.SinglePart']},
            'number_of_buttons': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.otherassembly': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'OtherAssembly', '_ormbases': ['computer.Assembly']},
            'assembly_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.Assembly']", 'unique': 'True', 'primary_key': 'True'}),
            'tech_details': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'computer.ram': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'RAM', '_ormbases': ['computer.SinglePart']},
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'}),
            'size_in_mo': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'computer.referencedesignator': {
            'Meta': {'object_name': 'ReferenceDesignator', '_ormbases': ['plmapp.ParentChildLinkExtension']},
            'parentchildlinkextension_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.ParentChildLinkExtension']", 'unique': 'True', 'primary_key': 'True'}),
            'reference_designator': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'computer.screen': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'Screen', '_ormbases': ['computer.SinglePart']},
            'horizontal_resolution': ('django.db.models.fields.IntegerField', [], {}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'}),
            'vertical_resolution': ('django.db.models.fields.IntegerField', [], {})
        },
        'computer.singlepart': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'SinglePart', '_ormbases': ['plmapp.Part']},
            'part_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Part']", 'unique': 'True', 'primary_key': 'True'}),
            'supplier': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tech_details': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'plmapp.groupinfo': {
            'Meta': {'object_name': 'GroupInfo', '_ormbases': ['auth.Group']},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groupinfo_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 17, 11, 50, 33, 168278)'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groupinfo_owner'", 'to': "orm['auth.User']"})
        },
        'plmapp.lifecycle': {
            'Meta': {'object_name': 'Lifecycle'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'official_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.State']"})
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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 17, 11, 50, 33, 205713)'}),
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
        'plmapp.state': {
            'Meta': {'object_name': 'State'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'})
        }
    }

    complete_apps = ['computer']
