from django.template import Library
from openPLM.apps.badges.utils import badge_count
from openPLM.apps.badges.models import LEVEL_CHOICES
level_choices = dict(LEVEL_CHOICES)

register = Library()

@register.filter
def is_in(value,arg):
    return value in arg

@register.filter
def level_count(badges, level):
    return badges.filter(level=level).count()

@register.filter
def level_title(level):
    return level_choices[level]

@register.filter('badge_count')
def _badge_count(user_or_qs):
    return badge_count(user_or_qs)

@register.filter
def number_awarded(badge, user_or_qs=None):
    return badge.number_awarded(user_or_qs)
 
@register.filter
def progress_start(badge):
    return badge.meta_badge.progress_start
 
@register.filter
def progress_finish(badge):
    return badge.meta_badge.progress_finish
 
@register.filter
def progress(badge, user):
    return badge.meta_badge.get_progress(user)
 
@register.filter
def is_in_progress(badge, user):
    return 0 < badge.meta_badge.get_progress(user) < progress_finish(badge) 
 
@register.filter
def progress_percentage(badge, user):
    prog = badge.meta_badge.get_progress_percentage(user=user)
    return max(min(prog, 100), 0)
