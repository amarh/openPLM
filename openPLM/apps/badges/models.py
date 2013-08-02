from django.utils import timezone

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from signals import badge_awarded
from managers import BadgeManager
from middleware import get_request

from openPLM.plmapp.models import UserProfile


_menu_items = UserProfile.menu_items

def menu_items(self):
    return _menu_items.fget(self) + ["badges"]

UserProfile.menu_items = property(menu_items)


if hasattr(settings, 'BADGE_LEVEL_CHOICES'):
    LEVEL_CHOICES = settings.BADGE_LEVEL_CHOICES
else:
    LEVEL_CHOICES = (
        ("1", "Bronze"),
        ("2", "Silver"),
        ("3", "Gold"),
        ("4", "Diamond"),
    )

class Badge(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    user = models.ManyToManyField(User, related_name="badges", through='BadgeToUser')
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES)

    icon = models.ImageField(upload_to='badge_images')

    objects = BadgeManager()

    @property
    def meta_badge(self):
        from utils import registered_badges
        return registered_badges[self.id]

    @property
    def title(self):
        return self.meta_badge.title

    @property
    def description(self):
        return self.meta_badge.description

    @property
    def link(self):
        """
        Returns a link to the user documentation if link_to_doc is set in the meta_badge.
        """
        if self.meta_badge.link_to_doc:
            return "%s%s" %(settings.DOCUMENTATION_URL, self.meta_badge.link_to_doc)
        else:
            return None

    def __unicode__(self):
        return u"%s" % self.title

    def get_absolute_url(self):
        return reverse('badge_detail', kwargs={'slug': self.id})

    def award_to(self, user, ignore_message=False):
        request = get_request()
        if request is None or request.user != user:
            return False
        has_badge = user.badges.filter(id=self.id).exists()
        if self.meta_badge.one_time_only and has_badge:
            return False
        if self.meta_badge.get_progress_percentage(user=user) < 100 :
            return False

        BadgeToUser.objects.create(badge=self, user=user)

        badge_awarded.send(sender=self.meta_badge, user=user, badge=self)

        if not ignore_message:
            message_template = _(u"You just got the %s Badge!")
            if request is not None:
                messages.info(request, message_template % self.title)

        return BadgeToUser.objects.filter(badge=self, user=user).count()

    def number_awarded(self, user_or_qs=None):
        """
        Gives the number awarded total. Pass in an argument to
        get the number per user, or per queryset.
        """
        kwargs = {'badge':self}
        if user_or_qs is None:
            pass
        elif isinstance(user_or_qs, User):
            kwargs.update(dict(user=user_or_qs))
        else:
            kwargs.update(dict(user__in=user_or_qs))
        return BadgeToUser.objects.filter(**kwargs).count()


class BadgeToUser(models.Model):
    badge = models.ForeignKey(Badge)
    user = models.ForeignKey(User)

    created = models.DateTimeField(default=timezone.now)
