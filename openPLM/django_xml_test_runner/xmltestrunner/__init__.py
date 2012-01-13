import signal
import unittest
import xmlrunner
from distutils import dir_util

from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner, DjangoTestRunner

class XMLTestRunner(DjangoTestRunner):
    
    def __init__(self, name=None, verbosity=0, failfast=False, **kwargs):
        super(XMLTestRunner, self).__init__(verbosity=verbosity, failfast=failfast, **kwargs)
        self.name = name

    def run(self, *args, **kwargs):
        """
        Runs the test suite after registering a custom signal handler
        that triggers a graceful exit when Ctrl-C is pressed.
        """
        self._default_keyboard_interrupt_handler = signal.signal(signal.SIGINT,
            self._keyboard_interrupt_handler)
        try:
            result = self._makeResult()
            output_dir = '.'
            if getattr(settings, 'TEST_OUTPUT_DIR', None):
                output_dir = settings.TEST_OUTPUT_DIR
            xmlrunner.XMLTestRunner(result, output_name=self.name,
                                    output_dir=output_dir).run(*args, **kwargs)
        finally:
            signal.signal(signal.SIGINT, self._default_keyboard_interrupt_handler)
        return result

    def _makeResult(self):
        result = xmlrunner._XMLTestResult()
        failfast = self.failfast

        def stoptest_override(func):
            def stoptest(test):
                # If we were set to failfast and the unit test failed,
                # or if the user has typed Ctrl-C, report and quit
                if (failfast and not result.wasSuccessful()) or \
                    self._keyboard_interrupt_intercepted:
                    result.stop()
                func(test)
            return stoptest

        setattr(result, 'stopTest', stoptest_override(result.stopTest))
        return result

class XMLTestSuiteRunner(DjangoTestSuiteRunner):
    def run_suite(self, suite, **kwargs):
        return XMLTestRunner(name="From_Test_Command", verbosity=self.verbosity, failfast=self.failfast).run(suite)