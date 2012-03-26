"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
#openPLM$ openPLM3D="enabled" ./manage.py test document3D --settings=settings_tests
from django.http import HttpResponse ,HttpResponseRedirect , HttpRequest
from django.test import TestCase
from openPLM.document3D.views import *
from openPLM.document3D.forms import *
from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.document3D.models import  Document3DController , Document_part_doc_links_Error
from django.core.files import File

 
    
class view_3dTest(CommonViewTest):

    def setUp(self):
        super(view_3dTest, self).setUp()
        self.document = Document3DController.create('doc1', 'Document3D',
                'a', self.user, self.DATA)
                
    def update_time(self,data):
        data.update({u'last_modif_time': [u'%s-%s-%s %s:%s:%s'%(self.document.mtime.year,self.document.mtime.month,self.document.mtime.day,self.document.mtime.hour,self.document.mtime.minute,self.document.mtime.second)],
           u'last_modif_microseconds' : [u'%s'%self.document.mtime.microsecond]
           })
                   
    def test_view3D_stp_decompose(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile) 
        self.controller.attach_to_document(self.document.object)                                                                   
        data = data1
        self.update_time(data)
        self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data) 
        response = self.get(self.document.object.plmobject_url+"3D/")        
        self.assertEqual(len(response.context["GeometryFiles"]), 3)
         
    def test_3D_no_stp_associe(self):   
    
        response = self.get(self.document.object.plmobject_url+"3D/")
        self.assertEqual(response.context["GeometryFiles"], [])
        self.assertEqual(response.context["javascript_arborescense"], False)
        
    def test_3D_stp_associe_sans_arborescense(self):   
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)       
        ArbreFile.objects.get(stp=new_doc_file).delete()
        response = self.get(self.document.object.plmobject_url+"3D/")    
        self.assertEqual(3, len(list(response.context["GeometryFiles"])))
        self.assertEqual(response.context["javascript_arborescense"], False)

    def test_3D_stp_valide_no_info(self):   
        f=open("document3D/data_test/valid_sans_information.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)       
        response = self.get(self.document.object.plmobject_url+"3D/")    
        self.assertEqual(response.context["GeometryFiles"],[])
        self.assertNotEqual(response.context["javascript_arborescense"], False)    
                
    def test_3D_stp_associe_sans_geometry_with_arborescense(self):   
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)       
        GeometryFile.objects.filter(stp=new_doc_file).delete()
        response = self.get(self.document.object.plmobject_url+"3D/")    
        self.assertEqual([], response.context["GeometryFiles"])
        self.assertNotEqual(response.context["javascript_arborescense"], False)  
       
