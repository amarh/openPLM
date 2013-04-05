from django.test import TransactionTestCase
from django.core import mail

from openPLM.plmapp.controllers import PartController, DocumentController
from openPLM.plmapp import models
from openPLM.plmapp import exceptions as exc
from openPLM.plmapp.utils import level_to_sign_str

from openPLM.plmapp.tests.base import BaseTestCase

D = "draft"
O = "official"
P = "proposed"
DE = "deprecated"

class AssemblyTestCase(BaseTestCase, TransactionTestCase):

    CONTROLLER = PartController
    TYPE = "Part"

    def setUp(self):
        super(AssemblyTestCase, self).setUp()
        self.doc = DocumentController.create("d1", "Document", "a", self.user, self.DATA)
        self.doc.promote(checked=True)
        self.DPOD = models.Lifecycle.objects.get(name="draft_proposed_official_deprecated")

    # utility methods

    def build_assembly(self, ref, state, data, children):
        ref_to_ctrls = {}

        def create(ref, state, data, children):
            rev = data.get("revision", "a")
            try:
                ctrl = ref_to_ctrls[(ref, rev)]
            except KeyError:
                user = data.get("user", self.user)
                doc = data.pop("doc", not children)
                signers = data.pop("signers", None)
                d = self.DATA.copy()
                d.update(data)
                ctrl = self.CONTROLLER.create(ref, self.TYPE, rev,
                    user, d, True, True)
                if doc:
                    ctrl.attach_to_document(self.doc)
                ctrl.object.state = models.State.objects.get(name=state)
                ctrl.object.save()
                ctrl.object.original_state = state
                if signers:
                    roles = ctrl.users.filter(role__startswith=models.ROLE_SIGN).values_list("role", flat=True)
                    ctrl.users.filter(role__startswith=models.ROLE_SIGN).end()
                    new_links = [models.PLMObjectUserLink(plmobject=ctrl.object,
                        user=u, role=r) for r in roles for u in signers]
                    models.PLMObjectUserLink.objects.bulk_create(new_links)

                ref_to_ctrls[(ref, rev)] = ctrl
            return ctrl

        def build_bom(ctrl, children):
            for i, (ref, state, data, children2) in enumerate(children):
                c = create(ref, state, data, children2)
                models.ParentChildLink.objects.create(parent=ctrl.object,
                        child=c.object, order=i, quantity=i, unit="-")
                build_bom(c, children2)
        ctrl = create(ref, state, data, children)
        build_bom(ctrl, children)
        return ctrl, ref_to_ctrls.values()

    def assertPromotion(self, assembly, state=O):
        ctrl, ctrls = self.build_assembly(*assembly)
        ctrl.promote_assembly()
        for c in ctrls:
            if c.lifecycle == ctrl.lifecycle and c.original_state == ctrl.original_state:
                obj = models.Part.objects.get(id=c.id)
                self.assertEqual(obj.state.name, state)

    def assertNotPromotion(self, assembly):
        ctrl, ctrls = self.build_assembly(*assembly)
        outbox = list(mail.outbox)
        self.assertRaises(exc.ControllerError, ctrl.promote_assembly)
        for c in ctrls:
            obj = models.Part.objects.get(id=c.id)
            self.assertEqual(obj.state.name, c.original_state)
        self.assertEqual(outbox, mail.outbox)

    # test cases

    def test_one_child(self):
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, []),
            ]),
        )

    def test_one_child_error(self):
        self.assertNotPromotion(
            ("P1", D, {}, [
                ("P2", D, {"doc": False}, []),
            ]),
        )

    def test_two_children(self):
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, []),
                ("P3", D, {}, []),
            ]),
        )

    def test_two_children_one_official(self):
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, []),
                ("P3", O, {}, []),
            ]),
        )

    def test_two_levels(self):
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", O, {}, []),
                ]),
            ]),
        )

    def test_three_levels0(self):
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", D, {}, [
                        ("P4", D, {}, []),
                    ]),
                ]),
            ]),
        )

    def test_three_levels1(self):
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", D, {}, [
                        ("P4", O, {}, []),
                    ]),
                ]),
            ]),
        )

    def test_three_levels2(self):
        # P3 and P4 are official
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", O, {}, [
                        ("P4", O, {}, []),
                    ]),
                ]),
            ]),
        )

    def test_same_last_children(self):
        # P3 is present twice
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", D, {}, []),
                ]),
                ("P4", D, {}, [
                    ("P3", D, {}, []),
                ]),
            ]),
        )

    def test_same_last_children2(self):
        # P3 is present twice and is official
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", O, {}, []),
                ]),
                ("P4", D, {}, [
                    ("P3", O, {}, []),
                ]),
            ]),
        )

    def test_bigger_assembly(self):
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", O, {}, []),
                ]),
                ("P4", D, {}, [
                    ("P3", O, {}, []),
                    ("P5", D, {}, []),
                    ("P6", D, {}, [
                        ("P2", D, {}, []),
                    ]),
                ]),
            ]),
        )

    def test_not_signer(self):
        brian = self.get_contributor()
        self.assertNotPromotion(
            ("P1", D, {}, [
                ("P2", D, {"signers": [brian]}, [
                    ("P3", D, {}, [
                        ("P4", D, {}, []),
                    ]),
                ]),
            ]),
        )

    def test_represented_signer(self):
        brian = self.get_contributor()
        models.DelegationLink.objects.create(delegator=brian,
                delegatee=self.user, role=level_to_sign_str(0))
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {"signers": [brian]}, [
                    ("P3", D, {}, [
                        ("P4", D, {}, []),
                    ]),
                ]),
            ]),
        )

    def test_not_last_signer(self):
        brian = self.get_contributor()
        self.assertNotPromotion(
            ("P1", D, {}, [
                ("P2", D, {"signers": [brian, self.user]}, [
                    ("P3", D, {}, [
                        ("P4", D, {}, []),
                    ]),
                ]),
            ]),
        )

    def test_to_proposed(self):
        data = { "lifecycle": self.DPOD }
        self.assertPromotion(
            ("P1", D, data.copy(), [
                ("P2", D, data.copy(), []),
                ("P3", D, data.copy(), []),
            ]), P,
        )

    def test_proposed_to_official(self):
        data = { "lifecycle": self.DPOD }
        self.assertPromotion(
            ("P1", P, data.copy(), [
                ("P2", P, data.copy(), []),
                ("P3", P, data.copy(), []),
            ]),
        )
    # TODO:
    #  * proposed state
    #  * different lifecycles
    #  * multiple revisions of the same part
    #  * alternates
    #  * multiple signers and last signer

