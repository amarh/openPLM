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

# 1 mm = 1 mm, 1 cm = 10 mm...
UNITS = {"mm" : 1,
         "cm" : 10,
         "in" : 25.4,
         "pt" : 25.4 / 72,
         "pc" : 12 * 25.4 / 72
        }

def convert(value, from_, to):
    """
    Example::

        >>> convert(10, "cm", "mm")
        100.0
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
    Example::

        >>> size_to_format("29.7cm", "21cm")
        'Others'
        >>> size_to_format("21cm", "29.7cm")
        'A4'
    """
    size = (normalize_length(width_lg), normalize_length(height_lg))
    return FORMATS.get(size, "Other")

def level_to_sign_str(level):
    types = {0 : "1st", 1 : "2nd", 3 : "3rd"}
    return "sign_%s_level" % types.get(level, "%dth" % (level + 1))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
