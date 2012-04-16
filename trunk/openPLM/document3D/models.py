import os.path

from django.db import models
from django.contrib import admin
from openPLM.plmapp.controllers import DocumentController
from openPLM.plmapp.models import *
from django.db.models import Q
from openPLM.document3D.classes import *
from openPLM.document3D.arborescense import *
import subprocess
import tempfile
import time
from django.core.files import File
import django.utils.simplejson as json
from openPLM.plmapp.controllers import get_controller
import copy







class Document3D(Document):
    u"""
    This model of document allows to treat files STEP for his later visualization. It extends Document with the attribute/tab 3D
    """
    
    PartDecompose = models.ForeignKey(Part,null=True)
    
    
    @property
    def menu_items(self):
        items = list(super(Document3D, self).menu_items)        
        items.extend(["3D"])
        return items

    def get_content_and_size(self, doc_file): 
        fileName, fileExtension = os.path.splitext(doc_file.filename)
        if fileExtension.upper() in ('.STP', '.STEP') and not doc_file.deprecated:
            

            product=read_ArbreFile(doc_file,recursif=True)# last True to generate arbre whit doc_file_path insteant doc_file_id
            
            if product and product.is_decomposed:
                temp_file = tempfile.NamedTemporaryFile(delete=True)
                temp_file.write(json.dumps(data_for_product(product)))
                temp_file.seek(0)
                dirname = os.path.dirname(__file__)
                composer = os.path.join(dirname, "generateComposition.py")
                if subprocess.call(["python", composer, temp_file.name]) == 0:
                    size =os.path.getsize(temp_file.name) 
                    return temp_file, size                   
                else:
                    raise Document3D_link_Error 
                
            else:
                return super(Document3D, self).get_content_and_size(doc_file)
            
            pass                
        else:
            return super(Document3D, self).get_content_and_size(doc_file)

#admin.site.register(Document3D)



from celery.task import task
@task(soft_time_limit=60*25,time_limit=60*25)
def handle_step_file(doc_file_pk):



    import logging
    logging.getLogger("GarbageCollector").setLevel(logging.ERROR)
    doc_file = DocumentFile.objects.get(pk=doc_file_pk)
    temp_file = tempfile.TemporaryFile()
    stdout = temp_file.fileno()
    if subprocess.call(["python", "document3D/generate3D.py",doc_file.file.path,str(doc_file.id),settings.MEDIA_ROOT+"3D/"],stdout=stdout) == 0:
        delete_ArbreFile(doc_file)
        delete_GeometryFiles(doc_file)
        generate_relations_BD(doc_file,stdout,temp_file)

    else:
        raise Document3D_link_Error
        pass

    
    
    

        
def generate_relations_BD(doc_file,stdout,temp_file):              
             
    os.lseek(stdout, 0, 0)
    arb = None
    decomposable = False
    for line in temp_file.readlines():
        line=line.rstrip("\n")
        if line.startswith("GEO:"):
            generateGeometry(line.lstrip("GEO:").split(" , "),doc_file)
        if line.startswith("ARB:"):
            arb = line.lstrip("ARB:")
        if line.startswith("Decomposable:"):
            decomposable = line.lstrip("Decomposable:").startswith("true")
    if arb:
        generateArborescense(arb, doc_file, decomposable)

            


def generateGeometry(name_index,doc_file):

    new_GeometryFile= GeometryFile()
    new_GeometryFile.stp = doc_file
    new_GeometryFile.file = name_index[0]
    new_GeometryFile.index = name_index[1]
    new_GeometryFile.save()

def generateArborescense(name, doc_file, decomposable):

    new_ArbreFile= ArbreFile()
    new_ArbreFile.stp = doc_file
    new_ArbreFile.file = name
    new_ArbreFile.decomposable = decomposable
    new_ArbreFile.save()
 

