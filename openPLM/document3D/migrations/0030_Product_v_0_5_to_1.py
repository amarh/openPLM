# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        from openPLM.document3D.classes import Product , Link , Matrix_rotation
        from openPLM.document3D.models import ArbreFile , Document3D , Location_link
        from openPLM.plmapp.models import ParentChildLink



        import django.utils.simplejson as json
        

        
        
        def migrate_Files_arb_0_5_to_1(index_id=[0],doc_file=False):
            try:
                if doc_file:    
                    list=[ArbreFile.objects.get(stp=doc_file)]
                else:   
                    list=ArbreFile.objects.all()      
                for arbre in list:    
                    product =Product_from_Arb_v_0_5(json.loads(arbre.file.read()))
                    if product.id==None:         
                        product.id=index_id[0]   
                        index_id[0]+=1
                        if product.links:
                            migrate_product(product,index_id)                
                        data=data_for_product_v_1(product)
                        output = open(arbre.file.path.encode(),"w+")
                        output.write(json.dumps(data))        
                        output.close()
                        stp_related,list_loc=get_step_related(arbre.stp)
                
                        for stp in stp_related:   
                            migrate_Files_arb_0_5_to_1(index_id,stp)
                return False
            except:
                pass          
                


            
            
            
            
        def migrate_product(product,index_id):


            for link in product.links:
                if not link.product.visited:
                    link.product.visited=True
                    link.product.id=index_id[0]           
                    index_id[0]+=1
                    migrate_product(link.product,index_id)        
                    
                


        def Product_from_Arb_v_0_5(arbre,product=False,product_root=False,deep=0,to_update_product_root=False):   

            label_reference=False
                         
            if not product_root: 
                product=generateProduct_v_0_5(arbre,deep)
                product_root=product
                
                
            elif to_update_product_root: #Important, in case of generation of a tree contained in several files, it supports updated product_root
                product=generateProduct_v_0_5(arbre,deep)
                product_assembly=search_assembly_v_0_5(product.name,label_reference,product.doc_id,product_root,product.geometry,product)
                if product_assembly: 
                    to_update_product_root.links.append(Link(product_assembly))
                    return False 
                else:
                    to_update_product_root.links.append(Link(product)) 
                      
                            
            for i in range(len(arbre)-1):
                
                product_child=generateProduct_v_0_5(arbre[i+1][1],deep+1)
                product_assembly=search_assembly_v_0_5(product_child.name,label_reference,product_child.doc_id,product_root,product_child.geometry,product)

                   
                if product_assembly:
                    product_child=product_assembly 
                    
                   
                                            
                generateLink_v_0_5(arbre[i+1],product,product_child) 
                       
                if not product_assembly:
                    Product_from_Arb_v_0_5(arbre[i+1][1],product_child,product_root,deep+1)  
                    
                   
            return product 


        def search_assembly_v_0_5(name,label,doc_id,product_root,geometry,product_father): 
            if product_root and not product_father==product_root: 
                for link in product_root.links:   
                    if (name and link.product.name==name and  
                    ((geometry and link.product.geometry) or (not geometry and not link.product.geometry))):                                       
                        if label:                    
                            if link.product.label_reference==label:
                                return link.product                                     
                        elif doc_id==link.product.doc_id and geometry==link.product.geometry:
                            return link.product                                        
                    product=search_assembly_v_0_5(name,label,doc_id,link.product, geometry ,product_father)
                    if product:
                        return product
                        
        def generateLink_v_0_5(arbre,product,product_child):
            product.links.append(Link(product_child))
            for i in range(len(arbre[0])):
                product.links[-1].add_occurrence(arbre[0][i][0],Matrix_rotation(arbre[0][i][1]))
                
                         
        def generateProduct_v_0_5(arbre,deep): #+ None in place of product.id
            label_reference=False
            return Product(arbre[0][0],deep,label_reference,arbre[0][1],None,arbre[0][3],arbre[0][2]) 
            
                  
        def data_for_product_v_1(product):
            output=[]    
            output.append([product.name,product.doc_id,product.geometry,product.doc_path,product.id])      
            for link in product.links:
                output.append(data_for_link_v_1(link))    
            return output            

                       
        def data_for_link_v_1(link):
            output=[]    
            name_loc=[]
            for i in range(link.quantity):             
                name_loc.append([link.names[i],link.locations[i].to_array()])                
            output.append(name_loc)        
            output.append(data_for_product_v_1(link.product))        
            return output
            
        def get_step_related_v_0_5(doc_file):
            stp_related=[]
            list_loc=[]
            Doc3D=Document3D.objects.get(id=doc_file.document.id)
            part=Doc3D.PartDecompose
            
            if part:
                list_link=ParentChildLink.objects.filter(parent=part, end_time=None)
                for i in range(len(list_link)):
                    locations=list(Location_link.objects.filter(link=list_link[i]))
                    if locations: 
                        
                        Doc3D=Document3D.objects.filter(PartDecompose=list_link[i].child)
                        if Doc3D.exists():
                            STP_file=Doc3D[0].files.filter(is_stp)
                            if STP_file.exists():
                                stp_related.append(STP_file[0])
                                list_loc.append(locations)
                            else:
                                raise Document3D_link_Error

            else:
                pass
            return stp_related , list_loc
              
        migrate_Files_arb_0_5_to_1()


    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")


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
        'document3D.arbrefile': {
            'Meta': {'object_name': 'ArbreFile'},
            'decomposable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.DocumentFile']"})
        },
        'document3D.document3d': {
            'Meta': {'ordering': "['type', 'reference', 'revision']", 'object_name': 'Document3D', '_ormbases': ['plmapp.Document']},
            'PartDecompose': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.Part']", 'null': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['plmapp.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'document3D.geometryfile': {
            'Meta': {'object_name': 'GeometryFile'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {}),
            'stp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plmapp.DocumentFile']"})
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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 25, 16, 59, 7, 958880)'}),
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
            'ctime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 25, 16, 59, 7, 932601)'}),
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
