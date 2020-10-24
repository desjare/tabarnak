"""
Tabarnak transcoder base unittest.TestCase classes
"""

import os
import time
import shutil
import unittest

test_dir = os.path.dirname(os.path.abspath(__file__))

tabarnak_path = os.path.join(test_dir, "..", "tabarnak.py")

class TabarnakTestCase(unittest.TestCase):
    """
    Base unittest.TestCase for all transcoder test case classes
    """
    # pylint: disable=too-many-instance-attributes

    output_timef = "-%d-%m-%Y-%H-%M-%S"
    output_log_ext = ".log"

    def setUp(self):
        """
        setUp each test case with an output directory and configure default transcoder arguments
        """
        self.output_suffix = time.strftime(self.output_timef, time.localtime())
        self.out_dir_name = self.id() + self.output_suffix
        self.output_dir = os.path.join(os.path.join(test_dir, "..", self.out_dir_name))
        self.output_dir = os.path.abspath(self.output_dir)

        self.test_log_path = os.path.join(self.output_dir, self.id() + self.output_log_ext)
        self.stdout_path = os.path.join(self.output_dir, self.id()+"-stdout.txt")
        self.stderr_path = os.path.join(self.output_dir, self.id()+"-stderr.txt")

        self.tabarnak_cmd = ["python3", tabarnak_path,"--output-dir", self.output_dir]
        self.tarbarnak_log_args = ["--log-path", self.test_log_path]

        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        """
        tearDown ran after each test. Remove output directory.
        """

        # check for errors and output stdout and stderr
        if hasattr(self, '_outcome'):
            result = self.defaultTestResult()  # these 2 methods have no side effects
            self._feedErrorsToResult(result, self._outcome.errors)

            error = self.list_to_reason(result.errors)
            failure = self.list_to_reason(result.failures)
            is_ok = not error and not failure

            if not is_ok:
                try:
                    with open(self.stdout_path, "r") as cmd_stdout:
                        print("\nOutputing stdout:\n%s" % (cmd_stdout.read()))
                except IOError as error:
                    print("Error outputing stderr %s" % (error))

                try:
                    with open(self.stderr_path, "r") as cmd_stderr:
                        print("\nOutputing stderr:\n%s" % (cmd_stderr.read()))

                except IOError as error:
                    print("Error outputing stderr %s" % (error))

        shutil.rmtree(self.output_dir, ignore_errors=True)
        self.output_dir = None
        self.test_log_path = None
        self.stdout_path = None
        self.stderr_path = None

    def list_to_reason(self, exc_list):
        """
        extract a reason from a test result errors or failures list
        """
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]
        return None
