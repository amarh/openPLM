#!/usr/bin/env python
# This file is adapted from https://pangalactic.us/repo/pgef
# Here is the license

#Copyright (c) 2009 Pan Galactic Enterprises

#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to use, copy,
#modify, merge, publish, distribute, and/or sell copies of the Software, and to
#permit persons to whom the Software is furnished to do so, subject to the
#following conditions:

#This permission notice shall be included in all copies or substantial portions
#of the Software.

#It is unlawful to falsely claim copyright or other rights in Pan Galactic
#Enterprises material, including the Software.

#PAN GALACTIC ENTERPRISES SHALL IN NO WAY BE LIABLE FOR ANY COSTS, EXPENSES,
#CLAIMS OR DEMANDS ARISING OUT OF USE OF THE SOFTWARE.  THE SOFTWARE IS PROVIDED
#"AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
#LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
#AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
#LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
#CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Modifications by Pierre Cosquer:
#  - entity names are converted to int
#  - typeinst dict is replaced by a defaultdict

"""
A generic (no dependencies on the rest of PanGalactic) reader/writer for
"Part 21 files" (ISO 10303-21, STEP "Clear Text Encoding", a serialization
format).  This module reads a STEP Part 21 data file into a set of
Python dictionaries.

"""

import re, sys, string, time
from optparse import OptionParser
from pprint import pprint
from simpleparse.common import numbers, strings, comments
from simpleparse.parser import Parser
from simpleparse import dispatchprocessor as dp
from collections import defaultdict

# Part 21 File syntax specification (informal)

# Productions whose names are all caps are formally named and specified in ISO
# 10303-21:2002(E).  Productions with lower-case names are either "convenience"
# productions invented for this parser, or are specified in ISO 10303-21:2002(E)
# somewhere other than the formal file syntax specification.

# NOTES:
# (1)  simplification:  "USER_DEFINED_KEYWORD" will be ignored for now (should
# essentially never occur in a STEP file produced from a COTS CAX tool), so
# "KEYWORD" == "STANDARD_KEYWORD" for our purposes here.
# (2)  some definitions:
# simple_instance ->   an unparsed simple entity instance
# complex_instance ->  an unparsed complex entity instance

p21_syntax = r'''
ENTITY_INSTANCE_NAME  := '#', [0-9]+
KEYWORD               := [A-Z_], [A-Z0-9_]*
<eol>                 := '\r'?, '\n'
<record_terminator>   := ')', ts, ';', eol
parameter_list        := -record_terminator, -record_terminator*
simple_instance       := ts, ENTITY_INSTANCE_NAME, ts, '=', ts, KEYWORD,
                         ts, eol?, '(', parameter_list, record_terminator
instance_list         := KEYWORD, ts, eol?, '(', parameter_list, ')', ts, eol?,
                         (KEYWORD, '(', parameter_list, ')', ts, eol?)*
complex_instance      := ts, ENTITY_INSTANCE_NAME, ts, '=', ts, '(',
                         parameter_list, record_terminator
<ts>                  := [ \t]*
<comma>               := ',', ts, eol?, ts
<nullline>            := ts, eol
<ignorable_stuff>     := (ts, c_comment)/nullline
<header_tag>          := 'HEADER;', eol?
<end_tag>             := 'ENDSEC;', eol
HEADER_SECTION        := header_tag, -end_tag*, end_tag
EXCHANGE_FILE         := 'ISO-10303-21;', eol?, ignorable_stuff*,
                         HEADER_SECTION, ignorable_stuff*,
                         ('DATA;',
                         (simple_instance/complex_instance/ignorable_stuff)*,
                         ts, 'ENDSEC;', eol),
                         (ignorable_stuff*,
                         ('DATA;',
                         (simple_instance/complex_instance/ignorable_stuff)*,
                         ts, 'ENDSEC;', eol))*,
                         ignorable_stuff*, 'END-ISO-10303-21;', nullline*
'''

def parse_entities(s):
    return map(int, re.findall(r'#(\d+)', s))

class Part21Preparser(Parser):
    """
    Preparser for Part 21 files.
    """

    def __init__(self, *arg):
        Parser.__init__(self, *arg)
        self.res = {}

    def buildProcessor(self):
        return Part21Processor(self.res)


