
from openPLM.plmapp.controllers.document import DocumentController
from openPLM.plmapp.exceptions import LockError
from openPLM.plmapp.tests.base import BaseTestCase
class DocNativeTestCase(BaseTestCase):


    def setUp(self):
        super(DocNativeTestCase, self).setUp()
        self.document = DocumentController.create('doc1', 'Document',
                'a', self.user, self.DATA)
                   
        
    def test_S_unlock_N_unlock__checkout_S(self):

        native=self.document.add_file(self.get_file("test.fcstd"))
        standar=self.document.add_file(self.get_file("test.stp"))
        self.document.lock(standar)
        native=self.document.deprecated_files.get(id=native.id)
        self.assertTrue(native.deprecated)
        self.assertTrue(standar.locked)
         
    def test_S_locked__Add_N(self):
        standar=self.document.add_file(self.get_file("test.stp"))
        
        self.document.lock(standar)
        self.assertRaises(ValueError, self.document.add_file,
                self.get_file("test.fcstd"))
        self.assertTrue(standar.locked)
        self.assertEqual(self.document.files.count(), 1)            
        
    def test_S_unlock_N_locked__checkout_S(self):

        native=self.document.add_file(self.get_file("test.fcstd"))
        standar=self.document.add_file(self.get_file("test.stp"))

        self.document.lock(native)
        self.assertRaises(LockError, self.document.lock, standar)
        self.assertEqual(native.locked, True)
        self.assertFalse(standar.locked)

    def test_S_locked__checkin_N(self):

        standar=self.document.add_file(self.get_file("test.stp"))

        self.document.lock(standar)
  
        self.document.checkin(standar,self.get_file("test.stp"))
        
        native=self.document.add_file(self.get_file("test.fcstd"))
        self.assertFalse(standar.locked)
        self.assertFalse(native.locked)    
        
    def test_N_lock_S_unloc__checkinN(self):
    
        standar=self.document.add_file(self.get_file("test.stp"))
        native=self.document.add_file(self.get_file("test.fcstd"))
        
        self.document.lock(native)
        
        self.document.checkin(native,self.get_file("test.fcstd"))
        self.document.checkin(standar,self.get_file("test.stp"))      
        
        self.assertFalse(standar.locked)
        self.assertFalse(native.locked) 
        
           
    def test_S_unlock_N_unlock__checkout_N(self):

        native=self.document.add_file(self.get_file("test.fcstd"))
        standar=self.document.add_file(self.get_file("test.stp"))

        self.document.lock(native)
           
        self.assertTrue(native.locked)
        self.assertEqual(standar.native_related, native)   
        self.assertFalse(standar.checkout_valid) 
        
    def test_N_locked__Add_S(self):
        native=self.document.add_file(self.get_file("test.fcstd"))
        self.document.lock(native)
                
        standar=self.document.add_file(self.get_file("test.stp"))
               
        self.assertTrue(native.locked)              
        self.assertFalse(standar.locked)  

