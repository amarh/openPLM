from openPLM.plmapp.base_views import handle_errors, secure_required, get_generic_data
from openPLM.document3D.forms import *
from openPLM.document3D.models import *
from openPLM.document3D.arborescense import *
from openPLM.document3D.decomposer import *
from openPLM.plmapp.forms import *
import openPLM.plmapp.models as models
from django.db import transaction
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect, HttpResponseForbidden
from openPLM.plmapp.tasks import update_indexes
from openPLM.plmapp.exceptions import LockError
from openPLM.plmapp.controllers import get_controller
from openPLM.plmapp.decomposers.base import Decomposer, DecomposersManager
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from openPLM.plmapp.views.main import r2r


@handle_errors
def display_3d(request, obj_ref, obj_revi):
    """ Manage html page for 3D

    Manage html page which displays the 3d files STEP of the selected object.
    It computes a context dictionnary based on

    .. include:: views_params.txt
    """

    obj_type = "Document3D"
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ctx['current_page'] = '3D'

    try:
        doc_file = obj.files.filter(is_stp)[0]
    except IndexError:
        doc_file = None

    if doc_file is None:
        GeometryFiles=[]
        javascript_arborescense=False
    else:
        GeometryFiles=list(GeometryFile.objects.filter(stp=doc_file))
        add_child_GeometryFiles(request.user,doc_file,GeometryFiles)
        product=read_ArbreFile(doc_file,request.user)
        javascript_arborescense=generate_javascript_for_3D(product)

    ctx.update({
        'GeometryFiles' : GeometryFiles ,
        'javascript_arborescense' : javascript_arborescense , })

    return r2r('Display3D.htm', ctx, request)


class StepDecomposer(Decomposer):

    def is_decomposable(self):
        decompose_valid = []
        if not Document3D.objects.filter(PartDecompose=self.part):
            for link in self.part.documentpartlink_part.all():
                try:
                    doc = Document3D.objects.get(id=link.document_id)
                    if not doc.PartDecompose:
                        file_stp = is_decomposable(doc)
                        if file_stp:
                            decompose_valid.append((link.document, file_stp))
                except:
                    pass
        self.decompose_valid = decompose_valid
        return len(decompose_valid) > 0

    def get_message(self):
        if self.decompose_valid:
            return render_to_string("decompose_msg.html", { "part" : self.part,
                "decomposable_docs" : self.decompose_valid })
        return ""

DecomposersManager.register(StepDecomposer)
#posibilidades , el objeto a sido modificado despues de acceder al formulario

Select_Doc_Part_types = formset_factory(Doc_Part_type_Form, extra=0)
Select_Order_Quantity_types = formset_factory(Order_Quantity_Form, extra=0)
@handle_errors
def display_decompose(request, obj_type, obj_ref, obj_revi, stp_id):

    #incluir los script para autocompletar nombres y esos ole1
    """
    Manage html page which displays the chidren of the selected object.
    It computes a context dictionnary based on

    .. include:: views_params.txt
    """

    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    stp_file=DocumentFile.objects.get(id=stp_id)

    doc_linked_to_part=obj.get_attached_documents().values_list("document_id", flat=True)
    if not stp_file.document_id in doc_linked_to_part:
        raise ValueError("Not allowed operation.The Document and the Part are not linked")
    if Document3D.objects.filter(PartDecompose=obj.object):
        raise ValueError("Not allowed operation.This Part already forms a part of another decomposition")
    try:
        doc3D=Document3D.objects.get(id=stp_file.document_id)
    except Document3D.DoesNotExist:
        raise ValueError("Not allowed operation.The document is not a subtype of document3D")

    if doc3D.PartDecompose:# y si el documento no es 3D
        raise ValueError("Not allowed operation.This Document already forms a part of another decomposition")

    if request.method == 'POST':

        extra_errors=""
        product=read_ArbreFile(stp_file)
        part_type_formset = Select_Doc_Part_types(request.POST)
        bom_formset = Select_Order_Quantity_types(request.POST)
        creation_formset = []
        last_time_modification=Form_save_time_last_modification(request.POST)
        #comprobar que la parte no ha sido descompuesta con anterioridad
        obj.block_mails()

        if last_time_modification.is_valid():
            old_modification_data_time=last_time_modification.cleaned_data['last_modif_time']
            old_modification_data_microsecond=last_time_modification.cleaned_data['last_modif_microseconds']

            options=clear_form(request ,part_type_formset,bom_formset,creation_formset)
            document_controller=DocumentController(stp_file.document,request.user)

            if options:

                # y si tiene un nativo   que hago con el
                if (same_time(old_modification_data_time, 
                              old_modification_data_microsecond,
                              document_controller.mtime)
                    and product and len(product.links) == len(options)
                    and stp_file.checkout_valid):

                    try:
                        native_related=stp_file.native_related
                        if native_related:
                            native_related.deprecated=True
                        document_controller.lock(stp_file)

                        try:
                            instances=decomposer_stp(stp_file,options,product,obj)
                        except Exception as excep:
                            if isinstance(excep, Document3D_decomposer_Error):
                                delete_files(excep.to_delete)
                            extra_errors = unicode(excep)
                        else:
                            update_indexes.delay(instances)
                            ctrl=get_controller(stp_file.document.type)
                            ctrl=ctrl(stp_file.document,obj._user)
                            ctrl.deprecate_file(stp_file)
                            Doc3D=Document3D.objects.get(id=ctrl.object.id)
                            Doc3D.PartDecompose=obj.object
                            Doc3D.save()
                            return HttpResponseRedirect(obj.plmobject_url+"BOM-child/")
                        finally:
                            document_controller.unlock(stp_file)

                    except LockError as excep:
                        extra_errors="Documentfile is locked"
                    finally:

                        if native_related:
                            native_related.deprecated=False
                            native_related.save(False)

                else:
                    extra_errors="The Document3D associated with the file STEP to decompose has been modified by another user while the forms were refilled:Please restart the process"
        else:
            extra_errors="Mistake reading of the last modification of the document, please restart the task"

    else:

        document_controller=DocumentController(stp_file.document,request.user)

        last_time_modification=Form_save_time_last_modification()
        last_time_modification.fields["last_modif_time"].initial=document_controller.mtime

        last_time_modification.fields["last_modif_microseconds"].initial=document_controller.mtime.microsecond
        product=read_ArbreFile(stp_file)
        if not product or not product.links:
            return HttpResponseRedirect(obj.plmobject_url+"BOM-child/")
        
        initial_bom_values = []
        for index, link in enumerate(product.links):
            order = (index + 1) * 10
            initial_bom_values.append({"order": order, "quantity" : link.quantity })

        part_type_formset = Select_Doc_Part_types(initial=[{} for i in range(len(product.links))])
        bom_formset = Select_Order_Quantity_types(initial=initial_bom_values)
        extra_errors = ""
        creation_formset = []
        group = obj.group
        for index, form in enumerate(part_type_formset.forms):
            name = product.links[index].product.name
            part_cform = get_creation_form(request.user, Part, None, index)
            part_cform.prefix = str(index*2)
            part_cform.fields["group"].initial = group
            part_cform.fields["name"].initial = name
            doc_cforms = get_creation_form(request.user, Document3D, None, index)
            doc_cforms.prefix = str(index*2+1)
            doc_cforms.fields["name"].initial = name 
            doc_cforms.fields["group"].initial = group
            creation_formset.append([part_cform, doc_cforms])

    forms = zip(part_type_formset.forms, creation_formset, bom_formset.forms)

    ctx.update({'current_page':'decomposer',  # aqui cambiar
                'forms' : forms,
                'part_type_formset' : part_type_formset,
                'bom_formset' : bom_formset,
                'extra_errors' :  extra_errors ,
                'last_time_modification' : last_time_modification

                })

    return r2r('DisplayDecompose.htm', ctx, request)


