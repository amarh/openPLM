from openPLM.plmapp.base_views import handle_errors, secure_required, get_generic_data
from openPLM.document3D.forms import *
from openPLM.document3D.models import *
from openPLM.document3D.arborescense import *
from openPLM.document3D.classes import *
from openPLM.plmapp.forms import *
from openPLM.plmapp.models import get_all_plmobjects
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
import tempfile

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
        #puede haberlos repetidos, arreglar
        GeometryFiles=list(GeometryFile.objects.filter(stp=doc_file))
        add_child_GeometryFiles(doc_file,GeometryFiles)
        product=read_ArbreFile(doc_file,True)
        javascript_arborescense=generate_javascript_for_3D(product)

    ctx.update({
        'GeometryFiles' : GeometryFiles ,
        'javascript_arborescense' : javascript_arborescense , })

    return r2r('Display3D.htm', ctx, request)


class StepDecomposer(Decomposer):

    __slots__ = ("part", "decompose_valid")

    def is_decomposable(self, msg=True):
        decompose_valid = []
        if not Document3D.objects.filter(PartDecompose=self.part).exists():
            links = DocumentPartLink.objects.filter(part=self.part,
                    document__type="Document3D",
                    document__document3d__PartDecompose=None).values_list("document", flat=True)
            for doc_id in links:
                try:
                    if msg:
                        doc = Document3D.objects.get(id=doc_id)
                    else:
                        doc = doc_id
                    file_stp = is_decomposable(doc)
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
        # invalid parts are parts already decomposed by a StepDecomposer
        invalid_parts = Document3D.objects.filter(PartDecompose__in=parts)\
                .values_list("PartDecompose", flat=True)
        links = list(DocumentPartLink.objects.filter(part__in=parts,
                document__type="Document3D", # Document3D has no subclasses
                document__document3d__PartDecompose=None). \
                exclude(part__in=invalid_parts).values_list("document", "part"))
        docs = [l[0] for l in links]
        # valid documents are document with a step file that is decomposable
        valid_docs = dict(ArbreFile.objects.filter(stp__document__in=docs,
            stp__deprecated=False, stp__locked=False,
            decomposable=True).values_list("stp__document", "stp"))
        for doc_id, part_id in links:
            if (doc_id not in valid_docs) or (part_id in decomposable):
                continue
            stp = DocumentFile.objects.only("document", "filename").get(id=valid_docs[doc_id])
            if stp.checkout_valid:
                decomposable.add(part_id)
        return decomposable

    def get_message(self):
        if self.decompose_valid:
            return render_to_string("decompose_msg.html", { "part" : self.part,
                "decomposable_docs" : self.decompose_valid })
        return ""

DecomposersManager.register(StepDecomposer)
#posibilidades , el objeto a sido modificado despues de acceder al formulario

