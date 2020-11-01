"""
Basic Acceptance Test Module
"""
import os
import shutil
import signal
import subprocess
import unittest

from tests.test_case_base import TestCaseBase
from tests.config import TEST_BAT_H264_DIR, TEST_BAT_INVALID_DIR
from tests.config import TEST_H264_FILE_2_SECONDS, TEST_H264_PATH_2_SECONDS

from tabarnak import tabarnak

test_dir = os.path.dirname(os.path.abspath(__file__))

class TestBAT(TestCaseBase):
    """
    Basic Acceptance Test TestCase
    """

    def test_basic(self):
        """
        Basic encoding test using BAT directory as source
        """
        cmd = self.cmd + ["--input-dir", TEST_BAT_H264_DIR, "--copy"]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "hevc")
        self.assert_copy(self.output_dir, 1)

    def test_basic_no_stdout_stderr_redirect(self):
        """
        Basic encoding test using BAT directory as source without redirecting outputs and errors
        """
        cmd = self.basic_cmd + ["--input-dir", TEST_BAT_H264_DIR]
        cmd += ["--strip-metadata", "--map-args", "-map 0"]
        cmd += ["--encoder-args", "-c:v libx265 -crf 20"]
        cmd += ["--duration-tolerance", 0]
        cmd += ["--percent-tolerance", 0]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "hevc")

    def test_basic_failure(self):
        """
        Basic encoding failure using invalid argument
        """
        args = ["--input-dir", TEST_BAT_H264_DIR, "--invalid-args"]
        cmd = self.cmd + args

        child_process_error = False
        try:
            self.run_cmd(cmd)
        except ChildProcessError:
            child_process_error = True

        self.assertEqual(child_process_error, True)

    def test_basic_failure_invalid_input(self):
        """
        Basic encoding failure using invalid input
        """
        args = ["--input-dir", TEST_BAT_INVALID_DIR]
        cmd = self.cmd + args

        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), False)

    def test_transcode_same_codec_skip(self):
        """
        Basic encoding test using BAT directory as source using h264
        """
        cmd = self.cmd + ["--input-dir", TEST_BAT_H264_DIR, "--h264"]
        self.run_cmd(cmd)

        # no files should be outputted
        self.assert_codec_name(self.output_dir, "h264", 0)

    def test_transcode_same_codec_skip_existing(self):
        """
        Basic encoding test using BAT directory as source existing file in output directory
        """
        output_file_path = os.path.join(self.output_dir, TEST_H264_FILE_2_SECONDS)
        shutil.copyfile(TEST_H264_PATH_2_SECONDS, output_file_path)

        cmd = self.cmd + ["--input-dir", TEST_BAT_H264_DIR]
        self.run_cmd(cmd)

    def test_enable_prometheus_logging(self):
        """
        Basic encoding test using BAT directory as source and enable prometheus logging
        """
        prometheus_log_path = os.path.join(self.output_dir, self.id() + ".prom")

        cmd = self.cmd + ["--input-dir", TEST_BAT_H264_DIR]
        cmd += ["--use-prometheus-logging", "--prometheus-log-path", prometheus_log_path]
        result = self.run_cmd(cmd)

        self.assertEqual(result.status(), True)
        self.assert_codec_name(self.output_dir, "hevc")

    def test_signal_handler(self):
        """
        send a signal to improve code test coverage
        """
        signal.signal(signal.SIGUSR1, tabarnak.signal_handler)
        results = subprocess.run(["kill", "-SIGUSR1", str(os.getpid())], check=False)

        self.assertTrue(results.returncode == 0)



if __name__ == '__main__':
    unittest.main() # pragma: no cover
