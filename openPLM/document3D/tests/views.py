"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
#openPLM3D="enabled" ./manage.py test document3D --settings=settings_tests
#/var/django/openPLM/trunk/docs$ make html
#firefox _build/html/index.html
#/var/django/openPLM/trunk/docs/devel/applications/document3D
from django.http import HttpResponse ,HttpResponseRedirect , HttpRequest
from django.test import TestCase
from openPLM.document3D.views import *
from openPLM.document3D.models import *
from openPLM.document3D.forms import *
from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.document3D.models import  Document3DController , Document_Generate_Bom_Error
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
           
    def update_data(self,data,new_doc_file,update_time=True):
        product=ArbreFile_to_Product(new_doc_file)
        index=[1]
        lifecycle='draft_official_deprecated'
        part_type='Part'
        decomposition_fromPOST_data(data,product,index,self.group.id,lifecycle,part_type)
        if update_time:
            self.update_time(data)
    """                       
    def test_view3D_stp_decompose(self):
        f=open("document3D/data_test/test2.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile) 
        self.controller.attach_to_document(self.document.object)        
        data={}   
        self.update_data(data,new_doc_file)
        self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertFalse(is_decomposable(self.document.object))
        reponse = self.get(self.document.object.plmobject_url+"3D/")        
        self.assertEqual(len(reponse.context["GeometryFiles"]), 5)
                       

            
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
       


    def test_bom_child(self):
        child1 = PartController.create("c1", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child1, 10 , 20)
        child2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        child3 = child2.create("c3", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child2, 10, 20)
        response = self.get(self.base_url + "BOM-child/", page="BOM-child")
        self.assertEqual(2, len(list(response.context["children"])))
        msg = response.context["decomposition_msg"]
        self.assertFalse(msg)
        
        
    def test_decompose_bom_child(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile) 
        self.controller.attach_to_document(self.document.object)
        response = self.get(self.base_url + "BOM-child/", page="BOM-child")  
        self.assertEqual(0, len(list(response.context["children"])))
        msg = response.context["decomposition_msg"]
        self.assertTrue(msg)
        
        
    def test_decompose_bom_child_whit_child_decomposable(self):
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
        decomposable_children = response.context["decomposable_children"]
        self.assertTrue(response.context["children"][0].link.child.id
            in decomposable_children)
        
    def test_try_decompose_bom_child_whit_no_links(self):
        f=open("document3D/data_test/valid_sans_information.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile) 
        self.controller.attach_to_document(self.document.object)
        response = self.get(self.base_url+"decompose/"+str(new_doc_file.id)+"/")  
                        
                  
    #verificar los links creados en las buenas coordenadas      
    def test_display_decompose_form_initial(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)  
        response = self.get(self.base_url+"decompose/"+str(new_doc_file.id)+"/")
        # TODO: check forms


    def test_display_decompose_form_post(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)    
                                                              
        data={}
        self.update_data(data,new_doc_file)


        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertRedirects(reponse_post, self.base_url + "BOM-child/")

           
    def test_display_decompose_time_modification_diferent(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                                          
        data={}
        self.update_data(data,new_doc_file)
        
        data.update({u'last_modif_time': [u'%s-%s-%s %s:%s:%s'%             (self.document.mtime.year,(self.document.mtime.month),self.document.mtime.day,self.document.mtime.hour-1,self.document.mtime.minute-2,self.document.mtime.second)],
           u'last_modif_microseconds' : [u'%s'%self.document.mtime.microsecond]
           })
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
        self.assertEqual(reponse_post.context["extra_errors"],"The Document3D associated with the file STEP to decompose has been modified by another user while the forms were refilled:Please restart the process")

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
        
    def test_display_decompose_bom_formset_error_post(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                          
        data = data2
        self.update_time(data)             
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse_post.context["bom_formset"].errors,[{'quantity': [u'This field is required.']}, {}])


    def test_display_decompose_part_type_formset_error_post(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                          
        data = data3
        self.update_time(data)       
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse_post.context["part_type_formset"].errors,
                [{'type_part': [u'Select a valid choice. Part54545 is not one of the available choices.']}, {}]
)
   
    def test_display_decompose_creation_formset_error_post(self):
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)     
        self.controller.attach_to_document(self.document.object)                                          
        data = data4 
        self.update_time(data)    
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        forms = reponse_post.context["forms"]         
        index=0
        for type, atributes, ord_qty in forms:
            if index==1:
                self.assertEqual(atributes[0].errors,{'group': [u'Bad group, check that the group exists and that you belong to this group.']})
            index+=1

    """   
                          




