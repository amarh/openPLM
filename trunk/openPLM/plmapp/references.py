import re
import datetime
from django.utils import timezone

from django.conf import settings

from django.utils.translation import ugettext_lazy as _
from openPLM.plmapp.models import PLMObject, Part, Document

#: Regular expression to test if a reference is invalid (forbidden characters)
rx_bad_ref = re.compile(r"[?/#\n\t\r\f]|\.\.")

#: default reference patterns, generates references like ``PART_00001`` and ``DOC_00001``
REFERENCE_PATTERNS = {
    "shared": False,
    "part": (u"PART_{number:05d}", r"^PART_(\d+)$"),
    "doc": (u"DOC_{number:05d}", r"^DOC_(\d+)$"),
}


def validate_reference(reference):
    """ Raises a :exc:`ValueError` if *reference* is not valid."""
    if rx_bad_ref.search(reference):
        raise ValueError(_(u"Bad reference: '#', '?', '/' and '..' are not allowed"))

def validate_revision(revision):
    """ Raises a :exc:`ValueError` if *revision* is not valid."""
    if not revision:
        raise ValueError("Empty value not permitted for revision")
    if rx_bad_ref.search(revision):
        raise ValueError(_(u"Bad revision: '#', '?', '/' and '..' are not allowed"))


def get_new_reference(user, cls, start=0, inbulk_cache=None):
    u"""
    Returns a new reference for creating a :class:`.PLMObject` of type
    *cls*.

    *user* is the user who will create the object.

    By default, the formatting is ``PART_000XX``
    if *cls* is a subclass of :class:`.Part` and ``DOC_000XX`` otherwise.

    The number is the count of Parts or Documents plus *start* plus 1.
    It is incremented while an object with the same reference already exists.
    *start* can be used to create several creation forms at once.

    Parts and documents have an independent reference number. For example,
    the first suggested part reference is ``PART_00001`` and the first
    suggested document is ``DOC_00001`` even if parts have been created.

    .. note::
        The returned referenced may not be valid if a new object has been
        created after the call to this function.
    """
    patterns = getattr(settings, "REFERENCE_PATTERNS", REFERENCE_PATTERNS)
    if patterns["shared"]:
        base_cls = PLMObject
        name = "part" if issubclass(cls, Part) else "doc"
    elif issubclass(cls, Part):
        base_cls, name = Part, "part"
    else:
        base_cls, name = Document, "doc"
    format = patterns[name][0]
    if inbulk_cache is not None and "max_" + name in inbulk_cache:
        max_ref = inbulk_cache["max_" + name]
    else:
        try:
            max_ref = base_cls.objects.order_by("-reference_number")\
                .values_list("reference_number", flat=True)[0]
        except IndexError:
            max_ref = 0
        if inbulk_cache is not None:
            inbulk_cache["max_" + name] = max_ref
    nb = max_ref + start + 1
    initials = user.first_name[:1] + user.last_name[:1]
    return format.format(user=user, now=timezone.now(),
            number=nb, initials=initials)

def parse_reference_number(reference, class_):
    """
    Parses *reference* and returns the reference number.
    The reference number is the text that increases after each
    creation of a new document or part.

    :param reference: reference of the created object
    :param class_: class of the created object
    :return: the reference number, 0 if there is no reference
    :rtype: int
    """
    try:
        patterns = getattr(settings, "REFERENCE_PATTERNS", REFERENCE_PATTERNS)
        name = "part" if issubclass(class_, Part) else "doc"
        reference_number = int(re.search(patterns[name][1], reference).group(1))
        if reference_number > 2**31 - 1:
            reference_number = 0
    except:
        reference_number = 0
    return reference_number

