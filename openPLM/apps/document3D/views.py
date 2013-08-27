import os
import fileinput
import json
from collections import namedtuple

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.files.base import File
from django.db import transaction
from django.http import (HttpResponse, HttpResponseRedirect,
        HttpResponseForbidden, Http404, StreamingHttpResponse)

from openPLM.plmapp.views.base import (handle_errors, secure_required,
        get_generic_data, get_obj, get_obj_by_id, init_ctx)
from openPLM.plmapp.views.ajax import ajax_login_required
from openPLM.apps.document3D import forms
from openPLM.apps.document3D import models
from openPLM.apps.document3D.arborescense import JSGenerator
from openPLM.apps.document3D import classes
from openPLM.plmapp import forms as pforms
from openPLM.plmapp import models as pmodels
from openPLM.plmapp.models import get_all_plmobjects
from openPLM.plmapp.tasks import update_indexes
from openPLM.plmapp.decomposers.base import Decomposer, DecomposersManager
from django.template.loader import render_to_string
from openPLM.plmapp.utils import r2r


@handle_errors
def display_3d(request, obj_ref, obj_revi):
    """
    3D view.

    This view is able to show a 3D file (STEP or STL) using WebGL.

    **Template:**

    :file:`Display3D.html`
    """

    obj, ctx = get_generic_data(request, "Document3D", obj_ref, obj_revi)
    ctx['current_page'] = '3D'
    ctx['stl'] = False

    try:
        doc_file = obj.files.filter(models.is_stp)[0]
    except IndexError:
        doc_file = None
        geometry_files = []
        javascript_arborescense=""
        try:
            doc_file = obj.files.filter(models.is_stl)[0]
            ctx["stl"] = True
            ctx["stl_file"] = doc_file
        except IndexError:
            pass
    else:
        product = obj.get_product(doc_file, True)
        geometry_files = obj.get_all_geometry_files(doc_file)
        geometry_files = [os.path.join(settings.MEDIA_URL, "3D", p) for p in geometry_files]
        javascript_arborescense = JSGenerator(product).get_js()

    ctx.update({
        'GeometryFiles' : json.dumps(geometry_files),
        'javascript_arborescense' : javascript_arborescense , })

    return r2r('Display3D.htm', ctx, request)


@secure_required
def display_public_3d(request, obj_ref, obj_revi):
    obj = get_obj("Document3D", obj_ref, obj_revi, request.user)
    if not obj.published and request.user.is_anonymous():
        return redirect_to_login(request.get_full_path())
    elif not obj.published and not obj.check_restricted_readable(False):
        raise Http404

    ctx = init_ctx("Document3D", obj_ref, obj_revi)
    ctx['stl'] = False

    try:
        doc_file = obj.files.filter(models.is_stp)[0]
    except IndexError:
        doc_file = None

        javascript_arborescense=""
        try:
            doc_file = obj.files.filter(models.is_stl)[0]
            ctx["stl"] = True
            ctx["stl_file"] = doc_file
        except IndexError:
            pass
    else:
        product = obj.get_product(doc_file, True)
        javascript_arborescense = JSGenerator(product).get_js()

    ctx.update({
        'is_readable' : True,
        'is_contributor': False,
        # disable the menu and the navigation_history
        'object_menu' : [],
        'navigation_history' : [],
        'obj' : obj,
        'javascript_arborescense' : javascript_arborescense,
    })

    return r2r("public_3d_view.html", ctx, request)


@secure_required
def public_3d_js(request, obj_id):
    obj = get_obj_by_id(int(obj_id), request.user)
    if not obj.is_document and not obj.type == "Document3D":
        raise Http404
    if not obj.published and request.user.is_anonymous():
        return redirect_to_login(request.get_full_path())
    elif not obj.published and not obj.check_restricted_readable(False):
        raise Http404
    try:
        doc_file = obj.files.filter(models.is_stp)[0]
    except IndexError:
        js_files = []
    else:
        js_files = obj.get_all_geometry_files(doc_file)
    if not js_files:
        return HttpResponse("")
    f = fileinput.FileInput(os.path.join(settings.MEDIA_ROOT, "3D", p) for p in js_files)
    response = StreamingHttpResponse(f, content_type="text/script")
    return response


