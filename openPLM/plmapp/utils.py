############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
#
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

"""
This module contains some functions which may be useful.
"""

import re
import string
import random
import os.path
from functools import wraps
from django.shortcuts import render_to_response
from django.template import RequestContext

class SeekedFile(object):
    """
    .. versionadded:: 1.1

    A file-like object that wraps an already opened
    and seeked file.

    This file-like can be read by PIL and is used to
    open an image contained in another file.
    """
    def __init__(self, file):
        self.shift = file.tell()
        self.file = file

    def read(self, *args):
        return self.file.read(*args)

    def readline(self, *args):
        return self.file.readline(*args)

    def readlines(self, *args):
        return self.file.readlines(*args)

    def tell(self):
        return self.file.tell() - self.shift

    def seek(self, offset, whence=0):
        return self.file.seek(offset + self.shift, whence)


def next_in_seq(seq, value):
    """
    Returns item next to *value* in the sequence *seq*

    Example::

        >>> next_in_seq("abcd", "b")
        'c'
        >>> next_in_seq(range(5), 2)
        3

    """
    return seq[seq.index(value) + 1]

def get_next_revision(revision):
    """
    Returns next revision for *revision*. For example, if *revision* represents
    an int, it returns a string of the value + 1.

    If it can not find a new revision, it returns ""

    Example::

        >>> get_next_revision("a")
        'b'
        >>> get_next_revision("r")
        's'
        >>> get_next_revision("z")
        'aa'
        >>> get_next_revision("A")
        'B'
        >>> get_next_revision("R")
        'S'
        >>> get_next_revision("Z")
        'AA'
        >>> get_next_revision("1")
        '2'
        >>> get_next_revision("41")
        '42'
        >>> get_next_revision("0041")
        '0042'
        >>> get_next_revision("a.b")
        'a.c'
        >>> get_next_revision("a-a")
        'a-b'
        >>> get_next_revision("a,a")
        'a,b'
        >>> get_next_revision("a.3")
        'a.4'
        >>> get_next_revision("a.b.1")
        'a.b.2'
        >>> get_next_revision("plop")
        ''
        >>> get_next_revision("a.plop")
        ''
        >>> get_next_revision("")
        ''
    """
    if len(revision) == 1:
        if revision in string.ascii_lowercase:
            if revision == "z":
                return "aa"
            else:
                return next_in_seq(string.ascii_lowercase, revision)
        if revision in string.ascii_uppercase:
            if revision == "Z":
                return "AA"
            else:
                return next_in_seq(string.ascii_uppercase, revision)
    if revision.isdigit():
        zeros = re.search(r"^(0*).+", revision).group(1)
        return zeros + "%d" % (int(revision) + 1)
    m = re.search(r"^(.*)([-.,])([^-.,]+)$", revision)
    if m:
        last = get_next_revision(m.group(3))
        if not last:
            return ""
        return m.group(1) + m.group(2) + last
    return ""

# 1 mm = 1 mm, 1 cm = 10 mm...
UNITS = {"mm" : 1,
         "cm" : 10,
         "in" : 25.4,
         "pt" : 25.4 / 72,
         "pc" : 12 * 25.4 / 72
        }

def convert(value, from_, to):
    """
    Convert *value* from *from_* unit to *to* unit.

    Example::

        >>> "%.3f" % convert(10, "cm", "mm")
        '100.000'
        >>> "%.3f" % convert(10, "mm", "cm")
        '1.000'
        >>> "%.3f" % convert(10, "in", "cm")
        '25.400'
        >>> "%.3f" % convert(72, "pt", "in")
        '1.000'
        >>> "%.3f" % convert(72, "pc", "in")
        '12.000'
    """
    return value * UNITS[from_] / float(UNITS[to])

def normalize_length(length):
    """
    Converts *length* to a length in mm, formatted as ``%.1f``

    Example ::

        >>> normalize_length("29.7cm")
        '297.0'
        >>> normalize_length("21.00001cm")
        '210.0'
        >>> normalize_length("7.5in")
        '190.5'
    """
    m = re.match(r"([\d.]+)([cmip][mntc])", length)
    value = float(m.group(1))
    unit = m.group(2)
    return "%.1f" % convert(value, unit, "mm")

