

from openPLM.plmapp.controllers import PLMObjectController, PartController, \
        DocumentController
import openPLM.plmapp.exceptions as exc
import openPLM.plmapp.models as models
from openPLM.plmapp.lifecycle import LifecycleList

from openPLM.plmapp.tests.base import BaseTestCase


class PartDocControllerTestCase(BaseTestCase):
    TYPE ="Part"
    CONTROLLER = PartController
   
    MATRICE = (
        ("draft","draft",False,False,True),
        ("draft","draft",False,True,True),
        ("draft","draft",True,False,True),
        ("draft","draft",True,True,True),
        ("draft","proposed",False,False,False),
        ("draft","proposed",False,True,True),
        ("draft","proposed",True,False,True),
        ("draft","proposed",True,True,True),
        ("draft","official",False,False,False),
        ("draft","official",False,True,False),
        ("draft","official",True,False,True),
        ("draft","official",True,True,True),
        ("draft","deprecated",False,False,False),
        ("draft","deprecated",False,True,False),
        ("draft","deprecated",True,False,False),
        ("draft","deprecated",True,True,False),
        ("proposed","draft",False,False,False),
        ("proposed","draft",False,True,False),
        ("proposed","draft",True,False,False),
        ("proposed","draft",True,True,False),
        ("proposed","proposed",False,False,False),
        ("proposed","proposed",False,True,False),
        ("proposed","proposed",True,False,False),
        ("proposed","proposed",True,True,False),
        ("proposed","official",False,False,False),
        ("proposed","official",False,True,False),
        ("proposed","official",True,False,False),
        ("proposed","official",True,True,False),
        ("proposed","deprecated",False,False,False),
        ("proposed","deprecated",False,True,False),
        ("proposed","deprecated",True,False,False),
        ("proposed","deprecated",True,True,False),
        ("official","draft",False,False,False),
        ("official","draft",False,True,True),
        ("official","draft",True,False,True),
        ("official","draft",True,True,True),
        ("official","proposed",False,False,False),
        ("official","proposed",False,True,False),
        ("official","proposed",True,False,False),
        ("official","proposed",True,True,False),
        ("official","official",False,False,False),
        ("official","official",False,True,False),
        ("official","official",True,False,False),
        ("official","official",True,True,False),
        ("official","deprecated",False,False,False),
        ("official","deprecated",False,True,False),
        ("official","deprecated",True,False,False),
        ("official","deprecated",True,True,False),
        ("deprecated","draft",False,False,False),
        ("deprecated","draft",False,True,False),
        ("deprecated","draft",True,False,False),
        ("deprecated","draft",True,True,False),
        ("deprecated","proposed",False,False,False),
        ("deprecated","proposed",False,True,False),
        ("deprecated","proposed",True,False,False),
        ("deprecated","proposed",True,True,False),
        ("deprecated","official",False,False,False),
        ("deprecated","official",False,True,False),
        ("deprecated","official",True,False,False),
        ("deprecated","official",True,True,False),
        ("deprecated","deprecated",False,False,False),
        ("deprecated","deprecated",False,True,False),
        ("deprecated","deprecated",True,False,False),
        ("deprecated","deprecated",True,True,False),
)

    def setUp(self):
        super(PartDocControllerTestCase, self).setUp()
        self.other_owner = self.get_contributor("Otherowner")
        self.other_owner.groups.add(self.group)
        self.other_owner.save()
        
        lcl = LifecycleList("dpop","official", "draft", 
               "proposed", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.states = dict((s, models.State.objects.get(name=s)) for s in lcl) 
        self.states["cancelled"] = models.get_cancelled_state()
        self.lifecycles = dict.fromkeys(lcl, lc)
        self.lifecycles["cancelled"] = models.get_cancelled_lifecycle()
        data = self.DATA.copy()
        data["lifecycle"] = lc
        self.part = PartController.create("p1","Part", "a", self.user, data,
                True, True)
        self.doc = DocumentController.create("d1","Document", "a",
                self.user, data, True, True)


    def test_attach(self):
        expected = []
        result_part = []
        result_doc = []
        for pstate, dstate, powner, downer, can_attach in self.MATRICE:
            self.part.object.state = self.states[pstate]
            self.part.object.lifecycle = self.lifecycles[pstate]
            self.doc.object.state = self.states[dstate]
            self.doc.object.lifecycle = self.lifecycles[dstate]
            self.part.set_owner(self.user if powner else self.other_owner, True)
            self.doc.set_owner(self.user if downer else self.other_owner, True)
            
            expected.append(can_attach)
            pctrl = PartController(self.part.object, self.user)
            result_part.append(pctrl.can_attach_document(self.doc.object))
            dctrl = DocumentController(self.doc.object, self.user)
            result_doc.append(dctrl.can_attach_part(self.part.object))
        self.assertEqual(expected, result_part)
        self.assertEqual(expected, result_doc)

    def test_detach(self):
        expected = []
        result_part = []
        result_doc = []
        self.doc.attach_to_part(self.part)
        for pstate, dstate, powner, downer, can_detach in self.MATRICE:
            self.part.object.state = self.states[pstate]
            self.part.object.lifecycle = self.lifecycles[pstate]
            self.doc.object.state = self.states[dstate]
            self.doc.object.lifecycle = self.lifecycles[dstate]
            self.part.set_owner(self.user if powner else self.other_owner, True)
            self.doc.set_owner(self.user if downer else self.other_owner, True)
            
            expected.append(can_detach)
            pctrl = PartController(self.part.object, self.user)
            result_part.append(pctrl.can_detach_document(self.doc.object))
            dctrl = DocumentController(self.doc.object, self.user)
            result_doc.append(dctrl.can_detach_part(self.part.object))
        self.assertEqual(expected, result_part)
        self.assertEqual(expected, result_doc)
