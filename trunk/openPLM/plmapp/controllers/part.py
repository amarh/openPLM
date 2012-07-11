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
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

"""
"""

import datetime
from collections import namedtuple

from django.db.models.query import Q

import openPLM.plmapp.models as models
from openPLM.plmapp.units import DEFAULT_UNIT
from openPLM.plmapp.controllers.plmobject import PLMObjectController
from openPLM.plmapp.controllers.base import get_controller

from openPLM.plmapp.exceptions import PermissionError

Child = namedtuple("Child", "level link")
Parent = namedtuple("Parent", "level link")

class PartController(PLMObjectController):
    u"""
    Controller for :class:`.Part`.

    This controller adds methods to manage Parent-Child links between two
    Parts.
    """

    def check_add_child(self, child):
        """
        Checks if *child"* can be added to *self*.
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
        get_controller(child.type)(child, self._user).check_readable()
        if self.is_ancestor(child):
            raise ValueError("Can not add child %s to %s, it is a parent" %
                                (child, self.object))
        link = self.parentchildlink_parent.filter(child=child, end_time=None)
        if link.exists():
            raise ValueError("Can not add child, %s is already a child of %s" %
                                (child, self.object))

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
                         "parent : %s\nchild : %s" % (self.object, child))
        return link

    def delete_child(self, child):
        u"""
        Deletes *child* from current children and records this action in the
        history.

        .. note::
            The link is not destroyed: its end_time is set to now.
        
        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        :raises: :exc:`.PermissionError` if :attr:`object` is not editable.
        """

        self.check_permission("owner")
        self.check_editable()
        if isinstance(child, PLMObjectController):
            child = child.object
        link = self.parentchildlink_parent.get(child=child, end_time=None)
        link.end_time = datetime.datetime.today()
        link.save()
        self._save_histo("Delete - %s" % link.ACTION_NAME, "child : %s" % child)

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
        link = models.ParentChildLink.objects.get(parent=self.object,
                                                  child=child, end_time=None)
        original_extension_data = link.get_extension_data()

        if (link.quantity == new_quantity and link.order == new_order and
            link.unit == new_unit and original_extension_data == extension_data):
            # do not make an update if it is useless
            return
        link.end_time = datetime.datetime.today()
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
        :raises: all permissions raised by :meth:`check_add_child`
        """
        if link.end_time != None or link.parent_id != self.id:
            raise ValueError("Invalid link")
        if isinstance(new_child, PLMObjectController):
            new_child = new_child.object
        if link.child == new_child:
            return link
        self.check_add_child(new_child)
        link.end_time = datetime.datetime.today()
        link.save()
        # make a new link
        link2, extensions = link.clone(child=new_child, end_time=None)
        details = u"Child changes from %s to %s" % (link.child, new_child)
        self._save_histo("Modify - %s" % link.ACTION_NAME, details)
        link2.save(force_insert=True)
        # save cloned extensions
        for ext in extensions:
            ext.link = link2
            ext.save(force_insert=True)
        return link2       

    def get_children(self, max_level=1, date=None,
            related=("child", "child__state", "child__lifecycle"),
            only_official=False):
        """
        Returns a list of all children at time *date*.
        
        :rtype: list of :class:`Child`
        """
        
        objects = models.ParentChildLink.objects.order_by("-order")\
                .select_related(*related)
        if date is None:
            links = objects.filter(end_time__exact=None)
        else:
            links = objects.filter(ctime__lte=date).exclude(end_time__lt=date)
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
        if only_official:
            # retrieves all official children at *date* and then prunes the
            # tree so that we only run one query
            res2 = []
            sh = models.StateHistory.objects.filter(plmobject__in=children_ids,
                    state_category=models.StateHistory.OFFICIAL)
            if date is None:
                sh = sh.filter(end_time__exact=None)
            else:
                sh = sh.filter(start_time__lte=date).exclude(end_time__lt=date)
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
        links = models.ParentChildLink.objects.filter(end_time__exact=None)
        parents = [part.id]
        last_children = []
        while parents:
            parents = links.filter(parent__in=parents).values_list("child", 
                    flat=True)
            if self.id in parents:
                return True
        return False
    
    def get_parents(self, max_level=1, date=None,
            related=("parent", "parent__state", "parent__lifecycle"),
            only_official=False):
        """
        Returns a list of all parents at time *date*.
        
        :rtype: list of :class:`Parent`
        """

        objects = models.ParentChildLink.objects.order_by("-order")\
                .select_related(*related)
        if not date:
            links = objects.filter(end_time__exact=None)
        else:
            links = objects.filter(ctime__lte=date).exclude(end_time__lt=date)
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
        if only_official:
            # retrieves all official children at *date* and then prunes the
            # tree so that we only run one query
            res2 = []
            sh = models.StateHistory.objects.filter(plmobject__in=parents_ids,
                    state_category=models.StateHistory.OFFICIAL)
            if date is None:
                sh = sh.filter(end_time__exact=None)
            else:
                sh = sh.filter(start_time__lte=date).exclude(end_time__lt=date)
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

    def revise(self, new_revision, child_links=None, documents=(),
            parents=()):
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
        new_controller = super(PartController, self).revise(new_revision)
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
        now = datetime.datetime.today()
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
        return models.Document.objects.filter(id__in=docs)

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
                         "Part : %s - Document : %s" % (self.object, document))

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
        link = self.documentpartlink_part.get(document=document)
        link.delete()
        self._save_histo(models.DocumentPartLink.ACTION_NAME + " - delete",
                         "Part : %s - Document : %s" % (self.object, document))

    def get_attached_documents(self):
        """
        Returns all :class:`.Document` attached to
        :attr:`~PLMObjectController.object`.
        """
        return self.documentpartlink_part.all()

    def get_detachable_documents(self):
        """
        Returns all attached documents the user can detach.
        """
        links = []
        for link in self.get_attached_documents().select_related("document"):
            doc = link.document
            if self.can_detach_document(doc):
                links.append(link.id)
        return self.documentpartlink_part.filter(id__in=links)
     
    def is_document_attached(self, document):
        """
        Returns True if *document* is attached to the current part.
        """

        if isinstance(document, PLMObjectController):
            document = document.object
        return self.documentpartlink_part.filter(document=document).exists()
    
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
                self.documentpartlink_part.filter(document__in=ids).delete()

    def cancel(self):
        """
        Cancels the object:

            * calls :meth:`.PLMObjectController.cancel`
            * removes all :class:`.DocumentPartLink` related to the object
            * removes all children/parents link (set their end_time)
        """
        super(PartController, self).cancel()
        self.get_attached_documents().delete()
        q = Q(parent=self.object) | Q(child=self.object)
        now = datetime.datetime.today()
        models.ParentChildLink.objects.filter(q, end_time=None).update(end_time=now)
        
    def check_cancel(self,raise_=True):
        res = super(PartController, self).check_cancel(raise_=raise_)
        if res :
            q = Q(parent=self.object) | Q(child=self.object)
            res = res and not models.ParentChildLink.objects.filter(q, end_time=None).exists()
            if (not res) and raise_ :
                raise PermissionError("This part is related to an other part.")
            res = res and not self.get_attached_documents()
            if (not res) and raise_ :
                raise PermissionError("This part has a document related to it.")
        return res

    def clone(self,form, user, child_links, documents, block_mails=False, no_index=False):
        new_ctrl = super(PartController, self).clone(form, user, block_mails, no_index)
        if child_links :
            for link in child_links:
                link.clone(save=True, parent=new_ctrl.object)
        if documents :
            for doc in documents:
                models.DocumentPartLink.objects.create(part=new_ctrl.object,
                    document=doc)
        return new_ctrl

    def has_links(self):
        """
        Return true if the part :
            * is a parent or a child
            * is attached to at least one document
        """
        q = Q(parent=self.object) | Q(child=self.object)
        res = not models.ParentChildLink.objects.filter(q, end_time=None).exists()
        res = res and not self.get_attached_documents().exists()
        return res
