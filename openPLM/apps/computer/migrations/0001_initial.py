# encoding: utf-8
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'SinglePart'
        db.create_table('computer_singlepart', (
            ('part_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['plmapp.Part'], unique=True, primary_key=True)),
            ('supplier', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('tech_details', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('computer', ['SinglePart'])

        # Adding model 'MotherBoard'
        db.create_table('computer_motherboard', (
            ('singlepart_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.SinglePart'], unique=True, primary_key=True)),
            ('motherboard_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('computer', ['MotherBoard'])

        # Adding model 'RAM'
        db.create_table('computer_ram', (
            ('singlepart_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.SinglePart'], unique=True, primary_key=True)),
            ('size_in_mo', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('computer', ['RAM'])

        # Adding model 'HardDisk'
        db.create_table('computer_harddisk', (
            ('capacity_in_go', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('singlepart_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.SinglePart'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('computer', ['HardDisk'])

        # Adding model 'ElectronicPart'
        db.create_table('computer_electronicpart', (
            ('singlepart_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.SinglePart'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('computer', ['ElectronicPart'])

        # Adding model 'MechanicalPart'
        db.create_table('computer_mechanicalpart', (
            ('singlepart_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.SinglePart'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('computer', ['MechanicalPart'])

        # Adding model 'Mouse'
        db.create_table('computer_mouse', (
            ('singlepart_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.SinglePart'], unique=True, primary_key=True)),
            ('number_of_buttons', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=3)),
        ))
        db.send_create_signal('computer', ['Mouse'])

        # Adding model 'KeyBoard'
        db.create_table('computer_keyboard', (
            ('singlepart_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.SinglePart'], unique=True, primary_key=True)),
            ('keymap', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('computer', ['KeyBoard'])

        # Adding model 'Screen'
        db.create_table('computer_screen', (
            ('horizontal_resolution', self.gf('django.db.models.fields.IntegerField')()),
            ('singlepart_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.SinglePart'], unique=True, primary_key=True)),
            ('vertical_resolution', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('computer', ['Screen'])

        # Adding model 'Assembly'
        db.create_table('computer_assembly', (
            ('part_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['plmapp.Part'], unique=True, primary_key=True)),
            ('manufacturer', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('computer', ['Assembly'])

        # Adding model 'ComputerSet'
        db.create_table('computer_computerset', (
            ('customer', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('assembly_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.Assembly'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('computer', ['ComputerSet'])

        # Adding model 'CentralUnit'
        db.create_table('computer_centralunit', (
            ('tech_characteristics', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('assembly_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.Assembly'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('computer', ['CentralUnit'])

        # Adding model 'OtherAssembly'
        db.create_table('computer_otherassembly', (
            ('assembly_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['computer.Assembly'], unique=True, primary_key=True)),
            ('tech_details', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('computer', ['OtherAssembly'])

        # Adding model 'BiosOs'
        db.create_table('computer_biosos', (
            ('part_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['plmapp.Part'], unique=True, primary_key=True)),
            ('size_in_mo', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('computer', ['BiosOs'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'SinglePart'
        db.delete_table('computer_singlepart')

        # Deleting model 'MotherBoard'
        db.delete_table('computer_motherboard')

        # Deleting model 'RAM'
        db.delete_table('computer_ram')

        # Deleting model 'HardDisk'
        db.delete_table('computer_harddisk')

        # Deleting model 'ElectronicPart'
        db.delete_table('computer_electronicpart')

        # Deleting model 'MechanicalPart'
        db.delete_table('computer_mechanicalpart')

        # Deleting model 'Mouse'
        db.delete_table('computer_mouse')

        # Deleting model 'KeyBoard'
        db.delete_table('computer_keyboard')

        # Deleting model 'Screen'
        db.delete_table('computer_screen')

        # Deleting model 'Assembly'
        db.delete_table('computer_assembly')

        # Deleting model 'ComputerSet'
        db.delete_table('computer_computerset')

        # Deleting model 'CentralUnit'
        db.delete_table('computer_centralunit')

        # Deleting model 'OtherAssembly'
        db.delete_table('computer_otherassembly')

        # Deleting model 'BiosOs'
        db.delete_table('computer_biosos')
    
    
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
        'computer.assembly': {
            'Meta': {'object_name': 'Assembly', '_ormbases': ['plmapp.Part']},
            'manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'part_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Part']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.biosos': {
            'Meta': {'object_name': 'BiosOs', '_ormbases': ['plmapp.Part']},
            'part_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Part']", 'unique': 'True', 'primary_key': 'True'}),
            'size_in_mo': ('django.db.models.fields.IntegerField', [], {})
        },
        'computer.centralunit': {
            'Meta': {'object_name': 'CentralUnit', '_ormbases': ['computer.Assembly']},
            'assembly_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.Assembly']", 'unique': 'True', 'primary_key': 'True'}),
            'tech_characteristics': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'computer.computerset': {
            'Meta': {'object_name': 'ComputerSet', '_ormbases': ['computer.Assembly']},
            'assembly_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.Assembly']", 'unique': 'True', 'primary_key': 'True'}),
            'customer': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'computer.electronicpart': {
            'Meta': {'object_name': 'ElectronicPart', '_ormbases': ['computer.SinglePart']},
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.harddisk': {
            'Meta': {'object_name': 'HardDisk', '_ormbases': ['computer.SinglePart']},
            'capacity_in_go': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.keyboard': {
            'Meta': {'object_name': 'KeyBoard', '_ormbases': ['computer.SinglePart']},
            'keymap': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.mechanicalpart': {
            'Meta': {'object_name': 'MechanicalPart', '_ormbases': ['computer.SinglePart']},
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.motherboard': {
            'Meta': {'object_name': 'MotherBoard', '_ormbases': ['computer.SinglePart']},
            'motherboard_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.mouse': {
            'Meta': {'object_name': 'Mouse', '_ormbases': ['computer.SinglePart']},
            'number_of_buttons': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'})
        },
        'computer.otherassembly': {
            'Meta': {'object_name': 'OtherAssembly', '_ormbases': ['computer.Assembly']},
            'assembly_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.Assembly']", 'unique': 'True', 'primary_key': 'True'}),
            'tech_details': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'computer.ram': {
            'Meta': {'object_name': 'RAM', '_ormbases': ['computer.SinglePart']},
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'}),
            'size_in_mo': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'computer.screen': {
            'Meta': {'object_name': 'Screen', '_ormbases': ['computer.SinglePart']},
            'horizontal_resolution': ('django.db.models.fields.IntegerField', [], {}),
            'singlepart_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['computer.SinglePart']", 'unique': 'True', 'primary_key': 'True'}),
            'vertical_resolution': ('django.db.models.fields.IntegerField', [], {})
        },
        'computer.singlepart': {
            'Meta': {'object_name': 'SinglePart', '_ormbases': ['plmapp.Part']},
            'part_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Part']", 'unique': 'True', 'primary_key': 'True'}),
            'supplier': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tech_details': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'plmapp.lifecycle': {
            'Meta': {'object_name': 'Lifecycle'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'primary_key': 'True'}),
            'official_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.State']"})
        },
        'plmapp.part': {
            'Meta': {'object_name': 'Part', '_ormbases': ['plmapp.PLMObject']},
            'plmobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.PLMObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        'plmapp.plmobject': {
            'Meta': {'unique_together': "(('reference', 'type', 'revision'),)", 'object_name': 'PLMObject'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plmobject_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 9, 30, 16, 9, 28, 392826)'}),
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
    
    complete_apps = ['computer']