class StepDecomposer(Decomposer):
    """
    :class:`.Decomposer` of Document3D.
    """

    __slots__ = ("part", "decompose_valid")

    def _get_decomposable_stpfile(self, doc):
        if not models.ArbreFile.objects.filter(stp__document=doc,
            stp__deprecated=False, stp__locked=False,
            decomposable=True).exists():
            return None
        try:
            stp_file = pmodels.DocumentFile.objects.only("document",
                    "filename").get(models.is_stp, locked=False,
                            deprecated=False, document=doc)
        except:
            return None
        else:
            if not models.ArbreFile.objects.filter(stp=stp_file, decomposable=True).exists():
                return None
            if stp_file.checkout_valid:
                return stp_file
            return None

    def is_decomposable(self, msg=True):
        decompose_valid = []
        if not models.Document3D.objects.filter(PartDecompose=self.part).exists():
            links = pmodels.DocumentPartLink.objects.now().filter(part=self.part,
                    document__type="Document3D",
                    document__document3d__PartDecompose=None).values_list("document", flat=True)
            for doc_id in links:
                try:
                    if msg:
                        doc = models.Document3D.objects.get(id=doc_id)
                    else:
                        doc = doc_id
                    file_stp = self._get_decomposable_stpfile(doc)
                    if file_stp and msg:
                        decompose_valid.append((doc, file_stp))
                    elif file_stp:
                        return True
                except:
                    pass
        else:
            try:
                doc = models.Document3D.objects.get(PartDecompose=self.part)
                file_stp = self._get_decomposable_stpfile(doc)
                if file_stp and msg:
                    decompose_valid.append((doc, file_stp))
                elif file_stp:
                    return True
            except:
                pass

        self.decompose_valid = decompose_valid
        return len(decompose_valid) > 0

    def get_decomposable_parts(self, parts):
        decomposable = set()
        if parts:
            # invalid parts are parts already decomposed by a StepDecomposer
            invalid_parts = models.Document3D.objects.filter(PartDecompose__in=parts)\
                    .values_list("PartDecompose", flat=True)
            links = list(pmodels.DocumentPartLink.objects.now().filter(part__in=parts,
                    document__type="Document3D", # Document3D has no subclasses
                    document__document3d__PartDecompose=None). \
                    exclude(part__in=invalid_parts).values_list("document", "part"))
            docs = [l[0] for l in links]
            if docs:
                # valid documents are documents with a step file that is decomposable
                valid_docs = dict(models.ArbreFile.objects.filter(stp__document__in=docs,
                    stp__deprecated=False, stp__locked=False,
                    decomposable=True).values_list("stp__document", "stp"))
                for doc_id, part_id in links:
                    if (doc_id not in valid_docs) or (part_id in decomposable):
                        continue
                    stp = pmodels.DocumentFile.objects.only("document", "filename").get(id=valid_docs[doc_id])
                    if stp.checkout_valid:
                        decomposable.add(part_id)
        return decomposable

    def get_message(self):
        if self.decompose_valid:
            return render_to_string("decompose_msg.html", { "part" : self.part,
                "decomposable_docs" : self.decompose_valid })
        return ""

DecomposersManager.register(StepDecomposer)

PartDoc = namedtuple("PartDoc", "part_type qty_form cforms name is_assembly prefix ref")
Assembly = namedtuple("Assembly", ("part_docs", "name", "visited", "depth", "type"))

INVALID_TIME_ERROR = "Error: document has been modified since the beginning of this task."

