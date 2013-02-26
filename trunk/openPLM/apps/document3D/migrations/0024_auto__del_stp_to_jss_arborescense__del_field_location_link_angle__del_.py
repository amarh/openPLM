# encoding: utf-8
import datetime
from django.utils import timezone
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'stp_to_jss_arborescense'
        db.delete_table('document3D_stp_to_jss_arborescense')

        # Deleting field 'Location_link.angle'
        db.delete_column('document3D_location_link', 'angle')

        # Deleting field 'Location_link.y'
        db.delete_column('document3D_location_link', 'y')

        # Deleting field 'Location_link.x'
        db.delete_column('document3D_location_link', 'x')

        # Deleting field 'Location_link.z'
        db.delete_column('document3D_location_link', 'z')

        # Deleting field 'Location_link.rx'
        db.delete_column('document3D_location_link', 'rx')

        # Deleting field 'Location_link.name_reference'
        db.delete_column('document3D_location_link', 'name_reference')

        # Deleting field 'Location_link.rz'
        db.delete_column('document3D_location_link', 'rz')

        # Deleting field 'Location_link.ry'
        db.delete_column('document3D_location_link', 'ry')

        # Adding field 'Location_link.x1'
        db.add_column('document3D_location_link', 'x1', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.x2'
        db.add_column('document3D_location_link', 'x2', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.x3'
        db.add_column('document3D_location_link', 'x3', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.x4'
        db.add_column('document3D_location_link', 'x4', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.y1'
        db.add_column('document3D_location_link', 'y1', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.y2'
        db.add_column('document3D_location_link', 'y2', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.y3'
        db.add_column('document3D_location_link', 'y3', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.y4'
        db.add_column('document3D_location_link', 'y4', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.z1'
        db.add_column('document3D_location_link', 'z1', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.z2'
        db.add_column('document3D_location_link', 'z2', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.z3'
        db.add_column('document3D_location_link', 'z3', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.z4'
        db.add_column('document3D_location_link', 'z4', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.name'
        db.add_column('document3D_location_link', 'name', self.gf('django.db.models.fields.CharField')(default='no_name', max_length=100), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'stp_to_jss_arborescense'
        db.create_table('document3D_stp_to_jss_arborescense', (
            ('stp', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plmapp.DocumentFile'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('js', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('document3D', ['stp_to_jss_arborescense'])

        # Adding field 'Location_link.angle'
        db.add_column('document3D_location_link', 'angle', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.y'
        db.add_column('document3D_location_link', 'y', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.x'
        db.add_column('document3D_location_link', 'x', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.z'
        db.add_column('document3D_location_link', 'z', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.rx'
        db.add_column('document3D_location_link', 'rx', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.name_reference'
        db.add_column('document3D_location_link', 'name_reference', self.gf('django.db.models.fields.CharField')(default='no_name', max_length=100), keep_default=False)

        # Adding field 'Location_link.rz'
        db.add_column('document3D_location_link', 'rz', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Location_link.ry'
        db.add_column('document3D_location_link', 'ry', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Deleting field 'Location_link.x1'
        db.delete_column('document3D_location_link', 'x1')

        # Deleting field 'Location_link.x2'
        db.delete_column('document3D_location_link', 'x2')

        # Deleting field 'Location_link.x3'
        db.delete_column('document3D_location_link', 'x3')

        # Deleting field 'Location_link.x4'
        db.delete_column('document3D_location_link', 'x4')

        # Deleting field 'Location_link.y1'
        db.delete_column('document3D_location_link', 'y1')

        # Deleting field 'Location_link.y2'
        db.delete_column('document3D_location_link', 'y2')

        # Deleting field 'Location_link.y3'
        db.delete_column('document3D_location_link', 'y3')

        # Deleting field 'Location_link.y4'
        db.delete_column('document3D_location_link', 'y4')

        # Deleting field 'Location_link.z1'
        db.delete_column('document3D_location_link', 'z1')

        # Deleting field 'Location_link.z2'
        db.delete_column('document3D_location_link', 'z2')

        # Deleting field 'Location_link.z3'
        db.delete_column('document3D_location_link', 'z3')

        # Deleting field 'Location_link.z4'
        db.delete_column('document3D_location_link', 'z4')

        # Deleting field 'Location_link.name'
        db.delete_column('document3D_location_link', 'name')


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
        'document3D.arbrefile_documentfile_stp': {
            'Meta': {'object_name': 'arbrefile_documentFile_stp'},
            'arbrefile': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.DocumentFile']"})
        },
        'document3D.document3d': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'Document3D', '_ormbases': ['plmapp.Document']},
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'document3D.location_link': {
            'Meta': {'object_name': 'Location_link', '_ormbases': ['plmapp.ParentChildLinkExtension']},
            'name': ('django.db.models.fields.CharField', [], {'default': "'no_name'", 'max_length': '100'}),
            'parentchildlinkextension_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.ParentChildLinkExtension']", 'unique': 'True', 'primary_key': 'True'}),
            'x1': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'x2': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'x3': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'x4': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'y1': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'y2': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'y3': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'y4': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'z1': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'z2': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'z3': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'z4': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        'document3D.stp_to_jss': {
            'Meta': {'object_name': 'stp_to_jss'},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {}),
            'js': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'stp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.DocumentFile']"})
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
        'plmapp.groupinfo': {
            'Meta': {'object_name': 'GroupInfo', '_ormbases': ['auth.Group']},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groupinfo_creator'", 'to': "orm['auth.User']"}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 2, 16, 4, 55, 906364)'}),
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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 2, 16, 4, 55, 908718)'}),
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

    complete_apps = ['document3D']
