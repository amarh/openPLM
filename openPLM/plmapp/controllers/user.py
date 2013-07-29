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
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

"""
This module contains a class called :class:`UserController` which
provides a controller for :class:`~django.contrib.auth.models.User`.
This class is similar to :class:`.PLMObjectController` but some methods
from :class:`.PLMObjectController` are not defined.
"""

import os
from django.conf import settings
from django.db.models.fields import FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.template import Context, Template
from django.shortcuts import get_object_or_404

import openPLM.plmapp.models as models
from openPLM.plmapp.mail import send_mail
from openPLM.plmapp.tasks import update_index
from openPLM.plmapp.utils import generate_password
from openPLM.plmapp.exceptions import PermissionError, DeleteFileError
from openPLM.plmapp.controllers.base import Controller, permission_required

NEW_ACCOUNT_SUBJECT = u"New account on OpenPLM"

class UserController(Controller):
    u"""
    Object used to manage a :class:`~django.contrib.auth.models.User` and store his
    modification in a history

    :attributes:
        .. attribute:: object

            The :class:`~django.contrib.auth.models.User` managed by the controller

    :param obj: managed object
    :type obj: an instance of :class:`~django.contrib.auth.models.User`
    :param user: user who modify *obj*
    :type user: :class:`~django.contrib.auth.models.User`

    .. note::
        This class does not inherit from :class:`.PLMObjectController`.

    """

    HISTORY = models.UserHistory

    __slots__ = Controller.__slots__ + ("creator", "owner",)

    def __init__(self, obj, user, block_mails=False, no_index=False):
        super(UserController, self).__init__(obj, user, block_mails, no_index)
        self.creator = obj
        self.owner = obj

    @classmethod
    def load(cls, type, reference, revision, user):
        return cls(get_object_or_404(models.User, username=reference), user)

    def get_verbose_name(self, attr_name):
        """
        Returns a verbose name for *attr_name*.

        Example::

            >>> ctrl.get_verbose_name("rank")
            u'role in PLM'
        """

        try:
            item = unicode(self.object._meta.get_field(attr_name).verbose_name)
        except FieldDoesNotExist:
            names = {
                     "rank" : _("role in PLM"),
                     "creator" : _("creator"),
                     "owner" : _("owner")}
            item = names.get(attr_name, attr_name)
        return item

    def update_from_form(self, form):
        u"""
        Updates :attr:`object` from data of *form*

        This method raises :exc:`ValueError` if *form* is invalid.
        """
        self.check_update_data()
        if form.is_valid():
            new_avatar = False
            previous_avatar = self.profile.avatar.path if self.profile.avatar else False
            if self._user != self.object:
                # to an user who has not yet logged in,
                # it is quite surprising to receive a mail saying something
                # has been modified
                self.block_mails()
            need_save = False
            for key, value in form.cleaned_data.iteritems():
                if key not in ("username", "avatar"):
                    setattr(self, key, value)
                    need_save = True
            avatar = form.cleaned_data["avatar"]
            if avatar:
                self.profile.avatar = avatar
                need_save = new_avatar = True

            if need_save:
                self.save()
            if new_avatar and previous_avatar:
                os.remove(previous_avatar)
        else:
            raise ValueError("form is invalid")

    def check_update_data(self):
        try:
            self.check_permission(models.ROLE_OWNER)
        except PermissionError as e:
            # its sponsor has permission to edit this form
            # if the user has not yet logged in
            try:
                link = models.DelegationLink.current_objects.get(delegator=self._user,
                    delegatee=self.object, role=models.ROLE_SPONSOR)
            except models.DelegationLink.DoesNotExist:
                raise e
            if self.object.last_login >= link.ctime:
                raise e

    def can_update_data(self):
        # for templates
        try:
            self.check_update_data()
        except PermissionError:
            can = False
        else:
            can = True
        return can

    def __setattr__(self, attr, value):
        # we override this method to make it to modify *object* directly
        # (or its profile)
        # if we modify *object*, we records the modification in **_histo*
        if hasattr(self, "object"):
            obj = object.__getattribute__(self, "object")
            profile = obj.profile
        else:
            obj = None
        if obj and (hasattr(obj, attr) or hasattr(profile, attr)) and \
           not attr in self.__slots__:
            obj2 = obj if hasattr(obj, attr) else profile
            old_value = getattr(obj2, attr)
            setattr(obj2, attr, value)
            # since x.verbose_name is a proxy methods, we need to get a real
            # unicode object (with capitalize)
            field = obj2._meta.get_field(attr).verbose_name.capitalize()
            if old_value != value:
                message = "%(field)s : changes from '%(old)s' to '%(new)s'" % \
                        {"field" : field, "old" : old_value, "new" : value}
                self._histo += message + "\n"
        else:
            super(UserController, self).__setattr__(attr, value)

    def __getattr__(self, attr):
        # we override this method to get attributes from *object* directly
        # (or its profile)
        obj = object.__getattribute__(self, "object")
        profile = obj.profile
        if hasattr(self, "object") and hasattr(obj, attr) and \
           not attr in self.__slots__:
            return getattr(obj, attr)
        elif hasattr(profile, attr) and not attr in self.__slots__:
            return getattr(profile, attr)
        else:
            return object.__getattribute__(self, attr)

    def save(self, with_history=True):
        u"""
        Saves :attr:`object` and records its history in the database.
        If *with_history* is False, the history is not recorded.
        """
        self.object.profile.save()
        super(UserController, self).save(with_history)
        update_index.delay("auth", "user", self.object.pk)

    def has_permission(self, role):
        if role == models.ROLE_OWNER:
            return self.object == self._user
        return False

    def get_object_user_links(self):
        """
        Returns all :class:`.Part` attached to :attr:`object`.
        """
        return self.plmobjectuserlink_user.now()

    @permission_required(role=models.ROLE_OWNER)
    def delegate(self, user, role):
        """
        Delegates role *role* to *user*.

        Possible values for *role* are:
            ``'notified'``
                valid for all users
            ``'owner'``
                valid only for contributors and administrators
            :samp:``'sign_{x}_level'``
                valid only for contributors and administrators
            ``'sign*'``
                valid only for contributors and administrators, means all sign
                roles that :attr:`object` has.

        :raise: :exc:`.PermissionError` if *user* can not have the role *role*
        :raise: :exc:`ValueError` if *user* is :attr:`object`
        """
        if user == self.object:
            raise ValueError("Bad delegatee (self)")
        if not user.is_active:
            raise ValueError("User account is inactive")
        if self._user.profile.restricted:
            raise PermissionError("A restricted account can not delegate a right")
        if user.profile.restricted:
            raise PermissionError("%s can not have role %s" % (user, role))
        if user.profile.is_viewer and role != 'notified':
            raise PermissionError("%s can not have role %s" % (user, role))
        if self.object.profile.is_viewer and role != 'notified':
            raise PermissionError("%s can not have role %s" % (self.object, role))
        if role == "sign*":
            qset = models.PLMObjectUserLink.current_objects.filter(user=self.object,
                        role__startswith="sign_").only("role")
            roles = set(link.role for link in qset)
        else:
            roles = [role]
        for r in roles:
            models.DelegationLink.current_objects.get_or_create(delegator=self.object,
                        delegatee=user, role=r)
        details = "%(delegator)s delegated the role %(role)s to %(delegatee)s"
        details = details % dict(role=role, delegator=self.object,
                                 delegatee=user)
        self._save_histo(models.DelegationLink.ACTION_NAME, details)

    @permission_required(role=models.ROLE_OWNER)
    def remove_delegation(self, delegation_link):
        """
        Removes a delegation (*delegation_link*). The delegator must be
        :attr:`object`, otherwise a :exc:`ValueError` is raised.
        """
        if delegation_link.delegator != self.object:
            raise ValueError("%s is not the delegator of %s" % (self.object, ValueError))
        details = "%(delegator)s removed his delegation for the role %(role)s to %(delegatee)s"
        details = details % dict(role=delegation_link.role, delegator=self.object,
                                 delegatee=delegation_link.delegatee)
        self._save_histo(models.DelegationLink.ACTION_NAME, details)
        delegation_link.end()

    def get_user_delegation_links(self):
        """
        Returns all delegatees of :attr:`object`.
        """
        return self.delegationlink_delegator.now().order_by("role", "delegatee__username")

    def get_sponsor_subject(self, new_user):
        subject = getattr(settings, "NEW_ACCOUNT_SUBJECT", NEW_ACCOUNT_SUBJECT)
        return Template(subject).render(Context(dict(new_user=new_user, sponsor=self._user)))

    @permission_required(role=models.ROLE_OWNER)
    def sponsor(self, new_user, is_contributor=True, restricted=False):
        self.check_contributor()
        if is_contributor and restricted:
            raise ValueError("An restricted account can not be a contributor account")
        email = new_user.email
        try:
            # checks *email*
            if settings.RESTRICT_EMAIL_TO_DOMAINS:
                # i don't know if a domain can contains a '@'
                domain = email.rsplit("@", 1)[1]
                if domain not in Site.objects.values_list("domain", flat=True):
                    raise PermissionError("Email's domain not valid")
        except AttributeError:
            # restriction disabled if the setting is not set
            pass
        password = generate_password()
        new_user.set_password(password)
        new_user.save()
        new_user.profile.is_contributor = is_contributor
        new_user.profile.restricted = restricted
        new_user.profile.save()
        link = models.DelegationLink(delegator=self._user, delegatee=new_user,
                role=models.ROLE_SPONSOR)
        link.save()
        ctx = {
                "new_user" : new_user,
                "sponsor" : self._user,
                "password" : password,
               }
        update_index.delay("auth", "user", new_user.pk)
        self._send_mail(send_mail, self.get_sponsor_subject(new_user), [new_user],
                ctx, "mails/new_account")
        models.UserHistory.objects.create(action="Create", user=self._user,
                plmobject=self._user, details="New user: %s" % new_user.username)
        models.UserHistory.objects.create(action="Create", user=self._user,
                plmobject=new_user, details="Account created")

    @permission_required(role=models.ROLE_OWNER)
    def resend_sponsor_mail(self, new_user):
        try:
            link = models.DelegationLink.current_objects.get(delegator=self._user,
                delegatee=new_user, role=models.ROLE_SPONSOR)
        except models.DelegationLink.DoesNotExist:
            raise PermissionError("You did not sponsored %s"
                    % new_user.username)
        # checks that new_user did not logged on openPLM to not
        # reset its password
        if new_user.last_login >= link.ctime:
            raise ValueError("Can not resend a sponsor mail:"
                    "%s has already logged on openPLM" % new_user)
        # generate a new password
        password = generate_password()
        new_user.set_password(password)
        new_user.save()
        # send a mail
        ctx = {
                "new_user" : new_user,
                "sponsor" : self._user,
                "password" : password,
               }
        self._send_mail(send_mail, self.get_sponsor_subject(new_user), [new_user],
                ctx, "mails/new_account")

    def check_readable(self, raise_=True):
        if self._user.profile.restricted:
            if self._user.id != self.object.id:
                if raise_:
                    raise PermissionError("You can not see this user account")
                return False
        return True

    def add_file(self, f):
        """
        Adds private file *f*. *f* should be a :class:`~django.core.files.File`
        with an attribute *name* (like an :class:`UploadedFile`).

        :return: the :class:`.PrivateFile` created.
        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
              :attr:`object`
        :raises: :exc:`ValueError` if the file size is superior to
                 :attr:`settings.MAX_FILE_SIZE`
        """
        self.check_permission("owner")
        self.check_contributor()

        if settings.MAX_FILE_SIZE != -1 and f.size > settings.MAX_FILE_SIZE:
            raise ValueError("File too big, max size : %d bytes" % settings.MAX_FILE_SIZE)

        f.name = f.name.encode("utf-8")
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
        doc_file = models.PrivateFile.objects.create(filename=f.name, size=size,
                        file=models.docfs.save(f.name,f), creator=self.object)
        self.save(False)
        # set read only file
        os.chmod(doc_file.file.path, 0400)
        # no history!
        return doc_file

    def delete_file(self, doc_file):
        """
        Deletes *doc_file*, the file attached to *doc_file* is physically
        removed.

        :exceptions raised:
            * :exc:`ValueError` if *doc_file*.creator is not self.object
            * :exc:`plmapp.exceptions.DeleteFileError` if *doc_file* is
              locked
            * :exc:`.PermissionError` if :attr:`_user` is not the owner of
              :attr:`object`

        :param doc_file: the file to be deleted
        :type doc_file: :class:`.PrivateFile`
        """

        self.check_permission("owner")
        if doc_file.creator != self.object:
            raise PermissionError("Not your file")
        path = os.path.realpath(doc_file.file.path)
        if not path.startswith(settings.DOCUMENTS_DIR):
            raise DeleteFileError("Bad path : %s" % path)
        os.chmod(path, 0700)
        os.remove(path)
        doc_file.delete()

    def update_file(self, formset):
        u"""
        Updates uploaded file informations with data from *formset*

        :param formset:
        :type formset: a modelfactory_formset of
                        :class:`~plmapp.forms.ModifyFileForm`
        :raises: :exc:`.PermissionError` if :attr:`_user` is not the owner of
              :attr:`object`
        """

        self.check_permission("owner")
        if formset.is_valid():
            for form in formset.forms:
                creator = form.cleaned_data["creator"]
                if creator.pk != self.object.pk:
                    raise ValueError("Not your file")
                delete = form.cleaned_data["delete"]
                filename = form.cleaned_data["id"]
                if delete:
                    self.delete_file(filename)


