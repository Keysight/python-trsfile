import unittest
import trsfile
import os
from os.path import dirname, abspath
from trsfile import TrsFile, Trace, trs_open, trs_create, TracePadding, SampleCoding

TMP_TRS_FILE = 'tmp.trs'

class TestGeneric(unittest.TestCase):

	def setUp(self):
		# Make sure no tmp exist
		if os.path.isfile(TMP_TRS_FILE):
			os.remove(TMP_TRS_FILE)

	def tearDown(self):
		# Make sure no tmp exist
		if os.path.isfile(TMP_TRS_FILE):
			os.remove(TMP_TRS_FILE)

	def test_inside_exception_empty(self):
		# While creating a trace, an exception is fired
		with self.assertRaises(RuntimeError):
			with trs_create(TMP_TRS_FILE, TracePadding.PAD) as trs_file:
				raise RuntimeError('some problem with the code')

		# Check if file exists
		self.assertTrue(os.path.isfile(TMP_TRS_FILE))

		# Check if it contains exactly zero traces
		with trs_open(TMP_TRS_FILE) as trs_file:
			self.assertEqual(len(trs_file), 0)

	def test_inside_exception(self):
		# While creating a trace, an exception is fired
		with self.assertRaises(RuntimeError):
			with trs_create(TMP_TRS_FILE, TracePadding.PAD) as trs_file:
				trs_file.append(Trace(SampleCoding.BYTE, []))
				raise RuntimeError('some problem with the code')

		# Check if file exists
		self.assertTrue(os.path.isfile(TMP_TRS_FILE))

		# Check if it contains exactly one trace
		with trs_open(TMP_TRS_FILE) as trs_file:
			self.assertEqual(len(trs_file), 1)

if __name__ == '__main__':
	unittest.main()
