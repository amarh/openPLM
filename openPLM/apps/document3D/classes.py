import hashlib
import string
import random
import os

def get_available_name(location, name):


    def rand():
        r = ""
        for i in xrange(7):
            r += random.choice(string.ascii_lowercase + string.digits)
        return r
    basename = os.path.basename(name)
    base, ext = os.path.splitext(basename)
    ext2 = ext.lstrip(".").lower() or "no_ext"
    md5 = hashlib.md5()
    md5.update(basename)
    md5_value = md5.hexdigest() + "-%s" + ext
    path = os.path.join(ext2, md5_value % rand())
    while os.path.exists(os.path.join(location, path)):
        path = os.path.join(ext2, md5_value % rand())
    return path

class Product(object):
    """
    Class used to represent the **arborescense** contained in a
    :class:`~django.core.files.File` **.stp**.A :class:`.Product` can be
    simple or an assembly, if it is an assembly in **links** we will
    guard the information about other :class:`.Product` that compose it.


    There are two ways of generating a :class:`.Product`, reading the file
    **.stp** across the class :class:`.NEW_STEP_Import` ( will refill the
    attribute **label_reference**  for every :class:`Product`), or reading
    a file **.arb** related to a :class:`.ArbreFile`  .
    Therefore there exist two ways of distinguishing the different :class:`.Product`,
    by means of the attribute **label_reference** if this one is not False ,
    or by means of the combination of attributes  **id** and **doc_id**.


    :model attributes:

    .. attribute:: links

        If the product is an assembly, links stores one or more
        :class:`.openPLM.apps.document3D.classes.Link` references to the products that compose it


    .. attribute:: label_reference

        When we generate an arborescense using :class:`.NEW_STEP_Import` ,
        here we will store the label that represents the :class:`.Product` ,
        if we generate the arborescense reading a file **.geo**, this attribute will be **False**

    .. attribute:: name

        Name of :class:`.Product` ,if the name is empty and there exists a
        :class:`.Link` at the :class:`.Product` , we will assign the name of the
        :class:`.Link` to the :class:`.Product`

    .. attribute:: doc_id

        Id of the :class:`.DocumentFile` that contains the :class:`.Product` ,
        in the case of :class:`~django.core.files.File` .stp decomposed them
        **doc_id** may be different for every :class:`.Product` of the arborescense

    .. attribute:: doc_path

        Path of the :class:`~django.core.files.File` represented by the :class:`.DocumentFile` that contains the product

    .. attribute:: part_to_decompose

        Used in the decomposition, it indicates the :class:`.Part` where the :class:`.Product` was decomposed

    .. attribute:: geometry

        If geometry is True (>=1) then the :class:`.Product` is single (without **links** )
        , and his value refers to the index that we will use to recover a :class:`.GeometryFile`

    .. attribute:: deep

        Depth in the arborescense

    .. attribute:: visited

        Used in the decomposition , indicates if a :class:`.Product`  has been visited in the tour of the arborescense

    .. attribute:: id

        identified the :class:`.Product`

    """
    __slots__ = ("label_reference","name","doc_id","links","geometry","deep","doc_path","visited","part_to_decompose","id")


    def __init__(self,name,deep,label_reference,doc_id,id,doc_path=None,geometry=False):
        #no tiene location
        self.links = []
        self.label_reference=label_reference
        self.name=name
        self.doc_id=doc_id
        self.doc_path=doc_path
        self.part_to_decompose=False
        self.geometry=geometry
        self.deep=deep
        self.id=id
        self.visited=False

    def set_geometry(self,geometry):
        self.geometry=geometry

    def set_new_root(self,new_doc_id,new_doc_path,for_child=False):
        #0 cant be a valid geometry index , 0==False
        old_id=self.doc_id
        self.doc_id=new_doc_id
        self.doc_path=new_doc_path
        for link in self.links:
            if link.product.doc_id == old_id or for_child:
                link.product.set_new_root(new_doc_id,new_doc_path,for_child)

    @property
    def is_decomposed(self):
        """
        If it is an assembly and any :class:`.Product` contents in its **links**
        are defined (**doc_id**) in another :class:`DocumentFile` (**doc_id**)
        """
        for link in self.links:
            if not link.product.doc_id == self.doc_id:
                return True
        return False

    @property
    def is_decomposable(self):
        """
        If it is an assembly and any :class:`.Product` contents in its **links**
        are defined (**doc_id**) in the same :class:`DocumentFile` (**doc_id**)
        """
        for link in self.links:
            if link.product.doc_id == self.doc_id:
                return True
        return False

    @property
    def is_assembly(self):
        if self.links:
            return self.name
        return False


