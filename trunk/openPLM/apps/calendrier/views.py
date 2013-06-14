from calendar import HTMLCalendar
from datetime import date, MAXYEAR
from itertools import groupby
# the datetime strftime() methods require year >= 1900
MINYEAR = 1900

from django.utils.dates import WEEKDAYS
from django.utils.html import conditional_escape as esc
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

try:
    from django_ical.views import ICalFeed
    from openPLM.apps.rss.feeds import RssFeed, TimelineRssFeed
    ICAL_INSTALLED = True
except ImportError:
    ICAL_INSTALLED = False

from openPLM.plmapp.views.base import handle_errors, get_generic_data
from openPLM.plmapp.utils import r2r
from openPLM.plmapp.views import display_object_history
from openPLM.plmapp import models

def parse_date(year, month):
    """ Parse *year* and *month* (string, integer or None) and
    returns a tuple of int (*year*, *month*).

    If *year* is None, the current year is returned.
    If *month* is None, the current month is returned.

    :raise: :exc:`.ValueError` if *year* < 1900, *year* > 9999,
        *month* < 1, *month* > 12 or *month* and *year* can not
        be converted to an integer or (*year* == 9999 and *month* == 12)
    """
    if year is not None:
        year = int(year)
    else:
        year = date.today().year
    if month is not None:
        month = int(month)
    else:
        month = date.today().month
    if (year < MINYEAR or year > MAXYEAR or month < 1 or month > 12
        or (year == MAXYEAR and month == 12)):
        raise ValueError("Month or year are out of range")
    return year, month

# inspired by http://uggedal.com/journal/creating-a-flexible-monthly-calendar-in-django/
# by Eivind Uggedal

class HistoryCalendar(HTMLCalendar):

    def __init__(self, histories):
        super(HistoryCalendar, self).__init__()
        self.histories = self.group_by_day(histories)

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            if date.today() == date(self.year, self.month, day):
                cssclass += ' today'
            if day in self.histories:
                cssclass += ' filled'
                body = ['<ul>']
                for history in self.histories[day]:
                    body.append('<li>')
                    body.append('<a href="%s">' % history.get_redirect_url()),
                    body.append(self.format_hline(history))
                    body.append('</a></li>')
                body.append('</ul>')
                return self.day_cell(cssclass, '<div class="daynumber">%d</div>%s' % (day, ''.join(body)))
            else:
                cssclass += ' empty'
            return self.day_cell(cssclass,'<div class="daynumber">%d</div>' % day)
        return self.day_cell('noday', '&nbsp;')

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super(HistoryCalendar, self).formatmonth(year,
                month).replace('class="month"', 'class="month Content"')

    def formatmonthname(self, *args, **kwargs):
        return ""

    def formatweekday(self, day):
        """
        Return a weekday name as a table header.
        """
        return '<th class="%s">%s</th>' % (self.cssclasses[day],
                WEEKDAYS[day].capitalize())

    def formatweekheader(self):
        """
        Return a header for a week as a table row.
        """
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return '<tr><th class="weeknumber"></th>%s</tr>' % s

    def formatweek(self, theweek):
        """
        Return a complete week as a table row.
        """
        first_day = date(self.year, self.month,
            [d[0] for d in theweek if d[0] != 0][0])
        week_number = int(first_day.strftime("%W"))
        w = '<td class="weeknumber">%d</td>' % week_number
        s = ''.join(self.formatday(d, wd) for (d, wd) in theweek)
        return '<tr>%s%s</tr>' % (w, s)

    def group_by_day(self, histories):
        field = lambda history: history.date.day
        return dict(
            [(day, list(items)) for day, items in groupby(histories, field)]
        )

    def day_cell(self, cssclass, body):
        return '<td class="%s">%s</td>' % (cssclass, body)

    def format_hline(self, history):
        return esc(history.action)

class RevisionHistoryCalendar(HistoryCalendar):

    def format_hline(self, history):
        return u'<span class="revision">%s</span>&nbsp;// %s' % (esc(history.plmobject.revision),
                esc(history.action))

class TimelineCalendar(HistoryCalendar):

    def group_by_day(self, histories):
        histories = super(TimelineCalendar, self).group_by_day(histories)
        # keep one history per day
        for l in histories.itervalues():
            added_plmobjects = set()
            unique_histories = []
            for h in l:
               if h.plmobject_id not in added_plmobjects:
                   unique_histories.append(h)
                   added_plmobjects.add(h.plmobject_id)
            l[:] = unique_histories
        return histories

    def format_hline(self, history):
        return history.title

