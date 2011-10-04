from django import template
from django.contrib.auth.models import User

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
        return isinstance(child, User)
 
    return False