Select_Doc_Part_types = formset_factory(Doc_Part_type_Form, extra=0)
Select_Order_Quantity_types = formset_factory(Order_Quantity_Form, extra=0)
#@handle_errors
def display_decompose(request, obj_type, obj_ref, obj_revi, stp_id):

    #incluir los script para autocompletar nombres y esos ole1
    """
    Manage html page which displays the chidren of the selected object.
    It computes a context dictionnary based on

    .. include:: views_params.txt
    """

    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    stp_file=DocumentFile.objects.get(id=stp_id)
    assemblys=[]
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
        #part_type_formset = Select_Doc_Part_types(request.POST)
        #bom_formset = Select_Order_Quantity_types(request.POST)
        last_time_modification=Form_save_time_last_modification(request.POST)
        #comprobar que la parte no ha sido descompuesta con anterioridad
        obj.block_mails()

        if last_time_modification.is_valid() and product:
            old_modification_data_time=last_time_modification.cleaned_data['last_modif_time']
            old_modification_data_microsecond=last_time_modification.cleaned_data['last_modif_microseconds']


            document_controller=DocumentController(stp_file.document,User.objects.get(username=settings.COMPANY))
            index=[1]
            if clear_form(request,assemblys,product,index):
                
                # y si tiene un nativo   que hago con el
                if (same_time(old_modification_data_time, 
                              old_modification_data_microsecond,
                              document_controller.mtime)
                    and product and stp_file.checkout_valid and not stp_file.locked):
                    

                    
                   
                    stp_file.locked=True
                    stp_file.locker=User.objects.get(username=settings.COMPANY)
                    stp_file.save(False)
                    native_related=stp_file.native_related
                       
                    if native_related:
                        native_related.deprecated=True
                        native_related.save(False)
                        native_related_pk=native_related.pk
                    else:
                        native_related_pk=None


                    try:
                        instances=[]
                        print "Empieza la decomposicion" 
                        generate_part_doc_links_AUX(request,product, obj,instances)
                        print "entra"
                        update_indexes.delay(instances) 
                    except Exception as excep:
                        if type(excep) == Document_part_doc_links_Error:
                            delete_files(excep.to_delete)

                        
                        
                        extra_errors = unicode(excep)
                        stp_file.locked = False
                        stp_file.locker = None
                        stp_file.save(False)
                        if native_related:
                            native_related.deprecated=False
                            native_related.save(False)
                    else:
                        decomposer_all.delay(stp_file.pk,json.dumps(data_for_product(product)),obj.object.pk,native_related_pk,obj._user.pk)
                        #decomposer_all(stp_file.pk,json.dumps(data_for_product(product)),obj.object.pk,native_related_pk,obj._user.pk)
                        return HttpResponseRedirect(obj.plmobject_url+"BOM-child/")
  




                else:
                    extra_errors="The Document3D associated with the file STEP to decompose has been modified by another user while the forms were refilled:Please restart the process"
                
            else:

                extra_errors="Mistake refilling the form, please check it"

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
        
        group = obj.group
        index=[1,0] # index[1] to evade generate holes in part_revision_default generation
        initialiser_assemblys(assemblys,product,group,request,index)
        deep_assemblys=sort_assemblys(assemblys)

        extra_errors = ""
        


    ctx.update({'current_page':'decomposer',  # aqui cambiar
                'deep_assemblys' : deep_assemblys,
                'extra_errors' :  extra_errors ,
                'last_time_modification' : last_time_modification

                })

    return r2r('DisplayDecompose.htm', ctx, request)
    
    
def sort_assemblys(assemblys):

    new_assembly=[]
    for elem in assemblys:
        print elem[3]
        for i in range(elem[3]+1-len(new_assembly)):
            new_assembly.append([])        
        new_assembly[elem[3]].append(elem)

    return new_assembly             

    

def clear_form(request,assemblys, product,index):


    creation_formset=[]
    initial_bom_values=[]
    initial_deep_values=[]
    child_assemblys=[]
    is_assembly=[]
    part_type=[]
    ord_quantity=[]
    prefix=[]
    ref=[]    
    valid=True
    if product.links:
        for link in product.links:
        

            ord_qty=Order_Quantity_Form(request.POST,prefix=index[0])
            link.visited=index[0] # para evitar en caso de nodos repetidos utilizar el link del padre


            if not ord_qty.is_valid():
                valid=False
     
            ord_quantity.append(ord_qty)
            is_assembly.append(link.product.is_assembly)
            child_assemblys.append(link.product.name)
                        
            if not link.product.visited:
                part_ctype=Doc_Part_type_Form(request.POST,prefix=index[0])
                if not part_ctype.is_valid():
                    valid=False        
                options=part_ctype.cleaned_data
                part = options["type_part"]
                cls = get_all_plmobjects()[part]
                part_form = get_creation_form(request.user, cls, request.POST,
                        prefix=str(index[0])+"-part")            
                doc_form = get_creation_form(request.user, Document3D,
                        request.POST, prefix=str(index[0])+"-document")                    
                if not part_form.is_valid():
                    valid=False
                if not doc_form.is_valid():
                    valid=False               

                prefix.append(index[0])
                creation_formset.append([part_form, doc_form])                                
                ref.append(None)          
                part_type.append(part_ctype) 
                link.product.visited=index[0]                 
                index[0]+=1            

                                              
                if not clear_form(request, assemblys, link.product,index):
                    valid=False
            else:
                index[0]+=1 
                part_type.append(False);creation_formset.append(False);prefix.append(False);ref.append(link.product.visited)
                                
        assemblys.append((zip(part_type ,ord_quantity,  creation_formset,  child_assemblys , is_assembly , prefix , ref )  , product.name , product.visited , product.deep))            
    return valid                                    
        
        
   