class Link(object):
    """

    Class used to represent a :class:`Link` with a :class:`.Product`,
    a :class:`Link` can have several references, each one with his own name and matrix of transformation.
    Every :class:`Link` points at a :class:`.Product`

    :model attributes:


    .. attribute:: names

        Name of each instances of the :class:`Link` , if the instance does not have name,
        it gets the name of its :class:`.Product` child

    .. attribute:: locations

        :class:`TransformationMatrix` of each instances of the :class:`Link`

    .. attribute:: product

        :class:`.Product` child of the :class:`Link`

    .. attribute:: quantity

        Number of instances of the :class:`Link`  (each instance has a **name** and **location**)

    .. attribute:: visited

        Used in the decomposition , indicates if a :class:`Link` has been visited in the tour of the arborescense

    """
    __slots__ = ("names","locations","product","quantity","visited")


    def __init__(self, product):

        self.names=[]
        self.locations=[]
        self.product=product
        self.quantity=0
        self.visited=False#used only in multi-level decomposition

    def add_occurrence(self, name, matrix):
        if not name.strip():
            self.names.append(self.product.name)
        else:
            self.names.append(name)
        if not self.product.name:
            self.product.name=name
        self.locations.append(matrix)
        self.quantity += 1


class TransformationMatrix(object):
    """

    Defines a non-persistent transformation in 3D space

     == == == == == = ==
     x1 x2 x3 x4  x = x'
     y1 y2 y3 y4  y = y'
     z1 z2 z3 z4  z = z'
     0  0  0  1   1 = 1
     == == == == == = ==


    """
    __slots__ = ("x1","x2","x3","x4","y1","y2","y3","y4","z1","z2","z3","z4")


    def __init__(self, coords):

        (self.x1, self.x2, self.x3, self.x4,
            self.y1, self.y2, self.y3, self.y4,
            self.z1, self.z2, self.z3, self.z4) = coords

    def to_array(self):
        return [self.x1, self.x2, self.x3, self.x4,
                self.y1, self.y2, self.y3, self.y4,
                self.z1, self.z2, self.z3, self.z4]