@handle_errors
def history_calendar(request, year=None, month=None, obj_type="-", obj_ref="-", obj_revi="-", timeline=False):
    """
    Calendar view.

    This view displays a history of the selected object and its revisions.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/history/calendar/[{year}/][{month}/]`
    :url: :samp:`/user/{username}/history/calendar/[{year}/][{month}/]``
    :url: :samp:`/group/{group_name}/history/calendar/[{year}/][{month}/]``
    :url: :samp:`/timeline/calendar/[{year}/][{month}/]``

    .. include:: ../../modules/views_params.txt

    **Template:**

    :file:`calendar.html`

    **Context:**

    ``RequestContext``

    ``calendar``
        the HTML calendar

    ``year``
        the given year (or the current year if not given)

    ``month``
        the given month (or the current month if not given)

    ``current_month``, ``next_month``, ``previous_month``
        :class:`.datetime.date` objects representing the current, next and previous
        months (may be None if the date is 1900/01 or 9999/12).

    ``ical_installed``
        True if django-ical is installed and iCalendar file can be generated

    ``prefix_url``
        a prefix to prepend to the url to go to the next and previous monthes.
        (can be ``""``, ``"../"`` or ``"../../"``).
    """

    prefix = ""
    if year is not None:
        prefix = "../"
    if month is not None:
        prefix += "../"

    year, month = parse_date(year, month)

    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if timeline:
        hcls = TimelineCalendar
        histories = models.timeline_histories(request.user, None, None, None, None)
        ctx['object_type'] = _("Timeline")
    elif hasattr(obj, "get_all_revisions"):
        # display history of all revisions
        histories = obj.histories
        hcls = RevisionHistoryCalendar
    else:
        histories = obj.histories
        hcls = HistoryCalendar
    histories = histories.filter(date__year=year, date__month=month).order_by("date")
    cal = hcls(histories).formatmonth(year, month)

    current_month = date(year=year, month=month, day=1)
    if month == 1:
        if year == MINYEAR:
            previous_month = None
        else:
            previous_month = date(year=year - 1, month=12, day=1)
    else:
        previous_month = date(year=year, month=month - 1, day=1)
    if month == 12:
        if year == MAXYEAR:
            next_month = None
        else:
            next_month = date(year=year + 1, month=1, day=1)
    elif month == 11 and year == MAXYEAR:
        next_month = None
    else:
        next_month = date(year=year, month=month + 1, day=1)

    ctx.update({
        'current_page' : 'history',
        'calendar' : mark_safe(cal),
        'year' : year,
        'month' : month,
        'current_month' : current_month,
        'next_month' : next_month,
        'previous_month' : previous_month,
        'prefix_url' : prefix,
        'ical_installed' : ICAL_INSTALLED,
        })
    return r2r('calendar.html', ctx, request)


HISTORY_TPL = "history_cal.html"
def history(request, *args, **kwargs):
    """A simple view that wraps :func:`.display_object_history`
    to use the template :file:`history_cal.html`"""
    kwargs["template"] = HISTORY_TPL
    return display_object_history(request, *args, **kwargs)

if ICAL_INSTALLED:
    class CalendarFeed(RssFeed, ICalFeed):

        def get_object(self, request, year=None, month=None, obj_type="-", obj_ref="-", obj_revi="-"):
            year, month = parse_date(year, month)
            obj = super(CalendarFeed, self).get_object(request, obj_type, obj_ref, obj_revi)
            obj.object.h_month = month
            obj.object.h_year = year
            return obj

        def items(self, obj):
            year = obj.h_year
            month = obj.h_month
            return obj.histories.filter(date__year=year, date__month=month).order_by("date")


        def item_title(self, item):
            if hasattr(item.plmobject, 'is_part'):
                return u"%s // %s // %s - %s" % (item.plmobject.type,
                    item.plmobject.reference, item.plmobject.revision,
                    item.action)
            elif hasattr(item.plmobject, 'username'):
                return u"%s %s (%s) - %s" % (item.plmobject.first_name,
                        item.plmobject.last_name, item.plmobject.username,
                        item.action)
            else:
                return u"Group %s - %s" % (item.plmobject.name, item.action)

        def item_start_datetime(self, item):
            return item.date

    class TimelineCalendarFeed(TimelineRssFeed, ICalFeed):

        def get_object(self, request, year=None, month=None):
            year, month = parse_date(year, month)
            obj = request.user
            obj.h_month = month
            obj.h_year = year
            return obj

        def items(self, obj):
            year = obj.h_year
            month = obj.h_month
            return models.timeline_histories(obj, None, None, None, None).filter(date__year=year, date__month=month).order_by("date")

        def item_title(self, item):
            return strip_tags(item.title)

        def item_start_datetime(self, item):
            return item.date