@handle_errors
def display_decompose(request, obj_type, obj_ref, obj_revi, stp_id):


    """
    :param obj_type: Type of the :class:`.Part` from which we want to realize the decomposition
    :param obj_ref: Reference of the :class:`.Part` from which we want to realize the decomposition
    :param obj_revi: Revision of the :class:`.Part` from which we want to realize the decomposition
    :param stp_id: Id that identify the :class:`.DocumentFile` contained in a :class:`.Document3D` attached to the :class:`.Part` (identified by **obj_type**, **obj_ref**, **obj_revi**) that we will decompose


    When we demand the decomposition across the web form, the following tasks are realized

    - We check that the :class:`.Document3D` that contains the :class:`.DocumentFile` (**stp_id**) that will be decomposed has not been modified since the generation of the form

    - We check the validity of the information got in the form

    - If exists a native :class:`.DocumentFile` file related to :class:`.DocumentFile` (**stp_id**) that will be decomposed
        then this one was depreciated (afterwards will be promoted)

    - The :class:`.DocumentFile` (**stp_id**) was locked (afterwards will be promoted)


    - We call the function :meth:`.generate_part_doc_links_AUX` (with the property **transaction.commit_on_success**)

        - We generate the arborescense (:class:`.product`) of the :class:`.DocumentFile` (**stp_id**)

        - The bom-child of Parts (in relation to the arborescense of the :class:`.DocumentFile` (**stp_id**)) has been generated

        - For every :class:`.ParentChildLink` generated in the previous condition  we attach all the :class:`.Location_link` relatives

        - To every generated :class:`.Part` a :class:`.Document3D` has been attached and this document has been set like the attribute PartDecompose of the :class:`.Part`

        - The attribute doc_id of every node of the arborescense (:class:`.Product`) is now the relative id of :class:`.Document3D` generated in the previous condition

        - To every generated :class:`.Document3D` has been added a new empty(locked) :class:`.DocumentFile` STP

        - The attribute doc_path of every node of the arborescense(:class:`.Product`) is now the path of :class:`.DocumentFile` STP generated in the previous condition

    - We update the indexes for the objects generated

    - We call the processus decomposer_all(with celeryd)

    """

    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    stp_file=pmodels.DocumentFile.objects.get(id=stp_id)
    assemblies=[]

    if stp_file.locked:
        raise ValueError("Not allowed operation.This DocumentFile is locked")
    if not obj.get_attached_documents().filter(document=stp_file.document).exists():
        raise ValueError("Not allowed operation.The Document and the Part are not linked")
    if (models.Document3D.objects.filter(PartDecompose=obj.object).exists()
            and not models.Document3D.objects.get(PartDecompose=obj.object).id==stp_file.document.id):
        #a same document could be re-decomposed for the same part

        raise ValueError("Not allowed operation.This Part already forms part of another split BOM")
    try:
        doc3D=models.Document3D.objects.get(id=stp_file.document_id)
    except models.Document3D.DoesNotExist:
        raise ValueError("Not allowed operation.The document is not a subtype of document3D")

    if doc3D.PartDecompose and not doc3D.PartDecompose.id==obj.object.id:
        raise ValueError("Not allowed operation.This Document already forms part of another split BOM")

    document_controller = models.Document3DController(doc3D, pmodels.User.objects.get(username=settings.COMPANY))
    if request.method == 'POST':
        extra_errors = ""
        product = document_controller.get_product(stp_file, False)
        last_mtime = forms.Form_save_time_last_modification(request.POST)
        obj.block_mails()

        if last_mtime.is_valid() and product:
            old_time = last_mtime.cleaned_data['last_modif_time']
            old_microseconds = last_mtime.cleaned_data['last_modif_microseconds']

            index=[1]
            if clean_form(request,assemblies,product,index,obj_type, {}):

                if (same_time(old_time, old_microseconds, document_controller.mtime)
                    and stp_file.checkout_valid and not stp_file.locked):

                    stp_file.locked=True
                    stp_file.locker=pmodels.User.objects.get(username=settings.COMPANY)
                    stp_file.save()

                    native_related=stp_file.native_related
                    if native_related:
                        native_related.deprecated=True
                        native_related.save()
                        native_related_pk=native_related.pk
                    else:
                        native_related_pk=None

                    try:
                        instances = []
                        old_product = json.dumps(product.to_list()) # we save the product before update nodes whit new doc_id and doc_path generated during the bomb-child
                        generate_part_doc_links_AUX(request, product, obj,instances,doc3D)
                        update_indexes.delay(instances)
                    except Exception as excep:
                        if isinstance(excep, models.Document_Generate_Bom_Error):
                            models.delete_files(excep.to_delete)

                        extra_errors = unicode(excep)
                        stp_file.locked = False
                        stp_file.locker = None
                        stp_file.save()
                        if native_related:
                            native_related.deprecated=False
                            native_related.save()
                    else:

                        models.decomposer_all.delay(stp_file.pk,
                                json.dumps(product.to_list()),
                                obj.object.pk, native_related_pk, obj._user.pk, old_product)

                        return HttpResponseRedirect(obj.plmobject_url+"BOM-child/")
                else:
                    extra_errors="The Document3D associated with the file STEP to analyze has been modified by another user while the forms were refilled:Please restart the process"

            else:
                extra_errors="Error refilling the form, please check it"
        else:
            extra_errors = INVALID_TIME_ERROR
    else:

        last_mtime=forms.Form_save_time_last_modification()
        last_mtime.fields["last_modif_time"].initial = stp_file.document.mtime
        last_mtime.fields["last_modif_microseconds"].initial= stp_file.document.mtime.microsecond
        product= document_controller.get_product(stp_file, False)
        if not product or not product.links:
            return HttpResponseRedirect(obj.plmobject_url+"BOM-child/")

        group = obj.group
        index=[1,0] # index[1] to evade generate holes in part_revision_default generation
        inbulk_cache = {}
        initialize_assemblies(assemblies,product,group,request.user,index,obj_type, inbulk_cache)
        extra_errors = ""

    deep_assemblies=sort_assemblies_by_depth(assemblies)
    ctx.update({'current_page':'decomposer',
                'deep_assemblies' : deep_assemblies,
                'extra_errors' :  extra_errors,
                'last_mtime' : last_mtime
    })
    return r2r('DisplayDecompose.htm', ctx, request)