def Product_from_Arb(arbre,product=False,product_root=False,deep=0,to_update_product_root=False):

    """

    :param arbre: chain of characters formatted (following the criteria of the function
                  :func:`.data_for_product`) that represents an arborescense. It contains necessary
                  information to construct :class:`.Product` and :class:`Link`

    :param product: Product that represents an arborescense , **ONLY** used in successive
                    recursive calls of the function
    :type plmobject: :class:`.Product`
    :param product_root: Product that represents a root arborescense , used to determine if
                         the product to generate is already present in the tree
    :type plmobject: :class:`.Product`
    :param deep: depth of **product** in the arborescense
    :param to_update_product_root: Product that represents a node of an arborescense
                                   (sub-branch of arborescense referenced by **product_root**)
    :type plmobject: :class:`.Product`



    The :class:`.Product` generated from a file **.arb** (The case of this function) have its attribute **label_reference** set to False.

    When we generate a :class:`.Product` using :class:`.NEW_STEP_Import` , the attribute **label_reference** will represent and identify the :class:`.Product`.


    From the information contained in a file **.arb** (**arbre**), it generates the corresponding :class:`Product`.
    In case of files STEP decomposed, this information can be distributed in several files **.arb** and due to the
    nature of the decomposition, a **product** could be generated more than once , to avoid this we use the **product_root**.
    Whenever we generate a new product we verify that it is not already present in **product_root**,we use **to_update_product_root**
    to support updated **product_root** (**to_update_product_root** is a branch of **product_root**)

    Example:
        - If we want to generate a **product** of a single file **.arb** :

            .. code-block:: python

                tree=Product_from_Arb(json.loads(new_ArbreFile.file.read()))


        - If we want to generate a **product** of a single file .arb and link this one like a branch
          of a certain **product_root_node** of an already existing **product_root**

            .. code-block:: python

                product=Product_from_Arb(json.loads(new_ArbreFile.file.read()),product=False, product_root=product_root, deep=xxx, to_update_product_root=product_root_node)

          This method generates the :class:`Link` between **product_root_node** and  **product** ,
          **BUT** it does not add the occurrences, generally this occurrences are stored in the
          existing  :class:`Location_link` between :class:`Part`

          After generating the **product** and the :class:`Link`, we will have to refill the
          :class:`Link` calling the function :meth:`.add_occurrence` for the :class:`Link`:

            .. code-block:: python

                    for location in locations:
                        product_root_node.links[-1].add_occurrence(location.name,location)
    """

    if not product_root:
        product=generateProduct(arbre,deep)
        product_root=product


    elif to_update_product_root: #Important, in case of generation of a tree contained in several files, it supports updated product_root
        product=generateProduct(arbre,deep)

        product_assembly=search_assembly(product,product_root)
        if product_assembly:
            to_update_product_root.links.append(Link(product_assembly))
            return False
        else:
            to_update_product_root.links.append(Link(product))


    for i in range(len(arbre)-1):
        product_child=generateProduct(arbre[i+1][1],deep+1)
        product_assembly=search_assembly(product_child,product_root)
        if product_assembly:
            product_child=product_assembly
        generateLink(arbre[i+1],product,product_child)
        if not product_assembly:
            Product_from_Arb(arbre[i+1][1],product_child,product_root,deep+1)
    return product



def generateLink(arbre,product,product_child):
    """
    :param arbre: chain of characters formatted (following the criteria of the function :func:`.data_for_product`)
                  that represents the different occurrences of a :class:`Link`
    :param product: :class:`Product` root of the assembly
    :param product_child: :class:`Product` child of the assembly

    """
    product.links.append(Link(product_child))
    for i in range(len(arbre[0])):
        product.links[-1].add_occurrence(arbre[0][i][0],TransformationMatrix(arbre[0][i][1]))


def generateProduct(arbre,deep):
    """
    :param arbre: chain of characters formatted (following the criteria of the function :class:`.data_for_product`) that represents a :class:`Product`
    :param deep: depth of :class:`Product`

    """
    label_reference=False
    return Product(arbre[0][0],deep,label_reference,arbre[0][1],arbre[0][4],arbre[0][3],arbre[0][2])


def search_assembly(product,product_root):
    """
    Checks if a :class:`Product` is already present in a arborescense :class:`Product` (**product_root**)
    There are two manners of comparison, across **label_reference**
    ( generated for :class:`.NEW_STEP_Import` for every :class:`Product`),
    or across **id** and **doc_id** (extracted of a file **.geo** for every :class:`Product`)

    :param product_root: :class:`Product` root of the arborescense
    :param product: :class:`Product` for that we look in the **product_root**

    """

    if product_root:
        for link in product_root.links:
            if product.label_reference:
                if link.product.label_reference==product.label_reference:
                    return link.product
            elif product.id==link.product.id and product.doc_id==link.product.doc_id:
                return link.product
            product_found=search_assembly(product,link.product)
            if product_found:
                return product_found


def data_for_product(product):
    """
    :param product: :class:`Product` for which the chain was generated

    generate a chain of characters formatted that contains information about a :class:`Product`

    """

    output = [[product.name,product.doc_id,product.geometry,product.doc_path,product.id]]
    for link in product.links:
        output.append(data_for_link(link))
    return output


def data_for_link(link):
    """
    :param product: :class:`Link` for which the chain was generated

    generate a chain of characters formatted that contains information about a :class:`Link`

    """
    output=[]
    name_loc=[]
    for i in range(link.quantity):
        name_loc.append([link.names[i],link.locations[i].to_array()])

    output.append(name_loc)
    output.append(data_for_product(link.product))

    return output

