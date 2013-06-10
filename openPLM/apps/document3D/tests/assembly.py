import os.path
import copy
from django.test import TransactionTestCase

from openPLM.plmapp.controllers import PartController
from openPLM.plmapp import models
from openPLM.plmapp import exceptions as exc
from openPLM.apps.document3D.models import Document3DController, is_stp
from openPLM.apps.document3D.assembly import AssemblyBuilder, get_assembly_info

from openPLM.plmapp.tests.base import BaseTestCase
from django.core.files.base import File, ContentFile


class DeferredId(object):

    def __init__(self, queryset):
        self.queryset = queryset

    def __int__(self):
        return self.queryset.values("id")[0]["id"]

    def __hash__(self):
        return hash(int(self))

    def __eq__(self, other):
        return int(self) == other
    def __ne__(self, other):
        return int(self) != other


_ASSEMBLY1 = {
    u'children': [
        {
            u'children': [],
            u'local_matrix': [4.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            u'local_name': u'L-BRACKET',
            u'native': u'L-BRACKET.native',
            u'part_name': u'L-BRACKET',
            u'step': u'L-BRACKET.step'
        },
        {
            u'children': [
                {
                    u'children': [],
                    u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    u'local_name': u'BOLT',
                    u'native': u'BOLT.native',
                    u'part_name': u'BOLT',
                    u'step': u'BOLT.step'
                },
                {
                    u'children': [],
                    u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 838.2, 0.0, 0.0, 1.0, 0.0],
                    u'local_name': u'NUT',
                    u'native': u'NUT.native',
                    u'part_name': u'NUT',
                    u'step': u'NUT.step'
                }
            ],
            u'local_matrix': [-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 254.0, 0.0, 0.0, 1.0, 508.0],
            u'local_name': u'NBA_ASM',
            u'native': u'NBA_ASM.native_asm',
            u'part_name': u'NBA_ASM',
            u'step': None
        },
        {
            u'children': [
                {
                    u'children': [],
                    u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    u'local_name': u'BOLT',
                    u'native': u'BOLT.native',
                    u'part_name': u'BOLT',
                    u'step': u'BOLT.step'
                },
                {
                    u'children': [],
                    u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 838.2, 0.0, 0.0, 1.0, 0.0],
                    u'local_name': u'NUT',
                    u'native': u'NUT.native',
                    u'part_name': u'NUT',
                    u'step': u'NUT.step'
                }
            ],
            u'local_matrix': [-1.0, 0.0, 0.0, 329.95567884195799, 0.0, -1.0, 0.0, 254.0, 0.0, 0.0, 1.0, 1079.5],
            u'local_name': u'NBA_ASM',
            u'native': u'NBA_ASM.native_asm',
            u'part_name': u'NBA_ASM',
            u'step': None
        },
        {
            u'children': [
                {
                    u'children': [],
                    u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    u'local_name': u'BOLT',
                    u'native': u'BOLT.native',
                    u'part_name': u'BOLT',
                    u'step': u'BOLT.step'
                },
                {
                    u'children': [],
                    u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 838.2, 0.0, 0.0, 1.0, 0.0],
                    u'local_name': u'NUT',
                    u'native': u'NUT.native',
                    u'part_name': u'NUT',
                    u'step': u'NUT.step'
                }
            ],
            u'local_matrix': [-1.0, 0.0, 0.0, -329.95567884195799, 0.0, -1.0, 0.0, 254.0, 0.0, 0.0, 1.0, 1079.5],
            u'local_name': u'NBA_ASM',
            u'native': u'NBA_ASM.native_asm',
            u'part_name': u'NBA_ASM',
            u'step': None
        }
    ],
    u'local_matrix': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    u'local_name': u'test',
    u'native': u'test.native_asm',
    u'part_name': u'test',
    u'step': None
}


def deferred_part(name):
    return {"id": DeferredId(models.Part.objects.filter(name=name))}