def initialiser_assemblys(assemblys,product,group,request,index):

    creation_formset=[]
    initial_bom_values=[]
    initial_deep_values=[]
    child_assemblys=[]
    is_assembly=[]
    part_type=[]
    ord_quantity=[]
    prefix=[]
    ref=[]
    if product.links:
        for order , link in enumerate(product.links):
            
            oq=Order_Quantity_Form(prefix=index[0])

            oq.fields["order"].initial=(order+1)*10
            oq.fields["quantity"].initial=link.quantity
            ord_quantity.append(oq)
            is_assembly.append(link.product.is_assembly)
            child_assemblys.append(link.product.name)
            if not link.product.visited:            
                part_type.append(Doc_Part_type_Form(prefix=index[0])) 
                part_cform = get_creation_form(request.user, Part, None, (index[1])) # index[0].initial=1 -> -1
                part_cform.prefix = str(index[0])+"-part"
                part_cform.fields["group"].initial = group
                part_cform.fields["name"].initial = link.product.name
                doc_cforms = get_creation_form(request.user, Document3D, None, (index[1]))
                doc_cforms.prefix = str(index[0])+"-document"
                doc_cforms.fields["name"].initial = link.product.name 
                doc_cforms.fields["group"].initial = group
                prefix.append(index[0])
                creation_formset.append([part_cform, doc_cforms])                                
                link.product.visited=index[0]
                ref.append(None)
                index[0]+=1
                index[1]+=1                   
                initialiser_assemblys(assemblys,link.product,group,request,index)                 
            else:
                #print "Initializer-el producto fue visitado: " , link.product.name 
                index[0]+=1 
                part_type.append(False);creation_formset.append(False);prefix.append(False);ref.append(link.product.visited)
                   

        #assemblys.insert(0,(zip(part_type ,ord_quantity,  creation_formset,  child_assemblys , is_assembly , prefix)  , product.name , product.visited))
        assemblys.append((zip(part_type ,ord_quantity,  creation_formset,  child_assemblys , is_assembly , prefix , ref )  , product.name , product.visited ,product.deep))

@transaction.commit_on_success
def generate_part_doc_links_AUX(request,product, parent_ctrl,instances):  # para generar bien el commit on succes

    generate_part_doc_links(request,product, parent_ctrl,instances)
         
def generate_part_doc_links(request,product, parent_ctrl,instances):



    to_delete=[]
    user = parent_ctrl._user
    
    #if product.links:    

    for link in product.links: 
        try:   

            oq=Order_Quantity_Form(request.POST,prefix=link.visited)
            oq.is_valid();options=oq.cleaned_data          
            order=options["order"];quantity=options["quantity"];unit=options["unit"]
            
            if not link.product.part_to_decompose: 
            


                part_ctype=Doc_Part_type_Form(request.POST,prefix=link.product.visited)
                part_ctype.is_valid();options=part_ctype.cleaned_data
                cls = get_all_plmobjects()[options["type_part"]]
                part_form = get_creation_form(user, cls, request.POST,
                            prefix=str(link.product.visited)+"-part") 
                              
                part_ctrl = parent_ctrl.create_from_form(part_form, user, True, True)
                instances.append((part_ctrl.object._meta.app_label,
                    part_ctrl.object._meta.module_name, part_ctrl.object._get_pk_val()))

                c_link = parent_ctrl.add_child(part_ctrl.object,quantity,order,unit)
                generate_extra_location_links(link, c_link)
                

                doc_form = get_creation_form(user, Document3D,
                        request.POST, prefix=str(link.product.visited)+"-document")              
                doc_ctrl = Document3DController.create_from_form(doc_form,
                        user, True, True)
                        
                link.product.part_to_decompose=part_ctrl.object
                to_delete.append(generateGhostDocumentFile(link.product,doc_ctrl))

                   
                instances.append((doc_ctrl.object._meta.app_label,
                    doc_ctrl.object._meta.module_name, doc_ctrl.object._get_pk_val()))
                part_ctrl.attach_to_document(doc_ctrl.object)
                
                
                Doc3D=Document3D.objects.get(id=doc_ctrl.object.id)
                Doc3D.PartDecompose=part_ctrl.object
                Doc3D.save()
                try:
                    generate_part_doc_links(request,link.product, part_ctrl,instances)
                except Exception as excep:
                    raise excep
                    
            else:
            
                c_link = parent_ctrl.add_child(link.product.part_to_decompose,quantity,order,unit)
                generate_extra_location_links(link, c_link)
                
            

        except Exception as excep:
            raise excep
            #raise Document_part_doc_links_Error(to_delete,link.product.name)    
    


            
 

