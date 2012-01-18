from django import template
from django.contrib.auth.models import User
from openPLM.plmapp.controllers.user import UserController

register = template.Library()

# from http://djangosnippets.org/snippets/1471/
@register.filter
def trunc(string, number, dots='...'):
    """ 
    truncate the {string} to {number} characters
    print {dots} on the end if truncated

    usage: {{ "some text to be truncated"|trunc:6 }}
    results: some te...
    """
    if not isinstance(string, basestring): 
        string = unicode(string)
    if len(string) <= number:
        return string
    return string[:number]+dots

@register.filter
def can_add(child, arg):
    parent, action = arg

    if action == "attach_doc":
        return parent.can_attach_document(child)
    elif action == "attach_part":
        return parent.can_attach_part(child)
    elif action == "add_child":
        return parent.can_add_child(child)
    elif action == "delegate":
        return isinstance(child, (User, UserController))
 
    return False

@register.filter
def button(css_class, options=""):
    classes = set([css_class, " ui-button", 
            "ui-button-text-only", "ui-widget", "ui-state-default",
            "ui-corner-all"])
    options = options.split(",")
    for opt in options:
        opt = opt.strip()
        if opt:
            if opt.startswith("icon"):
                classes.remove("ui-button-text-only")
            if opt.startswith("corner"):
                classes.remove("ui-corner-all")
            classes.add("ui-" + opt)
    return " ".join(classes)

def key(d, key_name):
    try:
        value = d[key_name]
    except KeyError:
        from django.conf import settings
        value = settings.TEMPLATE_STRING_IF_INVALID
    return value
key = register.filter('key', key)

def attr(o, attr_name):
    from django.conf import settings
    return getattr(o, attr_name, settings.TEMPLATE_STRING_IF_INVALID)
attr = register.filter('attr', attr)

