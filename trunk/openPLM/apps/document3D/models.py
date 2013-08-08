import os.path
import logging
import shutil
import subprocess
import tempfile
import copy
from collections import defaultdict
import json

from djcelery_transactions import task
from django.conf import settings
from django.db import models
from django.contrib import admin
from django.db.models import Q
from django.core.files import File


from openPLM.plmapp.controllers import get_controller, PartController
from openPLM.plmapp.files.formats import is_cad_file
from openPLM.apps.document3D import classes
from openPLM.plmapp.controllers import DocumentController
import openPLM.plmapp.models as pmodels
from openPLM.plmapp.exceptions import ControllerError

#./manage.py graph_models document3D > models.dot   dot -Tpng models.dot > models.png


class Document3D(pmodels.Document):
    u"""
    Model which allows to treat :class:`~django.core.files.File` **.stp**  attached to  :class:`.DocumentFile` for his later **visualization** and **decomposition**. It extends :class:`.Document` with the attribute/tab 3D

     .. attribute:: PartDecompose

        If the :class:`.Document3D` has been *decomposed*, :class:`.Part` from which we generate the **decomposition**
    """

    PartDecompose = models.ForeignKey(pmodels.Part,null=True)

    @property
    def menu_items(self):
        """
        Add Tab 3D
        """
        items = list(super(Document3D, self).menu_items)
        items.extend(["3D"])
        return items

    def get_content_and_size(self, doc_file):
        """
        :param doc_file: :class:`.DocumentFile` which contains the :class:`~django.core.files.File`
        :type plmobject: :class:`.DocumentFile`

        Returns the :class:`~django.core.files.File` related to the  :class:`.DocumentFile` (**doc_file**) and his *size*

        If the :class:`~django.core.files.File` contains in the :class:`.DocumentFile` (**doc_file**) is a **.stp** and was *decomposed* , this function calls a subprocess( :meth:`.composer` ) to rebuild the .stp :class:`~django.core.files.File`
        """

        fileName, fileExtension = os.path.splitext(doc_file.filename)
        if fileExtension.upper() in ('.STP', '.STEP') and not doc_file.deprecated:
            tempfile_size = self.recompose_step_file(doc_file)
            if tempfile_size:
                return tempfile_size[0] ,tempfile_size[1]  #temp_file , size

        return super(Document3D, self).get_content_and_size(doc_file)

    def recompose_step_file(self, doc_file):
        product = Document3DController(self, None).get_product(doc_file, True)

        if product and product.is_decomposed:
            temp_file = tempfile.NamedTemporaryFile(delete=True)
            temp_file.write(json.dumps(product.to_list()))
            temp_file.seek(0)
            dirname = os.path.dirname(__file__)
            composer = os.path.join(dirname, "generateComposition.py")
            if subprocess.call(["python", composer, temp_file.name]) == 0:
                size = os.path.getsize(temp_file.name)
                temp_file.seek(0)
                return temp_file, size
            else:
                raise RuntimeError("Could not recompose step file")
        return False

    @property
    def documents_related(self):
        """
        If the :class:`.Document3D` has been decomposed, it returns a list with all the :class:`.Document3D` that form part of the decomposition,
        and for every :class:`.Document3D` for ONLY ONE level of depth
        """
        document_related = []
        part = self.PartDecompose
        if part:
            links = pmodels.ParentChildLink.current_objects.filter(parent=part)
            for link in links:
                if Location_link.objects.filter(link=link).exists():
                    document_related.append(Document3D.objects.get(PartDecompose=link.child))
        return document_related

    @classmethod
    def get_creation_score(cls, files):
        if any(is_cad_file(f.filename) for f in files):
            return 50
        return super(Document3D, cls).get_creation_score(files)


admin.site.register(Document3D)


@task(name="openPLM.apps.document3D.handle_step_file",
      soft_time_limit=60*25,time_limit=60*25)