is_stp=Q(filename__iendswith=".stp") | Q(filename__iendswith=".step") 

   
class Document3DController(DocumentController):

                  
     
                      
    def handle_added_file(self, doc_file):

        fileName, fileExtension = os.path.splitext(doc_file.filename)
                      
        if fileExtension.upper() in ('.STP', '.STEP'):
            if self.object.files.filter(is_stp).exclude(id=doc_file.id):
                self.delete_file(doc_file)
                raise ValueError("Only one step documentfile allowed for each document3D") 
            handle_step_file.delay(doc_file.pk)
            #handle_step_file(doc_file.pk)    
              
        
                    
    def delete_file(self, doc_file):
    
        fileName, fileExtension = os.path.splitext(doc_file.filename)

        if fileExtension.upper() in ('.STP', '.STEP'):
            Document3D=self.object             
            delete_GeometryFiles(doc_file)
            delete_ArbreFile(doc_file)
                       
        super(Document3DController, self).delete_file(doc_file)
        

    def deprecate_file(self, doc_file,by_decomposition=False):
    
    
    
        self.check_permission("owner")
        self.check_editable()
        delete_GeometryFiles(doc_file)
        delete_ArbreFile(doc_file)          
        doc_file.deprecated=True
        doc_file.save()
        if by_decomposition:
            self._save_histo("File deprecated for decomposition", "file : %s" % doc_file.filename)           
        else:
            self._save_histo("File deprecated", "file : %s" % doc_file.filename)    
media3DGeometryFile = DocumentStorage(location=settings.MEDIA_ROOT+"3D/")      
class GeometryFile(models.Model):
    u"""
    Link between file STEP present in a Document3D and  files .js that represents his geometries   1..*
    """
    file = models.FileField(upload_to='.',storage=media3DGeometryFile)
    stp = models.ForeignKey(DocumentFile)
    index = models.IntegerField()

    def __unicode__(self):
        return u"GeometryFile<%d:%s, %d>" % (self.stp.id,
            self.stp.filename, self.index)
 
#admin.site.register(GeometryFile)

def delete_GeometryFiles(doc_file):


    to_delete=GeometryFile.objects.filter(stp=doc_file) 
    list_files=list(to_delete.values_list("file", flat=True))
    delete_files(list_files,media3DGeometryFile.location+"/")
    to_delete.delete()
    
 
          
media3DArbreFile = DocumentStorage(location=settings.MEDIA_ROOT+"3D/")
#admin.site.register(ArbreFile)
class ArbreFile(models.Model):
    file = models.FileField(upload_to='.',storage=media3DArbreFile)
    stp = models.ForeignKey(DocumentFile)
    decomposable = models.BooleanField()
     
def delete_ArbreFile(doc_file):


    to_delete=ArbreFile.objects.filter(stp=doc_file) 
    list_files=list(to_delete.values_list("file", flat=True))
    delete_files(list_files,media3DArbreFile.location+"/")
    to_delete.delete()   
    
def delete_files(list_files,ext=""):
    for name in list_files:
        filename=ext+name
        if os.path.exists(filename) and os.path.isfile(filename):
            os.remove(filename)
            
            
class Document3D_link_Error(Exception):
    def __unicode__(self):
        return u"Did not find a file stp associated with the link"
        
              
class Document3D_decomposer_Error(Exception):
    def __init__(self, to_delete=None):  
        self.to_delete=to_delete
    def __unicode__(self):
        return u"Error while the file step was decomposed"
        
class Document_part_doc_links_Error(Exception):
    def __init__(self, to_delete=None,assembly=None):
        self.to_delete=to_delete
        self.assembly=assembly    
    def __unicode__(self):
        return u"Columns reference, type, revision are not unique "+self.assembly         
        


