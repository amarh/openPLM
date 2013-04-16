"""
Copyright 2012 Peter Gebauer
Licensed under GNU GPLv3

General helper functions and classes.
Part of the django-webdav project.
"""
import sys
import os
import logging
import datetime
from django.utils import timezone
from django.http import HttpResponse
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element


class ClassNotFoundException(Exception):
    """
    Raised from the get_class function if unable to import the class.
    """


def get_class(name, raise_on_error = True):
    """
    Import module and return class from module attribute.
    Name arguments is specified using full name, i.e 'pack.mod.ClassName'.
    Raises ClassNotFoundException if import fails or module does not have
    the specified attribute.
    """
    if not name:
        return None
    modname = ".".join(name.split(".")[:-1])
    classname = name.split(".")[-1]
    try:
        __import__(modname)
    except ImportError, ie:
        if raise_on_error:
            raise ClassNotFoundException(ie)
        return None
    except ValueError, ve:
        if raise_on_error:
            raise ClassNotFoundException(ve)
        return None
    mod = sys.modules[modname]
    if hasattr(mod, classname):
        cls = getattr(mod, classname)
        return cls
    if raise_on_error:
        raise ClassNotFoundException("module '%s' has no attribute '%s'"
                                     %(modname, classname))
    return None


def format_http_datetime(dt):
    return dt.strftime('%a, %d %b %Y %H:%M:%S %Z').strip()


def format_iso8601_datetime(dt):
    return dt.strftime('%Y%m%dT%H:%M:%SZ').strip()


def get_propfind_properties_from_xml(xmlstring):
    if not xmlstring:
        return ["{DAV:}getcontentlength", "{DAV:}getlastmodified", "{DAV:}creationdate",
                "{DAV:}resourcetype", "{DAV:}checked-in","{DAV:}checked-out",
                 "{DAV:}supportedlock", "{DAV:}getcontenttype",
                ]
    ret = []
    tree = ET.fromstring(xmlstring)
    props = tree.findall("{DAV:}prop")
    if props:
        for prop in props:
            for child in prop.getchildren():
                name = child.tag
                ret.append(name)
    return ret


_element_type = type(Element("p"))
def add_value_to_element(element, value):
    if value is None:
        return
    setval = ""
    if isinstance(value, (datetime.date, datetime.datetime)):
        setval = format_http_datetime(value)
    elif isinstance(value, bool):
        setval = value and "T" or "F"
    elif isinstance(value, _element_type):
        element.append(value)
    elif isinstance(value, (list, tuple)):
        for v in value:
            add_value_to_element(element, v)
    elif isinstance(value, unicode):
        setval = value.encode("utf-8")
    else:
        setval = str(value)
    if setval:
        if element.text:
            element.text += setval
        else:
            element.text = setval

try:
    register_namespace = ET.register_namespace
except AttributeError:
    def register_namespace(prefix, uri):
        ET._namespace_map[uri] = prefix

def get_multistatus_response_xml(url_prefix, backend_items):
    register_namespace("D", "DAV:")
    root = Element("{DAV:}multistatus")
    if not url_prefix.endswith("/"):
        url_prefix += "/"
    for item in backend_items:
        response = Element("{DAV:}response")
        root.append(response)
        href = Element("{DAV:}href")
        url = ("%s%s"%(url_prefix, item.name)).strip()
        if url.endswith("/"):
            url = url[:-1]
        href.text = url
        response.append(href)

        for propset in item.property_sets:
            if propset:
                propstat = Element("{DAV:}propstat")
                response.append(propstat)
                prop = Element("{DAV:}prop")
                propstat.append(prop)
                for k, v in propset.items():
                    propitem = Element("%s"%k)
                    add_value_to_element(propitem, v)
                    prop.append(propitem)
                status = Element("{DAV:}status")
                status.text ="HTTP/1.1 %s"%propset.status
                propstat.append(status)

    s = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
    s += ET.tostring(root, encoding = "utf-8")
    return s +"\n"


def get_lock_response_xml(lock):
    ET.register_namespace("D", "DAV:")
    root = Element("{DAV:}prop")
    lockdiscovery = Element("{DAV:}lockdiscovery")
    root.append(lockdiscovery)
    activelock = Element("{DAV:}activelock")
    lockdiscovery.append(activelock)
    locktype = Element("{DAV:}locktype")
    locktype.append(Element("{DAV:}write"))
    activelock.append(locktype)
    lockscope = Element("{DAV:}lockscope")
    if lock.get("exclusive"):
        lockscope.append(Element("{DAV:}exclusive"))
    else:
        lockscope.append(Element("{DAV:}shared"))
    activelock.append(lockscope)
    depth = Element("{DAV:}depth")
    depth.text = lock.get("infinite", True) and "Infinity" or "0"
    activelock.append(depth)
    if lock.get("owner"):
        owner = Element("{DAV:}owner")
        href = Element("{DAV:}href")
        href.text = lock.get("owner")
        owner.append(href)
        activelock.append(owner)
    if lock.get("token"):
        locktoken = Element("{DAV:}locktoken")
        href = Element("{DAV:}href")
        href.text = lock.get("token")
        locktoken.append(href)
        activelock.append(locktoken)

    s = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
    s += ET.tostring(root, encoding = "utf-8")
    return s

