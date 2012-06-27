from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.apps.document3D.models import  Document3DController ,ArbreFile_to_Product
from django.core.files import File 
from openPLM.apps.document3D.tests.views import decomposition_fromPOST_data
class arborescense_Test(CommonViewTest):

    def setUp(self):
        super(arborescense_Test, self).setUp()
        self.document = Document3DController.create('doc1', 'Document3D',
                'a', self.user, self.DATA)
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        self.stp=self.document.add_file(myfile)
        self.controller.attach_to_document(self.document.object)
        self.data_to_decompose = self.update_data(self.stp)
        
        
        
    def update_time(self,data):
        data.update({u'last_modif_time': [u'%s-%s-%s %s:%s:%s'%(self.document.mtime.year,self.document.mtime.month,self.document.mtime.day,self.document.mtime.hour,self.document.mtime.minute,self.document.mtime.second)],
           u'last_modif_microseconds' : [u'%s'%self.document.mtime.microsecond]
           })
           
           
    def update_data(self,new_doc_file,update_time=True):
        data={}
        product=ArbreFile_to_Product(new_doc_file)
        index=[1]
        lifecycle='draft_official_deprecated'
        part_type='Part'
        decomposition_fromPOST_data(data,product,index,self.group.id,lifecycle,part_type)
        if update_time:
            self.update_time(data)
 
        return data
               
                      
                       
    def test_ArbreFile_to_Product(self):
        
        #We verify if the structure of the tree is the same for a file without decompose  and the new file generated once decomposed
        
        product=ArbreFile_to_Product(self.stp)
        reponse=self.post(self.base_url+"decompose/"+str(self.stp.id)+"/",self.data_to_decompose)
        product2=ArbreFile_to_Product(self.document.files[0],recursif=True)  

        self.assertTrue(same_estructure(product,product2))
    

    
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
        