def handle_step_file(doc_file_pk):
    """

    :param doc_file_pk: primery key of a :class:`.DocumentFile` that will be treated

    Method called by :meth:`.DocumentController.handle_added_file` when a STEP
    file is added to a Document3D.

    It calls a subprocess (:meth:`.generateGeometrys_Arborescense` ) that generates a file **.arb** and one or more files **.geo** (these files
    are necessary for the visualization 3D and the decomposition of the :class:`~django.core.files.File` **.stp** ),
    later these files will be attached to an :class:`.ArbreFile` and one or more :class:`.GeometryFile` and these classes with the :class:`.DocumentFile` determined by **doc_file_pk**

    """
    logging.getLogger("GarbageCollector").setLevel(logging.ERROR)
    logger = handle_step_file.get_logger()
    doc_file = pmodels.DocumentFile.objects.get(pk=doc_file_pk)
    temp_file = tempfile.TemporaryFile()
    error_file = tempfile.NamedTemporaryFile()
    stdout = temp_file.fileno()
    name = "%s.png" % (doc_file_pk)
    thumbnail_path = pmodels.thumbnailfs.path(name)

    try:
        dirname = os.path.dirname(__file__)
        status=subprocess.call(["python", os.path.join(dirname, "generate3D.py"), doc_file.file.path,
            str(doc_file.id), settings.MEDIA_ROOT+"3D/", thumbnail_path],
            stdout=stdout, stderr=error_file.fileno())
        if status == 0:
            """
            The subprocess is going to return a temporary file with the names of the files *.geo* and *.arb* generated.
            In the moment of his generation these files are not associated the documentFile
            """
            delete_ArbreFile(doc_file) #In case of an update, to erase the previous elements
            delete_GeometryFiles(doc_file)
            generate_relations_BD(doc_file,temp_file)# We associate the files generated to classes and the classes to the documentFile
            if os.path.exists(thumbnail_path):
                doc_file.no_index = True
                doc_file.thumbnail = os.path.basename(thumbnail_path)
                doc_file.save(update_fields=("thumbnail",))
        else:
            error_file.seek(0)
            temp_file.seek(0)
            logger.info(temp_file.read())
            logger.info(error_file.read())
            if status == -1:
                #MultiRootError  SEND MAIL?
                raise ValueError("OpenPLM does not support files STEP with multiple roots")
            elif status == -2:
                #OCCReadingStepError SEND MAIL?
                raise ValueError("PythonOCC could not read the file")
            else:
                #Indeterminate error SEND MAIL?
                raise ValueError("Error during the treatment of the file STEP")
    finally:
        temp_file.close()
        error_file.close()


def generate_relations_BD(doc_file,temp_file):
    """
    Function used when we add a new :class:`~django.core.files.File` **.stp** in a :class:`.Document3D`
    This function associates a series of files with classes :class:`.ArbreFile` and :class:`.GeometryFile`
    and this classes to a :class:`.DocumentFile`. The files were generated before the call to this function,
    their paths are known thanks to the information supplied in the temporary file(Every line of this file represents
    a file, the beginning of every line indicates the type of file)

    :param doc_file: object which will be updated
    :type plmobject: :class:`.DocumentFile`
    :param temp_file: :class:`.tempfile` that contains the path of the generated **.geo** and **.arb** files
    :type plmobject: :class:`.tempfile`
    """
    stdout = temp_file.fileno()
    os.lseek(stdout, 0, 0)
    arb = None
    decomposable = False
    for line in temp_file.readlines():
        line=line.rstrip("\n")
        if line.startswith("GEO:"):
            path, index = line.lstrip("GEO:").split(" , ")
            GeometryFile.objects.create(stp=doc_file, file=path, index=index)
        if line.startswith("ARB:"):
            arb = line.lstrip("ARB:")
        if line.startswith("Decomposable:"):
            decomposable = line.lstrip("Decomposable:").startswith("true")
    if arb:
        ArbreFile.objects.create(file=arb, stp=doc_file, decomposable=decomposable)

is_stp=Q(filename__iendswith=".stp") | Q(filename__iendswith=".step")#.stp , .STP , .step , .STEP
is_stl=Q(filename__iendswith=".stl") #.stl, .STL
is_catia=Q(filename__iendswith=".catpart") | Q(filename__iendswith=".catproduct")


