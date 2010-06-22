"""
This module contains some functions which may be useful.
"""

import re
import string

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