class Location_link(ParentChildLinkExtension):
    #redefinir el garbage collector
    x1=models.FloatField(default=lambda: 0)          
    x2=models.FloatField(default=lambda: 0) 
    x3=models.FloatField(default=lambda: 0) 
    x4=models.FloatField(default=lambda: 0) 
    y1=models.FloatField(default=lambda: 0)         
    y2=models.FloatField(default=lambda: 0) 
    y3=models.FloatField(default=lambda: 0) 
    y4=models.FloatField(default=lambda: 0) 
    z1=models.FloatField(default=lambda: 0)         
    z2=models.FloatField(default=lambda: 0) 
    z3=models.FloatField(default=lambda: 0) 
    z4=models.FloatField(default=lambda: 0)   

    name=models.CharField(max_length=100,default="no_name")    

    """               
    def Transforms(self):
    
        transformation=gp_Trsf()
        transformation.SetValues(self.x1,self.x2,self.x3,self.x4,self.y1,self.y2,self.y3,self.y4,self.z1,self.z2,self.z3,self.z4,1,1)
        return transformation
    """
              
    def to_array(self):    
        return [self.x1,self.x2,self.x3,self.x4,self.y1,self.y2,self.y3,self.y4,self.z1,self.z2,self.z3,self.z4]         

    @classmethod
    def apply_to(cls, parent):
        # only apply to all parts
        return True

    def clone(self, link, save, **data):
    
        x1=data.get("x1", self.x1)         
        x2=data.get("x2", self.x2)
        x3=data.get("x3", self.x3) 
        x4=data.get("x4", self.x4)
        y1=data.get("y1", self.y1)         
        y2=data.get("y2", self.y2) 
        y3=data.get("y3", self.y3)
        y4=data.get("y4", self.y4) 
        z1=data.get("z1", self.z1)         
        z2=data.get("z2", self.z2) 
        z3=data.get("z3", self.z3) 
        z4=data.get("z4", self.z4)   

        name=data.get("name", self.name)
        clone = Location_link(link=link, x1=x1,x2=x2,x3=x3,x4=x4, y1=y1,y2=y2,y3=y3,y4=y4,z1=z1,z2=z2,z3=z3,z4=z4,name=name)
        if save:
            clone.save()
        return clone
        
        
#admin.site.register(Location_link)
register_PCLE(Location_link)

def generate_extra_location_links(link,ParentChildLink):


    for i in range(link.quantity):
        loc=Location_link()
        loc.link=ParentChildLink
        
        array=link.locations[i].to_array()
        
        loc.name=link.names[i]
        loc.x1=array[0]        
        loc.x2=array[1]
        loc.x3=array[2] 
        loc.x4=array[3]
        loc.y1=array[4]         
        loc.y2=array[5] 
        loc.y3=array[6]
        loc.y4=array[7]
        loc.z1=array[8]         
        loc.z2=array[9] 
        loc.z3=array[10] 
        loc.z4=array[11]   
               
                   
        loc.save()       

@memoize_noarg
def get_all_plmDocument3Dtypes_with_level():
    lst = []
    level=">>"
    get_all_subclasses_with_level(Document3D, lst , level)
    return lst
    
     
@task(soft_time_limit=60*25,time_limit=60*25)
def decomposer_all(stp_file_pk,old_product,part_pk,native_related_pk,user_pk):
#old product debe estar actualizado con los path de los ghots y las id
#IMPORTANTE, si quiero limpiar en caso de fallo necesito meter en product la id de la parte para asi poder eliminar los links
    
    try:
        stp_file = DocumentFile.objects.get(pk=stp_file_pk)
        ctrl=get_controller(stp_file.document.type)
        user=User.objects.get(pk=user_pk)
        ctrl=ctrl(stp_file.document,user)
        
        product=generateArbre(json.loads(old_product))   

        new_stp_file=DocumentFile()
        name = new_stp_file.file.storage.get_available_name(product.name+".stp".encode("utf-8"))
        new_stp_path = os.path.join(new_stp_file.file.storage.location, name)
        f = File(open(new_stp_path, 'w'))   
        f.close()
        
        product.doc_path=new_stp_path
        
        
        temp_file = tempfile.NamedTemporaryFile(delete=True)
        temp_file.write(json.dumps(data_for_product(product)))
        temp_file.seek(0)   
        if subprocess.call(["python", "document3D/generateDecomposition.py",stp_file.file.path,temp_file.name]) == 0:
            #el id del root del old procduct tiene que seguir apuntando a a lo antiguao para actualizar los geo.js
            update_child_files_BD(product,user,product.doc_id) 
            update_root_BD(new_stp_file,stp_file,ctrl,product,f,name,part_pk)
               
        else:

            raise Document3D_link_Error      
    
    except Exception as excep:
        print unicode(excep)
        raise excep
        
    finally:
        if not native_related_pk==None:
            native_related = DocumentFile.objects.get(pk=native_related_pk)            
            native_related.deprecated=False
            native_related.save(False)
        stp_file.locked = False
        stp_file.locker = None
        stp_file.save(False)
 
        
    
    
