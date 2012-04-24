from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.document3D.models import  Document3DController ,ArbreFile_to_Product
from django.core.files import File 
class arborescense_Test(CommonViewTest):

    def setUp(self):
        super(arborescense_Test, self).setUp()
        self.document = Document3DController.create('doc1', 'Document3D',
                'a', self.user, self.DATA)
        f=open("document3D/data_test/test.stp")
        myfile = File(f)
        self.stp=self.document.add_file(myfile)
        self.controller.attach_to_document(self.document.object)
        self.data_to_decompose = data
        self.data_to_decompose.update({u'last_modif_time': [u'%s-%s-%s %s:%s:%s'%(self.document.mtime.year,self.document.mtime.month,self.document.mtime.day,self.document.mtime.hour,self.document.mtime.minute,self.document.mtime.second)],
           u'last_modif_microseconds' : [u'%s'%self.document.mtime.microsecond]
           })
          

               
                      
"""                       
    def test_ArbreFile_to_Product(self):
        
        #We verify if the structure of the tree is the same for a file without decompose  and the new file generated once decomposed
        
        product=ArbreFile_to_Product(self.stp)
        reponse=self.post(self.base_url+"decompose/"+str(self.stp.id)+"/",self.data_to_decompose)
        doc_file=self.document.files[0] 
        product2=ArbreFile_to_Product(doc_file,self.user)  
        self.assertTrue(same_estructure(product,product2))
    
"""
    
def same_estructure(product,product2):
    if product.name==product2.name:
        for i,link in enumerate(product.links):
            if link.names==product2.links[i].names:
                for t,loc in enumerate(link.locations):
                    if not loc.to_array()==product2.links[i].locations[t].to_array():
                        return False
                if not same_estructure(link.product,product2.links[i].product):
                    return False
            else:
                print product2.links[i].names ,link.names
                return False         
    else:
        return False
    
    return True
        
data={u'2-lifecycle': [u'draft_official_deprecated'], u'3-lifecycle': [u'draft_official_deprecated'], u'reference': [u'PART_00002'], u'form-0-quantity': [u'1'], u'form-1-order': [u'20'], u'3-revision': [u'a'], u'form-1-type_part': [u'Part'], u'initial-3-lifecycle': [u'draft_official_deprecated'], u'2-group': [u'2'], u'form-0-unit': [u'-'], u'1-lifecycle': [u'draft_official_deprecated'], u'3-group': [u'2'], u'group': [u'2'], u'1-revision': [u'a'], u'form-1-quantity': [u'3'], u'2-name': [u'NBA_ASM'], u'form-0-type_part': [u'Part'], u'csrfmiddlewaretoken': [u'6a0951fed02461061f796c63d98bb430', u'6a0951fed02461061f796c63d98bb430'], u'3-name': [u'NBA_ASM'], u'revision': [u'a'], u'initial-2-lifecycle': [u'draft_official_deprecated'], u'initial-1-lifecycle': [u'draft_official_deprecated'], u'form-1-unit': [u'-'], u'1-name': [u'L-BRACKET'], u'form-TOTAL_FORMS': [u'2', u'2'], u'2-reference': [u'PART_00003'], u'2-revision': [u'a'], u'form-INITIAL_FORMS': [u'2', u'2'],  u'lifecycle': [u'draft_official_deprecated'], u'initial-lifecycle': [u'draft_official_deprecated'], u'3-reference': [u'DOC_00003'], u'name': [u'L-BRACKET'], u'form-MAX_NUM_FORMS': [u'2', u'2'], u'1-group': [u'2'], u'form-0-type_document3D': [u'Document3D'], u'form-0-order': [u'10'], u'form-1-type_document3D': [u'Document3D'], u'1-reference': [u'DOC_00002']}
