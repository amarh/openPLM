import os
from django.conf import settings

from .base import *
from .main import *
from .document import *
from .part import *
from .user import *
from .group import *


# also test translations if asked
if os.environ.get("TEST_TRANS") == "on":
    test_cases = []
    def find_test_cases(base, r):
        r.append(base)
        for c in base.__subclasses__():
            find_test_cases(c, r)
    find_test_cases(CommonViewTest, test_cases)
    tpl = """class %(base)s__%(language)s(%(base)s):
    LANGUAGE = "%(language)s"
"""
    for language, language_name in settings.LANGUAGES:
        if language != "en":
            for base in test_cases:
                exec (tpl % (dict(base=base.__name__, language=language)))