data1={u'2-lifecycle': [u'draft_official_deprecated'],
  u'3-lifecycle': [u'draft_official_deprecated'],
  u'0-reference': [u'PART_00002'],
  u'form-0-quantity': [u'1'],
  u'form-1-order': [u'20'],
  u'3-revision': [u'a'],
  u'form-1-type_part': [u'Part'],
  u'initial-3-lifecycle': [u'draft_official_deprecated'],
  u'2-group': [u'2'],
  u'form-0-unit': [u'-'],
  u'1-lifecycle': [u'draft_official_deprecated'],
  u'3-group': [u'2'],
  u'0-group': [u'2'],
  u'1-revision': [u'a'],
  u'form-1-quantity': [u'3'],
  u'2-name': [u'NBA_ASM'],
  u'form-0-type_part': [u'Part'],
  u'3-name': [u'NBA_ASM'],
  u'0-revision': [u'a'],
  u'initial-2-lifecycle': [u'draft_official_deprecated'],
  u'initial-1-lifecycle': [u'draft_official_deprecated'],
  u'form-1-unit': [u'-'],
  u'1-name': [u'L-BRACKET'],
  u'form-TOTAL_FORMS': [u'2',
  u'2'],
  u'2-reference': [u'PART_00003'],
  u'2-revision': [u'a'],
  u'form-INITIAL_FORMS': [u'2', u'2'],
  u'0-lifecycle': [u'draft_official_deprecated'],
  u'initial-lifecycle': [u'draft_official_deprecated'],
  u'3-reference': [u'DOC_00003'],
  u'0-name': [u'L-BRACKET'],
  u'form-MAX_NUM_FORMS': [u'2', u'2'],
  u'1-group': [u'2'],
  u'form-0-type_document3D': [u'Document3D'],
  u'form-0-order': [u'10'],
  u'form-1-type_document3D': [u'Document3D'],
  u'1-reference': [u'DOC_00002']}


#u'reference': [u'PART_00001']
data6={u'2-lifecycle': [u'draft_official_deprecated'],
  u'3-lifecycle': [u'draft_official_deprecated'],
  u'0-reference': [u'PART_00001'],
  u'form-0-quantity': [u'1'],
  u'form-1-order': [u'20'],
  u'3-revision': [u'a'],
  u'form-1-type_part': [u'Part'],
  u'initial-3-lifecycle': [u'draft_official_deprecated'],
  u'2-group': [u'2'],
  u'form-0-unit': [u'-'],
  u'1-lifecycle': [u'draft_official_deprecated'],
  u'3-group': [u'2'],
  u'0-group': [u'2'],
  u'1-revision': [u'a'],
  u'form-1-quantity': [u'3'],
  u'2-name': [u'NBA_ASM'],
  u'form-0-type_part': [u'Part'],
  u'csrfmiddlewaretoken': [u'6a0951fed02461061f796c63d98bb430',
  u'6a0951fed02461061f796c63d98bb430'],
  u'3-name': [u'NBA_ASM'],
  u'0-revision': [u'a'],
  u'initial-2-lifecycle': [u'draft_official_deprecated'],
  u'initial-1-lifecycle': [u'draft_official_deprecated'],
  u'form-1-unit': [u'-'],
  u'1-name': [u'L-BRACKET'],
  u'form-TOTAL_FORMS': [u'2',
  u'2'],
  u'2-reference': [u'PART_00001'],
  u'2-revision': [u'a'],
  u'form-INITIAL_FORMS': [u'2', u'2'],
  u'0-lifecycle': [u'draft_official_deprecated'],
  u'initial-lifecycle': [u'draft_official_deprecated'],
  u'3-reference': [u'DOC_00003'],
  u'0-name': [u'L-BRACKET'],
  u'form-MAX_NUM_FORMS': [u'2',
  u'2'],
  u'1-group': [u'2'],
  u'form-0-type_document3D': [u'Document3D'],
  u'form-0-order': [u'10'],
  u'form-1-type_document3D': [u'Document3D'],
  u'1-reference': [u'DOC_00002']}