def sort_assemblies_by_depth(assemblies):

    new_assembly=[]
    for elem in assemblies:
        for i in range(elem[3]+1-len(new_assembly)):
            new_assembly.append([])
        new_assembly[elem[3]].append(elem)

    return new_assembly


def clean_form(request, assemblies, product, index, obj_type, inbulk_cache):

    """

    :param assemblies: will be refill whit the information necessary the generate the forms
    :param product: :class:`.Product` that represents the arborescense of the :class:`~django.core.files.File` .stp contained in a :class:`.DocumentFile`
    :param index: Use  to mark and to identify the **product** s that already have been visited
    :param obj_type: Type of the :class:`.Part` from which we want to realize the decomposition

    It checks the validity of the forms contained in **request**



    If the forms are not valid, it returns the information to refill the new forms contained in **assemblies**.

    Refill **assemblies** with the different assemblies of the file step , we use **index** to mark and to identify the **products** that already have been visited

    For every Assembly we have the next information:

        - Name of assembly

        - Visited , If assembly is sub-assembly of more than one assembly, this attribute will be **False** for all less one of the occurrences

            If visited is **False**, we will be able to modify only the attributes **Order** , **Quantity** and **Unit** refered to the :class:`.ParentChildLink` in the form

            If visited is not **False** , it will be a new id acording to **index** (>=1) generated to identify the assembly

        - Depth  of assembly

        - **obj_type** , type of :class:`.Part` of Assembly

        - A list with the products that compose the assembly

          for each element in the list:

                - part_type contains the form to select the type of :class:`.Part`

                - ord_quantity contains the forms to select Order , Quantity and Unit refered to the :class:`.ParentChildLink`

                - creation_formset contains the form for the creation of the part selected in part_type and of one :class:`.Document3D`

                - name_child_assemblies contains the name of the element

                - is_assembly determine if the element is a single product or another assembly

                - prefix contains the **index** of the assembly  if he is visited for first time , else is False

                - ref contains the **index** of the assembly if he was visited previously, else False

    """

    valid=True
    if product.links:
        part_docs = []
        for link in product.links:
            link.visited=index[0]
            oq = forms.Order_Quantity_Form(request.POST,prefix=index[0])
            if not oq.is_valid():
                valid=False

            is_assembly = link.product.is_assembly
            name = link.product.name
            if not link.product.visited:
                link.product.visited = index[0]

                part_type = forms.Doc_Part_type_Form(request.POST, prefix=index[0])
                if not part_type.is_valid():
                    valid = False
                part = part_type.cleaned_data["type_part"]
                cls = get_all_plmobjects()[part]
                part_cform = pforms.get_creation_form(request.user, cls, request.POST,
                        inbulk_cache=inbulk_cache, prefix=str(index[0])+"-part")
                doc_cform = pforms.get_creation_form(request.user, models.Document3D, request.POST,
                        inbulk_cache=inbulk_cache, prefix=str(index[0])+"-document")
                if not part_cform.is_valid():
                    valid = False
                if not doc_cform.is_valid():
                    valid = False
                prefix = index[0]
                part_docs.append(PartDoc(part_type, oq, (part_cform, doc_cform), name, is_assembly,
                    prefix, None))
                index[0]+=1
                if not clean_form(request, assemblies, link.product,index, part, inbulk_cache):
                    valid = False
            else:
                index[0]+=1
                part_docs.append(PartDoc(False, oq, False, name, is_assembly, None, link.product.visited))

        assemblies.append(Assembly(part_docs, product.name , product.visited , product.deep, obj_type))
    return valid


