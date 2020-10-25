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

        cmd = self.tabarnak_cmd + ["--input-dir", input_dir, "--copy"]
        self.run_tabarnak(cmd)

        self.assert_codec_name(self.output_dir, "hevc")

    def test_basic_no_stdout_stderr_redirect(self):
        """
        Basic encoding test using BAT directory as source without redirecting outputs and errors
        """
        input_dir = os.path.join(test_dir, "BAT", "H264")

        cmd = self.tabarnak_basic_cmd + ["--input-dir", input_dir]
        cmd += ["--strip-metadata", "--map-args", "-map 0"]
        cmd += ["--encoder-args", "-c:v libx265 -crf 20"]
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

    def test_basic_failure_invalid_input(self):
        """
        Basic encoding failure using invalid input
        """
        input_dir = os.path.join(test_dir, "BAT", "INVALID")
        args = ["--input-dir", input_dir]
        cmd = self.tabarnak_cmd + args

        try:
            self.run_tabarnak(cmd)
        except ChildProcessError:
            pass

    def test_transcode_same_codec_skip(self):
        """
        Basic encoding test using BAT directory as source using h264
        """
        input_dir = os.path.join(test_dir, "BAT", "H264")

        cmd = self.tabarnak_cmd + ["--input-dir", input_dir, "--h264"]
        self.run_tabarnak(cmd)

        # no files should be outputted
        self.assert_codec_name(self.output_dir, "h264", 0)


    def test_enable_prometheus_logging(self):
        """
        Basic encoding test using BAT directory as source and enable prometheus logging
        """
        input_dir = os.path.join(test_dir, "BAT", "H264")
        prometheus_log_path = os.path.join(self.output_dir, self.id() + ".prom")

        cmd = self.tabarnak_cmd + ["--input-dir", input_dir]
        cmd += ["--use-prometheus-logging", "--prometheus-log-path", prometheus_log_path]
        self.run_tabarnak(cmd)

        self.assert_codec_name(self.output_dir, "hevc")


if __name__ == '__main__':
    unittest.main()
