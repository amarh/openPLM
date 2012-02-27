
from openPLM.plmapp.controllers.document import DocumentController
from openPLM.plmapp.tests.base import BaseTestCase
from openPLM.plmapp.models import DocumentFile


class gestionDocNativeTestCase(BaseTestCase):


    def setUp(self):
        super(gestionDocNativeTestCase, self).setUp()
        self.document = DocumentController.create('doc1', 'Document',
                'a', self.user, self.DATA)
                   
        
    def test_S_unlock_N_unlock__checkout_S(self):

        native=self.document.add_file(self.get_file("test.fcstd"))
        standar=self.document.add_file(self.get_file("test.stp"))

        self.document.lock(standar)
        
        native=self.document.deprecated_files.get(id=native.id)

   
        self.assertEqual(native.deprecated, True)
        self.assertEqual(standar.locked, True)
        
         
    def test_S_locked__Add_N(self):
    
        
        standar=self.document.add_file(self.get_file("test.stp"))
        
        self.document.lock(standar)
        try:
            native=self.document.add_file(self.get_file("test.fcstd"))
        except ValueError as excep:
            self.assertEqual(standar.locked, True)
            self.assertEqual(excep.message, "File Native has a related Standar File locked")
             
        self.assertEqual(self.document.files.count(),1)            
  
        
    def test_S_unlock_N_locked__checkout_S(self):

        native=self.document.add_file(self.get_file("test.fcstd"))
        standar=self.document.add_file(self.get_file("test.stp"))

        self.document.lock(native)
        try:
            self.document.lock(standar)
        except ValueError as excep:
            self.assertEqual(native.locked, True)
            self.assertEqual(excep.message, "DocumentFile: check-out not possible , native related is locked")       
           
        self.assertEqual(standar.locked, False)
        self.assertEqual(native.locked, True) 


    def test_S_locked__checkin_N(self):

        standar=self.document.add_file(self.get_file("test.stp"))

        self.document.lock(standar)
        

  
        self.document.checkin(standar,self.get_file("test.stp"))
      
        
        native=self.document.add_file(self.get_file("test.fcstd"))
        
                
        self.assertEqual(standar.locked, False)
        self.assertEqual(native.locked, False)    
        
        
    def test_N_lock_S_unloc__checkinN(self):
    
        standar=self.document.add_file(self.get_file("test.stp"))
        native=self.document.add_file(self.get_file("test.fcstd"))
        
        self.document.lock(native)
        
        self.document.checkin(native,self.get_file("test.fcstd"))
        self.document.checkin(standar,self.get_file("test.stp"))      
        
        
                
        self.assertEqual(standar.locked, False)
        self.assertEqual(native.locked, False) 
        
           
    def test_S_unlock_N_unlock__checkout_N(self):

        native=self.document.add_file(self.get_file("test.fcstd"))
        standar=self.document.add_file(self.get_file("test.stp"))

        self.document.lock(native)
           
        self.assertEqual(native.locked, True)
        self.assertEqual(standar.native_related, native)   
        self.assertEqual(standar.checkout_valide, None) 
        
        
    def test_N_locked__Add_S(self):
    
        
        native=self.document.add_file(self.get_file("test.fcstd"))
        self.document.lock(native)
                
        standar=self.document.add_file(self.get_file("test.stp"))
               
        self.assertEqual(native.locked,True)              
        self.assertEqual(standar.locked,False)   