def generate_part_doc_links(prepare_list, links, parent_ctrl):
    index = 0
    doc_controllers = []
    instances = []
    user = parent_ctrl._user
    for ord_quantity, (part_form, doc_form)  in prepare_list:

        try:
            part_ctrl = parent_ctrl.create_from_form(part_form, user, True, True)
            instances.append((part_ctrl.object._meta.app_label,
                part_ctrl.object._meta.module_name, part_ctrl.object._get_pk_val()))

            link = parent_ctrl.add_child(part_ctrl.object,ord_quantity[1],ord_quantity[0],ord_quantity[2])
            generate_extra_location_links(links[index], link)
            doc_ctrl = Document3DController.create_from_form(doc_form,
                    user, True, True)
            instances.append((doc_ctrl.object._meta.app_label,
                doc_ctrl.object._meta.module_name, doc_ctrl.object._get_pk_val()))
            part_ctrl.attach_to_document(doc_ctrl.object)
            doc_controllers.append(doc_ctrl)

            index+=1
        except :
            raise Document_part_doc_links_Error()

    return doc_controllers , instances


def clear_form(request, part_type_formset, bom_formset, creation_formset):
    valid=True
    if bom_formset.is_valid():
        order_quantity_extra_links=[]
        for form in bom_formset.forms:
            if form.is_valid():

                options=form.cleaned_data
                order_quantity_extra_links.append([options["order"],options["quantity"],options["unit"]])
            else:
                valid = False
    else:

        valid=False

    if part_type_formset.is_valid():
        index=0
        for form in part_type_formset.forms:
            options=form.cleaned_data
            part = options["type_part"]
            cls = models.get_all_plmobjects()[part]
            part_form = get_creation_form(request.user, cls, request.POST,
                    prefix=str(index*2))
            if not part_form.is_valid():#son necesarios?
                valid=False
            doc_form = get_creation_form(request.user, Document3D,
                    request.POST, prefix=str(index*2+1))
            creation_formset.append([part_form,doc_form])

            if not doc_form.is_valid(): #son necesarios?
                valid=False
            index=index+1

    else:
        valid=False

    if valid:
        return zip(order_quantity_extra_links,creation_formset)
    else:
        return valid

@secure_required
@login_required
def ajax_part_creation_form(request, prefix):
    tf = Doc_Part_type_Form(request.GET, prefix=prefix)
    if tf.is_valid():
        cls = get_all_parts()[tf.cleaned_data["type_part"]]
        prefix = prefix.replace("form-", "")
        cf = get_creation_form(request.user, cls, prefix=str(int(prefix) * 2 ),
                data=dict(request.GET.iteritems()))
        return r2r("extra_attributes.html", {"creation_form" : cf}, request)
    return HttpResponseForbidden()
    
    

def same_time(old_modification_data,old_modification_data_microsecond,mtime):

    return (old_modification_data_microsecond == mtime.microsecond
            and old_modification_data.second == old_modification_data.second
            and old_modification_data.minute == old_modification_data.minute
            and old_modification_data.hour == old_modification_data.hour
            and old_modification_data.date()==old_modification_data.date())

########################################################################
@transaction.commit_on_success
def decomposer_stp(stp_file,options,product,obj):

    list_doc3D_controller , instances =generate_part_doc_links(options,product.links,obj)
    instances+=decomposer_all(stp_file,list_doc3D_controller,obj._user)
    return instances

    # TODO: send one mail listing all created objects

