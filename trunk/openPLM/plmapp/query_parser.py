import re
import string

from lepl import *

try:
    from haystack.query import SQ
except Exception:
    SQ = None

split = re.compile("[%s]" % re.escape(string.punctuation)).split

class Alternatives(List):

    def to_SQ(self):
        sq = SQ()
        for elem in self:
            sq |= elem.to_SQ()
        return sq


class Conjunctives(List):
    def to_SQ(self):
        sq = SQ()
        for elem in self:
            sq &= elem.to_SQ()
        return sq

class Query(Conjunctives):
    pass

class Text(List):
    
    def to_SQ(self):
        if len(self) == 2:
            qualifier, text = self
            qualifier = qualifier[1]
        else:
            qualifier = "content"
            text = self[0] 
        text = text.strip().lower()
        filters = {}
        if text.endswith("*"):
            sq = SQ()
            text = text.rstrip("*")
            items = split(text)
            for item in items[:-1]:
                sq &= SQ(**{ qualifier: item })
            suffix = "*" if qualifier == "content" else ""
            sq &= SQ(**{ qualifier + "__startswith" : items[-1]+suffix})
            return sq
        else:
            return SQ(**{ qualifier : text })

class Not(List):

    def to_SQ(self):
        return ~ self[0].to_SQ()

def get_query_parser():
    expr = Delayed()
    query = Delayed()
    alternatives = Delayed()
    operators = Literals("OR", "AND", "NOT", ")", "(")
    qualifier      = Word(Any(string.ascii_letters)) & Drop(Any(':='))  > 'qualifier'
    word           = ~Lookahead(operators) & (Word())
    phrase         = String()
    text           = phrase | word
    word_or_phrase = (Optional(qualifier) & text) > Text
    par_op         = ~Any("(")
    par_cl         = ~Any(")")
    separator_and  = Drop('AND')
    separator_or   = Drop('OR')
    with DroppedSpace():
        not_expr       = ~Literals("NOT") & expr > Not
        expr           += (par_op & alternatives & par_cl) | not_expr | word_or_phrase
        query          += expr[1:]    > Query
        conjunctives   = query[:, separator_and]        > Conjunctives
        alternatives   += conjunctives[:, separator_or] > Alternatives
    
    parser = alternatives
    parser.config.no_full_first_match()
    return parser.parse_string

__all__ = ["get_query_parser", "Conjunctives", "Alternatives", "Query", 
          "Text"]

if __name__ == "__main__":
    c = get_query_parser()
    for s in ('all of these words "with this phrase" '
                       'OR that OR this site:within.site '
                       'filetype:ps from:lastweek',
                "A:aa",
                "a OR",
                ": dd",
                "NOT data a",
                "(a b c)",
                "( a b c)",
                ",v;d!:;,:;",
                "NOT ( a  b )  OR (abc OR NOT De)",
                "( )))",
                '"dfdl',
                " a AND NOT b OR CC",
                ):
        s = s.strip()
        print s
        print c(s)[0]
