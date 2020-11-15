"""
Configuration Test Module
"""
import os
import json
import unittest

from tests.test_case_base import TestCaseBase

test_dir = os.path.dirname(os.path.abspath(__file__))

class TestConfiguration(TestCaseBase):
    """
    Configuration Test TestCase
    """

    def test_json_default_output_input(self):
        """
        test json input and output default configuration
        """

        # output json to stdout
        output_cmd = self.cmd + ["--output-json-config"]
        self.run_cmd(output_cmd)
        json_output_stream = None
        with open(self.stdout_path, "r") as json_file:
            json_output_stream = json_file.read()
            json_output = json.loads(json_output_stream)

        # write json to file
        json_output_path = os.path.join(self.output_dir, "config.json")
        with open(json_output_path, "w+") as json_file:
            json_file.write(json_output_stream)

        # import the config and output it
        input_cmd = self.cmd + ["--input-json-config", json_output_path]
        input_cmd +=  ["--output-json-config"]
        self.run_cmd(input_cmd)

        # make sure configs are equal
        json_output_from_input_config = None
        with open(self.stdout_path, "r") as json_file:
            json_output_from_input_config = json.loads(json_file.read())
        self.assertEqual(json_output, json_output_from_input_config)

    def test_yml_default_output_input(self):
        """
        test yml input and output default configuration
        """

        # output yml on to stdout
        output_cmd = self.cmd + ["--output-yml-config"]
        self.run_cmd(output_cmd)
        yml_output_stream = None
        with open(self.stdout_path, "r") as json_file:
            yml_output_stream = json_file.read()

        # write json to file
        yml_output_path = os.path.join(self.output_dir, "config.yml")
        with open(yml_output_path, "w+") as yml_file:
            yml_file.write(yml_output_stream)

        # import the config and output it
        input_cmd = self.cmd + ["--input-yml-config", yml_output_path]
        input_cmd +=  ["--output-yml-config"]
        self.run_cmd(input_cmd)

        # make sure configs are equal
        yml_output_stream_from_input_config = None
        with open(self.stdout_path, "r") as yml_file:
            yml_output_stream_from_input_config = yml_file.read()
        self.assertEqual(yml_output_stream, yml_output_stream_from_input_config)

if __name__ == '__main__':
    unittest.main() # pragma: no cover