class Document3DController(DocumentController):
    """
    A :class:`DocumentController` which manages
    :class:`.Document3D`

    It provides methods to deprecate and to manage (**visualization3D** and **decomposition**)files STEP.
    """

    __slots__ = DocumentController.__slots__ + ("_stps",)

    def __init__(self, *args, **kwargs):
        super(Document3DController, self).__init__(*args, **kwargs)
        self._stps = None

    def handle_added_file(self, doc_file):
        """
        If a :class:`~django.core.files.File` .stp is set like the file of a :class:`.DocumentFile` (**doc_file**) added to a :class:`.Document3D` , a special treatment (:meth:`.handle_step_file`) is begun (Only one file STEP allowed for each :class:`.Document3D` )
        """
        fileName, fileExtension = os.path.splitext(doc_file.filename)

        if fileExtension.upper() in ('.STP', '.STEP'):
            if self.object.files.filter(is_stp).exclude(id=doc_file.id):
                self.delete_file(doc_file)
                raise ValueError("Only one step documentfile allowed for each document3D")

            handle_step_file.delay(doc_file.pk)

    def revise(self, new_revision, selected_parts=(), **kwargs):
        rev = super(Document3DController, self).revise(new_revision, selected_parts, **kwargs)
        STP_file = self.object.files.filter(is_stp)
        if STP_file.exists():
            new_STP_file = rev.object.files.get(is_stp)
            if self.object.PartDecompose and self.object.PartDecompose in selected_parts:
                rev.object.PartDecompose=self.object.PartDecompose
                rev.object.save()
                product=self.get_product(STP_file[0], False)
                copy_geometry(product,new_STP_file)
                product.set_new_root(new_STP_file.id,new_STP_file.file.path,for_child=False)
                ArbreFile.create_from_product(product,new_STP_file)

            elif self.object.PartDecompose: #and not self.object.PartDecompose in selected_parts
                product=self.get_product(STP_file[0], True)
                tempfile_size = self.recompose_step_file(STP_file[0])
                if tempfile_size:
                    filename = new_STP_file.filename
                    path = pmodels.docfs.get_available_name(filename.encode("utf-8"))
                    shutil.copy(tempfile_size[0].name, pmodels.docfs.path(path))
                    new_doc = pmodels.DocumentFile.objects.create(file=path,
                        filename=filename, size=tempfile_size[1], document=rev.object)
                    new_doc.thumbnail = new_STP_file.thumbnail
                    if new_STP_file.thumbnail:
                        ext = os.path.splitext(new_STP_file.thumbnail.path)[1]
                        thumb = "%d%s" %(new_doc.id, ext)
                        dirname = os.path.dirname(new_STP_file.thumbnail.path)
                        thumb_path = os.path.join(dirname, thumb)
                        shutil.copy(new_STP_file.thumbnail.path, thumb_path)
                        new_doc.thumbnail = os.path.basename(thumb_path)
                    new_doc.locked = False
                    new_doc.locker = None
                    new_doc.save()
                    new_STP_file.delete()
                    new_STP_file=new_doc

                copy_geometry(product, new_STP_file)
                product.set_new_root(new_STP_file.id, new_STP_file.file.path, for_child=True)
                ArbreFile.create_from_product(product, new_STP_file)
            else:
                product=self.get_product(STP_file[0], False)
                copy_geometry(product,new_STP_file)
                product.set_new_root(new_STP_file.id,new_STP_file.file.path,for_child=False)
                ArbreFile.create_from_product(product,new_STP_file)
        return rev

    def delete_file(self, doc_file):
        """
        We erase also the classes :class:`.GeometryFile` and :class:`.ArbreFile` associated with the :class:`.DocumentFile` (**doc_file**)
        """
        super(Document3DController, self).delete_file(doc_file)
        fileName, fileExtension = os.path.splitext(doc_file.filename)
        if fileExtension.upper() in ('.STP', '.STEP'):
            delete_GeometryFiles(doc_file)
            delete_ArbreFile(doc_file)

    def deprecate_file(self, doc_file,by_decomposition=False):
        """
        A file can be depreciated for diverse motives, (when a file STEP is decomposed,
        when exists a native file associate to one file STEP and we realize a brute check-out of the STEP , the native will be deprecated , ...)

        :param doc_file: :class:`.DocumentFile` which will be deprecated

        """
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

    def get_all_geometry_files(self, doc_file):
        if self.PartDecompose is not None:
            pctrl = PartController(self.PartDecompose, self._user)
            if self._stps is None:
                children_ids = [c.link.child_id for c in pctrl.get_children(-1, related=("child__id"),
                    only=("child__id", "parent__id",))]
                if children_ids:
                    docs = pmodels.DocumentPartLink.objects.now().filter(document__type="Document3D",
                            part__in=children_ids).values_list("document", flat=True)
                    dfs = pmodels.DocumentFile.objects.filter(document__in=docs, deprecated=False)\
                            .filter(is_stp).values_list("id", flat=True)
                    self._stps = dfs
                else:
                    self._stps = pmodels.DocumentFile.objects.none().values_list("id", flat=True)
            q = Q(stp=doc_file)
            stps = list(self._stps)
            if stps:
                q |= Q(stp__in=stps)
            gfs = GeometryFile.objects.filter(q)
        else:
            gfs = GeometryFile.objects.filter(stp=doc_file)
        return gfs.values_list("file", flat=True)

    def get_product(self, doc_file, recursive=False):
        """
        Returns the :class:`.Product` associated to *doc_file*.
        If *recursive* is True, it returns a complet product, built by browsing
        the BOM of the attached part, if it has been decomposed.
        """
        try:
            af = ArbreFile.objects.get(stp=doc_file)
        except:
            return None
        product = classes.Product.from_list(json.loads(af.file.read()))
        if recursive and product:
            if self.PartDecompose is not None:
                # Here be dragons
                # this code try to reduce the number of database queries:
                # h queries (h: height of the BOM) to get children
                # + 1 query to doc-part links
                # + 1 query to get STP files
                # + 1 query to get location links
                # + 1 query to get ArbreFile
                pctrl = PartController(self.PartDecompose, self._user)
                children = pctrl.get_children(-1, related=("child__id"), only=("child__id", "parent__id",))
                if not children:
                    return product
                links, children_ids = zip(*[(c.link.id, c.link.child_id) for c in children])
                docs = []
                part_to_docs = defaultdict(list)
                for doc, part in pmodels.DocumentPartLink.current_objects.filter(document__type="Document3D",
                        part__in=children_ids).values_list("document", "part").order_by("-ctime"):
                    # order by -ctime to test the most recently attached document first
                    part_to_docs[part].append(doc)
                    docs.append(doc)
                if not docs:
                    return product

                dfs = dict(pmodels.DocumentFile.objects.filter(document__in=docs, deprecated=False)\
                        .filter(is_stp).values_list("document", "id"))
                # cache this values as it may be useful for get_all_geometry_files
                self._stps = dfs.values()
                locs = defaultdict(list)
                for l in Location_link.objects.filter(link__in=links):
                    locs[l.link_id].append(l)
                # read all jsons files
                jsons = {}
                for af in ArbreFile.objects.filter(stp__in=dfs.values()):
                    jsons[af.stp_id] = json.loads(af.file.read())
                # browse the BOM and build product
                previous_level = 0
                products = [product]
                for level, link in children:
                    if level <= previous_level:
                        del products[level:]
                    stp = None
                    for doc in part_to_docs[link.child_id]:
                        if doc in dfs:
                            stp = dfs[doc]
                            break
                    if stp is not None and stp in jsons:
                        pr = products[-1]
                        prod = classes.Product.from_list(jsons[stp], product=False,
                                product_root=product, deep=level, to_update_product_root=pr)
                        for location in locs[link.id]:
                            pr.links[-1].add_occurrence(location.name, location)
                        products.append(prod)
                    previous_level = level

        return product