class Part21Processor(dp.DispatchProcessor):
    """
    Processing object for postprocessing the Part 21 grammar definitions into a
    new generator.
    """

    def __init__(self, res):
        self.res = res
        # TODO:  set this up as a sqlite database
        # contents:  maps entity inst nbr (n) to unparsed content
        # insttype:  maps entity inst nbr (n) to KEYWORD (i.e. type)
        # insttype:  maps KEYWORD (i.e. type) (n) to entity inst nbr
        self.res['contents'] = {}
        self.res['insttype'] = {}
        self.res['typeinst'] = defaultdict(list)

    def ENTITY_INSTANCE_NAME(self, (tag, start, stop, subtags), buffer):
        """
        Process C{ENTITY_INSTANCE_NAME} production.
        """
        return dp.getString((tag, start, stop, subtags), buffer)[1:]

    def KEYWORD(self, (tag, start, stop, subtags), buffer):
        """
        Process C{KEYWORD} production.
        """
        return dp.getString((tag, start, stop, subtags), buffer)

    def parameter_list(self, (tag, start, stop, subtags), buffer):
        """
        Process C{simple_content} production.
        """
        return dp.getString((tag, start, stop, subtags), buffer)

    def instance_list(self, (tag, start, stop, subtags), buffer):
        """
        Process C{complex_content} production.

        @return:  a 2-tuple of (keywords, parameter lists), where keywords is
            the list of KEYWORD occurrences and parameter lists is a list of
            strings (each of which is an unparsed parameter list).
        """
        inst = dp.multiMap((tag, start, stop, subtags), buffer)
        return inst.get('KEYWORD'), inst.get('parameter_list')

    def simple_instance(self, (tag, start, stop, subtags), buffer):
        """
        Process C{simple_instance} production.
        """
        inst = dp.singleMap(subtags, self, buffer)
        iname = int(inst.get('ENTITY_INSTANCE_NAME'))
        self.res['contents'][iname] = inst.get('parameter_list')
        self.res['insttype'][iname] = inst.get('KEYWORD')
        self.res['typeinst'][inst.get('KEYWORD')].append(iname)

    def complex_instance(self, (tag, start, stop, subtags), buffer):
        """
        Process C{complex_instance} production.
        """
        inst = dp.singleMap(subtags, self, buffer)
        iname = int(inst.get('ENTITY_INSTANCE_NAME'))
        self.res['contents'][iname] = inst.get('parameter_list')
        self.res['insttype'][iname] = 'complex_type'
        self.res['typeinst'][inst.get('KEYWORD')].append(iname)

    def HEADER_SECTION(self, (tag, start, stop, subtags), buffer):
        """
        Process C{HEADER_SECTION} production.
        """
        self.res['header'] = dp.getString((tag, start, stop, subtags), buffer)


def readStepFile(f=None, perf=False, verbose=False, test=False):
    """
    (These docs are fiction at the moment ... ;)

    Read a STEP Part 21 file/stream and return a set of Python dictionaries.

    @param f:  path to a file containing STEP Part 21 data
    @type  f:  C{str}

    @param null:  a value to use for nulls in the data, which are
        represented by '$' in Part 21.  Attributes with null values will not
        be included in the instance dictionaries unless a value is supplied
        for null, in which case they will be included with that value
    @type  null:  C{str}

    @return:  a result C{dict} that contains 3 items:  (1) 'header', the
        unparsed header section of the part 21 file; (2) 'contents', a C{dict}
        that maps entity instance numbers (production: 'ENTITY_INSTANCE_NAME')
        to their unparsed content; and (3) 'insttype', a C{dict} that maps
        entity instance numbers to their declared types (production: 'KEYWORD').
    @rtype:   C{dict}
    """
    p = Part21Preparser(p21_syntax)
    if f:
        data = open(f).read()
        if perf:
            start = time.clock()
        success, result, nextchar = p.parse(data, production='EXCHANGE_FILE')
        if perf:
            end = time.clock()
            print "\nTotal parse time: %6.2f sec" % (end - start)
            print len(list(p.res.get('contents', [])))," instances\n"
        if test:
            print '---------------'
            print 'Sample of Data:'
            print '---------------'
            sample = data[:100]
            print sample
            print '\n------------'
            print 'Result Tree:'
            print '------------'
            pprint(p.res)
        return p.res


if __name__ == '__main__':
    usage = 'usage:  %prog [options] file.p21'
    optparser = OptionParser(usage)
    optparser.add_option("-p", "--perf", action='store_true',
                         dest="performance", default=False,
                         help="run the parser's unit tests")
    optparser.add_option("-t", "--test", action='store_true',
                         dest="test", default=False,
                         help="run the parser's unit tests")
    optparser.add_option("-v", "--verbose", action='store_true',
                         dest="verbose", default=False,
                         help="verbose output from test (no effect on normal function)")
    (options, args) = optparser.parse_args(args=sys.argv)
    # debugging:
    # print "options:  %s" % str(options)
    # print "args:     %s" % str(args)
    if len(args) > 1:
        readStepFile(f=args[1],
                     perf=options.performance,
                     verbose=options.verbose,
                     test=options.test)
    elif options.test:
        readStepFile(test=True,
                     perf=options.performance,
                     verbose=options.verbose)
    else:
        optparser.print_help()