class view_bomb_childTest(CommonViewTest):
    def setUp(self):
        super(view_bomb_childTest, self).setUp()
        self.document = Document3DController.create('doc1', 'Document3D',
                'a', self.user, self.DATA)

    def test_bomb_child(self):
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child1, 10 , 20)
        child2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        child3 = child2.create("c3", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child2, 10, 20)
        response = self.get(self.base_url + "BOM-child/", page="BOM-child")
        self.assertEqual(2, len(list(response.context["children"])))
        msg = response.context["decomposition_msg"]
        self.assertFalse(msg)
        
        
    def test_decompose_bomb_child(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile) 
        self.controller.attach_to_document(self.document.object)
        response = self.get(self.base_url + "BOM-child/", page="BOM-child")  
        self.assertEqual(0, len(list(response.context["children"])))
        msg = response.context["decomposition_msg"]
        self.assertTrue(msg)
        
        
    def test_decompose_bomb_child_whit_child_decomposable(self):
        child2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child2, 10, 20)
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile) 
        child2.attach_to_document(self.document.object)
        self.controller.attach_to_document(self.document.object)
        response = self.get(self.base_url + "BOM-child/", page="BOM-child")  
        self.assertEqual(1, len(list(response.context["children"])))
        msg = response.context["decomposition_msg"]
        self.assertTrue(msg)
        self.assertEqual(True, response.context["children"][0][1])        
        
    def test_try_decompose_bomb_child_whit_no_links(self):
        f=open("document3D/data_test/valid_sans_information.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile) 
        self.controller.attach_to_document(self.document.object)
        response = self.get(self.base_url+"decompose/"+str(new_doc_file.id)+"/")  
                        
class view_decomposeTest(CommonViewTest):

    def setUp(self):
        super(view_decomposeTest, self).setUp()
        self.document = Document3DController.create('doc1', 'Document3D',
                'a', self.user, self.DATA)


    def update_time(self,data):
        data.update({u'last_modif_time': [u'%s-%s-%s %s:%s:%s'%(self.document.mtime.year,self.document.mtime.month,self.document.mtime.day,self.document.mtime.hour,self.document.mtime.minute,self.document.mtime.second)],
           u'last_modif_microseconds' : [u'%s'%self.document.mtime.microsecond]
           })
                  
    #verificar los links creados en las buenas coordenadas      
    def test_display_decompose_form_initial(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)  
               
         
           
        Select_Doc_Part_types = formset_factory(Doc_Part_type_Form)
        Select_Order_Quantity_types = formset_factory(Order_Quantity_Form)
        data = {
        'form-TOTAL_FORMS': u'2',
        'form-INITIAL_FORMS': u'2',
        'form-MAX_NUM_FORMS': u'2',
        }
        quantity=[1,3]
        for i in range(2):
            order=(i+1)*10
            data.update({'form-%s-order'%i :u'%s'%order,
                         'form-%s-quantity'%i : u'%s'%quantity[i],
                         'form-%s-type_part'%i :u'Part',
                         'form-%s-type_document3D'%i : u'Document3D',
                        }) 
        form_Doc_Part_types = Select_Doc_Part_types(data)      
        form_Order_Quantity = Select_Order_Quantity_types(data) 
        
        
        reponse = self.get(self.base_url+"decompose/"+str(new_doc_file.id)+"/")

        self.assertEqual(reponse.context["form_Doc_Part_types"].as_table(), form_Doc_Part_types.as_table())
        self.assertEqual(reponse.context["form_Order_Quantity"].as_table(), form_Order_Quantity.as_table()) 
    
                  
               
 
    def test_display_decompose_form_post(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                                          
        data = data1
        self.update_time(data)
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertRedirects(reponse_post, self.base_url + "BOM-child/")
        
    def test_display_decompose_time_modification_diferent(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                                          
        data = data1
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse_post.context["extra_errors"],"The Document3D associated with the file STEP to decompose has been modified by another user while the forms were refilled:Please restart the process")
        
    def test_display_decompose_time_modification_invalid(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                                          
        data = data1
        data.update({u'last_modif_time': [u'not_valid'],
           u'last_modif_microseconds' : [u'not_valid']
           })
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse_post.context["extra_errors"],"Mistake reading of the last modification of the document, please restart the task")
        
                        
    def test_display_decompose_file_locked(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        self.document.lock(new_doc_file)     
        self.controller.attach_to_document(self.document.object)                                                          
        data = data1
        self.update_time(data)
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse_post.context["extra_errors"],"Documentfile is locked")
        
        
    def test_display_decompose_Document_part_doc_links_Error(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                                          
        data = data6
        self.update_time(data)
        reponse=self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse.context["extra_errors"],u"Columns reference, type, revision are not unique")
        
    def test_display_decompose_Document3D_decomposer_Error(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                                          
        data = data1
        self.update_time(data)
        GeometryFile.objects.filter(stp=new_doc_file).delete()
        reponse=self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse.context["extra_errors"],u"Error while the file step was decomposed")        

            
    def test_display_decompose_form_Order_Quantity_error_post(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                          
        data = data2
        self.update_time(data)             
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse_post.context["form_Order_Quantity"].errors,[{'quantity': [u'This field is required.']}, {}])

    
    
    def test_display_decompose_form_Doc_Part_types_error_post(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                          
        data = data3
        self.update_time(data)       
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse_post.context["form_Doc_Part_types"].errors,[{}, {'type_document3D': [u'Select a valid choice. not_exits_Document4D362182 is not one of the available choices.']}]
)
     
    def test_display_decompose_form_Doc_Part_attributes_error_post(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                          
        data = data4 
        self.update_time(data)    
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        zip=reponse_post.context["zip"]         
        index=0
        for type, atributes , ord_qty in zip:
            if index==1:
                self.assertEqual(atributes[0].errors,{'group': [u'Bad group, check that the group exists and that you belong to this group.']})
            index+=1
    
    def test_display_Ajax(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)   
        reponse_ajax = self.client.get("/ajax/decompose/"+data5)
        zip=reponse_ajax.context["zip"]
        index=0
        for type, atributes , ord_qty in zip:
            if index==1:
                self.assertEqual(atributes[0].as_table() ,data5_1)
            index+=1                                     


 



data1={u'2-lifecycle': [u'draft_official_deprecated'], u'3-lifecycle': [u'draft_official_deprecated'], u'reference': [u'PART_00002'], u'form-0-quantity': [u'1'], u'form-1-order': [u'20'], u'3-revision': [u'a'], u'form-1-type_part': [u'Part'], u'initial-3-lifecycle': [u'draft_official_deprecated'], u'2-group': [u'2'], u'form-0-unit': [u'-'], u'1-lifecycle': [u'draft_official_deprecated'], u'3-group': [u'2'], u'group': [u'2'], u'1-revision': [u'a'], u'form-1-quantity': [u'3'], u'2-name': [u'NBA_ASM'], u'form-0-type_part': [u'Part'], u'csrfmiddlewaretoken': [u'6a0951fed02461061f796c63d98bb430', u'6a0951fed02461061f796c63d98bb430'], u'3-name': [u'NBA_ASM'], u'revision': [u'a'], u'initial-2-lifecycle': [u'draft_official_deprecated'], u'initial-1-lifecycle': [u'draft_official_deprecated'], u'form-1-unit': [u'-'], u'1-name': [u'L-BRACKET'], u'form-TOTAL_FORMS': [u'2', u'2'], u'2-reference': [u'PART_00003'], u'2-revision': [u'a'], u'form-INITIAL_FORMS': [u'2', u'2'],  u'lifecycle': [u'draft_official_deprecated'], u'initial-lifecycle': [u'draft_official_deprecated'], u'3-reference': [u'DOC_00003'], u'name': [u'L-BRACKET'], u'form-MAX_NUM_FORMS': [u'2', u'2'], u'1-group': [u'2'], u'form-0-type_document3D': [u'Document3D'], u'form-0-order': [u'10'], u'form-1-type_document3D': [u'Document3D'], u'1-reference': [u'DOC_00002']}


#u'reference': [u'PART_00001']
data6={u'2-lifecycle': [u'draft_official_deprecated'], u'3-lifecycle': [u'draft_official_deprecated'], u'reference': [u'PART_00001'], u'form-0-quantity': [u'1'], u'form-1-order': [u'20'], u'3-revision': [u'a'], u'form-1-type_part': [u'Part'], u'initial-3-lifecycle': [u'draft_official_deprecated'], u'2-group': [u'2'], u'form-0-unit': [u'-'], u'1-lifecycle': [u'draft_official_deprecated'], u'3-group': [u'2'], u'group': [u'2'], u'1-revision': [u'a'], u'form-1-quantity': [u'3'], u'2-name': [u'NBA_ASM'], u'form-0-type_part': [u'Part'], u'csrfmiddlewaretoken': [u'6a0951fed02461061f796c63d98bb430', u'6a0951fed02461061f796c63d98bb430'], u'3-name': [u'NBA_ASM'], u'revision': [u'a'], u'initial-2-lifecycle': [u'draft_official_deprecated'], u'initial-1-lifecycle': [u'draft_official_deprecated'], u'form-1-unit': [u'-'], u'1-name': [u'L-BRACKET'], u'form-TOTAL_FORMS': [u'2', u'2'], u'2-reference': [u'PART_00001'], u'2-revision': [u'a'], u'form-INITIAL_FORMS': [u'2', u'2'],  u'lifecycle': [u'draft_official_deprecated'], u'initial-lifecycle': [u'draft_official_deprecated'], u'3-reference': [u'DOC_00003'], u'name': [u'L-BRACKET'], u'form-MAX_NUM_FORMS': [u'2', u'2'], u'1-group': [u'2'], u'form-0-type_document3D': [u'Document3D'], u'form-0-order': [u'10'], u'form-1-type_document3D': [u'Document3D'], u'1-reference': [u'DOC_00002']}

data2={u'2-lifecycle': [u'draft_official_deprecated'], u'3-lifecycle': [u'draft_official_deprecated'], u'reference': [u'PART_00002'], u'form-0-quantity': [u''], u'form-1-order': [u'20'], u'3-revision': [u'a'], u'form-1-type_part': [u'Part'], u'initial-3-lifecycle': [u'draft_official_deprecated'], u'2-group': [u'2'], u'form-0-unit': [u'-'], u'1-lifecycle': [u'draft_official_deprecated'], u'3-group': [u'2'], u'group': [u'2'], u'1-revision': [u'a'], u'form-1-quantity': [u'3'], u'2-name': [u'NBA_ASM'], u'form-0-type_part': [u'Part'], u'csrfmiddlewaretoken': [u'6a0951fed02461061f796c63d98bb430', u'6a0951fed02461061f796c63d98bb430'], u'3-name': [u'NBA_ASM'], u'revision': [u'a'], u'initial-2-lifecycle': [u'draft_official_deprecated'], u'initial-1-lifecycle': [u'draft_official_deprecated'], u'form-1-unit': [u'-'], u'1-name': [u'L-BRACKET'], u'form-TOTAL_FORMS': [u'2', u'2'], u'2-reference': [u'PART_00003'], u'2-revision': [u'a'], u'form-INITIAL_FORMS': [u'2', u'2'],  u'lifecycle': [u'draft_official_deprecated'], u'initial-lifecycle': [u'draft_official_deprecated'], u'3-reference': [u'DOC_00003'], u'name': [u'L-BRACKET'], u'form-MAX_NUM_FORMS': [u'2', u'2'], u'1-group': [u'2'], u'form-0-type_document3D': [u'Document3D'], u'form-0-order': [u'10'], u'form-1-type_document3D': [u'Document3D'], u'1-reference': [u'DOC_00002']}



data3 ={u'2-lifecycle': [u'draft_official_deprecated'], u'3-lifecycle': [u'draft_official_deprecated'], u'reference': [u'PART_00002'], u'form-0-quantity': [u'1'], u'form-1-order': [u'20'], u'3-revision': [u'a'], u'form-1-type_part': [u'Part'], u'initial-3-lifecycle': [u'draft_official_deprecated'], u'2-group': [u'2'], u'form-0-unit': [u'-'], u'1-lifecycle': [u'draft_official_deprecated'], u'3-group': [u'2'], u'group': [u'2'], u'1-revision': [u'a'], u'form-1-quantity': [u'3'], u'2-name': [u'NBA_ASM'], u'form-0-type_part': [u'Part'], u'csrfmiddlewaretoken': [u'6a0951fed02461061f796c63d98bb430', u'6a0951fed02461061f796c63d98bb430'], u'3-name': [u'NBA_ASM'], u'revision': [u'a'], u'initial-2-lifecycle': [u'draft_official_deprecated'], u'initial-1-lifecycle': [u'draft_official_deprecated'], u'form-1-unit': [u'-'], u'1-name': [u'L-BRACKET'], u'form-TOTAL_FORMS': [u'2', u'2'], u'2-reference': [u'PART_00003'], u'2-revision': [u'a'], u'form-INITIAL_FORMS': [u'2', u'2'],  u'lifecycle': [u'draft_official_deprecated'], u'initial-lifecycle': [u'draft_official_deprecated'], u'3-reference': [u'DOC_00003'], u'name': [u'L-BRACKET'], u'form-MAX_NUM_FORMS': [u'2', u'2'], u'1-group': [u'2'], u'form-0-type_document3D': [u'Document3D'], u'form-0-order': [u'10'], u'form-1-type_document3D': [u'not_exits_Document4D362182'], u'1-reference': [u'DOC_00002']}
 
#u'2-group': [u'1'] 
data4 ={u'2-lifecycle': [u'draft_official_deprecated'], u'3-lifecycle': [u'draft_official_deprecated'], u'reference': [u'PART_00002'], u'form-0-quantity': [u'1'], u'form-1-order': [u'20'], u'3-revision': [u'a'], u'form-1-type_part': [u'Part'], u'initial-3-lifecycle': [u'draft_official_deprecated'], u'2-group': [u'1'], u'form-0-unit': [u'-'], u'1-lifecycle': [u'draft_official_deprecated'], u'3-group': [u'2'], u'group': [u'2'], u'1-revision': [u'a'], u'form-1-quantity': [u'3'], u'2-name': [u'NBA_ASM'], u'form-0-type_part': [u'Part'], u'csrfmiddlewaretoken': [u'6a0951fed02461061f796c63d98bb430', u'6a0951fed02461061f796c63d98bb430'], u'3-name': [u'NBA_ASM'], u'revision': [u'a'], u'initial-2-lifecycle': [u'draft_official_deprecated'], u'initial-1-lifecycle': [u'draft_official_deprecated'], u'form-1-unit': [u'-'], u'1-name': [u'L-BRACKET'], u'form-TOTAL_FORMS': [u'2', u'2'], u'2-reference': [u'PART_00003'], u'2-revision': [u'a'], u'form-INITIAL_FORMS': [u'2', u'2'],  u'lifecycle': [u'draft_official_deprecated'], u'initial-lifecycle': [u'draft_official_deprecated'], u'3-reference': [u'DOC_00003'], u'name': [u'L-BRACKET'], u'form-MAX_NUM_FORMS': [u'2', u'2'], u'1-group': [u'2'], u'form-0-type_document3D': [u'Document3D'], u'form-0-order': [u'10'], u'form-1-type_document3D': [u'not_exits_Document4D362182'], u'1-reference': [u'DOC_00002']}
 
#form-1-type_part=SinglePart 
data5 ="""?csrfmiddlewaretoken=6a0951fed02461061f796c63d98bb430&form-TOTAL_FORMS=2&form-INITIAL_FORMS=2&form-MAX_NUM_FORMS=2&form-TOTAL_FORMS=2&form-INITIAL_FORMS=2&form-MAX_NUM_FORMS=2&last_modif_time=2012-03-06+16%3A43%3A01&last_modif_microseconds=705294&form-0-order=10&form-0-quantity=1&form-0-type_part=Part&reference=PART_00004&revision=a&name=L-BRACKET&lifecycle=draft_official_deprecated&initial-lifecycle=draft_official_deprecated&group=2&form-0-type_document3D=Document3D&1-reference=DOC_00007&1-revision=a&1-name=L-BRACKET&1-lifecycle=draft_official_deprecated&initial-1-lifecycle=draft_official_deprecated&1-group=2&form-1-order=20&form-1-quantity=3&form-1-type_part=SinglePart&2-reference=PART_00005&2-revision=a&2-name=NEW_BOLT&2-lifecycle=draft_official_deprecated&initial-2-lifecycle=draft_official_deprecated&2-group=2&2-supplier=&2-tech_details=Ubuntu&form-1-type_document3D=Document3D&3-reference=DOC_00008&3-revision=a&3-name=NBA_ASM&3-lifecycle=draft_official_deprecated&initial-3-lifecycle=draft_official_deprecated&3-group=2 HTTP/1.1"""
#u'form-1-type_part': [u'SinglePart'] u'1-name': [u'BOLT_NEW']
data5_1 ="""<tr><th><label for="id_2-reference">Reference:</label></th><td><input id="id_2-reference" type="text" name="2-reference" value="PART_00002" maxlength="50" /></td></tr>
<tr><th><label for="id_2-revision">Revision:</label></th><td><input id="id_2-revision" type="text" name="2-revision" value="a" maxlength="50" /></td></tr>
<tr><th><label for="id_2-lifecycle">Lifecycle:</label></th><td><select name="2-lifecycle" id="id_2-lifecycle">
<option value="draft_official_deprecated" selected="selected">Lifecycle&lt;draft_official_deprecated&gt;</option>
</select><input type="hidden" name="initial-2-lifecycle" value="draft_official_deprecated" id="initial-2-id_2-lifecycle" /></td></tr>
<tr><th><label for="id_2-name">Name:</label></th><td><input type="text"  autocomplete="off" name="2-name" id="id_2-name"/>
                <script type="text/javascript"><!--//
                $('#id_2-name').autocomplete({"source": "/ajax/complete/SinglePart/name/"});//--></script>
                <br />Name of the product</td></tr>
<tr><th><label for="id_2-group">Group:</label></th><td><select name="2-group" id="id_2-group">
<option value="" selected="selected">---------</option>
<option value="2">grp</option>
</select></td></tr>
<tr><th><label for="id_2-supplier">Supplier:</label></th><td><input type="text"  autocomplete="off" name="2-supplier" id="id_2-supplier"/>
                <script type="text/javascript"><!--//
                $('#id_2-supplier').autocomplete({"source": "/ajax/complete/SinglePart/supplier/"});//--></script>
                </td></tr>
<tr><th><label for="id_2-tech_details">Tech details:</label></th><td><textarea id="id_2-tech_details" rows="10" cols="40" name="2-tech_details"></textarea></td></tr>"""