media3DGeometryFile = pmodels.DocumentStorage(location=settings.MEDIA_ROOT+"3D/")
class GeometryFile(models.Model):
    u"""

    Link between :class:`.DocumentFile` that contains a :class:`~django.core.files.File` **.stp** present in a :class:`.Document3D` and a file **.geo** that represents his geometry
    A :class:`.DocumentFile` can have zero or many :class:`.GeometryFile` associated , to identify the different :class:`.GeometryFile` attached to one :class:`.DocumentFile` we use the
    attribute index. (**index** should be **>=1**)

    The information contained in the file **.geo** will allow to generate the  3D view of the :class:`.DocumentFile`

     .. attribute:: stp

        :class:`.DocumentFile` of relation

     .. attribute:: file

        file **.geo**

     .. attribute:: index

        to identify the different :class:`.GeometryFile` attached to one :class:`.DocumentFile`  (>=1)

    """
    file = models.FileField(upload_to='.',storage=media3DGeometryFile)
    stp = models.ForeignKey(pmodels.DocumentFile)
    index = models.IntegerField()

    def __unicode__(self):
        return u"GeometryFile<%d:%s, %d>" % (self.stp.id,
            self.stp.filename, self.index)

#admin.site.register(GeometryFile)

def delete_GeometryFiles(doc_file):
    """
    Physically deletes (*.geo* files) and logically deletes :class:`.GeometryFiles` associated
    to *doc_file*

    :param doc_file: :class:`.DocumentFile`
    """
    to_delete = GeometryFile.objects.filter(stp=doc_file)
    files = to_delete.values_list("file", flat=True)
    delete_files(files, media3DGeometryFile.location)
    to_delete.delete()


