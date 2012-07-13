from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.apps.document3D.models import  Document3DController, Document3D
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
        product = self.document.get_product(self.stp)
        index=[1]
        lifecycle='draft_official_deprecated'
        part_type='Part'
        decomposition_fromPOST_data(data,product,index,self.group.id,lifecycle,part_type)
        if update_time:
            self.update_time(data)
 
        return data
               
    def test_get_product(self):
        #We verify if the structure of the tree is the same for a file without decompose  and the new file generated once decomposed
        
        product = self.document.get_product(self.stp)
        self.post(self.base_url+"decompose/"+str(self.stp.id)+"/",self.data_to_decompose)
        ctrl = Document3DController(Document3D.objects.get(id=self.document.id), self.user)
        product2 = ctrl.get_product(ctrl.files[0], True)  
        self.assertTrue(same_structure(product,product2))
    

    
def same_structure(product,product2):
    if product.name==product2.name:
        for link in product.links:
            print link.names
            try:
                print product2.links
                print[l.names for l in product2.links]
                link2 = [l for l in product2.links if l.names == link.names][0]
            except IndexError:
                return False
            loc1 = set(tuple(loc.to_array()) for loc in link.locations)
            loc2 = set(tuple(loc.to_array()) for loc in link2.locations)
            if loc1 != loc2:
                return False
            if not same_structure(link.product, link2.product):
                return False
    else:
        return False
    
    return True
        

