"""
Basic Acceptance Test Module
"""
import os
import unittest

from tabarnak_test_case import TabarnakTestCase

test_dir = os.path.dirname(os.path.abspath(__file__))

class TestBAT(TabarnakTestCase):
    """
    Basic Acceptance Test TestCase
    """

    def test_basic(self):
        """
        Basic encoding test using BAT directory as source
        """
        input_dir = os.path.join(test_dir, "BAT", "H264")

        cmd = self.tabarnak_cmd + ["--input-dir", input_dir]
        self.run_tabarnak(cmd)

        self.assert_codec_name(self.output_dir, "hevc")

    def test_basic_failure(self):
        """
        Basic encoding failure using invalid argument
        """
        input_dir = os.path.join(test_dir, "BAT", "H264")
        args = ["--input-dir", input_dir, "--invalid-args"]
        cmd = self.tabarnak_cmd + args

        try:
            self.run_tabarnak(cmd)
        except ChildProcessError:
            pass


if __name__ == '__main__':
    unittest.main()
