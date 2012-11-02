from calendar import HTMLCalendar
from datetime import date, MAXYEAR
from itertools import groupby
# the datetime strftime() methods require year >= 1900
MINYEAR = 1900

from django.db.models import Q
from django.conf import settings
from django.utils.dates import WEEKDAYS
from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp.base_views import handle_errors, get_generic_data
from openPLM.plmapp.views.main import r2r, display_object_history
from openPLM.plmapp import models

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
        p = history.plmobject
        return u'''<span class="type">%s</span>&nbsp;//
<span class="reference">%s</span>&nbsp;//
<span class="revision">%s</span>''' % (esc(p.type), esc(p.reference), esc(p.revision))

@handle_errors
def history_calendar(request, year=None, month=None, obj_type="-", obj_ref="-", obj_revi="-", timeline=False):
    """
    History view.
    
    This view displays a history of the selected object and its revisions.

    :url: :samp:`/object/{obj_type}/{obj_ref}/{obj_revi}/history/`
    :url: :samp:`/user/{username}/history/`
    :url: :samp:`/group/{group_name}/history/`
    :url: :samp:`/timeline/`
    
    .. include:: views_params.txt 

    **Template:**
    
    :file:`attribute.html`

    **Context:**

    ``RequestContext``

    ``object_history``
        list of :class:`.AbstractHistory`

    ``show_revisions``
        True if the template should show the revision of each history row
    
    ``show_identifiers``
        True if the template should show the type, reference and revision
        of each history row
    """

    prefix = ""
    if year is not None:
        prefix = "../"
        year = int(year)
    else:
        year = date.today().year
        
    if month is not None:
        prefix += "../"
        month = int(month)
    else:
        month = date.today().month
  
    if year < MINYEAR or year > MAXYEAR or month < 1 or month > 12:
        return ValueError("Month or year are out of range")

    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if timeline:
        hcls = TimelineCalendar
        # global timeline: shows objects owned by the company and readable objects
        q = Q(plmobject__owner__username=settings.COMPANY)
        q |= Q(plmobject__group__in=request.user.groups.all())
        history = models.History.objects.filter(q)
        history = history.select_related("plmobject__type", "plmobject__reference",
            "plmobject__revision")
        ctx['object_type'] = _("Timeline")
    elif hasattr(obj, "get_all_revisions"):
        # display history of all revisions
        objects = [o.id for o in obj.get_all_revisions()]
        history = obj.HISTORY.objects.filter(plmobject__in=objects)
        history = history.select_related("plmobject__revision")
        hcls = RevisionHistoryCalendar
    else:
        history = obj.HISTORY.objects.filter(plmobject=obj.object)
        hcls = HistoryCalendar
    history = history.order_by('date').filter(
        date__year=int(year), date__month=month
        )
    cal = hcls(history).formatmonth(year, month)

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
        })
    return r2r('calendar.html', ctx, request)


HISTORY_TPL = "history_cal.html"
def history(request, *args, **kwargs):
    kwargs["template"] = HISTORY_TPL
    return display_object_history(request, *args, **kwargs)


