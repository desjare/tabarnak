"""
Factory Acceptance Test Module
"""
import os
import unittest

from tests.test_case_base import TestCaseBase
from tests.config import TEST_FAT_H264_DIR, TEST_FAT_VP8_DIR, TEST_FAT_HEVC_DIR
from tests.config import TEST_FAT_DNXHD_DIR

test_dir = os.path.dirname(os.path.abspath(__file__))

class TestFAT(TestCaseBase):
    """
    Factory Acceptance Test TestCase
    """

    def test_basic_h264(self):
        """
        Basic h264 to hevc encoding test using BAT directory as source
        """
        cmd = self.cmd + ["--input-dir", TEST_FAT_H264_DIR]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "hevc")
        self.assert_copy(self.output_dir, 1)

    def test_basic_vp8(self):
        """
        Basic vp8 to hevc encoding test using BAT directory as source
        """
        cmd = self.cmd + ["--input-dir", TEST_FAT_VP8_DIR]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "hevc")
        self.assert_copy(self.output_dir, 1)

    def test_basic_dnxhd(self):
        """
        Basic dnxhd to hevc encoding test using BAT directory as source
        """

        cmd = self.cmd + ["--input-dir", TEST_FAT_DNXHD_DIR, "--percent-tolerance", "96"]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "hevc")
        self.assert_copy(self.output_dir, 1)

    def test_basic_hevc(self):
        """
        Basic hevc to h264 encoding test using BAT directory as source
        """
        cmd = self.cmd + ["--input-dir", TEST_FAT_HEVC_DIR, "--h264"]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "h264")
        self.assert_copy(self.output_dir, 1)


if __name__ == '__main__':
    unittest.main() # pragma: no cover
