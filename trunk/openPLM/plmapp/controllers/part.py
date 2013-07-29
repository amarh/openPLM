############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
#
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

"""
"""
import difflib
from itertools import imap, izip_longest, groupby
from operator import attrgetter, itemgetter
from collections import namedtuple, defaultdict

from django.db import transaction
from django.db.models.query import Q
from django.utils import timezone

import openPLM.plmapp.models as models
from openPLM.plmapp.utils.units import DEFAULT_UNIT
from openPLM.plmapp.controllers.plmobject import PLMObjectController
from openPLM.plmapp.controllers.base import get_controller
from openPLM.plmapp.files.formats import is_cad_file
from openPLM.plmapp.exceptions import PermissionError, PromotionError
from openPLM.plmapp.tasks import update_indexes
from openPLM.plmapp.utils import level_to_sign_str

Child = namedtuple("Child", "level link")
Parent = namedtuple("Parent", "level link")

def unique_justseen(iterable, key=None):
    "List unique elements, preserving order. Remember only the element just seen."
    # unique_justseen('AAAABBBCCDAABBB') --> A B C D A B
    # unique_justseen('ABBCcAD', str.lower) --> A B C A D
    return imap(next, imap(itemgetter(1), groupby(iterable, key)))

def flatten_bom(data):
    flatten = []
    for doc in data["documents"][data["obj"].id]:
        flatten.append(("document", doc, data["states"][doc.id]))
    for part in data["alternates"][data["obj"].id]:
        flatten.append(("alternate", part, data["states"][part.id]))
    for child in data["children"]:
        link = child.link
        ext_data = data["extension_data"][link.id]
        ext = tuple(ext_data.get(key, "") for key, name in data["extra_columns"])
        flatten.append(("part", child, data["states"].get(link.child_id), ext))
        for doc in data["documents"][link.child_id]:
            flatten.append(("document", doc, data["states"].get(doc.id)))
        for part in data["alternates"][link.child_id]:
            flatten.append(("alternate", part, data["states"][part.id]))
    return flatten


def get_last_children(children):
    previous_level = 0
    last_children = []
    for c in children:
        if last_children and c.level > previous_level:
            del last_children[-1]
        last_children.append(c)
        previous_level = c.level
    return last_children


