import os.path
import re

VERSION = (2, 1, 0, 'dev', 0)

def get_svn_revision(path):
    """
    Returns the SVN revision in the form SVN-XXXX,
    where XXXX is the revision number.

    Returns SVN-unknown if anything goes wrong, such as an unexpected
    format of internal SVN files.

    *path* must be a directory whose SVN info you want to
    inspect. If it's not provided, this will use the root django/ package
    directory.
    """
    # from old djnago.utils.version package (< 1.5)
    rev = None
    entries_path = '%s/.svn/entries' % path

    try:
        entries = open(entries_path, 'r').read()
    except IOError:
        pass
    else:
        # Versions >= 7 of the entries file are flat text.  The first line is
        # the version number. The next set of digits after 'dir' is the revision.
        if re.match('(\d+)', entries):
            rev_match = re.search('\d+\s+dir\s+(\d+)', entries)
            if rev_match:
                rev = rev_match.groups()[0]
        # Older XML versions of the file specify revision as an attribute of
        # the first entries node.
        else:
            from xml.dom import minidom
            dom = minidom.parse(entries_path)
            rev = dom.getElementsByTagName('entry')[0].getAttribute('revision')

    if rev:
        return u'SVN-%s' % rev
    return u'SVN-unknown'

def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    else:
        if VERSION[3] != 'final':
            version = '%s %s %s' % (version, VERSION[3], VERSION[4])
    svn_rev = get_svn_revision(os.path.dirname(__file__))
    if svn_rev != u'SVN-unknown':
        version = "%s %s" % (version, svn_rev)
    return version