media3DArbreFile = pmodels.DocumentStorage(location=settings.MEDIA_ROOT+"3D/")
#admin.site.register(ArbreFile)
class ArbreFile(models.Model):
    u"""
    Link between :class:`.DocumentFile` that contains a :class:`~django.core.files.File` **.stp** present in a :class:`.Document3D` and  a file **.arb** that represents his arborescense
    A :class:`.DocumentFile` STEP have one :class:`.ArbreFile` associated

    The information contained in the file **.arb** will allow to generate the  3D view and the decomposition of the :class:`.DocumentFile`

     .. attribute:: stp

        :class:`.DocumentFile` of relation

     .. attribute:: file

        :class:`~django.core.files.File` **.arb**

     .. attribute:: decomposable

        this attribute indicates if the :class:`.DocumentFile` can be decompose
    """
    file = models.FileField(upload_to='.',storage=media3DArbreFile)
    stp = models.ForeignKey(pmodels.DocumentFile)
    decomposable = models.BooleanField()

    @classmethod
    def create_from_product(cls, product, doc_file):
        """
        Creates a new ArbreFile from product. Its content is seririalized to
        a new *..arb* file.

        Returns the created ArbreFile.
        """
        data=product.to_list()
        filename, ext = os.path.splitext(doc_file.filename)
        arbre_file = ArbreFile(decomposable=product.is_decomposable)
        arbre_file.stp = doc_file
        name = arbre_file.file.storage.get_available_name(filename+".arb")
        path = os.path.join(arbre_file.file.storage.location, name)
        arbre_file.file = name
        arbre_file.save()
        directory = os.path.dirname(path.encode())
        if not os.path.exists(directory):
            os.makedirs(directory)
        output = open(path.encode(),"w")
        output.write(json.dumps(data))
        output.close()
        return arbre_file


def delete_ArbreFile(doc_file):
    """

    Erase physical (file **.arb**) and logically the :class:`.ArbreFile` associated with a :class:`.DocumentFile` (**doc_file**)


    :param doc_file: :class:`.DocumentFile`


    """

    to_delete = ArbreFile.objects.filter(stp=doc_file)
    files = to_delete.values_list("file", flat=True)
    delete_files(files, media3DArbreFile.location)
    to_delete.delete()

def delete_files(files, location=""):
    for name in files:
        filename = os.path.join(location, name)
        if os.path.exists(filename) and os.path.isfile(filename):
            os.remove(filename)


class Document3D_decomposer_Error(ControllerError):

    def __unicode__(self):
        return u"Error while the file step was split"


class Document_Generate_Bom_Error(ControllerError):
    def __init__(self, to_delete=None,assembly=None):
        self.to_delete=to_delete# DocumentFiles generated
        self.assembly=assembly
    def __unicode__(self):
        return u"Columns reference, type, revision are not unique between the products of the assembly "+self.assembly #meter referencia



class Location_link(pmodels.ParentChildLinkExtension):
    """
    Extend :class:`.ParentChildLinkExtension`
    Represents the matrix of transformation (rotation and translation) and the name of one relation between assemblies.
    When a file STEP is decomposed in Parts a :class:`.ParentChildLink` is generated between the Parts
    and each of these :class:`.ParentChildLink` could have attached one or more :class:`.Location_link`

    Defines a non-persistent transformation in 3D space


     == == == == == = ==
     x1 x2 x3 x4  x = x'
     y1 y2 y3 y4  y = y'
     z1 z2 z3 z4  z = z'
     0  0  0  1   1 = 1
     == == == == == = ==
    """
    x1 = models.FloatField(default=lambda: 0)
    x2 = models.FloatField(default=lambda: 0)
    x3 = models.FloatField(default=lambda: 0)
    x4 = models.FloatField(default=lambda: 0)
    y1 = models.FloatField(default=lambda: 0)
    y2 = models.FloatField(default=lambda: 0)
    y3 = models.FloatField(default=lambda: 0)
    y4 = models.FloatField(default=lambda: 0)
    z1 = models.FloatField(default=lambda: 0)
    z2 = models.FloatField(default=lambda: 0)
    z3 = models.FloatField(default=lambda: 0)
    z4 = models.FloatField(default=lambda: 0)

    name = models.CharField(max_length=100, default="no_name")

    def to_array(self):
        return [self.x1, self.x2, self.x3, self.x4,
                self.y1, self.y2, self.y3, self.y4,
                self.z1, self.z2, self.z3, self.z4]

    @classmethod
    def apply_to(cls, parent):
        # only apply to all parts
        return True

    def clone(self, link, save, **data):

        x1 = data.get("x1", self.x1)
        x2 = data.get("x2", self.x2)
        x3 = data.get("x3", self.x3)
        x4 = data.get("x4", self.x4)
        y1 = data.get("y1", self.y1)
        y2 = data.get("y2", self.y2)
        y3 = data.get("y3", self.y3)
        y4 = data.get("y4", self.y4)
        z1 = data.get("z1", self.z1)
        z2 = data.get("z2", self.z2)
        z3 = data.get("z3", self.z3)
        z4 = data.get("z4", self.z4)

        name = data.get("name", self.name)
        clone = Location_link(link=link, name=name,
                x1=x1, x2=x2, x3=x3, x4=x4,
                y1=y1, y2=y2, y3=y3, y4=y4,
                z1=z1,z2=z2,z3=z3,z4=z4)
        if save:
            clone.save()
        return clone