FORMATS = {
    ("841.0", "1189.0") : "A0",
    ("594.0", "841.0") : "A1",
    ("420.0", "594.0") : "A2",
    ("297.0", "420.0") : "A3",
    ("210.0", "297.0") : "A4",
    ("148.0", "210.0") : "A5",
    ("105.0", "148.0") : "A6",
    ("74.0", "105.0") : "A7",
    ("52.0", "74.0") : "A8",
    ("37.0", "52.0") : "A9",
    ("26.0", "37.0") : "A10",
}
CFORMATS = [(x, x) for x in FORMATS.itervalues()]
CFORMATS.sort()
CFORMATS.append(("Other", "Other"))
def size_to_format(width_lg, height_lg):
    """
    Converts a size to a page format

    Example::

        >>> size_to_format("29.7cm", "21cm")
        'Other'
        >>> size_to_format("21cm", "29.7cm")
        'A4'
    """
    size = (normalize_length(width_lg), normalize_length(height_lg))
    return FORMATS.get(size, "Other")

def level_to_sign_str(level):
    """
    Converts a level (int, starting from 0) to a sign role

    Example::

        >>> level_to_sign_str(0)
        'sign_1st_level'
        >>> level_to_sign_str(1)
        'sign_2nd_level'
        >>> level_to_sign_str(2)
        'sign_3rd_level'
        >>> level_to_sign_str(3)
        'sign_4th_level'
        >>> level_to_sign_str(4)
        'sign_5th_level'
        >>> level_to_sign_str(10)
        'sign_11th_level'
    """

    types = {0 : "1st", 1 : "2nd", 2 : "3rd"}
    return "sign_%s_level" % types.get(level, "%dth" % (level + 1))

def memoize_noarg(func):
    """
    Decorator which memoize result of *func*. *func* must not take arguments
    """
    @wraps(func)
    def wrapper():
        if not hasattr(wrapper, "_result"):
            wrapper._result = func()
        return wrapper._result
    return wrapper

password_chars = string.ascii_letters + string.digits + "@!=&/*-_"
def generate_password(length=12):
    """
    Generates a random password of *length* characters.
    """
    return "".join(random.choice(password_chars) for x in xrange(length))


def can_generate_pdf():
    """
    Returns ``True`` if openPLM can generate pdf files, i.e, pisa (xhtml2pdf)
    is installed.
    """
    from django.conf import settings
    return 'openPLM.apps.pdfgen' in settings.INSTALLED_APPS

def get_ext(filename):
    """
    .. versionadded:: 1.1

    Returns the extension of *filename* (dot include).

    It stripped all ".{number}" extensions if they are present.

    Example:
        >>> get_ext("filename.png")
        '.png'
        >>> get_ext("filename.prt.2")
        '.prt'
        >>> get_ext("filename.prt")
        '.prt'
        >>> get_ext("filename.1")
        '.1'
    """
    filename, ext = os.path.splitext(filename)
    if ext and ext[1:].isdigit():
        filename, ext2 = os.path.splitext(filename)
        if ext2:
            ext = ext2
    return ext


def get_pages_num(total_pages, current_page):
    """
    .. versionadded:: 1.1

    Returns the pages to display for the pagination
    """
    page = int(current_page)
    total = int(total_pages)
    if total < 5:
        pages = range(1, total + 1)
    else:
        if page < total-1:
            if page > 2:
                pages = range(page-2, page+3)
            else:
                pages = range (1,6)
        else:
            pages = range(total-4, total+1)
    return pages


def filename_to_name(filename):
    """
    .. versionadded:: 1.2

    Returns a clean version of a filename that should be
    more suitable as a document name.

    Example:
        >>> filename_to_name("/tmp/hello.pdf")
        'hello'
        >>> filename_to_name(u"/tmp/Hello_world.pdf")
        u'Hello world'
        >>> filename_to_name(u"/tmp/heLLoWorlD.xyz")
        u'heLLoWorlD'
    """
    basename = os.path.basename(filename)
    return os.path.splitext(basename)[0].replace("_", " ")


def r2r(template, dictionary, request):
    """
    Shortcut for:

    ::

        render_to_response(template, dictionary,
                              context_instance=RequestContext(request))
    """
    return render_to_response(template, dictionary,
                              context_instance=RequestContext(request))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