def initialize_assemblies(assemblies,product,group,user,index, obj_type, inbulk_cache):
    """

    :param assemblies: will be refill whit the information necessary the generate the forms
    :param product: :class:`.Product` that represents the arborescense of the :class:`~django.core.files.File` .stp contained in a :class:`.DocumentFile`
    :param index: Use  to mark and to identify the **product** s that already have been visited
    :param obj_type: Type of the :class:`.Part` from which we want to realize the decomposition
    :param group: group by default from which we want to realize the decomposition


    Returns in assemblies a list initialized with the different assemblies of the file step


    For every Assembly we have the next information:

        - Name of assembly

        - Visited , If assembly is sub-assembly of more than an assembly, this attribute will be **False** for all less one of the occurrences

            If visited is **False**, we will be able to modify only the attributes **Order** , **Quantity** and **Unit** refered to the :class:`.ParentChildLinkin` in the form

            If visited is not **False** , it will be a new id acording to **index** (>=1) generated to identify the assembly

        - Depth  of assembly

        - **obj_type** , type of :class:`.Part` of Assembly

        - A list with the products that compose the assembly

          for each element in the list:

                - part_type contains the form to select the type of :class:`.Part`

                - ord_quantity contains the forms to select Order , Quantity and Unit refered to the :class:`.ParentChildLink`

                - creation_formset contains the form for the creation of the part selected in part_type and of one :class:`.Document3D`

                - name_child_assemblies contains the name of the element

                - is_assembly determine if the element is a single product or another assembly

                - prefix contains the **index** of the assembly if he is visited for first time , else is False

                - ref contains the **index** of the assembly if he was visited previously, else False

    """
    if product.links:
        part_docs = []
        for order, link in enumerate(product.links):
            prefix = index[0]
            oq=forms.Order_Quantity_Form(prefix=index[0])
            oq.fields["order"].initial = (order + 1)*10
            oq.fields["quantity"].initial = link.quantity
            is_assembly = link.product.is_assembly
            name = link.product.name
            if not link.product.visited:
                link.product.visited = index[0]
                part_type = forms.Doc_Part_type_Form(prefix=index[0])
                part_cform = pforms.get_creation_form(user, pmodels.Part, None, index[1], inbulk_cache) # index[0].initial=1 -> -1
                part_cform.prefix = str(index[0])+"-part"
                part_cform.fields["group"].initial = group
                part_cform.fields["name"].initial = link.product.name
                doc_cform = pforms.get_creation_form(user, models.Document3D, None, index[1], inbulk_cache)
                doc_cform.prefix = str(index[0])+"-document"
                doc_cform.fields["name"].initial = link.product.name
                doc_cform.fields["group"].initial = group
                prefix = index[0]

                part_docs.append(PartDoc(part_type, oq, (part_cform, doc_cform), name, is_assembly,
                    prefix, None))
                index[0]+=1
                index[1]+=1
                initialize_assemblies(assemblies,link.product,group,user,index, "Part", inbulk_cache)
            else:
                index[0]+=1
                part_docs.append(PartDoc(False, oq, False, name, is_assembly, None, link.product.visited))

        assemblies.append(Assembly(part_docs, product.name, product.visited, product.deep, obj_type))

