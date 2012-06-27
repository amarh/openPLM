from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.apps.document3D.models import  Document3DController, is_decomposable , ArbreFile_to_Product
from django.core.files import File

#from openPLM.apps.document3D.decomposer import decomposer_all  , is_decomposable  #decomposer_product #diviser
from openPLM.apps.document3D.STP_converter_WebGL import NEW_STEP_Import
class decomposer_Test(CommonViewTest):

    def setUp(self):
        super(decomposer_Test, self).setUp()
        self.document = Document3DController.create('doc1', 'Document3D',
                'a', self.user, self.DATA)
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        myfile.name="test.stp"
        self.stp=self.document.add_file(myfile)

        self.ctrl2 = Document3DController.create('doc2', 'Document3D',
                'a', self.user, self.DATA)
        self.links=ArbreFile_to_Product(self.stp).links
        self.my_step_importer=NEW_STEP_Import(self.stp.file.path,self.stp.id)
        self.product=self.my_step_importer.generate_product_arbre() 
            
    def test_is_decomposable(self):

        self.assertTrue(is_decomposable(self.document))
        self.assertFalse(is_decomposable(self.ctrl2))
        
        native=self.document.add_file(self.get_file("test.fcstd"))
        self.document.lock(native)
        self.assertFalse(is_decomposable(self.document))
        
        self.document.unlock(native)
        self.document.lock(self.stp)
        self.assertFalse(is_decomposable(self.document))

