# from: http://djangosnippets.org/snippets/2211/ by cronosa
import os
import logging
from django.conf import settings
EXCLUDED_APPS = getattr(settings, 'TEST_EXCLUDE', [])
from django.test.simple import DjangoTestSuiteRunner
from django_xml_test_runner.xmltestrunner import XMLTestSuiteRunner

if os.environ.get("TEST_OUTPUT", "stdin") == "xml":
    TestSuiteRunner = XMLTestSuiteRunner
else:
    TestSuiteRunner= DjangoTestSuiteRunner

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
        return suite
