from django.db import models
from django.contrib import admin
from openPLM.plmapp.controllers import DocumentController
from openPLM.plmapp.models import *
#from openPLM.plmapp.filehandlers import HandlersManager
from OCC.gp import *
from django.db.models import Q



#from django.db.models import get_model




#eliminar navegabilidad
#delete del model elimina el stp de docs/stp/ ??



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

        
        
        
        


admin.site.register(Document3D)



from celery.task import task
@task
def handle_step_file(doc_file_pk,object_id,user_id):

    import logging
    logging.getLogger("GarbageCollector").setLevel(logging.ERROR)
    from openPLM.document3D.STP_converter_WebGL import NEW_STEP_Import
    from openPLM.document3D.arborescense import write_ArbreFile
    doc_file = DocumentFile.objects.get(pk=doc_file_pk)
    user=User.objects.get(id=user_id)
    object=Document3D.objects.get(id=object_id)
    controller=Document3DController(object,user) 


    delete_GeometryFiles(doc_file)

    my_step_importer = NEW_STEP_Import(doc_file) 
    my_step_importer.procesing_geometrys()
    product_arbre=my_step_importer.generate_product_arbre()
    write_ArbreFile(product_arbre,doc_file)
    
   
    return True
            
                           


is_stp=Q(filename__iendswith=".stp") | Q(filename__iendswith=".step") 

   
class Document3DController(DocumentController):

                  
     
                      
    def handle_added_file(self, doc_file):

        fileName, fileExtension = os.path.splitext(doc_file.filename)
                      
        if fileExtension.upper() in ('.STP', '.STEP'):
            if self.object.files.filter(is_stp).exclude(id=doc_file.id):
                self.delete_file(doc_file)
                raise ValueError("Only one step documentfile allowed for each document3D")  
            handle_step_file.delay(doc_file.pk,self.object.id,self._user.id)
           
              
        
                    
    def delete_file(self, doc_file):
    
        fileName, fileExtension = os.path.splitext(doc_file.filename)

        if fileExtension.upper() in ('.STP', '.STEP'):
            Document3D=self.object             
            delete_GeometryFiles(doc_file)
            delete_ArbreFile(doc_file)
                       
        super(Document3DController, self).delete_file(doc_file)
        

    def deprecate_file(self, doc_file):
    
    
    
        self.check_permission("owner")
        self.check_editable()
        delete_GeometryFiles(doc_file)
        delete_ArbreFile(doc_file)          
        doc_file.deprecated=True
        doc_file.save()
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
 
admin.site.register(GeometryFile)

def delete_GeometryFiles(doc_file):


    to_delete=GeometryFile.objects.filter(stp=doc_file) 
    list_files=list(to_delete.values_list("file", flat=True))
    delete_files(list_files,media3DGeometryFile.location)
    to_delete.delete()
    
 
          
media3DArbreFile = DocumentStorage(location=settings.MEDIA_ROOT+"3D/")
class ArbreFile(models.Model):
    file = models.FileField(upload_to='.',storage=media3DArbreFile)
    stp = models.ForeignKey(DocumentFile)
     
def delete_ArbreFile(doc_file):


    to_delete=ArbreFile.objects.filter(stp=doc_file) 
    list_files=list(to_delete.values_list("file", flat=True))
    delete_files(list_files,media3DArbreFile.location)
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
    def __unicode__(self):
        return u"Columns reference, type, revision are not unique"        
        
class Product(object):

    __slots__ = ("label_reference","name","doc_id","links","geometry","color")
    
    
    def __init__(self,name,doc_id,label_reference=False,geometry_ref=False,color=False):
        #no tiene location
        self.links = []
        self.label_reference=label_reference
        self.name=name
        self.doc_id=doc_id   #cambiar por step product id
        self.geometry=geometry_ref
        self.color=color
    def set_shape_geometry_related(self,geometry_ref,color):
        self.geometry=geometry_ref
        self.color=color        
    
class Link(object):

    __slots__ = ("names","locations","product","quantity")
    
    
    def __init__(self,product):
  
        self.names=[]           
        self.locations=[]
        self.product=product
        self.quantity=0


    def add_occurrence(self,name,Matrix_rotation):
        if name==u' ' or name==u'':
            self.names.append(self.product.name)    
        else:
            self.names.append(name)
        self.locations.append(Matrix_rotation)
        self.quantity=self.quantity+1

        
class Matrix_rotation(object):

    __slots__ = ("x1","x2","x3","x4","y1","y2","y3","y4","z1","z2","z3","z4")
    
    
    def __init__(self,transformation,list_coord=False):
    
        if list_coord:
            self.x1=list_coord[0]           
            self.x2=list_coord[1] 
            self.x3=list_coord[2] 
            self.x4=list_coord[3] 
            self.y1=list_coord[4]         
            self.y2=list_coord[5] 
            self.y3=list_coord[6] 
            self.y4=list_coord[7] 
            self.z1=list_coord[8]         
            self.z2=list_coord[9] 
            self.z3=list_coord[10] 
            self.z4=list_coord[11]    

        else:   

            m=transformation.VectorialPart()
            gp=m.Row(1)
            self.x1=gp.X()           
            self.x2=gp.Y()
            self.x3=gp.Z()
            self.x4=transformation.Transforms()[0]
            gp=m.Row(2)
            self.y1=gp.X()          
            self.y2=gp.Y()
            self.y3=gp.Z()
            self.y4=transformation.Transforms()[1]
            gp=m.Row(3)
            self.z1=gp.X()         
            self.z2=gp.Y()
            self.z3=gp.Z()
            self.z4=transformation.Transforms()[2]   
    def Transformation(self):
        transformation=gp_Trsf()
        transformation.SetValues(self.x1,self.x2,self.x3,self.x4,self.y1,self.y2,self.y3,self.y4,self.z1,self.z2,self.z3,self.z4,1,1)
        return transformation     
        
    def to_array(self):    
        return [self.x1,self.x2,self.x3,self.x4,self.y1,self.y2,self.y3,self.y4,self.z1,self.z2,self.z3,self.z4] 

"""                    
class Geometry(object):
    
    __slots__ = ("reference", "red", "green", "blue")
    
    def __init__(self,colour,ref):
        self.reference=ref
        if colour:
            self.red=colour.Red()
            self.green=colour.Green()
            self.blue=colour.Blue()
        else:
            self.red = self.green = self.blue = 0        
"""

class Location_link(ParentChildLinkExtension):

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

               
    def Transforms(self):
    
        transformation=gp_Trsf()
        transformation.SetValues(self.x1,self.x2,self.x3,self.x4,self.y1,self.y2,self.y3,self.y4,self.z1,self.z2,self.z3,self.z4,1,1)
        return transformation      
        

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
        
        
admin.site.register(Location_link)
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

class TemplateFiletoDownload(object):
    def __init__(self, path): 
        self.path = path
    def __iter__(self):  
        try: 
            with open(self.path, "rb") as f:
                for line in f:
                    yield line 
        finally:
            os.remove(self.path)                   

@memoize_noarg
def get_all_plmDocument3Dtypes_with_level():
    lst = []
    level=">>"
    get_all_subclasses_with_level(Document3D, lst , level)
    return lst            
    
