from openPLM.plmapp.base_views import handle_errors, secure_required, get_generic_data
from openPLM.document3D.forms import *
from openPLM.document3D.models import *
from openPLM.document3D.arborescense import *
from openPLM.document3D.decomposer import *
from openPLM.plmapp.forms import *
import openPLM.plmapp.models as models
from django.db import transaction
from django.forms.formsets import formset_factory
from django.http import HttpResponse ,HttpResponseRedirect
from openPLM.plmapp.tasks import update_indexes
from openPLM.plmapp.exceptions import LockError
from mimetypes import guess_type
from openPLM.document3D.composer import composer
from openPLM.plmapp.controllers import get_controller
import openPLM.plmapp.forms as forms
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

    if request.method == 'POST':
        form = Form3D(request.POST, document=obj) #important Document3DController.files dont return step_original , Document3D.files will return step_original
        if form.is_valid():
            options = form.cleaned_data
            doc_file = options["Display"]
            GeometryFiles=list(GeometryFile.objects.filter(stp=doc_file))
            add_child_GeometryFiles(request.user,doc_file,GeometryFiles)
            product=read_ArbreFile(doc_file,request.user)
            javascript_arborescense=generate_javascript_for_3D(product)

            ctx.update({'select_stp_form': form, 'GeometryFiles' : GeometryFiles,'javascript_arborescense' : javascript_arborescense, })
            return r2r('Display3D.htm', ctx, request)

    form = Form3D(document=obj)#important Document3DController.files dont return step_original , Document3D.files will return step_original

    doc_file = form.fields["Display"].initial

    if doc_file is None:
        GeometryFiles=[]
        javascript_arborescense=False
    else:
        GeometryFiles=list(GeometryFile.objects.filter(stp=doc_file))
        add_child_GeometryFiles(request.user,doc_file,GeometryFiles)
        product=read_ArbreFile(doc_file,request.user)
        javascript_arborescense=generate_javascript_for_3D(product)

    ctx.update({'select_stp_form': form,
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
        Select_Doc_Part_types = formset_factory(Doc_Part_type_Form)
        Select_Order_Quantity_types = formset_factory(Order_Quantity_Form)
        form_Doc_Part_types = Select_Doc_Part_types(request.POST)
        form_Order_Quantity = Select_Order_Quantity_types(request.POST)
        form_Doc_Part_attributes = []
        last_time_modification=Form_save_time_last_modification(request.POST)
        #comprobar que la parte no ha sido descompuesta con anterioridad

        if last_time_modification.is_valid():
            old_modification_data_time=last_time_modification.cleaned_data['last_modif_time']
            old_modification_data_microsecond=last_time_modification.cleaned_data['last_modif_microseconds']

            options=clear_form(request ,form_Doc_Part_types,form_Order_Quantity,form_Doc_Part_attributes)
            document_controller=DocumentController(stp_file.document,request.user)

            if options:

                # y si tiene un nativo   que hago con el
                if  same_time(old_modification_data_time,old_modification_data_microsecond,document_controller.mtime) and product and len(product.links)==len(options) and stp_file.checkout_valid:

                    try:
                        native_related=stp_file.native_related
                        if native_related:
                            native_related.deprecated=True
                        document_controller.lock(stp_file)

                        try:
                            instances=decomposer_stp(stp_file,options,product,obj)
                        except Exception as excep:
                            if type(excep) == Document3D_decomposer_Error:
                                delete_files(excep.to_delete)
                            extra_errors=excep.__unicode__()
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
        Select_Doc_Part_types = formset_factory(Doc_Part_type_Form)
        Select_Order_Quantity_types = formset_factory(Order_Quantity_Form)
        data = {
        'form-TOTAL_FORMS': u'%s'%len(product.links),
        'form-INITIAL_FORMS': u'%s'%len(product.links),
        'form-MAX_NUM_FORMS': u'%s'%len(product.links),
        }
        index=0
        for link in product.links:
            order=(index+1)*10
            data.update({'form-%s-order'%index :u'%s'%order,
                         'form-%s-quantity'%index : u'%s'%link.quantity,
                         'form-%s-type_part'%index :u'Part',
                         'form-%s-type_document3D'%index : u'Document3D',
                        })
            index=index+1

        form_Doc_Part_types = Select_Doc_Part_types(data)
        form_Order_Quantity = Select_Order_Quantity_types(data)
        extra_errors=""
        form_Doc_Part_attributes = []
        names=[]
        index=0
        for form in form_Doc_Part_types.forms:
            part_attributes=get_creation_form(request.user,models.get_all_plmobjects()["Part"],None, index)
            part_attributes.prefix=index*2
            part_attributes.fields["group"].initial=obj.object.group
            part_attributes.fields["name"].initial=product.links[index].product.name
            doc_attributes=get_creation_form(request.user,models.get_all_plmobjects()["Document3D"],None,index)
            doc_attributes.prefix=index*2+1
            doc_attributes.fields["name"].initial=product.links[index].product.name
            doc_attributes.fields["group"].initial=obj.object.group
            form_Doc_Part_attributes.append([part_attributes,doc_attributes])
            index=index+1

    zip_list=zip(form_Doc_Part_types.forms,form_Doc_Part_attributes,form_Order_Quantity.forms)

    ctx.update({'current_page':'decomposer',  # aqui cambiar
                'object_type': 'Document3D',
                'zip' : zip_list,
                'form_Doc_Part_types' : form_Doc_Part_types,
                'form_Order_Quantity' : form_Order_Quantity,
                'extra_errors' :  extra_errors ,
                'last_time_modification' : last_time_modification

                })

    return r2r('DisplayDecompose.htm', ctx, request)


def generate_part_doc_links(prepare_list,links,obj):
    index=0
    list_document_controller=[]
    instances = []
    for ord_quantity , part_doc_create_form  in prepare_list:

        try:
            part_controller=obj.create_from_form(part_doc_create_form[0],obj._user, True, True)
            instances.append((part_controller.object._meta.app_label,part_controller.object._meta.module_name, part_controller.object._get_pk_val()))

            ParentChildLink = obj.add_child(part_controller.object,ord_quantity[1],ord_quantity[0],ord_quantity[2])
            generate_extra_location_links(links[index],ParentChildLink)
            form = part_doc_create_form[1]
            controller_cls = get_controller(form.Meta.model.__name__)
            doc_controller=controller_cls.create_from_form(part_doc_create_form[1],obj._user, True, True)
            instances.append((doc_controller.object._meta.app_label,doc_controller.object._meta.module_name, doc_controller.object._get_pk_val()))
            part_controller.attach_to_document(doc_controller.object)
            list_document_controller.append(doc_controller)

            index+=1
        except :
            raise  Document_part_doc_links_Error

    return list_document_controller , instances


@handle_errors
def clear_form(request,form_Doc_Part_types,form_Order_Quantity,form_Doc_Part_attributes):
    valid=True
    if form_Order_Quantity.is_valid():
        order_quantity_extra_links=[]
        for form in form_Order_Quantity.forms:
            if form.is_valid():

                options=form.cleaned_data
                order_quantity_extra_links.append([options["order"],options["quantity"],options["unit"]])
            else:
                valid = False
    else:

        valid=False

    if form_Doc_Part_types.is_valid():
        index=0
        for form in form_Doc_Part_types.forms:
            options=form.cleaned_data
            part = options["type_part"]
            cls = models.get_all_plmobjects()[part]
            part_form = get_creation_form(request.user, cls, request.POST,0,prefix=index*2)
            if not part_form.is_valid():#son necesarios?
                valid=False
            doc = options["type_document3D"]
            cls = models.get_all_plmobjects()[doc]
            doc_form = get_creation_form(request.user, cls, request.POST,0,prefix=index*2+1)
            form_Doc_Part_attributes.append([part_form,doc_form])

            if not doc_form.is_valid(): #son necesarios?
                valid=False
            index=index+1

    else:
        valid=False

    if valid:
        return zip(order_quantity_extra_links,form_Doc_Part_attributes)
    else:
        return valid


@secure_required
@login_required
def ajax_decompose_form(request):
    Select_Doc_Part_types = formset_factory(Doc_Part_type_Form)
    form_Doc_Part_types = Select_Doc_Part_types(request.GET)
    Select_Order_Quantity_types = formset_factory(Order_Quantity_Form)
    form_Order_Quantity = Select_Order_Quantity_types(request.GET)
    last_time_modification=Form_save_time_last_modification(request.GET)

    form_Doc_Part_attributes = []
    index=0
    if form_Doc_Part_types.is_valid():
        for form in form_Doc_Part_types.forms:
            if form.is_valid(): # es necesario este valid?
                options=form.cleaned_data
                part = options["type_part"]
                part_attributes=get_creation_form(request.user,models.get_all_plmobjects()[part])
                part_attributes.prefix=index*2
                doc= options["type_document3D"]
                doc_attributes=get_creation_form(request.user,models.get_all_plmobjects()[doc])
                doc_attributes.prefix=index*2+1
                form_Doc_Part_attributes.append([part_attributes,doc_attributes])
                index=index+1

        zip_list=zip(form_Doc_Part_types.forms,form_Doc_Part_attributes,form_Order_Quantity.forms)

        ctx={
                'current_page':'BOM-child',  # aqui cambiar
                'object_type': 'Document3D',
                'zip' : zip_list,
                'form_Doc_Part_types' : form_Doc_Part_types,
                'form_Order_Quantity' : form_Order_Quantity,
                'last_time_modification' : last_time_modification,
                }

        return r2r('GenerateSimple.htm', ctx, request)

def same_time(old_modification_data,old_modification_data_microsecond,mtime):

    return (old_modification_data_microsecond == mtime.microsecond
            and old_modification_data.second == old_modification_data.second
            and old_modification_data.minute == old_modification_data.minute
            and old_modification_data.hour == old_modification_data.hour
            and old_modification_data.date()==old_modification_data.date())


@handle_errors
def download(request, docfile_id, filename=""):
    """
    View to download a document file.

    :param request: :class:`django.http.QueryDict`
    :param docfile_id: :attr:`.DocumentFile.id`
    :type docfile_id: str
    :return: a :class:`django.http.HttpResponse`
    """

    doc_file = DocumentFile.objects.get(id=docfile_id)
    ctrl=DocumentController(doc_file.document,request.user)
    ctrl.check_readable()
    name = doc_file.filename.encode("utf-8", "ignore")
    mimetype = guess_type(name, False)[0]
    if not mimetype:
        mimetype = 'application/octet-stream'

    fileName, fileExtension = os.path.splitext(doc_file.filename)
    if fileExtension.upper() in ('.STP', '.STEP') and not doc_file.deprecated:

        tempfile=composer(doc_file,request.user)
        size=os.path.getsize(tempfile.path)

        response = HttpResponse(tempfile, mimetype=mimetype)
        response["Content-Length"] = size

    else:
        response = HttpResponse(file(doc_file.file.path), mimetype=mimetype)
        response["Content-Length"] = doc_file.file.size

    if not filename:
        response['Content-Disposition'] = 'attachment; filename="%s"' % name

    return response

#######################################################################
@handle_errors
def display_files(request,  obj_ref, obj_revi):
    """
    Manage html page which displays the files (:class:`DocumentFile`) uploaded in the selected object.
    It computes a context dictionnary based on
    add new donwload for stp decomposed
    .. include:: views_params.txt
    """
    obj_type="Document3D"
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    if not hasattr(obj, "files"):
        raise TypeError()
    if request.method == "POST":
        formset = get_file_formset(obj, request.POST)
        if formset.is_valid():
            obj.update_file(formset)
            return HttpResponseRedirect(".")
    else:
        formset = get_file_formset(obj)

    archive_form = forms.ArchiveForm()

    ctx.update({'current_page':'files',
                'file_formset': formset,
                'archive_form' : archive_form,
                'deprecated_files' : obj.deprecated_files,
               })
    return r2r('displayfiles3D.html', ctx, request)

########################################################################
@transaction.commit_on_success
def decomposer_stp(stp_file,options,product,obj):

    list_doc3D_controller , instances =generate_part_doc_links(options,product.links,obj)
    instances+=decomposer_all(stp_file,list_doc3D_controller,obj._user)
    return instances

    # TODO: send one mail listing all created objects

