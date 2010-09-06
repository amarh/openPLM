from django import template

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


