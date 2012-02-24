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
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
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

    def get_children(self, max_level=1, date=None,
            related=("child", "child__state", "child__lifecycle")):
        """
        Returns a list of all children at time *date*.
        
        :rtype: list of :class:`Child`
        """
        
        objects = models.ParentChildLink.objects.order_by("-order")\
                .select_related(*related)
        if not date:
            links = objects.filter(end_time__exact=None)
        else:
            links = objects.filter(ctime__lt=date).exclude(end_time__lt=date)
        res = []
        parents = [self.object.id]
        level = 1
        last_children = []
        while parents and (max_level < 0 or level <= max_level):
            qs = links.filter(parent__in=parents)
            parents = []
            last = []
            for link in qs.iterator():
                parents.append(link.child_id)
                child = Child(level, link)
                last.append(child)
                if level == 1:
                    res.insert(0, child)
                else:
                    for c in last_children:
                        if c.link.child_id == link.parent_id:
                            res.insert(res.index(c) +1, child)
                            break
            last_children = last 
            level += 1
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
            related=("parent", "parent__state", "parent__lifecycle")):
        """
        Returns a list of all parents at time *date*.
        
        :rtype: list of :class:`Parent`
        """

        objects = models.ParentChildLink.objects.order_by("-order")\
                .select_related(*related)
        if not date:
            links = objects.filter(end_time__exact=None)
        else:
            links = objects.filter(ctime__lt=date).exclude(end_time__lt=date)
        res = []
        children = [self.object.id]
        level = 1
        last_parents = []
        while children and (max_level < 0 or level <= max_level):
            qs = links.filter(child__in=children)
            children = []
            last = []
            for link in qs.iterator():
                children.append(link.parent_id)
                parent = Parent(level, link)
                last.append(parent)
                if level == 1:
                    res.insert(0, parent)
                else:
                    for c in last_parents:
                        if c.link.parent_id == link.child_id:
                            res.insert(res.index(c) +1, parent)
                            break
            last_parents = last 
            level += 1
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

    def revise(self, new_revision):
        # same as PLMObjectController + add children
        new_controller = super(PartController, self).revise(new_revision)
        for level, link in self.get_children(1):
            link.clone(save=True, parent=new_controller.object)
        return new_controller

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
        return bool(self.documentpartlink_part.filter(document=document))
    
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