data2={u'2-lifecycle': [u'draft_official_deprecated'],
  u'3-lifecycle': [u'draft_official_deprecated'],
  u'0-reference': [u'PART_00002'],
  u'form-0-quantity': [u''],
  u'form-1-order': [u'20'],
  u'3-revision': [u'a'],
  u'form-1-type_part': [u'Part'],
  u'initial-3-lifecycle': [u'draft_official_deprecated'],
  u'2-group': [u'2'],
  u'form-0-unit': [u'-'],
  u'1-lifecycle': [u'draft_official_deprecated'],
  u'3-group': [u'2'],
  u'0-group': [u'2'],
  u'1-revision': [u'a'],
  u'form-1-quantity': [u'3'],
  u'2-name': [u'NBA_ASM'],
  u'form-0-type_part': [u'Part'],
  u'3-name': [u'NBA_ASM'],
  u'0-revision': [u'a'],
  u'initial-2-lifecycle': [u'draft_official_deprecated'],
  u'initial-1-lifecycle': [u'draft_official_deprecated'],
  u'form-1-unit': [u'-'],
  u'1-name': [u'L-BRACKET'],
  u'form-TOTAL_FORMS': [u'2',
  u'2'],
  u'2-reference': [u'PART_00003'],
  u'2-revision': [u'a'],
  u'form-INITIAL_FORMS': [u'2',
  u'2'],
  u'0-lifecycle': [u'draft_official_deprecated'],
  u'initial-lifecycle': [u'draft_official_deprecated'],
  u'3-reference': [u'DOC_00003'],
  u'0-name': [u'L-BRACKET'],
  u'form-MAX_NUM_FORMS': [u'2', u'2'],
  u'1-group': [u'2'],
  u'form-0-type_document3D': [u'Document3D'],
  u'form-0-order': [u'10'],
  u'form-1-type_document3D': [u'Document3D'],
  u'1-reference': [u'DOC_00002']}



data3 ={u'2-lifecycle': [u'draft_official_deprecated'],
  u'3-lifecycle': [u'draft_official_deprecated'],
  u'0-reference': [u'PART_00002'],
  u'form-0-quantity': [u'1'],
  u'form-1-order': [u'20'],
  u'3-revision': [u'a'],
  u'form-1-type_part': [u'Part'],
  u'initial-3-lifecycle': [u'draft_official_deprecated'],
  u'2-group': [u'2'],
  u'form-0-unit': [u'-'],
  u'1-lifecycle': [u'draft_official_deprecated'],
  u'3-group': [u'2'],
  u'0-group': [u'2'],
  u'1-revision': [u'a'],
  u'form-1-quantity': [u'3'],
  u'2-name': [u'NBA_ASM'],
  u'form-0-type_part': [u'Part54545'],
  u'3-name': [u'NBA_ASM'],
  u'0-revision': [u'a'],
  u'initial-2-lifecycle': [u'draft_official_deprecated'],
  u'initial-1-lifecycle': [u'draft_official_deprecated'],
  u'form-1-unit': [u'-'],
  u'1-name': [u'L-BRACKET'],
  u'form-TOTAL_FORMS': [u'2',
  u'2'],
  u'2-reference': [u'PART_00003'],
  u'2-revision': [u'a'],
  u'form-INITIAL_FORMS': [u'2',
  u'2'],
  u'0-lifecycle': [u'draft_official_deprecated'],
  u'initial-lifecycle': [u'draft_official_deprecated'],
  u'3-reference': [u'DOC_00003'],
  u'0-name': [u'L-BRACKET'],
  u'form-MAX_NUM_FORMS': [u'2',
  u'2'],
  u'1-group': [u'2'],
  u'form-0-type_document3D': [u'Document3D'],
  u'form-0-order': [u'10'],
  u'1-reference': [u'DOC_00002']}
 
