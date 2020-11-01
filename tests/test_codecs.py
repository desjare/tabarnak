"""
Basic Acceptance Test Module
"""
import os
import unittest

from tests.test_case_base import TestCaseBase
from tests.config import TEST_BAT_VP8_DIR, TEST_BAT_DNXHD_DIR

test_dir = os.path.dirname(os.path.abspath(__file__))

class TestCodecs(TestCaseBase):
    """
    Codecs TestCase
    """

    def test_vp8(self):
        """
        Basic vp8 encoding test using BAT directory as source
        """
        cmd = self.cmd + ["--input-dir", TEST_BAT_VP8_DIR]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "hevc")

    def test_dnxhd_tolerance_fail(self):
        """
        Basic dhxhd encoding test using BAT directory as source
        that fails before the file size difference is too large
        """
        cmd = self.cmd + ["--input-dir", TEST_BAT_DNXHD_DIR]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), False)
        self.assert_codec_name(self.output_dir, "hevc")

    def test_dnxhd(self):
        """
        Basic dhxhd encoding test using BAT directory as source
        """
        cmd = self.cmd + ["--input-dir", TEST_BAT_DNXHD_DIR, "--percent-tolerance", "96"]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "hevc")

if __name__ == '__main__':
    unittest.main() # pragma: no cover
