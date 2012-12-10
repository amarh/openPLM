import re

from django import template
from django.contrib.auth.models import User, Group
from django.template import Node, resolve_variable

from haystack.models import SearchResult

from openPLM.plmapp.controllers import (DocumentController, PartController,
        UserController, GroupController)
from openPLM.plmapp import models
from openPLM.plmapp.utils import get_pages_num


register = template.Library()

@register.filter
def can_add(obj, arg):
    """
    Test if an object can be linked to the current object.
    
    :param obj: object to test
    :type obj: it can be an instance of :class:`.DocumentFile`, :class:`.Part` or :class:`.UserController`
    
    :param arg: arguments here are the current object and the action for link creation
    
    :return: True if the action can be processed on the current object
    """
   
    # TODO: replace this with the callable (cur_obj.can_attach_document...)
    cur_obj, action = arg

    if isinstance(obj, models.DocumentFile):
        obj = obj.document
    if action == "attach_doc":
        return cur_obj.can_attach_document(obj)
    elif action == "attach_part":
        return cur_obj.can_attach_part(obj)
    elif action == "add_child":
        return cur_obj.can_add_child2(obj)
    elif action == "add_alternate":
        # FIXME: can_add_alternate is slow
        # something like can_add_chil2 could improve performance (less queries)
        return cur_obj.can_add_alternate(obj)
    elif action == "delegate" or (action.startswith("add_") and action != "add_reader"):
        if isinstance(obj, (User, UserController)):
            if not obj.is_active:
                return False
            if obj.get_profile().restricted:
                return False
            if hasattr(cur_obj, "check_in_group"):
                from django.conf import settings
                if obj.username == settings.COMPANY:
                    return False
                if cur_obj.check_in_group(obj):
                    if action.startswith("add_"):
                        role = action[4:]
                        return not cur_obj.plmobjectuserlink_plmobject.now().filter(user=obj,
                            role=role).exists()
                    return True
            return True
    elif action in ("delegate-reader", "add_reader"):
        if isinstance(obj, (User, UserController)):
            if not obj.is_active:
                return False
            if obj.get_profile().restricted:
                if action == "add_reader":
                    return not cur_obj.plmobjectuserlink_plmobject.now().filter(user=obj,
                            role=models.ROLE_READER).exists()
                return True
    return False

@register.filter
def can_add_type(parent_type, child_type):
    """
    Used in Bom View.
    
    :param parent_type: Type of the parent, the current part
    :param child_type: type of the object that may be added as child
    
    :return: True if child_type is a type of object that can be added to parent_type
    """
    part_types = models.get_all_parts()
    return parent_type in part_types and child_type in part_types

@register.filter    
def can_link(current_type, suggested_type):
    """
    Used in Doc-Parts views.
    
    :param current_type: type of the current object (part or document)
    :param suggested_type: type of the object that may be attached to the current one
    
    :return: True if current_type is a type of object that can be attached to current_type object
    """
    doc_types = models.get_all_documents()
    part_types = models.get_all_parts()
    return ((current_type in doc_types and suggested_type in part_types) or
            (current_type in part_types and suggested_type in doc_types))
    
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
                classes.discard("ui-button-text-only")
            if opt.startswith("corner"):
                classes.discard("ui-corner-all")
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

def indice(l, index):
    return l[index]

indice = register.filter('indice', indice)

def attr(o, attr_name):
    from django.conf import settings
    return getattr(o, attr_name, settings.TEMPLATE_STRING_IF_INVALID)
attr = register.filter('attr', attr)

@register.filter
def is_plmobject(result):
    """
    Returns True if the object behind *result* is an instance of :class:`.PLMObject`
    """
    return issubclass(result.model, models.PLMObject)

@register.filter
def is_documentfile(result):
    """
    Returns True if the object behind *result* is an instance of :class:`.DocumentFile`
    """
    return issubclass(result.model, models.DocumentFile)

@models.cache_lifecycle_stuff
def get_state_class(plmobject):
    """
    Returns the state class ("cancelled", "draft", "proposed", "official",
    or "deprecated") of *plmobject*.
    """
    state, lifecycle = (plmobject.state_id, plmobject.lifecycle_id)
    if lifecycle == models.get_cancelled_lifecycle().name:
        return "cancelled"
    lc = models.Lifecycle.objects.get(name=lifecycle)
    if state == lc.official_state_id:
        return "official"
    if state == lc.first_state.name:
        return "draft"
    if state == lc.last_state.name:
        return "deprecated"
    return "proposed"

@register.filter
def result_class(result):
    """
    Returns a css class according to result.
    """
    if result.state_class:
        return result.state_class
    if issubclass(result.model, (models.PLMObject, models.DocumentFile)):
        result.state_id = result.state
        result.lifecycle_id = result.lifecycle
        if result.state_id and result.lifecycle_id:
            return "state-" + get_state_class(result)
    return ""