#admin.site.register(Location_link)
pmodels.register_PCLE(Location_link)


def generate_extra_location_links(link, pcl):
    """
    Creates all :class:`Location_link` bound to *link and *pcl*.

    :param link: :class:`.openPLM.apps.document3D.classes.Link` which will be used to create :class:`.Location_link`
    :type plmobject: :class:`.Link`
    :param ParentChildLink: Parent child link that is extended
    :type plmobject: :class:`.ParentChildLink`

    """
    # Location_link inherits from PCLE: it is not possible to call bulk_create
    for i in range(link.quantity):
        loc = Location_link()
        loc.link = pcl
        array = link.locations[i].to_array()
        loc.name = link.names[i]
        (loc.x1, loc.x2, loc.x3, loc.x4,
         loc.y1, loc.y2, loc.y3, loc.y4,
         loc.z1, loc.z2, loc.z3, loc.z4) = map(lambda x: 0.0 if abs(x) < 1e-50 else x, array)
        loc.save()


@task(name="openPLM.apps.document3D.decomposer_all",
      soft_time_limit=60*25,time_limit=60*25)
def decomposer_all(stp_file_pk,arbre,part_pk,native_related_pk,user_pk,old_arbre):
    """

    :param arbre: Information contained in file **.arb** that allows to generate a :class:`.Product` that represents the arborescense of the :class:`~django.core.files.File` .stp to decompose , his nodes contains doc_id and doc_path of new :class:`.DocumentFile` created in the arborescense
    :type plmobject: :class:`.Product`
    :param stp_file_pk: primery key of a :class:`.DocumentFile` that contains the :class:`~django.core.files.File` that will be decomposed
    :param part_pk: primery key of a :class:`.Part` attached to the :class:`.Document3D` that contains the :class:`.DocumentFile` that will be decomposed
    :param native_related_pk: If exists a native file related to the :class:`.DocumentFile` that will be decomposed ,  contains the primary key of the :class:`.DocumentFile` related to the native file


    This function departs from a :class:`.DocumentFile` (**stp_file_pk**) associated with a :class:`.Document3D` attached to a :class:`.Part` (``part_pk``) and from
    the :class:`.Product` related to the :class:`.DocumentFile` in order to decompose :class:`~django.core.files.File` .stp.With this purpose it realizes a call to the subprocess
    :meth:`.generateDecomposition.py`.



    -**Preconditions** ,before calling to this function, the following steps must have been realized:

        -The bom-child of Parts (in relation to the :class:`.Product` (generate across the **arbre**)) has been generated

        -For every :class:`.ParentChildLink` generated in the previous condition we attach all the :class:`.Location_link` relatives

        -To every generated :class:`.Part` a :class:`.Document3D` has been attached and the :class:`.Document3D` has been set like the attribute PartDecompose of the :class:`.Part`

        -The attribute doc_id of every node of the :class:`.Product` (generate across the **arbre**) is now the relative id of :class:`.Document3D` generated in the previous condition

        -To every generated :class:`.Document3D` has been added a new empty(locked) :class:`.DocumentFile` .stp

        -The attribute doc_path of every node of the :class:`.Product` is now the path of :class:`.DocumentFile` generated in the previous condition

        -The :class:`.DocumentFile` (**stp_file_pk**) is locked

        -If exists a native :class:`.DocumentFile` (**native_related_pk**) related to the :class:`.DocumentFile` (**stp_file_pk**), then this one was depreciated (afterwards will be promoted)




    -**Treatment**


        -The subprocess  :meth:`.generateDecomposition.py` is going to write in to doc_path of every node of the :class:`.Product` (generate across the **arbre**) the corresponding decomposed file


    -**Postconditions**

        -For every generated :class:`.Document3D` , the new :class:`.DocumentFile` added is unlocked

        -For every new :class:`.DocumentFile` , his :class:`.GeometryFile` and :class:`.ArbreFile` have been generated

        -The root :class:`.DocumentFile` (**stp_file_pk**) has been deprecated and unlocked

        -A new root :class:`.DocumentFile` has been generated according to the situation

        -If exists a native :class:`.DocumentFile` (**native_related_pk**) related to the :class:`.DocumentFile` (**stp_file_pk**), then this one was promoted

        -We set the :class:`.Part` (**part_pk**) like the attribute PartDecompose of the :class:`.Document3D` that contains the :class:`.DocumentFile` (**stp_file_pk**)
    """
    try:
        stp_file = pmodels.DocumentFile.objects.get(pk=stp_file_pk)
        ctrl=get_controller(stp_file.document.type)
        user=pmodels.User.objects.get(pk=user_pk)
        ctrl=ctrl(stp_file.document,user)
        part=pmodels.Part.objects.get(pk=part_pk)

        product=classes.Product.from_list(json.loads(arbre))   #whit doc_id and doc_path updated for every node
        old_product=classes.Product.from_list(json.loads(old_arbre)) # doc_id and doc_path original
        new_stp_file=pmodels.DocumentFile()
        name = new_stp_file.file.storage.get_available_name((product.name+".stp").encode("utf-8"))
        new_stp_path = os.path.join(new_stp_file.file.storage.location, name)
        f = File(open(new_stp_path, 'w'))
        f.close()

        product.doc_path=new_stp_path # the old documentfile will be deprecated
        product.doc_id=new_stp_file.id # the old documentfile will be deprecated

        temp_file = tempfile.NamedTemporaryFile(delete=True)
        temp_file.write(json.dumps(product.to_list()))
        temp_file.seek(0)
        dirname = os.path.dirname(__file__)
        if subprocess.call(["python", os.path.join(dirname, "generateDecomposition.py"),
            stp_file.file.path,temp_file.name]) == 0:

            update_child_files_BD(product,user,old_product)
            update_root_BD(new_stp_file,stp_file,ctrl,product,f,name,part)

        else:

            raise Document3D_decomposer_Error
    except:
        raise Document3D_decomposer_Error

    finally:
        if native_related_pk is not None:
            native_related = pmodels.DocumentFile.objects.get(pk=native_related_pk)
            native_related.deprecated=False
            native_related.save()
        stp_file.locked = False
        stp_file.locker = None
        stp_file.save()



