from openPLM.apps.document3D.views import *
from openPLM.apps.document3D.models import *
from openPLM.apps.document3D.forms import *
from openPLM.apps.document3D.classes import *
from openPLM.plmapp.tests.views import CommonViewTest
from openPLM.apps.document3D.models import Document3DController
from openPLM.plmapp.decomposers import DecomposersManager
from django.core.files import File
from json import loads

from django.test.utils import override_settings

@override_settings(TIME_ZONE="UTC")
class view_3dTest(CommonViewTest):

    def setUp(self):
        super(view_3dTest, self).setUp()
        self.document = Document3DController.create('doc1', 'Document3D',
                'a', self.user, self.DATA)

    def update_time(self,data):
        data.update({u'last_modif_time': [u'%s-%s-%s %s:%s:%s'%(self.document.mtime.year,self.document.mtime.month,self.document.mtime.day,self.document.mtime.hour,self.document.mtime.minute,self.document.mtime.second)],
           u'last_modif_microseconds' : [u'%s'%self.document.mtime.microsecond]
           })

    def update_data(self,new_doc_file,update_time=True):
        data={}
        new_ArbreFile=ArbreFile.objects.get(stp=new_doc_file)
        product =Product.from_list(json.loads(new_ArbreFile.file.read()))

        index=[1]
        lifecycle='draft_official_deprecated'
        part_type='Part'
        decomposition_fromPOST_data(data,product,index,self.group.id,lifecycle,part_type)
        if update_time:
            self.update_time(data)

        return data

    def test_view3D_stp_decompose(self):
        f=open("apps/document3D/data_test/test2.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        self.controller.attach_to_document(self.document.object)

        data=self.update_data(new_doc_file)

        self.assertTrue(DecomposersManager.is_decomposable(self.controller.object))
        self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertFalse(DecomposersManager.is_decomposable(self.controller.object))
        response = self.get(self.document.object.plmobject_url+"3D/")
        self.assertEqual(len(loads(response.context["GeometryFiles"])), 5)

    def test_3D_no_stp_associe(self):
        response = self.get(self.document.object.plmobject_url+"3D/")
        self.assertFalse(loads(response.context["GeometryFiles"]))
        self.assertFalse(response.context["javascript_arborescense"])

    def test_3D_stp_associe_sans_arborescense(self):
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        ArbreFile.objects.get(stp=new_doc_file).delete()
        response = self.get(self.document.object.plmobject_url+"3D/")
        self.assertEqual(3, len(loads(response.context["GeometryFiles"])))
        self.assertFalse(response.context["javascript_arborescense"])

    def test_3D_stp_valide_no_info(self):
        f=open("apps/document3D/data_test/valid_sans_information.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        response = self.get(self.document.object.plmobject_url+"3D/")
        self.assertFalse(loads(response.context["GeometryFiles"]))
        self.assertTrue(response.context["javascript_arborescense"])

    def test_3D_stp_associe_sans_geometry_with_arborescense(self):
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        GeometryFile.objects.filter(stp=new_doc_file).delete()
        response = self.get(self.document.object.plmobject_url+"3D/")
        self.assertFalse(loads(response.context["GeometryFiles"]))
        self.assertTrue(response.context["javascript_arborescense"])

    def test_decompose_bom_child(self):
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        self.controller.attach_to_document(self.document.object)
        response = self.get(self.base_url + "BOM-child/", page="BOM-child")
        self.assertEqual(0, len(list(response.context["children"])))
        msg = response.context["decomposition_msg"]
        self.assertTrue(msg)


    def test_decompose_bom_child_whit_child_decomposable(self):
        child2 = PartController.create("c2", "Part", "a", self.user, self.DATA)
        self.controller.add_child(child2, 10, 20)
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        child2.attach_to_document(self.document.object)
        self.controller.attach_to_document(self.document.object)
        response = self.get(self.base_url + "BOM-child/", page="BOM-child")
        self.assertEqual(1, len(list(response.context["children"])))
        msg = response.context["decomposition_msg"]
        self.assertTrue(msg)
        decomposable_children = response.context["decomposable_children"]
        self.assertTrue(response.context["children"][0].link.child.id
            in decomposable_children)


    def test_try_decompose_bom_child_whit_no_links(self):
        f=open("apps/document3D/data_test/valid_sans_information.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        self.controller.attach_to_document(self.document.object)
        response = self.get(self.base_url+"decompose/"+str(new_doc_file.id)+"/")
        self.assertRedirects(response, self.base_url + "BOM-child/")


    #verificar los links creados en las buenas coordenadas
    def test_display_decompose_form_initial(self):
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        self.controller.attach_to_document(self.document.object)
        response = self.get(self.base_url+"decompose/"+str(new_doc_file.id)+"/")
        # TODO: check forms


    def test_display_decompose_time_modification_diferent(self):
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        self.controller.attach_to_document(self.document.object)

        data=self.update_data(new_doc_file,update_time=False)

        data.update({u'last_modif_time': [u'%s-%s-%s %s:%s:%s'%             (self.document.mtime.year,(self.document.mtime.month),self.document.mtime.day,self.document.mtime.hour-1,self.document.mtime.minute,self.document.mtime.second)],
           u'last_modif_microseconds' : [u'%s'%(self.document.mtime.microsecond-1)]
           })
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse_post.context["extra_errors"],"The Document3D associated with the file STEP to analyze has been modified by another user while the forms were refilled:Please restart the process")



    def test_display_decompose_time_modification_invalid(self):
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        self.controller.attach_to_document(self.document.object)

        data=self.update_data(new_doc_file,update_time=False)
        data.update({u'last_modif_time': [u'not_valid'],
           u'last_modif_microseconds' : [u'not_valid']
           })
        reponse_post = self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertEqual(reponse_post.context["extra_errors"], INVALID_TIME_ERROR)


    def test_display_decompose_file_locked(self):
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        self.document.lock(new_doc_file)
        self.controller.attach_to_document(self.document.object)

        data=self.update_data(new_doc_file)
        response = self.client.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertTemplateUsed(response, "error.html")

    def test_display_decompose_Document_part_doc_links_Error(self):
        f=open("apps/document3D/data_test/test.stp")
        myfile = File(f)
        new_doc_file=self.document.add_file(myfile)
        self.controller.attach_to_document(self.document.object)
        data=self.update_data(new_doc_file)
        #u'reference': [u'PART_00001']

        data.update({
                "1-part-reference" : [u'2'],
                "1-part-revision" : [u'2'],
                "2-part-reference" : [u'2'],
                "2-part-revision" : [u'2'],
        })

        reponse=self.post(self.base_url+"decompose/"+str(new_doc_file.id)+"/",data)
        self.assertTrue(reponse.context["extra_errors"].startswith(u"Columns reference, type, revision are not unique"))


def decomposition_fromPOST_data(data,product,index,group,lifecycle,part_type):

    if product.links:
        for order , link in enumerate(product.links):
            data.update({
                    "%s-order"%index[0] : [u'%s'%((order+1)*10)],
                    "%s-quantity"%index[0] : [u'%s'%link.quantity],
                    "%s-unit"%index[0] : [u'-'],
            })
            if not link.product.visited:
                data.update({
                "%s-type_part"%index[0] : [u'%s'%part_type],
                "%s-part-reference"%index[0] : [u'%s'%index[0]],
                "%s-part-revision"%index[0] : [u'%s'%index[0]],
                "%s-part-name"%index[0]     :  [u'%s'%index[0]],
                "%s-part-lifecycle"%index[0] : [u'%s'%lifecycle] ,
                "%s-part-group"%index[0] : [u'%s'%group] ,
                "%s-document-reference"%index[0] : [u'%s'%index[0]],
                "%s-document-revision"%index[0] : [u'%s'%index[0]],
                "%s-document-name"%index[0]     :  [u'%s'%index[0]],
                "%s-document-lifecycle"%index[0] : [u'%s'%lifecycle] ,
                "%s-document-group"%index[0] :[u'%s'%group] ,
                })
                link.product.visited=True
                index[0]+=1
                decomposition_fromPOST_data(data,link.product,index,group,lifecycle,part_type)
            else:
                index[0]+=1

