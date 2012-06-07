from openPLM.plmapp.tests.controllers import PartControllerTest
from openPLM.plmapp.tests.views import PartViewTestCase

from openPLM.bicycle.models import BicycleController

class BicycleControllerTest(PartControllerTest):
    TYPE = "Bicycle"
    CONTROLLER = BicycleController
    DATA = {"nb_wheels" : 2}


class BicycleViewTestCase(PartViewTestCase):
    TYPE = "Bicycle"
    DATA = {"nb_wheels" : 2,
            "color" : "blue"}
    
    # our custom attributes view adds the ":" so, we redefine this test
    def test_display_attributes(self):
        response = self.client.get(self.base_url + "attributes/")
        self.assertEqual(response.status_code,  200)
        self.failUnless(response.context["object_attributes"])
        attributes = dict(response.context["object_attributes"])
        # name : empty value
        self.assertEqual(attributes["name:"], "")
        # owner and creator : self.user
        self.assertEqual(attributes["owner:"], self.user)
        self.assertEqual(attributes["creator:"], self.user)    
    
    def test_display_attributes2(self):
        response = self.client.get(self.base_url + "attributes/")
        self.assertEqual(response.status_code, 200)
        self.failUnless(response.context["object_attributes"])
        attributes = dict(response.context["object_attributes"])
        self.assertEqual(attributes["Number of wheels:"], self.DATA["nb_wheels"])
        self.assertEqual(attributes["color:"], self.DATA["color"])
        self.assertEqual(attributes["details:"], "")
