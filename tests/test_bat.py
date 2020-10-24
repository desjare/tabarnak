"""
Basic Acceptance Test Module
"""
import os
import subprocess
import unittest

from tabarnak_test_case import TabarnakTestCase

test_dir = os.path.dirname(os.path.abspath(__file__))
tabarnak_path = os.path.join(test_dir, "..", "tabarnak.py")


class TestBAT(TabarnakTestCase):
    """
    Basic Acceptance Test TestCase
    """

    def test_basic(self):
        """
        Basic encoding test using BAT directory as source
        """

        with open(self.stdout_path, "w+") as cmd_stdout, open(self.stderr_path, "w+") as cmd_stderr:

            input_dir = os.path.join(test_dir, "BAT", "H264")

            cmd = self.tabarnak_cmd + ["--input-dir", input_dir] + self.tarbarnak_log_args

            results = subprocess.run(cmd, stdout=cmd_stdout, stderr=cmd_stderr, check=True)

        self.assertEqual(results.returncode, 0)

if __name__ == '__main__':
    unittest.main()
