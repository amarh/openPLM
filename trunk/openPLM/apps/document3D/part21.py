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


# The original parser was written using pyparsing.
# This is a rewritting which uses LEPL
# Currently it does not handle comments.

"""
A generic (no dependencies on the rest of PanGalactic) reader/writer for
"Part 21 files" (ISO 10303-21, STEP "Clear Text Encoding", a serialization
format).

"""

import sys, string
from optparse import OptionParser


from lepl import *

import time

def groupInParens(expr):
    return Literal("(") & expr & Literal(")")
pre = '0123'
HEX = string.hexdigits
BINARY = Word(pre, HEX)

DIGIT = string.digits
LOWER = string.lowercase
UPPER = string.uppercase + '_'
STRING = String("'") #sglQuotedString.setParseAction(removeQuotes)
ENUMERATION = '.' + Word(UPPER, UPPER + DIGIT) + '.'
ENTITY_INSTANCE_NAME = Regexp(r'#\d+') # Word('#',DIGIT)

REAL = Limit(Real())
STANDARD_KEYWORD = Regexp(r'[A-Z_][A-Z_0-9]+') #Word(UPPER, UPPER + DIGIT)
USER_DEFINED_KEYWORD = '!' + STANDARD_KEYWORD
KEYWORD = USER_DEFINED_KEYWORD % STANDARD_KEYWORD

OMITTED_PARAMETER = '*'
LIST = Delayed()
PARAMETER = Delayed()
TYPED_PARAMETER = Delayed()
PARAMETER_LIST = Delayed()

comma_sep = Drop(",")
STEP = Delayed()

class EntityInstance(List):
    pass


with DroppedSpace(Whitespace()[:]):

    LIST = groupInParens( PARAMETER_LIST )

    UNTYPED_PARAMETER = First(Any("*$"), REAL, STRING , ENTITY_INSTANCE_NAME,
                        ENUMERATION , BINARY , LIST)
    PARAMETER += (TYPED_PARAMETER % UNTYPED_PARAMETER)
    TYPED_PARAMETER += (KEYWORD & groupInParens( PARAMETER ))
    PARAMETER_LIST += PARAMETER[:,comma_sep]
    SIMPLE_RECORD = KEYWORD & groupInParens( PARAMETER_LIST )
    SUBSUPER_RECORD = groupInParens(SIMPLE_RECORD[1:] )
    ENTITY_INSTANCE = ENTITY_INSTANCE_NAME & '=' & ( SIMPLE_RECORD % SUBSUPER_RECORD ) & ';' > EntityInstance

    DATA_SECTION = (Literal('DATA') & Optional( groupInParens( PARAMETER_LIST )) & ';' & ENTITY_INSTANCE[:] & Literal('ENDSEC;')) > List

    HEADER_ENTITY = KEYWORD & groupInParens( PARAMETER_LIST ) & ";" > List
    HEADER_SECTION = (Literal("HEADER;") &
            HEADER_ENTITY[3:] &
            Literal("ENDSEC;")) > List
    EXCHANGE_FILE = Limit(Literal("ISO-10303-21;") & HEADER_SECTION &
            DATA_SECTION[1:] & Literal("END-ISO-10303-21;")) > List

    STEP += EXCHANGE_FILE & Eos()

if __name__ == '__main__':
    from logging import basicConfig, DEBUG, ERROR
    usage = 'usage:  %prog [options] file.p21'
    optparser = OptionParser(usage)
    optparser.add_option("-t", "--time", action='store_true',
                         dest="show_time", default=False,
                         help="show the time consumed")
    (options, args) = optparser.parse_args(args=sys.argv[1:] or ['-h'])
    basicConfig(level=ERROR)
    if args[0] != '-h':
        f = open(args[0])
        if options.show_time:
            startTime = time.clock()
        #STEP.config.low_memory(500)
        STEP.config.no_full_first_match()
        STEP.config.optimize_or()
        STEP.config.no_memoize()
        STEP.config.compile_to_re()
        print "parsing"
        res = STEP.parse_file(f)
        print res[0]