@transaction.commit_on_success
def generate_part_doc_links_AUX(request,product, parent_ctrl,instances,doc3D):
    # wraps generate_part_doc_links with @commit_on_succes
    # it is not possible to decorate this function since it is recursive
    generate_part_doc_links(request,product, parent_ctrl,instances,doc3D, {})

def generate_part_doc_links(request,product, parent_ctrl,instances,doc3D, inbulk_cache):
    """
    :param product: :class:`.Product` that represents the arborescense
    :param parent_ctrl: :class:`.Part` from which we want to realize the decomposition
    :param instances: Use to trace the items to update

    Parses forms and generates:


    - The bom-child of Parts (in relation to the **product**)

    - For every :class:`.ParentChildLink` generated in the previous condition we attach all the :class:`.Location_link` relatives

    - To every generated :class:`.Part` a :class:`.Document3D` has been attached and Document3D has been set like the attribute PartDecompose of the Part

    - The attribute doc_id of every node of the arborescense(**product**) is now the relative id of :class:`.DocumentFile` generated in the previous condition

    - To every generated :class:`.Document3D` has been added a new empty(locked) :class:`.DocumentFile` STP ( :meth:`.generateGhostDocumentFile` )

    - The attribute doc_path of every node of the arborescense(**product**) is now the path of :class:`.DocumentFile` STP generated in the previous condition
    """

    to_delete=[]
    user = parent_ctrl._user
    company = pmodels.User.objects.get(username=settings.COMPANY)
    other_files = list(doc3D.files.exclude(models.is_stp))
    for link in product.links:
        try:

            oq=forms.Order_Quantity_Form(request.POST,prefix=link.visited)
            oq.is_valid()
            options=oq.cleaned_data
            order=options["order"]
            quantity=options["quantity"]
            unit=options["unit"]

            if not link.product.part_to_decompose:

                part_ctype=forms.Doc_Part_type_Form(request.POST,prefix=link.product.visited)
                part_ctype.is_valid()
                options = part_ctype.cleaned_data
                cls = get_all_plmobjects()[options["type_part"]]
                part_form = pforms.get_creation_form(user, cls, request.POST,
                    inbulk_cache=inbulk_cache, prefix=str(link.product.visited)+"-part")

                part_ctrl = parent_ctrl.create_from_form(part_form, user, True, True)

                instances.append((part_ctrl.object._meta.app_label,
                    part_ctrl.object._meta.module_name, part_ctrl.object._get_pk_val()))

                c_link = parent_ctrl.add_child(part_ctrl.object,quantity,order,unit)

                models.generate_extra_location_links(link, c_link)

                doc_form = pforms.get_creation_form(user, models.Document3D, request.POST,
                    inbulk_cache=inbulk_cache, prefix=str(link.product.visited)+"-document")
                doc_ctrl = models.Document3DController.create_from_form(doc_form,
                        user, True, True)

                link.product.part_to_decompose=part_ctrl.object
                to_delete.append(generateGhostDocumentFile(link.product, doc_ctrl.object, company))

                instances.append((doc_ctrl.object._meta.app_label,
                    doc_ctrl.object._meta.module_name, doc_ctrl.object._get_pk_val()))
                part_ctrl.attach_to_document(doc_ctrl.object)
                new_Doc3D = doc_ctrl.object
                new_Doc3D.PartDecompose = part_ctrl.object
                new_Doc3D.no_index = True
                new_Doc3D.save()

                for doc_file in other_files:
                    filename, ext = os.path.splitext(doc_file.filename)
                    # add files with the same name (for example a .sldXXX
                    # or.CATXXX file)
                    if filename == link.product.name:
                        f = File(doc_file.file)
                        f.name = doc_file.filename
                        f.size = doc_file.size
                        df = doc_ctrl.add_file(f, False, False)
                        if doc_file.thumbnail:
                            doc_ctrl.add_thumbnail(df, File(doc_file.thumbnail))
                        instances.append((df._meta.app_label, df._meta.module_name, df.pk))
                        instances.append((doc_file._meta.app_label, doc_file._meta.module_name, doc_file.pk))
                        doc_file.no_index = True
                        doc_file.deprecated = True
                        doc_file.save()

                generate_part_doc_links(request,link.product, part_ctrl,instances,doc3D, inbulk_cache)

            else:

                c_link = parent_ctrl.add_child(link.product.part_to_decompose,quantity,order,unit)
                models.generate_extra_location_links(link, c_link)

        except Exception:
            raise models.Document_Generate_Bom_Error(to_delete,link.product.name)

