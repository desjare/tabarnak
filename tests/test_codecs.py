"""
Basic Acceptance Test Module
"""
import os
import unittest

from tests.test_case_base import TestCaseBase
from tests.config import TEST_BAT_VP8_DIR

test_dir = os.path.dirname(os.path.abspath(__file__))

class TestCodecs(TestCaseBase):
    """
    Codecs TestCase
    """

    def test_vp8(self):
        """
        Basic encoding test using BAT directory as source
        """
        cmd = self.cmd + ["--input-dir", TEST_BAT_VP8_DIR]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "hevc")

if __name__ == '__main__':
    unittest.main()
