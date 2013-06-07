# from: http://djangosnippets.org/snippets/2211/ by cronosa
import os
import logging
import doctest
from django.conf import settings
EXCLUDED_APPS = getattr(settings, 'TEST_EXCLUDE', [])
from django.test.simple import DjangoTestSuiteRunner
from django_xml_test_runner.xmltestrunner import XMLTestSuiteRunner

COLORS = False
if os.environ.get("TEST_OUTPUT", "stdin") == "xml":
    TestSuiteRunner = XMLTestSuiteRunner
else:
    TestSuiteRunner= DjangoTestSuiteRunner

    try:
        from pygments import highlight
        from pygments.lexers import PythonTracebackLexer
        from pygments.formatters import Terminal256Formatter
        PYGMENTS = True
    except ImportError:
        PYGMENTS = False

    if PYGMENTS:
        try:
            from django.utils.unittest import TextTestRunner, TextTestResult
            COLORS = True
        except ImportError:
            try:
                from unittest2 import TextTestRunner, TextTestResult
                COLORS = True
            except ImportError:
                pass

    if COLORS:

        class HighlightedTextTestResult(TextTestResult):

            def _exc_info_to_string(self, err, test):
                code = super(HighlightedTextTestResult, self)._exc_info_to_string(err, test)
                return highlight(code, PythonTracebackLexer(),
                        Terminal256Formatter(style="vim"))

        class HighlightedTextTestRunner(TextTestRunner):
            resultclass = HighlightedTextTestResult


class OpenPLMTestSuiteRunner(TestSuiteRunner):
    def __init__(self, *args, **kwargs):
        from django.conf import settings
        settings.TESTING = True
        south_log = logging.getLogger("south")
        south_log.setLevel(logging.WARNING)
        super(OpenPLMTestSuiteRunner, self).__init__(*args, **kwargs)

    def build_suite(self, *args, **kwargs):
        suite = super(OpenPLMTestSuiteRunner, self).build_suite(*args, **kwargs)
        if not args[0] and not getattr(settings, 'RUN_ALL_TESTS', False):
            tests = []
            for case in suite:
                pkg = case.__class__.__module__.split('.')[0]
                if pkg == "openPLM":
                    tests.append(case)
            suite._tests = tests
            from openPLM.plmapp import utils, lifecycle
            suite.addTest(doctest.DocTestSuite(utils))
            suite.addTest(doctest.DocTestSuite(lifecycle))
        return suite

    if COLORS:
        def run_suite(self, suite, **kwargs):
            return HighlightedTextTestRunner(
                verbosity=self.verbosity, failfast=self.failfast).run(suite)