def generateGhostDocumentFile(product, document, locker):
    """
    :param product: :class:`.Product` that represents the arborescense
    :param Doc_controller: :class:`.Document3DController` from which we want to generate the :class:`.DocumentFile`


    For one :class:`.Product` (**product**) and one :class:`.Document3DController` (**Doc_controller**), generates a :class:`.DocumentFile` with a file .stp emptily without indexation

    It updates the attributes **doc_id** and **doc_path** of the :class:`.Product` (**product**) in relation of the generated :class:`.DocumentFile`

    """
    doc_file = pmodels.DocumentFile()
    name = doc_file.file.storage.get_available_name(product.name+".stp")
    path = os.path.join(doc_file.file.storage.location, name)
    f = File(open(path.encode(), 'w'))
    f.close()
    doc_file.no_index = True
    doc_file.filename = "Ghost.stp"
    doc_file.size = f.size
    doc_file.file = name
    doc_file.document = document
    doc_file.locked = True
    doc_file.locker = locker
    doc_file.save()
    product.doc_id = doc_file.id
    product.doc_path = doc_file.file.path
    return doc_file.file.path


@secure_required
@ajax_login_required
def ajax_part_creation_form(request, prefix):
    """
    It updates the form of an assembly determined by **prefix** without recharging the whole page and respecting the information introduced up to the moment

    The attributes can change depending on the type of part selected

    """
    tf = forms.Doc_Part_type_Form(request.GET, prefix=prefix)

    if tf.is_valid():
        cls = pmodels.get_all_parts()[tf.cleaned_data["type_part"]]
        cf = pforms.get_creation_form(request.user, cls, prefix=prefix+"-part",
                data=dict(request.GET.iteritems()))

        return r2r("extra_attributes.html", {"creation_form" : cf}, request)

    return HttpResponseForbidden()


def same_time(old_modification_data,old_modification_data_microsecond,mtime):
    d = old_modification_data.replace(microsecond=int(old_modification_data_microsecond))
    return d == mtime