"""      
@transaction.commit_on_success           
def generate_part_doc_links(prepare_list, links, parent_ctrl):

    index=0;
    doc_controllers = []
    instances = []
    to_delete=[]
    user = parent_ctrl._user
    for  ord_quantity, (part_form, doc_form)  in prepare_list:

        try:
            part_ctrl = parent_ctrl.create_from_form(part_form, user, True, True)
            instances.append((part_ctrl.object._meta.app_label,
                part_ctrl.object._meta.module_name, part_ctrl.object._get_pk_val()))

            link = parent_ctrl.add_child(part_ctrl.object,ord_quantity[1],ord_quantity[0],ord_quantity[2])
            generate_extra_location_links(links[index], link)
            doc_ctrl = Document3DController.create_from_form(doc_form,
                    user, True, True)
                    
            to_delete.append(generateGhostDocumentFile(links[index].product,doc_ctrl))

               
            instances.append((doc_ctrl.object._meta.app_label,
                doc_ctrl.object._meta.module_name, doc_ctrl.object._get_pk_val()))
            part_ctrl.attach_to_document(doc_ctrl.object)
            doc_controllers.append(doc_ctrl)
            index+=1
        except :
            raise Document_part_doc_links_Error(to_delete)
            
    update_indexes.delay(instances)
"""
    
def generateGhostDocumentFile(product,Doc_controller):
    #importante modifica el arbol

    doc_file=DocumentFile()
    name = doc_file.file.storage.get_available_name(product.name+".stp")
    path = os.path.join(doc_file.file.storage.location, name)
    f = File(open(path.encode(), 'w'))
    f.close()   

    Doc_controller.check_permission("owner")
    Doc_controller.check_editable()
    
    if settings.MAX_FILE_SIZE != -1 and f.size > settings.MAX_FILE_SIZE:
        raise ValueError("File too big, max size : %d bytes" % settings.MAX_FILE_SIZE)
            
    if Doc_controller.has_standard_related_locked(f.name):
        raise ValueError("Native file has a standard related locked file.") 
           
    doc_file.no_index=True        
    doc_file.filename="Ghost"
    doc_file.size=f.size
    doc_file.file=name
    doc_file.document=Doc_controller.object
    doc_file.locked = True
    doc_file.locker = User.objects.get(username=settings.COMPANY)
    doc_file.save()  
    
    
    ##
    product.doc_id=doc_file.id

    product.doc_path=doc_file.file.path 

    ##
    return doc_file.file.path

    


"""
def clear_form(request, part_type_formset, bom_formset):
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
            cls = get_all_plmobjects()[part]
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
"""
@secure_required
@login_required
def ajax_part_creation_form(request, prefix):


    tf = Doc_Part_type_Form(request.GET, prefix=prefix)

    if tf.is_valid():

        cls = get_all_parts()[tf.cleaned_data["type_part"]]

        cf = get_creation_form(request.user, cls, prefix=prefix+"-part",
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