def update_root_BD(new_stp_file,stp_file,ctrl,product,f,name,part_pk):
    
    new_stp_file.filename=product.name+".stp".encode("utf-8")
    new_stp_file.file=name
    new_stp_file.size=f.size
    new_stp_file.document=ctrl.object
    new_stp_file.save()
    os.chmod(new_stp_file.file.path, 0400)  
    ctrl._save_histo("File generated by decomposition", "file : %s" % new_stp_file.filename)    
    product.links=[]
    product.doc_id=new_stp_file.id
    product.doc_path=new_stp_file.file.path
    generate_ArbreFile(product,new_stp_file)     
    ctrl.deprecate_file(stp_file,by_decomposition=True)                          
    Doc3D=Document3D.objects.get(id=ctrl.object.id)
    Doc3D.PartDecompose=Part.objects.get(pk=part_pk)
    Doc3D.save()
    
def update_child_files_BD(product,user,old_id):

    #
        
    for link in product.links:
        if not link.product.visited:
            link.product.visited=True
            product_copy=copy.copy(link.product)  
            doc_file=DocumentFile.objects.get(id=product_copy.doc_id)
            doc_file.filename=product_copy.name+".stp".encode("utf-8")
            doc_file.no_index=False 
            doc_file.size=os.path.getsize(doc_file.file.path) 
            doc_file.locked = False
            doc_file.locker = None
            doc_file.save()
            os.chmod(doc_file.file.path, 0400)   
            product_copy.links=[]
            update_geometry(product_copy,doc_file,old_id)
            generate_ArbreFile(product_copy,doc_file)
                    
            ctrl=get_controller(doc_file.document.type)
            ctrl=ctrl(doc_file.document,user)
            ctrl._save_histo("File generated by decomposition", "file : %s" % doc_file.filename)
            update_child_files_BD(link.product,user,old_id)
    
def is_decomposable(doc3d):
    if not ArbreFile.objects.filter(stp__document=doc3d, 
            stp__deprecated=False, stp__locked=False,
            decomposable=True).exists():
        return False
    try:
        stp_file=DocumentFile.objects.only("document",
                "filename").get(is_stp, locked=False,
                deprecated=False, document=doc3d) #solo abra uno pero por si las moscas
    except:
        return False
    if not ArbreFile.objects.filter(stp=stp_file, decomposable=True).exists():
        return False
    if stp_file.checkout_valid:
        return stp_file      
    return False


def update_geometry(product,doc_file,old_doc_id):

    
   
    if not product.geometry==None:

        old_GeometryFile=GeometryFile.objects.get(stp__id=old_doc_id,index=product.geometry)
        new_GeometryFile= GeometryFile()           

        fileName, fileExtension = os.path.splitext(doc_file.filename)

           
        new_GeometryFile.file = new_GeometryFile.file.storage.get_available_name(fileName+".geo")
        new_GeometryFile.stp = doc_file
        new_GeometryFile.index = product.geometry
        new_GeometryFile.save() 

                     
        infile = open(old_GeometryFile.file.path,"r")
        outfile = open(new_GeometryFile.file.path,"w")

        for line in infile.readlines(): 
            new_line=line.replace("_%s_%s"%(product.geometry,old_doc_id),"_%s_%s"%(product.geometry,doc_file.id))
            outfile.write(new_line)

        



    




           
    