def update_root_BD(new_stp_file,stp_file,ctrl,product,file,name,part):
    """

    :param stp_file: :class:`.DocumentFile` that was decomposed (will be deprecated)
    :param new_stp_file: :class:`.DocumentFile` that will replace the :class:`.DocumentFile` that was decomposed
    :param product: :class:`.Product` that represents the arborescense of the :class:`.DocumentFile` that was decomposed
    :param part: :class:`.Part` attached to the :class:`.Document3D` that contains the :class:`.DocumentFile` that was decomposed
    :param ctrl: :class:`.Document3DController` that contains the :class:`.DocumentFile` that was decomposed
    :param file: :class:`~django.core.files.File` that contains the new file .stp root
    :param name: name for the :class:`.DocumentFile` (new_stp_file)
    :type plmobject: :class:`.Product`



    Updates a :class:`.DocumentFile` (**stp_file**) that was used like root in a decomposition , deprecating it and replacing by a new :class:`.DocumentFile` (**new_stp_file**)

    This update consists in:

        Connect the :class:`.DocumentFile` (**new_stp_file**) to the :class:`.Document3D` (**ctrl.object**)

        Generate a new :class:`.ArbreFile` for the **new_stp_file** (**product**.doc_id and **product**.doc_path related to the **new_stp_file**)

        Fix the attribute PartDecompose of the :class:`.Document3D` (**ctrl**.object) to the :class:`.Part` (**part**)

        Deprecate the :class:`.DocumentFile` (**stp_file**)

    """
    doc3D=Document3D.objects.get(id=stp_file.document_id)
    doc3D.PartDecompose=part
    doc3D.save()
    new_stp_file.filename=product.name+".stp".encode("utf-8")
    new_stp_file.file=name
    new_stp_file.size=file.size
    new_stp_file.document=ctrl.object
    new_stp_file.save()
    os.chmod(new_stp_file.file.path, 0400)
    ctrl._save_histo("File generated by decomposition", "file : %s" % new_stp_file.filename)
    product.links=[]

    product.doc_id=new_stp_file.id
    product.doc_path=new_stp_file.file.path

    ArbreFile.create_from_product(product,new_stp_file)
    ctrl.deprecate_file(stp_file,by_decomposition=True)


