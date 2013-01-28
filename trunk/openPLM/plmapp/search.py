import re
from haystack.query import SearchQuerySet

from openPLM.plmapp.query_parser import get_query_parser

_lifecycle_queries = re.compile(r'lifecycle|state|cancel')

class SmartSearchQuerySet(SearchQuerySet):
    """
    A :class:`.SearchQuerySet` which :meth:`.auto_query` handles complex
    queries.

    Supported queries:

        * wildcards (ex: ``*``, ``quer*``)
        * boolean operators (AND, OR, NOT)
        * phrases (ex: ``"a phrase"``)
        * qualifiers (ex: ``type:value``)
        * parenthesis (ex: ``(a AND b) OR c)``
        * a mix of all previous features (``type:val* OR (NOT "a phrase")``)
    """

    _PARSER = get_query_parser()

    def auto_query(self, query_string):
        clone = self._clone()
        query_string = query_string.strip()
        query = self._PARSER(query_string)[0].to_SQ()
        clone = clone.filter(query)
        if _lifecycle_queries.search(query_string) is None:
            clone = clone.exclude(state_class="cancelled")
        return clone

