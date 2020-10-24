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

            results = subprocess.run(cmd, stdout=cmd_stdout, stderr=cmd_stderr, check=False)

        output_file = "H.264-720x480-1-audio-tracks-mono-vorbis-eng-2-seconds.mkv"
        output_path = os.path.join(self.output_dir, output_file)
        self.assertEqual(results.returncode, 0)
        self.assertTrue(os.path.exists(output_path))
        self.assertEqual(self.fetch_codec_name(output_path), "hevc")
        self.assertEqual(self.fetch_duration_in_frames(output_path), 2)


    def test_basic_failure(self):
        """
        test basic failure: invalid argument
        """

        with open(self.stdout_path, "w+") as cmd_stdout, open(self.stderr_path, "w+") as cmd_stderr:

            input_dir = os.path.join(test_dir, "BAT", "H264")
            args = ["--input-dir", input_dir, "--invalid-args"]
            cmd = self.tabarnak_cmd + args + self.tarbarnak_log_args

            results = subprocess.run(cmd, stdout=cmd_stdout, stderr=cmd_stderr, check=False)

        self.assertEqual(results.returncode, 2)


if __name__ == '__main__':
    unittest.main()