def deferred_doc(name, checkin=True):
    return {"id": DeferredId(models.Document.objects.filter(name=name)),
            "checkin": checkin}

def deferred_file(name):
    return {"id": DeferredId(models.DocumentFile.objects.filter(deprecated=False, filename=name)),}


_UPDATED_ASSEMBLY1 = {
    u'children': [
        {
            u'children': [],
            u'local_matrix': [4.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            u'local_name': u'L-BRACKET',
            u'native': deferred_file('L-BRACKET.native'),
            u'part': deferred_part('L-BRACKET'),
            u'document': deferred_doc('L-BRACKET'),
            u'step': deferred_file(u'l-bracket.step'),
        },
        {
            u'children': [
                {
                    u'children': [],
                    u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    u'local_name': u'BOLT',
                    u'native': deferred_file('BOLT.native'),
                    u'part': deferred_part('BOLT'),
                    u'document': deferred_doc('BOLT'),
                    u'step': deferred_file(u'bolt.step'),
                },
                {
                    u'children': [],
                    u'local_matrix': [1.5, 5.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    u'local_name': u'BOLT',
                    u'native': deferred_file('BOLT.native'),
                    u'part': deferred_part('BOLT'),
                    u'document': deferred_doc('BOLT'),
                    u'step': deferred_file(u'bolt.step'),
                },
                {
                    u'children': [],
                    u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 838.2, 0.0, 0.0, 1.0, 0.0],
                    u'local_name': u'NUT',
                    u'native': deferred_file('NUT.native'),
                    u'part': deferred_part('NUT'),
                    u'document': deferred_doc('NUT'),
                    u'step': deferred_file(u'nut.step'),
                }
            ],
            u'local_matrix': [-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 254.0, 0.0, 0.0, 1.0, 508.0],
            u'local_name': u'NBA_ASM',
            u'native': deferred_file('NBA_ASM.native_asm'),
            u'part': deferred_part('NBA_ASM'),
            u'document': deferred_doc('NBA_ASM'),
            u'step': deferred_file(u'NBA_ASM.step'),
        },
        {
            u'children': [],
            u'local_name': u'NBA_ASM',
            u'local_matrix': [-1.0, 0.0, 0.0, 329.95567884195799, 0.0, -1.0, 0.0, 254.0, 0.0, 0.0, 1.0, 1079.5],
            u'native': deferred_file('NBA_ASM.native_asm'),
            u'part': deferred_part('NBA_ASM'),
            u'document': deferred_doc('NBA_ASM'),
            u'step': deferred_file(u'NBA_ASM.step'),
        },
        {
            u'children': [],
            u'local_matrix': [-1.0, 0.0, 0.0, -329.95567884195799, 0.0, -1.0, 0.0, 254.0, 0.0, 0.0, 1.0, 1079.5],
            u'local_name': u'NBA_ASM',
            u'native': deferred_file('NBA_ASM.native_asm'),
            u'part': deferred_part('NBA_ASM'),
            u'document': deferred_doc('NBA_ASM'),
            u'step': deferred_file(u'NBA_ASM.step'),
        }
    ],
    u'local_matrix': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    u'local_name': u'test',
    u'native': deferred_file('test.native_asm'),
    u'part': deferred_part('test'),
    u'document': deferred_doc('test'),
    u'step': deferred_file(u'test.step'),
}



def get_natives(*names):
    r = []
    for name in names:
        f = ContentFile(name)
        f.name = name
        r.append(f)
    return r

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data_test")

def get_steps(*names):
    r = []
    for name in names:
        f = File(open(os.path.join(DATA_PATH, name)))
        f.name = name
        r.append(f)
    return r


class AssemblyBuilderTestCase(BaseTestCase, TransactionTestCase):

    CONTROLLER = Document3DController
    DATA = {
        "name": "test",
    }

    def assertLink(self, pcl, name, parent, order, quantity):
        self.assertEqual(name, pcl.child.name)
        self.assertEqual(parent, pcl.parent)
        self.assertEqual(order, pcl.order)
        self.assertEqual(quantity, pcl.quantity)
        self.assertEqual("-", pcl.unit)
        self.assertEqual(quantity, len(pcl.extensions))

    def assertDoc(self, part, step, native):
        docs = part.documentpartlink_part.now()
        self.assertEqual(1, len(docs))
        doc = docs[0].document.get_leaf_object()
        self.assertEqual(part, doc.PartDecompose)
        self.assertEqual(2, len(doc.files))
        self.assertEqual([step, native],
            list(doc.files.order_by("ctime").values_list("filename", flat=True)))

    def assertProduct(self, ctrl):
        stp = ctrl.files.filter(is_stp)[0]
        product = ctrl.get_product(stp, True)
        self.assertEqual(ctrl.name, product.name)

    def test_build_assembly(self):
        self.assertEqual(0, models.PLMObject.objects.all().count())
        ctrl = self.create("d1", "Document3D")
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        df = builder.build_assembly(_ASSEMBLY1, natives, steps, False)

        self.assertEqual(5, models.Document.objects.all().count())
        self.assertEqual(5, models.Part.objects.all().count())
        # root
        self.assertEqual("test.native_asm", df.filename)
        root = PartController(ctrl.PartDecompose, self.user)
        self.assertDoc(root.object, "test.step", "test.native_asm")
        self.assertEqual("test", root.name)
        children = root.get_children(-1)
        self.assertEqual(4, len(children))
        # l-bracket
        pcl = children[0].link
        child = pcl.child
        self.assertLink(pcl, "L-BRACKET", root.object, 1, 1)
        self.assertEqual([4.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            pcl.extensions[0].to_array())
        self.assertDoc(child, u"l-bracket.step", u"L-BRACKET.native")
        # nba_asm
        pcl = children[1].link
        child = nba_asm = pcl.child
        self.assertLink(pcl, "NBA_ASM", root.object, 2, 3)
        self.assertDoc(child, u"NBA_ASM.step", u"NBA_ASM.native_asm")
        # bolt
        pcl = children[2].link
        child = pcl.child
        self.assertLink(pcl, "BOLT", nba_asm, 1, 1)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")
        # nut
        pcl = children[3].link
        child = pcl.child
        self.assertLink(pcl, "NUT", nba_asm, 2, 1)
        self.assertDoc(child, u"nut.step", u"NUT.native")

        # check product is valid
        self.assertProduct(ctrl)

    def test_update_assembly_locations(self):
        ctrl = self.create("d1", "Document3D")
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.build_assembly(_ASSEMBLY1, natives, steps, False)

        tree = copy.deepcopy(_UPDATED_ASSEMBLY1)
        m1 = [1, 7, 5, 9, 5, 4, 3, 2, 2, 0, 5, 1]
        tree["children"][0]["local_matrix"] = m1
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.update_assembly(tree, natives, steps)
        self.assertEqual(5, models.Document.objects.all().count())
        self.assertEqual(5, models.Part.objects.all().count())
        # root
        root = PartController(ctrl.PartDecompose, self.user)
        self.assertDoc(root.object, "test.step", "test.native_asm")
        self.assertEqual("test", root.name)
        children = root.get_children(-1)
        self.assertEqual(4, len(children))
        # l-bracket
        pcl = children[0].link
        child = pcl.child
        self.assertLink(pcl, "L-BRACKET", root.object, 1, 1)
        self.assertEqual(m1, pcl.extensions[0].to_array())
        self.assertDoc(child, u"l-bracket.step", u"L-BRACKET.native")
        # nba_asm
        pcl = children[1].link
        child = nba_asm = pcl.child
        self.assertLink(pcl, "NBA_ASM", root.object, 2, 3)
        self.assertDoc(child, u"NBA_ASM.step", u"NBA_ASM.native_asm")
        # bolt
        pcl = children[2].link
        child = pcl.child
        self.assertLink(pcl, "BOLT", nba_asm, 1, 2)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")
        # nut
        pcl = children[3].link
        child = pcl.child
        self.assertLink(pcl, "NUT", nba_asm, 2, 1)
        self.assertDoc(child, u"nut.step", u"NUT.native")

        # check product is valid
        self.assertProduct(ctrl)

    def test_update_assembly_more_bolts(self):
        ctrl = self.create("d1", "Document3D")
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.build_assembly(_ASSEMBLY1, natives, steps, False)

        tree = copy.deepcopy(_UPDATED_ASSEMBLY1)
        m1 = [1, 7, 5, 9, 5, 4, 3, 2, 2, 0, 5, 1]
        tree["children"].append(
            {
                u'children': [],
                u'local_matrix': m1,
                u'local_name': u'BOLT',
                u'native': deferred_file('BOLT.native'),
                u'part': deferred_part('BOLT'),
                u'document': deferred_doc('BOLT'),
                u'step': deferred_file(u'bolt.step'),
            }
        )

        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.update_assembly(tree, natives, steps)
        self.assertEqual(5, models.Part.objects.all().count())
        self.assertEqual(5, models.Document.objects.all().count())
        # root
        root = PartController(ctrl.PartDecompose, self.user)
        self.assertDoc(root.object, "test.step", "test.native_asm")
        self.assertEqual("test", root.name)
        children = root.get_children(-1)
        self.assertEqual(5, len(children))
        # l-bracket
        pcl = children[0].link
        child = pcl.child
        self.assertLink(pcl, "L-BRACKET", root.object, 1, 1)
        self.assertDoc(child, u"l-bracket.step", u"L-BRACKET.native")
        # nba_asm
        pcl = children[1].link
        child = nba_asm = pcl.child
        self.assertLink(pcl, "NBA_ASM", root.object, 2, 3)
        self.assertDoc(child, u"NBA_ASM.step", u"NBA_ASM.native_asm")
        # bolt
        pcl = children[2].link
        child = pcl.child
        first_bolt = child.id
        self.assertLink(pcl, "BOLT", nba_asm, 1, 2)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")
        # nut
        pcl = children[3].link
        child = pcl.child
        self.assertLink(pcl, "NUT", nba_asm, 2, 1)
        self.assertDoc(child, u"nut.step", u"NUT.native")
        # new bolt
        pcl = children[4].link
        child = pcl.child
        self.assertLink(pcl, "BOLT", root.object, 3, 1)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")
        self.assertEqual(first_bolt, child.id)

        # minor revisions of document files
        for doc in models.Document.objects.all():
            for f in doc.files:
                self.assertEqual(2, f.revision)
        # check product is valid
        self.assertProduct(ctrl)

    def test_update_removed_nut(self):
        ctrl = self.create("d1", "Document3D")
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.build_assembly(_ASSEMBLY1, natives, steps, False)

        tree = copy.deepcopy(_UPDATED_ASSEMBLY1)
        del tree["children"][1]["children"][2]
        steps = get_steps("bolt.step", "l-bracket.step")
        builder = AssemblyBuilder(ctrl)
        builder.update_assembly(tree, natives, steps)
        self.assertEqual(5, models.Part.objects.all().count())
        self.assertEqual(5, models.Document.objects.all().count())
        # root
        root = PartController(ctrl.PartDecompose, self.user)
        self.assertDoc(root.object, "test.step", "test.native_asm")
        self.assertEqual("test", root.name)
        children = root.get_children(-1)
        self.assertEqual(3, len(children))
        # l-bracket
        pcl = children[0].link
        child = pcl.child
        self.assertLink(pcl, "L-BRACKET", root.object, 1, 1)
        self.assertDoc(child, u"l-bracket.step", u"L-BRACKET.native")
        # nba_asm
        pcl = children[1].link
        child = nba_asm = pcl.child
        self.assertLink(pcl, "NBA_ASM", root.object, 2, 3)
        self.assertDoc(child, u"NBA_ASM.step", u"NBA_ASM.native_asm")
        # bolt
        pcl = children[2].link
        child = pcl.child
        self.assertLink(pcl, "BOLT", nba_asm, 1, 2)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")

        # minor revisions of document files
        for doc in models.Document.objects.all():
            for f in doc.files:
                if doc.name == "NUT":
                    self.assertEqual(1, f.revision)
                else:
                    self.assertEqual(2, f.revision)
        # check product is valid
        self.assertProduct(ctrl)

        # NUT
        nut = models.Part.objects.get(name="NUT")
        self.assertFalse(nut.parentchildlink_child.now())

    def test_update_new_rod(self):
        ctrl = self.create("d1", "Document3D")
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.build_assembly(_ASSEMBLY1, natives, steps, False)

        tree = copy.deepcopy(_UPDATED_ASSEMBLY1)
        tree["children"].append(
            {
                u'children': [],
                u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                u'local_name': u'ROD',
                u'native': u'ROD.native',
                u'part_name': u'ROD',
                u'step': u'ROD.step'
            }
        )
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native", "ROD.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step", "rod.step")
        builder = AssemblyBuilder(ctrl)
        builder.update_assembly(tree, natives, steps)
        self.assertEqual(6, models.Part.objects.all().count())
        self.assertEqual(6, models.Document.objects.all().count())
        # root
        root = PartController(ctrl.PartDecompose, self.user)
        self.assertDoc(root.object, "test.step", "test.native_asm")
        self.assertEqual("test", root.name)
        children = root.get_children(-1)
        self.assertEqual(5, len(children))
        # l-bracket
        pcl = children[0].link
        child = pcl.child
        self.assertLink(pcl, "L-BRACKET", root.object, 1, 1)
        self.assertDoc(child, u"l-bracket.step", u"L-BRACKET.native")
        # nba_asm
        pcl = children[1].link
        child = nba_asm = pcl.child
        self.assertLink(pcl, "NBA_ASM", root.object, 2, 3)
        self.assertDoc(child, u"NBA_ASM.step", u"NBA_ASM.native_asm")
        # bolt
        pcl = children[2].link
        child = pcl.child
        self.assertLink(pcl, "BOLT", nba_asm, 1, 2)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")
        # nut
        pcl = children[3].link
        child = pcl.child
        self.assertLink(pcl, "NUT", nba_asm, 2, 1)
        self.assertDoc(child, u"nut.step", u"NUT.native")
        # rod
        pcl = children[4].link
        child = pcl.child
        self.assertLink(pcl, "ROD", root.object, 3, 1)
        self.assertDoc(child, u"rod.step", u"ROD.native")

        # minor revisions of document files
        for doc in models.Document.objects.all():
            for f in doc.files:
                if doc.name == "ROD":
                    self.assertEqual(1, f.revision)
                else:
                    self.assertEqual(2, f.revision)
        # check product is valid
        self.assertProduct(ctrl)

    def test_update_new_assembly(self):
        ctrl = self.create("d1", "Document3D")
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.build_assembly(_ASSEMBLY1, natives, steps, False)

        tree = copy.deepcopy(_UPDATED_ASSEMBLY1)
        tree["children"].append(
            {
                u'children': [
                    {
                        u'children': [],
                        u'local_matrix': [1.5, 5.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                        u'local_name': u'BOLT',
                        u'native': deferred_file('BOLT.native'),
                        u'part': deferred_part('BOLT'),
                        u'document': deferred_doc('BOLT'),
                        u'step': deferred_file(u'bolt.step'),
                    },
                    {
                        u'children': [],
                        u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 838.2, 0.0, 0.0, 1.0, 0.0],
                        u'local_name': u'NUT',
                        u'native': deferred_file('NUT.native'),
                        u'part': deferred_part('NUT'),
                        u'document': deferred_doc('NUT'),
                        u'step': deferred_file(u'nut.step'),
                    },
                ],
                u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                u'local_name': u'ROD',
                u'native': u'ROD.native_asm',
                u'part_name': u'ROD',
            }
        )
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native", "ROD.native_asm")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.update_assembly(tree, natives, steps)
        self.assertEqual(6, models.Part.objects.all().count())
        self.assertEqual(6, models.Document.objects.all().count())
        # root
        root = PartController(ctrl.PartDecompose, self.user)
        self.assertDoc(root.object, "test.step", "test.native_asm")
        self.assertEqual("test", root.name)
        children = root.get_children(-1)
        self.assertEqual(7, len(children))
        # l-bracket
        pcl = children[0].link
        child = pcl.child
        self.assertLink(pcl, "L-BRACKET", root.object, 1, 1)
        self.assertDoc(child, u"l-bracket.step", u"L-BRACKET.native")
        # nba_asm
        pcl = children[1].link
        child = nba_asm = pcl.child
        self.assertLink(pcl, "NBA_ASM", root.object, 2, 3)
        self.assertDoc(child, u"NBA_ASM.step", u"NBA_ASM.native_asm")
        # bolt
        pcl = children[2].link
        child = pcl.child
        self.assertLink(pcl, "BOLT", nba_asm, 1, 2)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")
        # nut
        pcl = children[3].link
        child = pcl.child
        self.assertLink(pcl, "NUT", nba_asm, 2, 1)
        self.assertDoc(child, u"nut.step", u"NUT.native")
        # rod
        pcl = children[4].link
        rod = child = pcl.child
        self.assertLink(pcl, "ROD", root.object, 3, 1)
        self.assertDoc(child, u"ROD.step", u"ROD.native_asm")
        # rod -> bolt
        pcl = children[5].link
        child = pcl.child
        self.assertLink(pcl, "BOLT", rod, 1, 1)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")
        # rod -> nut
        pcl = children[6].link
        child = pcl.child
        self.assertLink(pcl, "NUT", rod, 2, 1)
        self.assertDoc(child, u"nut.step", u"NUT.native")

        # minor revisions of document files
        for doc in models.Document.objects.all():
            for f in doc.files:
                if doc.name == "ROD":
                    self.assertEqual(1, f.revision)
                else:
                    self.assertEqual(2, f.revision)
        # check product is valid
        self.assertProduct(ctrl)

    def test_update_no_checkin(self):
        ctrl = self.create("d1", "Document3D")
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.build_assembly(_ASSEMBLY1, natives, steps, False)

        tree = copy.deepcopy(_UPDATED_ASSEMBLY1)
        tree["children"][0]["document"]["checkin"] = False
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native")
        steps = get_steps("bolt.step", "nut.step")
        builder = AssemblyBuilder(ctrl)
        builder.update_assembly(tree, natives, steps)
        self.assertEqual(5, models.Part.objects.all().count())
        self.assertEqual(5, models.Document.objects.all().count())
        # root
        root = PartController(ctrl.PartDecompose, self.user)
        self.assertDoc(root.object, "test.step", "test.native_asm")
        self.assertEqual("test", root.name)
        children = root.get_children(-1)
        self.assertEqual(4, len(children))
        # l-bracket
        pcl = children[0].link
        child = pcl.child
        self.assertLink(pcl, "L-BRACKET", root.object, 1, 1)
        self.assertDoc(child, u"l-bracket.step", u"L-BRACKET.native")
        # nba_asm
        pcl = children[1].link
        child = nba_asm = pcl.child
        self.assertLink(pcl, "NBA_ASM", root.object, 2, 3)
        self.assertDoc(child, u"NBA_ASM.step", u"NBA_ASM.native_asm")
        # bolt
        pcl = children[2].link
        child = pcl.child
        self.assertLink(pcl, "BOLT", nba_asm, 1, 2)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")
        # nut
        pcl = children[3].link
        child = pcl.child
        self.assertLink(pcl, "NUT", nba_asm, 2, 1)
        self.assertDoc(child, u"nut.step", u"NUT.native")

        # minor revisions of document files
        for doc in models.Document.objects.all():
            for f in doc.files:
                if doc.name == "L-BRACKET":
                    self.assertEqual(1, f.revision)
                else:
                    self.assertEqual(2, f.revision)
        # check product is valid
        self.assertProduct(ctrl)

    def test_update_add_existing_rod(self):
        rod = self.create("rod", "Document3D")
        rod.name = "ROD"
        rod.save()
        rod_step = rod.add_file(get_steps("rod.step")[0])
        rod_native = rod.add_file(get_natives("ROD.native")[0])
        rod_part = PartController.create("rod", "Part", "a", self.user,
            {"group": self.group, "lifecycle": rod.lifecycle, "name": rod.name})
        rod.attach_to_part(rod_part)
        rod.PartDecompose = rod_part.object
        rod.save()

        ctrl = self.create("d1", "Document3D")
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native", "ROD.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step", "rod.step")
        builder = AssemblyBuilder(ctrl)
        builder.build_assembly(_ASSEMBLY1, natives, steps, False)

        tree = copy.deepcopy(_UPDATED_ASSEMBLY1)
        tree["children"].append(
            {
                u'children': [],
                u'local_matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                u'local_name': u'ROD',
                u'native': {"id": rod_native.id},
                u'part': {"id": rod_part.id},
                u'document': {"id": rod.id, "checkin": True},
                u'step': {"id": rod_step.id},
            }
        )
        natives = get_natives("test.native_asm", "NBA_ASM.native_asm",
                "NUT.native", "BOLT.native", "L-BRACKET.native", "ROD.native")
        steps = get_steps("bolt.step", "l-bracket.step", "nut.step", "rod.step")
        builder = AssemblyBuilder(ctrl)
        builder.update_assembly(tree, natives, steps)
        self.assertEqual(6, models.Part.objects.all().count())
        self.assertEqual(6, models.Document.objects.all().count())
        # root
        root = PartController(ctrl.PartDecompose, self.user)
        self.assertDoc(root.object, "test.step", "test.native_asm")
        self.assertEqual("test", root.name)
        children = root.get_children(-1)
        self.assertEqual(5, len(children))
        # l-bracket
        pcl = children[0].link
        child = pcl.child
        self.assertLink(pcl, "L-BRACKET", root.object, 1, 1)
        self.assertDoc(child, u"l-bracket.step", u"L-BRACKET.native")
        # nba_asm
        pcl = children[1].link
        child = nba_asm = pcl.child
        self.assertLink(pcl, "NBA_ASM", root.object, 2, 3)
        self.assertDoc(child, u"NBA_ASM.step", u"NBA_ASM.native_asm")
        # bolt
        pcl = children[2].link
        child = pcl.child
        self.assertLink(pcl, "BOLT", nba_asm, 1, 2)
        self.assertDoc(child, u"bolt.step", u"BOLT.native")
        # nut
        pcl = children[3].link
        child = pcl.child
        self.assertLink(pcl, "NUT", nba_asm, 2, 1)
        self.assertDoc(child, u"nut.step", u"NUT.native")
        # rod
        pcl = children[4].link
        child = pcl.child
        self.assertEqual(child.id, rod_part.id)
        self.assertLink(pcl, "ROD", root.object, 3, 1)
        self.assertDoc(child, u"rod.step", u"ROD.native")

        # minor revisions of document files
        for doc in models.Document.objects.all():
            for f in doc.files:
                self.assertEqual(2, f.revision)
        # check product is valid
        self.assertProduct(ctrl)
