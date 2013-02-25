import signal
import xmlrunner

from unittest import TextTestRunner
from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

class XMLTestRunner(TextTestRunner):

    def __init__(self, name=None, verbosity=0, failfast=False, **kwargs):
        super(XMLTestRunner, self).__init__(verbosity=verbosity, **kwargs)
        self.name = name

    def run(self, *args, **kwargs):
        """
        Runs the test suite after registering a custom signal handler
        that triggers a graceful exit when Ctrl-C is pressed.
        """
        try:
            result = self._makeResult()
            output_dir = '.'
            if getattr(settings, 'TEST_OUTPUT_DIR', None):
                output_dir = settings.TEST_OUTPUT_DIR
            xmlrunner.XMLTestRunner(result, output_name=self.name,
                                    output_dir=output_dir).run(*args, **kwargs)
        finally:
            pass
        return result

    def _makeResult(self):
        result = xmlrunner._XMLTestResult()

        def stoptest_override(func):
            def stoptest(test):
                # If we were set to failfast and the unit test failed,
                # or if the user has typed Ctrl-C, report and quit
                func(test)
            return stoptest

        setattr(result, 'stopTest', stoptest_override(result.stopTest))
        return result

class XMLTestSuiteRunner(DjangoTestSuiteRunner):
    def run_suite(self, suite, **kwargs):
        return XMLTestRunner(name="From_Test_Command", verbosity=self.verbosity).run(suite)