# yes, this is a really bad way to detect an email
# but we may have to hide something like user@<em>domain</em>
# it is only use to hide an email
_email_rx = re.compile(r"\b[\w.>_<%+-]+@[\w_<>-]+(\.[\w_><-]+)+\b")
@register.filter
def hide_emails(text):
    """
    Returns *text* with all emails removed.
    """
    from django.conf import settings
    if getattr(settings, "HIDE_EMAILS", False):
        text = _email_rx.sub("", text)
    return text

# from http://djangosnippets.org/snippets/2428/ by naktinis

"""
The tag generates a parameter string in form '?param1=val1&param2=val2'.
The parameter list is generated by taking all parameters from current
request.GET and optionally overriding them by providing parameters to the tag.

This is a cleaned up version of http://djangosnippets.org/snippets/2105/. It
solves a couple of issues, namely:
 * parameters are optional
 * parameters can have values from request, e.g. request.GET.foo
 * native parsing methods are used for better compatibility and readability
 * shorter tag name

Usage: place this code in your appdir/templatetags/add_get_parameter.py
In template:
{% load add_get_parameter %}
<a href="{% add_get param1='const' param2=variable_in_context %}">
Link with modified params
</a>

It's required that you have 'django.core.context_processors.request' in
TEMPLATE_CONTEXT_PROCESSORS

Original version's URL: http://django.mar.lt/2010/07/add-get-parameter-tag.html
"""

class AddGetParameter(Node):
    def __init__(self, values):
        self.values = values
        
    def render(self, context):
        req = resolve_variable('request', context)
        params = req.GET.copy()
        for key, value in self.values.items():
            params[key] = value.resolve(context)
        return '?%s' %  params.urlencode()


@register.tag
def add_get(parser, token):
    pairs = token.split_contents()[1:]
    values = {}
    for pair in pairs:
        s = pair.split('=', 1)
        values[s[0]] = parser.compile_filter(s[1])
    return AddGetParameter(values)


@register.inclusion_tag('snippets/pagination.html')
def show_pages_bar(page, request):
    return {
            "objects" : page,
            "request" : request,
            "pages" : get_pages_num(page.paginator.num_pages, page.number),
            }


class IsObjectReadableNode(template.Node):
    def render(self, context):
        obj = context["object"]
        try:
            user = context["request"].user
            context["is_object_readable"] = is_readable(obj, user)
        except KeyError, AttributeError:
            context["is_object_readable"] = True
        return ''

def do_is_object_readable(parser, token):
    try:
        tag_name, = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires no arguments" % token.contents.split()[0]
    return IsObjectReadableNode()    
register.tag('is_object_readable', do_is_object_readable)

@register.filter
def is_readable(obj, user):
    from django.conf import settings
    if user.username == settings.COMPANY:
        return True
    # plmobjects are readable if:
    #  * they are official, deprecated or cancelled
    #  * user is their owner
    #  * user is in their group
    if isinstance(obj, models.PLMObject):
        if obj.is_official or obj.is_deprecated or obj.is_cancelled:
            return True
        if obj.owner_id == user.id:
            return True
        if not hasattr(user, "group_ids"):
            # cache group ids as it may be used to test another object
            # in the page
            user.group_ids = set(user.groups.all().values_list("id", flat=True))
        return obj.group_id in user.group_ids
    elif isinstance(obj, SearchResult):
        if is_plmobject(obj) or is_documentfile(obj):
            if not hasattr(user, "group_names"):
                user.group_names = set(user.groups.all().values_list("name", flat=True))
        if is_plmobject(obj):
            state_class = result_class(obj)
            if state_class in ("state-official", "state-deprecated", "state-cancelled"):
                return True
            if obj.owner == user.username:
                return True
            if obj.group is None:
                try:
                    gr = models.PLMObject.objects.filter(id=obj.pk).values_list("group__name", flat=True)[0]
                except IndexError: # deleted object, not yet unindexed
                    return False
                return gr in user.group_names
            return obj.group in user.group_names
        elif is_documentfile(obj):
            if obj.group:
                if obj.group in user.group_names:
                    return True
                else:
                    # the document may be official, deprecated...
                    s, l = (models.PLMObject.objects.filter(id=obj.document_id)
                            .values_list("state", "lifecycle"))[0]
                    obj.state_id = s
                    obj.lifecycle_id = l
                    return get_state_class(obj) in ("official", "deprecated",
                            "cancelled")
            # document file indexed before the revision [1848]
            if obj.object is None: # deleted object
                return False
            doc = obj.object.document
            return is_readable(doc, user)

    # other objects: readable
    return True

@register.filter
def main_type(obj):
    if isinstance(obj, (models.User, UserController)):
        return "user"
    if isinstance(obj, (models.Part, PartController)):
        return "part"
    if isinstance(obj, (models.Document, DocumentController)):
        return "document"
    if isinstance(obj,(models.Group, GroupController)):
        return "group"
    if hasattr(obj, "has_key") and "type" in obj:
        if obj["type"] in models.get_all_parts():
            return "part"
        if obj["type"] in models.get_all_documents():
            return "document"
        return obj["type"]
    return ""

