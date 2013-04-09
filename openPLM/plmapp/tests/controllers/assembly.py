from django.test import TransactionTestCase
from django.core import mail

from openPLM.plmapp.controllers import PartController
from openPLM.plmapp import models
from openPLM.plmapp import exceptions as exc
from openPLM.plmapp.utils import level_to_sign_str
from openPLM.plmapp.lifecycle import LifecycleList


from openPLM.plmapp.tests.base import BaseTestCase

D = "draft"
O = "official"
P = "proposed"
DE = "deprecated"
I = "issue"

class AssemblyTestCase(BaseTestCase, TransactionTestCase):

    CONTROLLER = PartController
    TYPE = "Part"

    def setUp(self):
        super(AssemblyTestCase, self).setUp()
        self.DPOD = models.Lifecycle.objects.get(name="draft_proposed_official_deprecated")
        official_state = models.State.objects.get(name=O)
        # only create the Document object, not all Link objects
        self.doc = models.Document.objects.create(type="Document", reference="d1",
                revision="a", lifecycle=self.DPOD, state=official_state,
                creator=self.user, owner=self.user, group=self.group)

    # utility methods

    def build_assembly(self, ref, state, data, children):
        ref_to_ctrls = {}

        def create(ref, state, data, children):
            rev = data.get("rev", "a")
            try:
                ctrl = ref_to_ctrls[(ref, rev)]
            except KeyError:
                user = data.get("user", self.user)
                doc = data.pop("doc", not children)
                signers = data.pop("signers", None)
                approvers = data.pop("approvers", [])
                prev = data.pop("prev", None)
                next = data.pop("next", None)
                d = self.DATA.copy()
                d.update(data)
                ctrl = self.CONTROLLER.create(ref, self.TYPE, rev,
                    user, d, True, True)
                object = ctrl.object
                if doc:
                    models.DocumentPartLink.objects.create(part=object, document=self.doc)
                if object.state.name != state:
                    object.state = models.State.objects.get(name=state)
                    object.save(update_fields=("state",))
                object.original_state = state
                if signers:
                    roles = ctrl.users.filter(role__startswith=models.ROLE_SIGN).values_list("role", flat=True)
                    ctrl.users.filter(role__startswith=models.ROLE_SIGN).end()
                    new_links = [models.PLMObjectUserLink(plmobject=object,
                        user=u, role=r) for r in roles for u in signers]
                    models.PLMObjectUserLink.objects.bulk_create(new_links)
                if prev:
                    rev = ref_to_ctrls[(ref, prev)].object
                    models.RevisionLink.objects.create(old=rev, new=object)
                if next:
                    rev = ref_to_ctrls[(ref, next)].object
                    models.RevisionLink.objects.create(old=object, new=rev)

                if approvers:
                    lcl = object.lifecycle.to_states_list()
                    next_state = lcl.next_state(state)
                    nxt = models.State.objects.get(name=next_state)
                    models.PromotionApproval.objects.bulk_create(
                        models.PromotionApproval(user=user, plmobject=object,
                            current_state=object.state, next_state=nxt)
                        for user in approvers)

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
            obj = models.Part.objects.get(id=c.id)
            if c.lifecycle == ctrl.lifecycle and c.original_state == ctrl.original_state:
                self.assertEqual(obj.state.name, state)
            else:
                self.assertEqual(obj.state.name, c.original_state)

    def assertNotPromotion(self, assembly):
        ctrl, ctrls = self.build_assembly(*assembly)
        outbox = list(mail.outbox)
        self.assertRaises((ValueError, exc.ControllerError), ctrl.promote_assembly)
        for c in ctrls:
            obj = models.Part.objects.get(id=c.id)
            self.assertEqual(obj.state.name, c.original_state)
        self.assertEqual(outbox, mail.outbox)

    def get_issue_lifecycle(self):
        lcl = LifecycleList("lc_asm", O, D, P, I, O, DE)
        return models.Lifecycle.from_lifecyclelist(lcl)

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

    def test_last_signer_one_approver(self):
        brian = self.get_contributor()
        self.assertPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", D, {"signers": [brian, self.user], "approvers": [brian]}, []),
                ]),
            ]),
        )

    def test_not_last_signer2(self):
        brian = self.get_contributor()
        john = self.get_contributor("john")
        self.assertNotPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", D, {"signers": [brian, john, self.user], "approvers": [brian]}, []),
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

    def test_to_proposed2(self):
        data = { "lifecycle": self.DPOD }
        self.assertPromotion(
            ("P1", D, data.copy(), [
                ("P2", D, data.copy(), [
                    ("P3", D, data.copy(), []),
                ]),
            ]), P,
        )

    def test_to_proposed3(self):
        data = { "lifecycle": self.DPOD }
        self.assertPromotion(
            ("P1", D, data.copy(), [
                ("P2", D, data.copy(), [
                    ("P3", P, data.copy(), []),
                ]),
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

    def test_proposed_to_official2(self):
        data = { "lifecycle": self.DPOD }
        self.assertPromotion(
            ("P1", P, data.copy(), [
                ("P2", P, data.copy(), [
                    ("P3", P, data.copy(), []),
                ]),
            ]),
        )

    def test_proposed_to_official3(self):
        data = { "lifecycle": self.DPOD }
        self.assertPromotion(
            ("P1", P, data.copy(), [
                ("P2", P, data.copy(), [
                    ("P3", O, data.copy(), []),
                ]),
            ]),
        )

    def test_proposed_to_official4(self):
        data = { "lifecycle": self.DPOD }
        self.assertPromotion(
            ("P1", P, data.copy(), [
                ("P2", P, data.copy(), [
                    ("P3", O, data.copy(), []),
                    ("P4", P, data.copy(), []),
                ]),
                ("P5", P, data.copy(), [
                    ("P3", O, data.copy(), []),
                    ("P2", P, data.copy(), []),
                ]),
            ]),
        )

    def test_proposed_no_doc(self):
        data = { "lifecycle": self.DPOD }
        p3_data = {"lifecycle": self.DPOD, "doc": False}
        self.assertNotPromotion(
            ("P1", D, data.copy(), [
                ("P2", P, data.copy(), []),
                ("P3", D, p3_data, []),
            ]),
        )

    def test_draft_to_proposed_issue(self):
        data = { "lifecycle": self.get_issue_lifecycle()}
        self.assertPromotion(
            ("P1", D, data.copy(), [
                ("P2", D, data.copy(), [
                    ("P3", I, data.copy(), []),
                ]),
            ]), P
        )

    def test_proposed_to_issue(self):
        data = { "lifecycle": self.get_issue_lifecycle()}
        self.assertPromotion(
            ("P1", P, data.copy(), [
                ("P2", P, data.copy(), [
                    ("P3", P, data.copy(), []),
                ]),
            ]), I
        )

    def test_proposed_to_issue2(self):
        data = { "lifecycle": self.get_issue_lifecycle()}
        self.assertPromotion(
            ("P1", P, data.copy(), [
                ("P2", P, data.copy(), [
                    ("P3", P, data.copy(), []),
                    ("P4", O, data.copy(), []),
                ]),
            ]), I
        )

    def test_proposed_to_issue3(self):
        data = { "lifecycle": self.get_issue_lifecycle()}
        self.assertPromotion(
            ("P1", P, data.copy(), [
                ("P2", I, data.copy(), [
                    ("P3", I, data.copy(), []),
                    ("P4", O, data.copy(), []),
                ]),
            ]), I
        )

    def test_issue_to_official(self):
        data = { "lifecycle": self.get_issue_lifecycle()}
        self.assertPromotion(
            ("P1", I, data.copy(), [
                ("P2", I, data.copy(), [
                    ("P3", I, data.copy(), []),
                    ("P4", I, data.copy(), []),
                ]),
            ]),
        )

    def test_issue_to_official2(self):
        data = { "lifecycle": self.get_issue_lifecycle()}
        self.assertPromotion(
            ("P1", I, data.copy(), [
                ("P2", I, data.copy(), [
                    ("P3", O, data.copy(), []),
                    ("P4", DE, data.copy(), []),
                ]),
            ]),
        )

    def test_issue_to_official3(self):
        data = { "lifecycle": self.get_issue_lifecycle()}
        self.assertPromotion(
            ("P1", I, data.copy(), [
                ("P2", I, data.copy(), [
                    ("P3", O, data.copy(), []),
                    ("P4", DE, data.copy(), []),
                ]),
                ("P5", I, data.copy(), [
                    ("P2", I, data.copy(), []),
                    ("P3", O, data.copy(), []),
                ]),
            ]),
        )

    def test_revisions(self):
        # P3/a and P3/b
        self.assertNotPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", D, {}, []),
                ]),
                ("P4", D, {}, [
                    ("P3", D, {"rev": "b", "prev": "a"}, []),
                ]),
            ]),
        )

    def test_revisions2(self):
        # P3/a and P3/b
        self.assertNotPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", D, {}, []),
                ]),
                ("P3", D, {"rev": "b", "prev": "a"}, []),
            ]),
        )

    def test_revisions3(self):
        # P3/a and P3/b
        self.assertNotPromotion(
            ("P1", D, {}, [
                ("P2", D, {}, [
                    ("P3", D, {"rev": "b"}, []),
                ]),
                ("P3", D, {"next": "b"}, []),
            ]),
        )


    # TODO:
    #  * alternates

