from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.apps.document3D.models import  Document3DController
import openPLM.apps.document3D.views

from openPLM.plmapp.decomposers import DecomposersManager
from django.core.files import File

class DecomposerTestCase(CommonViewTest):

    def setUp(self):
        super(DecomposerTestCase, self).setUp()
        self.document = Document3DController.create('doc1', 'Document3D',
                'a', self.user, self.DATA)
        self.controller.attach_to_document(self.document)

        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        myfile.name="test.stp"
        self.stp=self.document.add_file(myfile)

        self.ctrl2 = Document3DController.create('doc2', 'Document3D',
                'a', self.user, self.DATA)
            
    def test_is_decomposable(self):

        self.assertTrue(DecomposersManager.is_decomposable(self.controller.object))
        
        native = self.document.add_file(self.get_file("test.fcstd"))
        self.document.lock(native)
        self.assertFalse(DecomposersManager.is_decomposable(self.controller.object))
        
        self.document.unlock(native)
        self.document.lock(self.stp)
        self.assertFalse(DecomposersManager.is_decomposable(self.controller.object))

        self.controller.detach_document(self.document)
        self.controller.attach_to_document(self.ctrl2)
        self.assertFalse(DecomposersManager.is_decomposable(self.controller.object))