def update_child_files_BD(product,user,old_product):
    """
    :param product: :class:`.Product` that represents a sub-arborescense of the file **.stp** that was decomposed UPDATE whit the news doc_id and doc_path generating in the bomb-child
    :param old_product: :class:`.Product` that represents a sub-arborescense ORIGINAL of the file **.stp** that was decomposed



    Updates a :class:`.DocumentFile` STEP that WAS NOT root in a decomposition, to know which :class:`.DocumentFile` to update we use the attribute **product**.doc_id of the arborescense(**product**)

    This update consists in:

        Generate a new :class:`.ArbreFile` for each  :class:`.DocumentFile` STEP present in the arborescense(**product**)

        Generate news :class:`.GeometryFile` for the :class:`.DocumentFile` STEP (Copies of the GeometryFiles of the root :class:`.DocumentFile` (Identified for **old_product**.doc_id))

    """

    for link, old_link in zip(product.links,old_product.links):
        if not link.product.visited:
            link.product.visited=True
            product_copy=copy.copy(link.product)
            old_product_copy=copy.copy(old_link.product)
            product_copy.links=[]       #when we decompose we delete the links
            old_product_copy.links=[]
            doc_file=pmodels.DocumentFile.objects.get(id=product_copy.doc_id)
            doc_file.filename=product_copy.name+".stp".encode("utf-8")
            doc_file.no_index=False
            doc_file.size=os.path.getsize(doc_file.file.path)
            doc_file.locked = False
            doc_file.locker = None
            doc_file.save()
            os.chmod(doc_file.file.path, 0400)

            copy_geometry(old_product_copy,doc_file) #we utilise old_product
            ArbreFile.create_from_product(product_copy,doc_file)
            doc_file.document.no_index=False # to reverse no_index=True make in document3D.views.generate_part_doc_links
            doc_file.document.save()
            ctrl=get_controller(doc_file.document.type)
            ctrl=ctrl(doc_file.document,user,True)
            ctrl._save_histo("File generated by decomposition", "file : %s" % doc_file.filename)
            update_child_files_BD(link.product,user,old_link.product)

def copy_geometry(product, doc_file):
    """
    :param product: :class:`.Product` that represents a sub-arborescense original of the file step that was decompose
    :param doc_file: :class:`.DocumentFile` for which the files **.geo** that generated


    Copy the content of all :class:`.GeometryFile` (determined by his index(**product**.geometry)) present in the :class:`.Product` (**product**) and his childrens  for a :class:`.DocumentFile` (**doc_file**) generating and connecting news entitys :class:`.GeometryFile`


    To differentiate the content of a file **.geo** we use the combination index (determined by **product**.geometry) more id (**product**.doc_id)

    """

    if product.geometry:
        product.visited = True
        old_GeometryFile = GeometryFile.objects.get(stp__id=product.doc_id, index=product.geometry)
        new_GeometryFile = GeometryFile()
        fileName, fileExtension = os.path.splitext(doc_file.filename)

        new_GeometryFile.file = new_GeometryFile.file.storage.get_available_name(fileName+".geo")
        new_GeometryFile.stp = doc_file
        new_GeometryFile.index = product.geometry
        new_GeometryFile.save()

        with open(old_GeometryFile.file.path, "r") as infile:
            with open(new_GeometryFile.file.path, "w") as outfile:
                old_var = "_%s_%s" % (product.geometry, product.doc_id)
                new_var = "_%s_%s" % (product.geometry, doc_file.id)
                for line in infile.readlines():
                    new_line = line.replace(old_var, new_var)
                    outfile.write(new_line)

    for link in product.links:
        if not link.product.visited:
            copy_geometry(link.product, doc_file)


