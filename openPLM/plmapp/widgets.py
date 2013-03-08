from django import forms
from django.forms.widgets import flatatt
from django.utils.encoding import smart_unicode
from django.utils.html import escape
from json import JSONEncoder
from django.utils.safestring import mark_safe

class JQueryAutoComplete(forms.TextInput):
    def __init__(self, source, options={}, attrs={}):
        """
        A :class:`TextInput` widget that enable auto completion through JQuery.

        *source* can be a list containing the autocomplete values or a
        string containing the url used for the XHR request.

        For available options see the autocomplete sample page::
        http://jquery.bassistance.de/autocomplete/"""

        self.options = {}
        self.attrs = {'autocomplete': 'off'}
        self.source = source
        if isinstance(source, basestring):
            self.source = escape(source)
        if options:
            self.options = options
        self.attrs.update(attrs)

    def render_js(self, field_id):
        data = self.options.copy()
        data["source"] = self.source
        args = JSONEncoder().encode(data)
        return u'$(\'#%s\').autocomplete(%s);' % (field_id, args)

    def render(self, name, value=None, attrs=None):
        final_attrs = self.build_attrs(attrs, name=name)
        if value:
            final_attrs['value'] = escape(smart_unicode(value))

        if not self.attrs.has_key('id'):
            final_attrs['id'] = 'id_%s' % name

        # I added here the mark_safe in order to prevent escaping:
        return mark_safe(u'''<input type="text" %(attrs)s/>
                <script type="text/javascript"><!--//
                %(js)s//--></script>
                ''' % {
                    'attrs' : flatatt(final_attrs),
                    'js' : self.render_js(final_attrs['id']),
                })


class MarkdownWidget(forms.Textarea):
    class Media:
        css = {
            'all': ('css/jquery.markedit.css',)
        }
        js = ('js/showdown.js', 'js/jquery.markedit.js', )

    def __init__(self):
        super(MarkdownWidget, self).__init__()
        self.attrs["class"] = "markedit"


