"""
Tabarnak transcoder base unittest.TestCase classes
"""
# pylint: disable=no-self-use

import os
import time
import shutil
import subprocess
import sys
import unittest

import tabarnak

ffprobe_path = shutil.which("ffprobe")

probe_cmd = [ffprobe_path, "-v", "error"]
probe_of = ["-of" , "default=noprint_wrappers=1:nokey=1"]
probe_vstream = ["-select_streams",  "v:0"]
probe_codec_cmd = probe_cmd + probe_vstream + ["-show_entries", "stream=codec_name"] + probe_of
probe_duration_cmd = probe_cmd + ["-show_entries", "format=duration"] + probe_of

media_ext = [".mkv", ".mp4", ".webm"]

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

        self.tarbarnak_log_args = ["--log-path", self.test_log_path]

        self.tabarnak_cmd = ["--output-dir", self.output_dir]
        self.tabarnak_cmd += ["--stdout-path", self.stdout_path]
        self.tabarnak_cmd += ["--stderr-path", self.stderr_path]
        self.tabarnak_cmd += self.tarbarnak_log_args

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

    def run_tabarnak(self, cmd):
        """
        run tarbarnak main utility method
        """
        argv_copy = sys.argv.copy()

        try:
            tabarnak.main(cmd)

        finally:
            sys.argv = argv_copy

    def assert_codec_name(self, output_dir, codec_name, count=None):
        """
        assert that all file in output_dir are of a certain codec
        """
        media_files = 0

        for root, _, files in os.walk(output_dir, topdown=False):
            for name in files:
                _, ext = os.path.splitext(name)
                if not ext in media_ext:
                    continue

                output_path = os.path.join(root, name)

                self.assertEqual(self.fetch_codec_name(output_path), codec_name)
                self.assertGreater(self.fetch_duration_in_frames(output_path), 0)

                media_files += 1

        if count is not None:
            self.assertEqual(media_files, count)

                


    def list_to_reason(self, exc_list):
        """
        extract a reason from a test result errors or failures list
        """
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]
        return None


    def fetch_codec_name(self, path):
        """
        return codec name of a media file giving its path
        """

        check_output_cmd = probe_codec_cmd.copy()
        check_output_cmd += [path]

        results = subprocess.run(check_output_cmd, stdout=subprocess.PIPE, check=True)
        codec = results.stdout.decode('utf-8').replace("\n","")

        return codec

    def fetch_duration_in_frames(self, path):
        """
        fetch duration in frames (int) of a media file giving its path
        """
        check_output_cmd = probe_duration_cmd.copy()
        check_output_cmd += [path]

        results = subprocess.run(check_output_cmd, stdout=subprocess.PIPE, check=True)
        duration = results.stdout.decode('utf-8').replace("\n","")

        frame_duration = 0.0
        try:
            frame_duration = float(duration)
        except ValueError:
            pass

        return int(frame_duration)