class PartController(PLMObjectController):
    u"""
    Controller for :class:`.Part`.

    This controller adds methods to manage Parent-Child links between two
    Parts.
    """

    __slots__ = PLMObjectController.__slots__ + ("can_add_child2", )

    def __init__(self, *args, **kwargs):
        super(PartController, self).__init__(*args, **kwargs)
        # an optimized version of can_add_child can be computed
        # to test several objects (for example: search results)
        self.can_add_child2 = lambda c: self.can_add_child(c)

    def check_add_child(self, child):
        """
        Checks if *child* can be added to *self*.
        If *child* can not be added, an exception is raised.

        :param child: child to be added
        :type child: :class:`.Part`

        :raises: :exc:`ValueError` if *child* is already a child or a parent.
        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        """
        self.check_permission("owner")
        self.check_editable()
        if child.is_cancelled:
            raise ValueError("Can not add child: child is cancelled.")
        if child.is_deprecated:
            raise ValueError("Can not add child: child is deprecated.")
        if not child.is_part:
            raise TypeError("Can not add child: not a Part")
        # check if child is not a parent
        if child.id == self.object.id:
            raise ValueError("Can not add child: child is current object")
        if isinstance(child, PartController):
            child.check_readable()
            child_ctrl = child
            child = child.object
        else:
            child_ctrl = get_controller(child.type)(child, self._user)
            child_ctrl.check_readable()
        if self.is_ancestor2(child):
            raise ValueError("Can not add child %s to %s, it is a parent" %
                                (child, self.object))
        link = self.parentchildlink_parent.now().filter(child=child)
        if link.exists():
            raise ValueError("Can not add child, %s is already a child of %s" %
                                (child, self.object))

        if self.is_alternate(child):
            raise ValueError("Can not add child, %s is an alternate part of %s" %
                                (child, self.object))
        # alternate siblings
        children = [c.link.child_id for c in self.get_children(1)]
        children += models.AlternatePartSet.get_related_parts(children)
        if set(p.id for p in child_ctrl.get_alternates()) & set(children):
            raise ValueError("Can not add child, %s is an alternate part of one of the children" % child)


    def precompute_can_add_child2(self):
        is_owner = self.check_permission("owner", raise_=False)
        if is_owner and self.is_editable:
            links = models.ParentChildLink.current_objects
            parents = set([self.id])
            parents.update(models.AlternatePartSet.get_related_parts(parents))
            invalid_ids = set(parents)
            while parents:
                parents = set(links.filter(child__in=parents).values_list("parent",
                        flat=True))
                parents.update(models.AlternatePartSet.get_related_parts(parents))
                parents.difference_update(invalid_ids)
                invalid_ids.update(parents)
            children = set(self.parentchildlink_parent.now().values_list("child", flat=True))
            children.update(models.AlternatePartSet.get_related_parts(children))
            invalid_ids.update(children)
            invalid_ids.add(self.object.id)
            def can_add(child):
                if child.is_part and child.id not in invalid_ids:
                    valid_state = not (child.is_cancelled or child.is_deprecated)
                    if valid_state:
                        child_ctrl = get_controller(child.type)(child, self._user)
                        return child_ctrl.check_readable(False)
                return False
            self.can_add_child2 = can_add
        else:
            self.can_add_child2 = lambda y: False

    def can_add_child(self, child):
        """
        Returns True if *child* can be added to *self*.
        """

        can_add = False
        try:
            self.check_add_child(child)
            can_add = True
        except StandardError:
            pass
        return can_add

    def add_child(self, child, quantity, order, unit=DEFAULT_UNIT, **extension_data):
        """
        Adds *child* to *self*.

        :param child: added child
        :type child: :class:`.Part`
        :param quantity: amount of *child*
        :type quantity: positive float
        :param order: order
        :type order: positive int
        :param unit: a valid unit

        Extra arguments are used to create relevant :class:`.ParentChildLinkExtension`.

        :raises: :exc:`ValueError` if *child* is already a child or a parent.
        :raises: :exc:`ValueError` if *quantity* or *order* are negative.
        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        :raises: :exc:`.PermissionError` if :attr:`object` is not editable.
        """

        if isinstance(child, PLMObjectController):
            child = child.object
        self.check_add_child(child)
        if order < 0 or quantity < 0:
            raise ValueError("Quantity or order is negative")
        # data are valid : create the link
        link = models.ParentChildLink()
        link.parent = self.object
        link.child = child
        link.quantity = quantity
        link.order = order
        link.unit = unit
        link.save()
        # handle plces
        for PCLE in models.get_PCLEs(self.object):
            name = PCLE._meta.module_name
            if name in extension_data and PCLE.one_per_link():
                ext = PCLE(link=link, **extension_data[name])
                ext.save()
        # records creation in history
        self._save_histo(link.ACTION_NAME,
                         "parent : %s (%s//%s//%s) => child : %s (%s//%s//%s), quantity : %s %s, order : %s" % (self.object.name, self.object.type, self.object.reference, self.object.revision, child.name, child.type, child.reference, child.revision, link.quantity, link.unit, link.order))
        return link

    def delete_child(self, child):
        u"""
        Deletes *child* from current children and records this action in the
        history.

        .. note::
            The link is not destroyed: its :attr:`.ParentChildLink.end_time`
            is set to now.

        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        :raises: :exc:`.PermissionError` if :attr:`object` is not editable.
        """

        self.check_permission("owner")
        self.check_editable()
        if isinstance(child, PLMObjectController):
            child = child.object
        link = self.parentchildlink_parent.now().get(child=child)
        link.end()
        self._save_histo("Undo - %s" % link.ACTION_NAME, "child : %s (%s//%s//%s)" % (child.name, child.type, child.reference, child.revision))

    def modify_child(self, child, new_quantity, new_order, new_unit,
            **extension_data):
        """
        Modifies information about *child*.

        :param child: added child
        :type child: :class:`.Part`
        :param new_quantity: amount of *child*
        :type new_quantity: positive float
        :param new_order: order
        :type new_order: positive int

        Extra arguments are used to modify relevant :class:`.ParentChildLinkExtension`.

        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        :raises: :exc:`.PermissionError` if :attr:`object` is not editable.
        """

        self.check_permission("owner")
        self.check_editable()
        if isinstance(child, PLMObjectController):
            child = child.object
        if new_order < 0 or new_quantity < 0:
            raise ValueError("Quantity or order is negative")
        link = models.ParentChildLink.current_objects.get(parent=self.object,
                                                  child=child)
        original_extension_data = link.get_extension_data()

        if (link.quantity == new_quantity and link.order == new_order and
            link.unit == new_unit and original_extension_data == extension_data):
            # do not make an update if it is useless
            return link
        link.end_time = timezone.now()
        link.save()
        # make a new link
        link2, extensions = link.clone(quantity=new_quantity, order=new_order,
                       unit=new_unit, end_time=None, extension_data=extension_data)
        details = ""
        if link.quantity != new_quantity:
            details += "quantity changes from %f to %f\n" % (link.quantity, new_quantity)
        if link.order != new_order:
            details += "order changes from %d to %d" % (link.order, new_order)
        if link.unit != new_unit:
            details += "unit changes from %s to %s" % (link.unit, new_unit)

        # TODO: details of extension changes

        self._save_histo("Modify - %s" % link.ACTION_NAME, details)
        link2.save(force_insert=True)
        # save cloned extensions
        for ext in extensions:
            ext.link = link2
            ext.save(force_insert=True)
        # add new extensions
        for PCLE in models.get_PCLEs(self.object):
            name = PCLE._meta.module_name
            if (name in extension_data and name not in original_extension_data
                and PCLE.one_per_link()):
                ext = PCLE(link=link2, **extension_data[name])
                ext.save()
        return link2

    def replace_child(self, link, new_child):
        """
        Replaces a child by another one.

        :param link: link being replaced, its data (extensions included)
                     are copied
        :type link: :class:`.ParentChildLink`
        :param new_child: the new child
        :type new_child: :class:`.Part`

        :raises: :exc:`ValueError` if the link is invalid (already completed
                 or its parent is not the current object)
        :raises: all permission errors raised by :meth:`check_add_child`
        """
        if link.end_time != None or link.parent_id != self.id:
            raise ValueError("Invalid link")
        if isinstance(new_child, PLMObjectController):
            new_child = new_child.object
        if link.child == new_child:
            return link
        try:
            existing_link = self.parentchildlink_parent.now().get(child=new_child)
            if link.unit != existing_link.unit:
                raise ValueError("Different units")
            extra_qty = existing_link.quantity
        except models.ParentChildLink.DoesNotExist:
            self.check_add_child(new_child)
            existing_link = None
            extra_qty = 0
        link.end()
        if existing_link is not None:
            existing_link.end()
        # make a new link
        link2, extensions = link.clone(child=new_child, end_time=None,
            quantity=link.quantity + extra_qty)
        details = u"Child changes from %s to %s" % (link.child, new_child)
        self._save_histo("Modify - %s" % link.ACTION_NAME, details)
        link2.save(force_insert=True)
        # save cloned extensions
        for ext in extensions:
            ext.link = link2
            ext.save(force_insert=True)
        # copy extensions of the existing link
        if existing_link is not None:
            existing_link.end()
            l3, extensions = existing_link.clone(save=False, child=new_child)
            for ext in extensions:
                if not ext.one_per_link():
                    ext.link = link2
                    ext.save(force_insert=True)
        return link2

    def get_children(self, max_level=1, date=None,
            related=("child", "child__state", "child__lifecycle"),
            only_official=False, only=None):
        """
        Returns a list of all children at time *date*.

        :param max_level: maximum level of children, ``-1``
            returns all descendants, ``1`` returns direct children
        :param related: a list of related fields that are given
            to retrieve the :class:`.ParentChildLink`
        :param only_official: True if the result should be pruned to
            only include official children
        :param only: a list of fields that are given to limit the
            retrieved field of the :class:`.ParentChildLink`
        :rtype: list of :class:`Child`
        """

        links = models.ParentChildLink.objects.at(date).order_by("-order")\
                .select_related(*related)
        if only is not None:
            links = links.only(*only)
        res = []
        parents = [self.object.id]
        level = 1
        last_children = []
        children_ids = []
        while parents and (max_level < 0 or level <= max_level):
            qs = links.filter(parent__in=parents)
            parents = []
            last = []
            for link in qs.iterator():
                parents.append(link.child_id)
                child = Child(level, link)
                last.append(child)
                children_ids.append(link.child_id)
                if level == 1:
                    res.insert(0, child)
                else:
                    for c in last_children:
                        if c.link.child_id == link.parent_id:
                            res.insert(res.index(c) +1, child)
                            break
            last_children = last
            level += 1
        if only_official and res:
            # retrieves all official children at *date* and then prunes the
            # tree so that we only run one query
            res2 = []
            sh = models.StateHistory.objects.at(date).officials().filter(plmobject__in=children_ids)
            valid_children = set(sh.values_list("plmobject_id", flat=True))
            # level_threshold is used to cut a "branch" of the tree
            level_threshold = len(res) + 1 # all levels are inferior to this value
            for child in res:
                if child.level > level_threshold:
                    continue
                if child.link.child_id in valid_children:
                    res2.append(child)
                    level_threshold = len(res) + 1
                else:
                    level_threshold = child.level
            res = res2
        return res

    def is_ancestor(self, part):
        """
        Returns True if *part* is an ancestor of the current object.
        """
        links = models.ParentChildLink.current_objects
        parents = [part.id]
        while parents:
            parents = links.filter(parent__in=parents).values_list("child",
                    flat=True)
            if self.id in parents:
                return True
        return False

    def is_ancestor2(self, part):
        # TODO: rename this method
        links = models.ParentChildLink.current_objects
        alternates = self.get_alternates()
        tested_parts = set(p.id for p in alternates)
        tested_parts.add(self.id)
        parents = [part.id]
        parents += models.AlternatePartSet.get_related_parts(parents)
        while parents:
            parents += models.AlternatePartSet.get_related_parts(parents)
            parents = list(links.filter(parent__in=parents).values_list("child",
                    flat=True))
            if not tested_parts.isdisjoint(parents):
                return True
        return False


    def get_parents(self, max_level=1, date=None,
            related=("parent", "parent__state", "parent__lifecycle"),
            only_official=False, only=None):
        """
        Returns a list of all parents at time *date*.

        :param max_level: maximum level of parents, ``-1``
            returns all ancestors, ``1`` returns direct parents
        :param related: a list of related fields that are given
            to retrieve the :class:`.ParentChildLink`
        :param only_official: True if the result should be pruned to
            only include official parents
        :param only: a list of fields that are given to limit the
            retrieved field of the :class:`.ParentChildLink`
        :rtype: list of :class:`Parent`
        """

        links = models.ParentChildLink.objects.at(date).order_by("-order")\
                .select_related(*related)
        if only is not None:
            links = links.only(*only)
        res = []
        children = [self.object.id]
        level = 1
        last_parents = []
        parents_ids = []
        while children and (max_level < 0 or level <= max_level):
            qs = links.filter(child__in=children)
            children = []
            last = []
            for link in qs.iterator():
                children.append(link.parent_id)
                parent = Parent(level, link)
                last.append(parent)
                parents_ids.append(link.parent_id)
                if level == 1:
                    res.insert(0, parent)
                else:
                    for c in last_parents:
                        if c.link.parent_id == link.child_id:
                            res.insert(res.index(c) +1, parent)
                            break
            last_parents = last
            level += 1
        if only_official and res:
            # retrieves all official children at *date* and then prunes the
            # tree so that we only run one query
            res2 = []
            sh = models.StateHistory.objects.at(date).officials().filter(plmobject__in=parents_ids)
            valid_parents = set(sh.values_list("plmobject_id", flat=True))
            # level_threshold is used to cut a "branch" of the tree
            level_threshold = len(res) + 1 # all levels are inferior to this value
            for parent in res:
                if parent.level > level_threshold:
                    continue
                if parent.link.parent_id in valid_parents:
                    res2.append(parent)
                    level_threshold = len(res) + 1
                else:
                    level_threshold = parent.level
            res = res2
        return res

    def update_children(self, formset):
        u"""
        Updates children informations with data from *formset*

        :param formset:
        :type formset: a modelfactory_formset of
                        :class:`~plmapp.forms.ModifyChildForm`

        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        :raises: :exc:`.PermissionError` if :attr:`object` is not editable.
        """

        self.check_permission("owner")
        self.check_editable()
        if formset.is_valid():
            for form in formset.forms:
                parent = form.cleaned_data["parent"]
                if parent.pk != self.object.pk:
                    raise ValueError("Bad parent %s (%s expected)" % (parent, self.object))
                delete = form.cleaned_data["delete"]
                child = form.cleaned_data["child"]
                if delete:
                    self.delete_child(child)
                else:
                    quantity = form.cleaned_data["quantity"]
                    order = form.cleaned_data["order"]
                    unit = form.cleaned_data["unit"]
                    self.modify_child(child, quantity, order, unit,
                            **form.extensions)

    def get_bom(self, date, level, state="all", show_documents=False, show_alternates=False):
        """
        .. versionadded:: 1.2

        Returns some data about children that will be displayed
        in BOM view.

        :param date: date of the BOM (see :meth:`.get_children`)
        :param level: level of the BOM, valid options are
                      ``"first"``, ``"all"`` and ``"last"``.
        :param state: set to ``"official"`` to hide unofficial parts and document
        :param show_documents: True if attached document are displayed

        It returns a dictionary containing the following keys:

        ``children``
            list of :class:`Child`, see :meth:`.get_children`

        ``extra_columens``
            list of extra column headers (field name, verbose name):
            its the list of BOMs extensions bound to the object

        ``extension_data``
            dictionary (link id -> extension values)

        ``level``
            the given *level*

        ``documents``
            dictionary (part id -> document)

        ``states``
            dictionary (plmobject id -> state) containing the state (str)
            of displayed objects at date *date*

        ``obj``
            this controller
        """
        max_level = 1 if level == "first" else -1
        only_official = state == "official"
        children = self.get_children(max_level, date=date, only_official=only_official)
        if level == "last" and children:
            # only get "leaf" children
            children = get_last_children(children)
        children = list(children)
        # pcle
        extra_columns = []
        extension_data = defaultdict(dict)
        if children:
            for PCLE in models.get_PCLEs(self.object):
                fields = PCLE.get_visible_fields()
                if fields:
                    extra_columns.extend((f, PCLE._meta.get_field(f).verbose_name)
                            for f in fields)
                    pcles = PCLE.objects.filter(link__in=(c.link.id for c in children))
                    pcles = pcles.values("link_id", *fields)
                    for pcle in pcles:
                        extension_data[pcle["link_id"]].update(pcle)

        ids = set([self.id] + [c.link.child_id for c in children])
        # alternates
        alternates = defaultdict(list) # part id -> list of alternate parts
        if show_alternates:
            ps = models.AlternatePartSet.objects.at(date).filter(parts__in=ids).distinct()
            alt = list(models.Part.objects.filter(alternatepartsets__in=ps).\
                    extra(select={"psid":"alternatepartset_id"}))
            if only_official and alt:
                sh = models.StateHistory.objects.at(date).officials().filter(plmobject__in=alt)
                official_alt = set(sh.values_list("plmobject_id", flat=True))
                alt = [p for p in alt if p.id in official_alt]
            id2ps = dict((p.id, p.psid) for p in alt)
            for part_id in ids:
                try:
                    psid = id2ps[part_id]
                    alternates[part_id] = [p for p in alt if p.psid == psid and p.id != part_id]
                except KeyError:
                    pass
            ids.update(p.id for p in alt)

        # get attached documents
        documents = defaultdict(list) # part id -> list of documents
        doc_ids = set()
        if show_documents:
            links = models.DocumentPartLink.objects.at(date).filter(part__in=ids).\
                    order_by("document__reference", "document__revision").\
                    select_related("document", "document__state")
            for link in links:
                documents[link.part_id].append(link.document)
                doc_ids.add(link.document_id)
        # get state of object at *date*
        states = models.StateHistory.objects.at(date).filter(plmobject__in=ids | doc_ids)
        if only_official:
            states = states.officials()
        states = dict(states.values_list("plmobject", "state"))
        if only_official and show_documents:
            # remove unofficial documents
            for docs in documents.itervalues():
                official_docs = (d for d in docs if d.id in states)
                docs[:] = official_docs # in place copy
        return {
                'children' : children,
                'extra_columns' : extra_columns,
                'extension_data' : extension_data,
                'states' : states,
                'documents' : documents,
                'level' : level,
                'obj' : self,
                'alternates' : alternates,
                }

    def cmp_bom(self, date1, date2, level="first", state="all", show_documents=False,
            show_alternates=False):
        """
        .. versionadded:: 1.2

        Compares two BOMs at date *date1* and *date2*.

        dates, *level*, *state* and *show_documents* are described in :meth:`.get_bom`.

        It returns a dictionary containing the following keys:

        ``diff``
            diff result, it is a sequence of tuples
            (tag, first BOM rows, second BOM rows)
            (see :meth:`.difflib.SequenceMatcher.get_opcodes`)

        ``boms``
            tuple of BOMs (at date *date1* and date *date2*)

        """
        bom1 = self.get_bom(date1, level, state, show_documents, show_alternates)
        bom2 = self.get_bom(date2, level, state, show_documents, show_alternates)
        s1 = flatten_bom(bom1)
        s2 = flatten_bom(bom2)
        matcher = difflib.SequenceMatcher(None, s1, s2)
        diff = ((tag, izip_longest(s1[i1:i2], s2[j1:j2]))
            for tag, i1, i2, j1, j2 in matcher.get_opcodes())
        ctx = {
                "diff" : diff,
                "boms" : (bom1, bom2),
                }
        return ctx

    def revise(self, new_revision, child_links=None, documents=(),
            parents=(), **kwargs):
        """
        Revises the part. Does the same thing as :meth:`.PLMObjectController.revise`
        and:

            * copies all :class:`.ParentChildLink` of *child_links*, with the
              new revision as the new parent. If *child_links* is None (the
              default), all current children are copied. If an empty sequence
              is given, no links are copied.

            * attaches all document of *documents*, by default, no documents
              are attached. The method :meth:`get_suggested_documents` returns a
              list of documents that should be interesting.

            * replaces all parent links in *parents*. This arguments must be
              a list of tuples (link (an instance of :class:`.ParentChildLink`),
              parent (an instance of :class:`.PLMObject`)) where *parent* is
              the parent whose the bom will be modified and *link* is the
              source of data (quantity, unit, order...). *link* will be
              ended if *parent* is a parent of the current part.
              The method :meth:`get_suggested_parents` returns a list of
              tuples that may interest the user who revises this part.
        """
        # same as PLMObjectController + add children
        new_controller = super(PartController, self).revise(new_revision, **kwargs)
        # adds the children
        if child_links is None:
            child_links = (x.link for x in self.get_children(1))
        for link in child_links:
            link.clone(save=True, parent=new_controller.object)
        # attach the documents
        for doc in documents:
            models.DocumentPartLink.objects.create(part=new_controller.object,
                    document=doc)
        # for each parent, replace its child with the new revision
        now = timezone.now()
        for link, parent in parents:
            link.clone(save=True, parent=parent, child=new_controller.object)
            if link.parent_id == parent.id:
                link.end_time = now
                link.save()
        return new_controller

    def get_suggested_documents(self):
        """
        Returns a QuerySet of documents that should be suggested when the
        user revises the part.

        A document is suggested if:

            a. it is attached to the current part and:

                1. it is a *draft* and its superior revisions, if they exist,
                   are *not* attached to the part

                   or

                2. it is *official* and its superior revisions, if they exist,
                   are *not* attached to the part

                   or

                3. it is *official* and a superior revision is attached *and*
                   another superior revision is not attached to the part

            b. it is *not* attached to the current part, an inferior revision
               is attached to the part and:

                1. it is a draft

                   or

                2. it is official

        """
        docs = []
        links = self.get_attached_documents()
        attached_documents = set(link.document_id for link in links)
        for link in links:
            document = link.document
            ctrl = PLMObjectController(document, self._user)
            revisions = ctrl.get_next_revisions()
            attached_revisions = [d for d in revisions if d.id in attached_documents]
            other_revisions = set(revisions).difference(attached_revisions)
            if not attached_revisions:
                if document.is_draft or document.is_official:
                    docs.append(document.id)
            else:
                if document.is_official and not other_revisions:
                    docs.append(document.id)
            for rev in other_revisions:
                if rev.is_official or rev.is_draft:
                    docs.append(rev.id)
        if docs:
            return models.Document.objects.filter(id__in=docs)
        else:
            return models.Document.objects.none()

    def get_suggested_parents(self):
        """
        Returns a list of suggested parents that should be suggested
        when the part is revised.

        This method returns a list of tuple (link (an instance of
        :class:`.ParentChildLink`), parent (an instance of :class:`.PLMObject`)).
        It does not returns a list of links, since it may suggest a part
        that is not a parent but whose one of its previous revision is a parent.
        We need a link to copy its data (order, quantity, unit and extensions).

        A part is suggested as a parent if:

            a. it is already a parent and:

                1. no superior revisions are a parent and its state is draft
                   or official

                   or

                2. no superior revisions exist and its state is proposed.

            b. it is not a parent, a previous revision is a parent, its state
               is a draft or a parent. In that case, the link of the most
               superior parent revision is used.

        """
        parents = self.get_parents(1)
        links = []
        ids = set(p.link.parent_id for p in parents)
        for level, link in parents:
            parent = link.parent
            ctrl = PLMObjectController(parent, self._user)
            revisions = ctrl.get_next_revisions()
            attached_revisions = [d for d in revisions if d.id in ids]
            other_revisions = set(revisions).difference(attached_revisions)
            if not attached_revisions:
                if parent.is_draft or parent.is_official or \
                    (parent.is_proposed and not other_revisions):
                    links.append((link, parent))
            for p in other_revisions:
                if p.is_draft or p.is_official:
                    links.append((link, p.part))
        # it is possible that some parts are suggested twice or more
        # if they are not a parent (they are a superior revision of a parent)
        # so we must clean up links
        links2 = dict() # id -> (link, parent)
        for link, parent in links:
            if parent.id in ids:
                links2[parent.id] = (link, parent)
            else:
                # it is not a parent
                try:
                    l, p = links2[parent.id]
                    if l.parent.ctime < link.parent.ctime:
                        # true if parent is a superior revision
                        links2[parent.id] = (link, parent)
                except KeyError:
                    links2[parent.id] = (link, parent)
        return links2.values()

    def attach_to_document(self, document):
        """
        Links *document* (a :class:`.Document`) with
        :attr:`~PLMObjectController.object`.

        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        """

        self.check_attach_document(document)
        if isinstance(document, PLMObjectController):
            document = document.object
        self.documentpartlink_part.create(document=document)
        self._save_histo(models.DocumentPartLink.ACTION_NAME,
                         "%s (%s//%s//%s) <=> %s (%s//%s//%s)" % (self.object.name, self.object.type, self.object.reference, self.object.revision, document.name, document.type, document.reference, document.revision))

    def detach_document(self, document):
        """
        Delete link between *document* (a :class:`.Document`)
        and :attr:`~PLMObjectController.object`.

        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        """

        self.check_attach_document(document, True)
        if isinstance(document, PLMObjectController):
            document = document.object
        link = self.documentpartlink_part.now().get(document=document)
        link.end()
        self._save_histo("Undo " + models.DocumentPartLink.ACTION_NAME,
                         "%s (%s//%s//%s) <=> %s (%s//%s//%s)" % (self.object.name, self.object.type, self.object.reference, self.object.revision, document.name, document.type, document.reference, document.revision))

    def get_attached_documents(self, time=None):
        """
        Returns all :class:`.Document` attached to
        :attr:`~PLMObjectController.object`.
        """
        return self.documentpartlink_part.at(time)

    def get_detachable_documents(self):
        """
        Returns all attached documents the user can detach.
        """
        links = []
        for link in self.get_attached_documents().select_related("document"):
            doc = link.document
            if self.can_detach_document(doc):
                links.append(link.id)
        if links:
            return self.documentpartlink_part.filter(id__in=links)
        else:
            return models.DocumentPartLink.objects.none()

    def is_document_attached(self, document):
        """
        Returns True if *document* is attached to the current part.
        """

        if isinstance(document, PLMObjectController):
            document = document.object
        return self.documentpartlink_part.now().filter(document=document).exists()

    def check_attach_document(self, document, detach=False):
        if not hasattr(document, "is_document") or not document.is_document:
            raise TypeError("%s is not a document" % document)
        self.check_contributor()
        if not (self.is_draft or document.is_draft):
            raise ValueError("Can not attach: one of the part or document's state must be draft.")
        if self.is_cancelled:
            raise ValueError("Can not attach: part is cancelled.")
        if self.is_deprecated:
            raise ValueError("Can not attach: part is deprecated.")
        if document.is_cancelled:
            raise ValueError("Can not attach: document is cancelled.")
        if document.is_deprecated:
            raise ValueError("Can not attach: document is deprecated.")
        if self.is_proposed:
            raise ValueError("Can not attach: part's state is %s" % self.state.name)
        if isinstance(document, PLMObjectController):
            document.check_readable()
            ctrl = document
            document = document.object
        else:
            ctrl = get_controller(document.type)(document, self._user)
            ctrl.check_readable()
        self.check_readable()
        if document.is_draft and self.is_draft:
            owner_ok = True
        elif document.is_draft or document.is_proposed:
            owner_ok = ctrl.check_permission("owner", raise_=False)
        else:
            self.check_editable()
            owner_ok = False
        if not owner_ok:
            self.check_permission("owner")

        if self.is_document_attached(document):
            if not detach:
                raise ValueError("Document is already attached to the part.")
        elif detach:
            raise ValueError("Document is not attached to the part.")

    def can_attach_document(self, document):
        """
        Returns True if *document* can be attached to the current part.
        """
        can_attach = False
        try:
            self.check_attach_document(document)
            can_attach = True
        except StandardError:
            pass
        return can_attach

    def can_detach_document(self, document):
        """
        Returns True if *document* can be detached.
        """
        can_detach = False
        try:
            self.check_attach_document(document, True)
            can_detach = True
        except StandardError:
            pass
        return can_detach

    def update_doc_cad(self, formset):
        u"""
        Updates doc_cad informations with data from *formset*

        :param formset:
        :type formset: a modelfactory_formset of
                        :class:`~plmapp.forms.ModifyChildForm`

        :raises: :exc:`ValueError` if one of the document is not detachable.
        """

        docs = set()
        if formset.is_valid():
            for form in formset.forms:
                part = form.cleaned_data["part"]
                if part.pk != self.object.pk:
                    raise ValueError("Bad part %s (%s expected)" % (part, self.object))
                delete = form.cleaned_data["delete"]
                document = form.cleaned_data["document"]
                if delete:
                    docs.add(document)
            if docs:
                for doc in docs:
                    self.check_attach_document(doc, True)
                ids = (d.id for d in docs)
                self.documentpartlink_part.filter(document__in=ids).end()

    def _deprecate(self):
        super(PartController, self)._deprecate()
        self.end_alternate()

    def cancel(self):
        """
        Cancels the object:

            * calls :meth:`.PLMObjectController.cancel`
            * removes all :class:`.DocumentPartLink` related to the object
            * removes all children/parents link (set their end_time)
        """
        super(PartController, self).cancel()
        self.get_attached_documents().end()
        self.end_alternate()
        q = Q(parent=self.object) | Q(child=self.object)
        models.ParentChildLink.current_objects.filter(q).end()

    def check_cancel(self,raise_=True):
        res = super(PartController, self).check_cancel(raise_=raise_)
        if res :
            q = Q(parent=self.object) | Q(child=self.object)
            res = res and not models.ParentChildLink.current_objects.filter(q).exists()
            if (not res) and raise_ :
                raise PermissionError("This part is related to an other part.")
            res = res and not self.get_attached_documents().exists()
            if (not res) and raise_ :
                raise PermissionError("This part has a document related to it.")
        return res

    def clone(self,form, user, child_links, documents, block_mails=False, no_index=False):
        """
        Clones the object :

        calls PLMObjectController.clone()

        :param child_links: list of :class:`.ParentChildLink` selected to be cloned with the new part as parent
        :param documents: list of :class:`.Document` selected to be attached to the new part
        """
        new_ctrl = super(PartController, self).clone(form, user, block_mails, no_index)
        if child_links :
            for link in child_links:
                link.clone(save=True, parent=new_ctrl.object)
        if documents :
            for doc in documents:
                models.DocumentPartLink.objects.create(part=new_ctrl.object,
                    document=doc)
        details = "to %s (%s//%s//%s)" %(new_ctrl.name, new_ctrl.type, new_ctrl.reference, new_ctrl.revision)
        self._save_histo("Clone", details)
        return new_ctrl

    def has_links(self):
        """
        Return true if the part :

            * is a parent or a child
            * is attached to at least one document
        """
        q = Q(parent=self.object) | Q(child=self.object)
        res = models.ParentChildLink.current_objects.filter(q).exists()
        res = res or self.get_attached_documents().exists()
        return res

    def get_cad_files(self):
        """
        Returns an iterable of all :class:`.DocumentFile` related
        to *part* that contain a CAD file. It retrieves all non deprecated
        files of all documents parts to *part* and its children and
        filters these files according to their extension (see :meth:`.is_cad_file`).
        """
        children = self.get_children(-1, related=("child",))
        children_ids = set(c.link.child_id for c in children)
        children_ids.add(self.id)
        links = models.DocumentPartLink.current_objects.filter(part__in=children_ids)
        docs = links.values_list("document", flat=True)
        d_o_u = "document__owner__username"
        files = models.DocumentFile.objects.filter(deprecated=False,
                    document__in=set(docs))
        # XXX : maybe its faster to build a complex query than retrieving
        # each file and testing their extension
        return (df for df in files.select_related(d_o_u) if is_cad_file(df.filename))

    def check_add_alternate(self, part, check_perm=True):
        if check_perm:
            self.check_permission("owner")
            self.check_editable()
        # FIXME: untested !!!

        # TODO: better error messages, permissions

        if part.is_cancelled:
            raise ValueError("Can not add alternate: part is cancelled.")
        if part.is_deprecated:
            raise ValueError("Can not add alternate: part is deprecated.")
        if not part.is_part:
            raise ValueError("Not a part")
        if part.id == self.id:
            raise ValueError("same part")
        # get alternate part sets
        partset = None
        try:
            partset = self.alternatepartsets.now().get()
        except models.AlternatePartSet.DoesNotExist:
            pass
        try:
            other_partset = part.alternatepartsets.now().get()
        except models.AlternatePartSet.DoesNotExist:
            other_partset = None
        if partset is not None and other_partset is not None:
            if partset == other_partset:
                raise ValueError("Already an alternate part")
            else:
                raise ValueError("Merging of two alternate part sets is not yet supported")
        # 3 cases:
        #  - self and part have no alternates
        #  - self has alternates
        #  - part has alternates
        alternates = []
        if partset is not None:
            alternates = list(partset.parts.all())
            tested_part = part
        elif other_partset is not None:
            alternates = list(other_partset.parts.all())
            tested_part = self.object

        # revisions
        if not alternates:
            revision_valid = not (self.type == part.type and self.reference == part.reference)
        else:
            revision_valid = all((p.type, p.reference) != (tested_part.type, tested_part.reference)
                    for p in alternates if p.id != tested_part.id)
        if not revision_valid:
            raise ValueError("Invalid revision")

        # ancestors
        links = models.ParentChildLink.current_objects
        parents = [part.id, self.id] + [p.id for p in alternates]
        built_set = set(parents[:])
        while parents:
            parents = list(links.filter(child__in=parents).values_list("parent",
                    flat=True))
            parents += models.AlternatePartSet.get_related_parts(parents)
            if not built_set.isdisjoint(parents):
                raise ValueError("Ancestor")

        # siblings
        if not alternates:
            p1 = set(links.filter(child=self.object).values_list("parent", flat=True))
            p2 = set(links.filter(child=part).values_list("parent", flat=True))
        else:
            p1 = set(links.filter(child=tested_part).values_list("parent", flat=True))
            p2 = set(links.filter(child__in=alternates).values_list("parent", flat=True))
        if p1 & p2:
            raise ValueError("sibling")

    def add_alternate(self, part, check_perm=True):
        self.check_add_alternate(part, check_perm)
        partset = models.AlternatePartSet.join(self.object, getattr(part, "object", part))
        # TODO: HISTO
        return partset

    def can_add_alternate(self, part):
        can = True
        try:
            self.check_add_alternate(part)
        except:
            can = False
        return can

    def is_alternate(self, part):
        my_partset = models.AlternatePartSet.get_partset(self.object)
        if my_partset is None:
            return False
        other_partset = models.AlternatePartSet.get_partset(part)
        return my_partset == other_partset

    def delete_alternate(self, part):
        # permissions ?
        self.check_permission("owner")
        self.check_editable()
        partset = models.AlternatePartSet.get_partset(self.object)
        # TODO: histo
        return partset.remove_part(part)

    def end_alternate(self):
        # FIXME : rename me
        partset = models.AlternatePartSet.get_partset(self.object)
        if partset:
            return partset.remove_part(self.object)
        return None

    def get_alternates(self, date=None):
        try:
            partset = self.alternatepartsets.at(date).get()
            return partset.parts.exclude(id=self.id)
        except models.AlternatePartSet.DoesNotExist:
            return []

    def promote(self, *args, **kwargs):
        # replace alternate links of previous revision
        try:
            previous_revision = self.revisionlink_new.now().get().old.part
            partset = models.AlternatePartSet.get_partset(previous_revision)
        except models.RevisionLink.DoesNotExist:
            partset = None
        r = super(PartController, self).promote(*args, **kwargs)
        if partset and self.is_official:
            # previous_revision has been deprecated or cancelled
            # and partset has been ended by _deprecated() or cancel()
            # self should replace previous_revision
            try:
                other_part = partset.parts.exclude(id=previous_revision.id)[0]
                # do not check owner permission since the company owns the part
                self.add_alternate(other_part, check_perm=False)
            except (ValueError, PermissionError):
                # it should not failed, except if another alternate set was built
                # or if alternate/bom rules are not respected
                pass
        if self.is_deprecated:
            self.end_alternate()
        return r

    @transaction.commit_on_success
    def promote_assembly(self):
        # FIXME Inefficient version
        # FIXME does not check if alternates part are promoted
        if not (self.is_proposed or self.is_draft):
            raise ValueError("invalid state")

        if self.is_promotable():
            # do not need to promote the whole assembly, children are already promoted
            self.approve_promotion()
            return

        # check permission
        lcl = self.lifecycle.to_states_list()
        role = level_to_sign_str(lcl.index(self.state.name))
        self.check_permission(role)

        self.block_mails()
        self.object.no_index = True

        children = self.get_children(-1)

        # checks if multiple revisions of the same part are present
        # XXX: replace old revisions with the newest in assembly ?
        parts = [self.object]
        parts.extend(c.link.child for c in children)
        parts.sort(key=attrgetter("type", "reference", "revision"))
        parts = unique_justseen(parts, attrgetter("id"))
        for (type, ref), group in groupby(parts, attrgetter("type", "reference")):
            group = list(group)
            if len(group) >= 2:
                # at least two revisions
                revisions = u", ".join(p.revision for p in group)
                msg = (u"Several revisions of the same part are present: "
                       u"{type}, {ref}, {revisions}")
                msg = msg.format(type=type, ref=ref, revisions=revisions)
                raise ValueError(msg)

        # XXX: get leaf parts ?

        # check if assembly is promotable
        to_promote = [c for c in children
                if c.link.child.state == self.state and c.link.child.lifecycle == self.lifecycle]
        # promote last children first
        to_promote.sort(key=attrgetter("level"), reverse=True)
        # remove duplicated children, only keep children with the higher level
        to_promote2 = []
        to_promote_ids = set()
        for c in to_promote:
            if c.link.child_id not in to_promote_ids:
                to_promote2.append(c.link.child)
                to_promote_ids.add(c.link.child_id)
        to_promote = to_promote2

        # other children have a different lifecycle or are already promoted
        # they can not be at a previous state because their parents could not
        # have been promoted in that case

        # the assembly is promotable if the last children are promotable
        if self.is_draft:
            # proposed last children are always promotable
            last_children = (c.link.child for c in get_last_children(children))
            if not all(child.is_promotable() for child in last_children if child.id in to_promote_ids):
                # TODO: only test if they all have an official document attached
                # fixme: list parts
                raise PromotionError("Some children are not promotable")

        ctrls = [PartController(c, self._user, True, True) for c in to_promote]
        ctrls.append(self)
        updated = to_promote[:]
        updated.append(self.object)
        if not all(ctrl.is_last_promoter() for ctrl in ctrls):
            # TODO: get all required signers in one query
            # and compare with represented signers
            # must still check signer permission
            raise PromotionError()
        for ctrl in ctrls:
            # TODO: create (state) histories in bulk
            updated.extend(ctrl.promote(checked=True)["updated_revisions"])

        # send mails and update indexes
        for ctrl in ctrls:
            # TODO merge mails ?
            ctrl.unblock_mails()
        update_indexes.delay([(c._meta.app_label, c._meta.module_name, c.pk) for c in updated])