#u'2-group': [u'1'] 
data4 ={u'2-lifecycle': [u'draft_official_deprecated'],
  u'3-lifecycle': [u'draft_official_deprecated'],
  u'0-reference': [u'PART_00002'],
  u'form-0-quantity': [u'1'],
  u'form-1-order': [u'20'],
  u'3-revision': [u'a'],
  u'form-1-type_part': [u'Part'],
  u'initial-3-lifecycle': [u'draft_official_deprecated'],
  u'2-group': [u'1'],
  u'form-0-unit': [u'-'],
  u'1-lifecycle': [u'draft_official_deprecated'],
  u'3-group': [u'2'],
  u'0-group': [u'2'],
  u'1-revision': [u'a'],
  u'form-1-quantity': [u'3'],
  u'2-name': [u'NBA_ASM'],
  u'form-0-type_part': [u'Part'],
  u'3-name': [u'NBA_ASM'],
  u'0-revision': [u'a'],
  u'initial-2-lifecycle': [u'draft_official_deprecated'],
  u'initial-1-lifecycle': [u'draft_official_deprecated'],
  u'form-1-unit': [u'-'],
  u'1-name': [u'L-BRACKET'],
  u'form-TOTAL_FORMS': [u'2',
  u'2'],
  u'2-reference': [u'PART_00003'],
  u'2-revision': [u'a'],
  u'form-INITIAL_FORMS': [u'2',
  u'2'],
  u'0-lifecycle': [u'draft_official_deprecated'],
  u'initial-lifecycle': [u'draft_official_deprecated'],
  u'3-reference': [u'DOC_00003'],
  u'0-name': [u'L-BRACKET'],
  u'form-MAX_NUM_FORMS': [u'2',
  u'2'],
  u'1-group': [u'2'],
  u'form-0-type_document3D': [u'Document3D'],
  u'form-0-order': [u'10'],
  u'form-1-type_document3D': [u'not_exits_Document4D362182'],
  u'1-reference': [u'DOC_00002']}
  
  
def decomposition_fromPOST_data(data,product,index,group,lifecycle,part_type):

    if product.links:
        for order , link in enumerate(product.links):
            data.update({
                    "%s-order"%index[0] : [u'%s'%((order+1)*10)],
                    "%s-quantity"%index[0] : [u'%s'%link.quantity],
                    "%s-unit"%index[0] : [u'-'],
            })            
            if not link.product.visited: 
                data.update({
                "%s-type_part"%index[0] : [u'%s'%part_type],
                "%s-part-reference"%index[0] : [u'%s'%index[0]],
                "%s-part-revision"%index[0] : [u'%s'%index[0]],
                "%s-part-name"%index[0]     :  [u'%s'%index[0]],  
                "%s-part-lifecycle"%index[0] : [u'%s'%lifecycle] , 
                "%s-part-group"%index[0] : [u'%s'%group] ,  
                "%s-document-reference"%index[0] : [u'%s'%index[0]],
                "%s-document-revision"%index[0] : [u'%s'%index[0]],
                "%s-document-name"%index[0]     :  [u'%s'%index[0]],  
                "%s-document-lifecycle"%index[0] : [u'%s'%lifecycle] ,
                "%s-document-group"%index[0] :[u'%s'%group] ,    
                })
                link.product.visited=True         
                index[0]+=1                 
                decomposition_fromPOST_data(data,link.product,index,group,lifecycle,part_type)                 
            else:
                index[0]+=1 

                   


        
