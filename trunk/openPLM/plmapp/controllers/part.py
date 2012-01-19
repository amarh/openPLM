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
        if not child.is_part:
            raise TypeError("Can not add child: not a Part")
        # check if child is not a parent
        if child.id == self.object.id:
            raise ValueError("Can not add child: child is current object")
        get_controller(child.type)(child, self._user).check_readable()
        parents = (p.link.parent.pk for p in self.get_parents(-1))
        if child.pk in parents:
            raise ValueError("Can not add child %s to %s, it is a parent" %
                                (child, self.object))
        link = self.parentchildlink_parent.filter(child=child, end_time=None)
        if link:
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
        # check if child is not already a direct child
        if child.pk in (c.link.child.pk for c in self.get_children(1)):
            raise ValueError("%s is already a child of %s" % (child, self.object))
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

    def get_children(self, max_level=1, current_level=1, date=None):
        """
        Returns a list of all children at time *date*.
        
        :rtype: list of :class:`Child`
        """

        if max_level != -1 and current_level > max_level:
            return []
        if not date:
            links = self.parentchildlink_parent.filter(end_time__exact=None)
        else:
            links = self.parentchildlink_parent.filter(ctime__lt=date).exclude(end_time__lt=date)
        res = []
        for link in links.order_by("order", "child__reference"):
            res.append(Child(current_level, link))
            pc = PartController(link.child, self._user)
            res.extend(pc.get_children(max_level, current_level + 1, date))
        return res
    
    def get_parents(self, max_level=1, current_level=1, date=None):
        """
        Returns a list of all parents at time *date*.
        
        :rtype: list of :class:`Parent`
        """

        if max_level != -1 and current_level > max_level:
            return []
        if not date:
            links = self.parentchildlink_child.filter(end_time__exact=None)
        else:
            links = self.parentchildlink_child.filter(ctime__lt=date).exclude(end_time__lt=date)
        res = []
        for link in links:
            res.append(Parent(current_level, link))
            pc = PartController(link.parent, self._user)
            res.extend(pc.get_parents(max_level, current_level + 1, date))
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

        self.check_permission("owner")
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
     
    def is_document_attached(self, document):
        """
        Returns True if *document* is attached to the current part.
        """

        if isinstance(document, PLMObjectController):
            document = document.object
        return bool(self.documentpartlink_part.filter(document=document))
    
    def check_attach_document(self, document):
        self.check_permission("owner")
        if not hasattr(document, "is_document") or not document.is_document:
            raise TypeError("%s is not a document" % document)

        if isinstance(document, PLMObjectController):
            document.check_readable()
            document = document.object
        else:
            get_controller(document.type)(document, self._user).check_readable()
        if self.is_document_attached(document):
            raise ValueError("Document is already attached.")

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

    def update_doc_cad(self, formset):
        u"""
        Updates doc_cad informations with data from *formset*
        
        :param formset:
        :type formset: a modelfactory_formset of 
                        :class:`~plmapp.forms.ModifyChildForm`
        
        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
            :attr:`object`.
        """
        
        self.check_permission("owner")
        if formset.is_valid():
            for form in formset.forms:
                part = form.cleaned_data["part"]
                if part.pk != self.object.pk:
                    raise ValueError("Bad part %s (%s expected)" % (part, self.object))
                delete = form.cleaned_data["delete"]
                document = form.cleaned_data["document"]
                if delete:
                    self.detach_document(document)

