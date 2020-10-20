import os
import time
import subprocess
import unittest

test_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(os.path.join(test_dir, "..", "test_output_" + time.strftime("%d-%m-%Y-%H-%M-%S", time.localtime()) ))

tabarnak_path = os.path.join(test_dir, "..", "tabarnak.py")

class TestBAT(unittest.TestCase):
    def test_basic(self):
        """
        Test that it can sum a list of integers
        """
        os.makedirs(output_dir, exist_ok=True)

        cmd_stdout = open(os.path.join(output_dir, "test_basic_stdout.txt"), "w+")
        cmd_stderr = open(os.path.join(output_dir, "test_basic_stderr.txt"), "w+")

        results = subprocess.run(["python3", tabarnak_path, "--output-dir", output_dir], stdout=cmd_stdout, stderr=cmd_stderr)

        self.assertEqual(results.returncode, 0)

        cmd_stdout.close()
        cmd_stderr.close()

if __name__ == '__main__':
    unittest.main()
