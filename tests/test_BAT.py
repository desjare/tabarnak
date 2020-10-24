import os
import time
import shutil
import subprocess
import unittest

test_dir = os.path.dirname(os.path.abspath(__file__))
tabarnak_path = os.path.join(test_dir, "..", "tabarnak.py")

class TestBAT(unittest.TestCase):

	def setUp(self):

		self.output_dir = os.path.join(os.path.join(test_dir, "..", "test_output_" + self.id() + time.strftime("-%d-%m-%Y-%H-%M-%S", time.localtime()) ))
		self.tabarnak_cmd = ["python3", tabarnak_path,"--output-dir", self.output_dir]

		os.makedirs(self.output_dir, exist_ok=True)

	def tearDown(self):
		# FIXME TBM_desjare: might want to add this later
		# if hasattr(self, '_outcome'):
		#     result = self.defaultTestResult()  # these 2 methods have no side effects
		#     self._feedErrorsToResult(result, self._outcome.errors)

		#     error = self.list_to_reason(result.errors)
		#     failure = self.list_to_reason(result.failures)
		#     ok = not error and not failure

		#     if not ok:
		#         # might want to prevent output_dir removal here
		#         pass
		
		shutil.rmtree(self.output_dir, ignore_errors=True)
		self.output_dir = None

	def list_to_reason(self, exc_list):
		if exc_list and exc_list[-1][0] is self:
			return exc_list[-1][1]

	def test_basic(self):
		"""
		Basic encoding test using BAT directory as source
		"""
		stdout_path = self.id()+".txt"
		stderr_path = self.id()+".txt"

		with open(stdout_path, "w+") as cmd_stdout, open(stderr_path, "w+") as cmd_stderr:

			input_dir = os.path.join(test_dir, "BAT", "H264")
			log_path = os.path.join(self.output_dir, "test_basic.log")

			results = subprocess.run(self.tabarnak_cmd.copy() + ["--input-dir", input_dir,"--log-path", log_path], stdout=cmd_stdout, stderr=cmd_stderr)

		self.assertEqual(results.returncode, 0 )

if __name__ == '__main__':
	unittest.main()
