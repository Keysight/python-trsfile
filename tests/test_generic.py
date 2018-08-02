import unittest
import trsfile
import os
from pathlib import Path
from trsfile import TrsFile

class TestGeneric(unittest.TestCase):
	def test_open(self):
		with trsfile.open(Path(__file__).parent / 'data' / '90x500xfloat.trs') as trs_file:
			self.assertIsInstance(trs_file, TrsFile)

			# Assume both handles to be not closed
			self.assertFalse(trs_file.file_handle.closed)
			self.assertFalse(trs_file.handle.closed)

	def test_close(self):
		trs_file = trsfile.open(Path(__file__).parent / 'data' / '90x500xfloat.trs')
		self.assertIsInstance(trs_file, TrsFile)
		trs_file.close()

		# Assume both handles to be closed
		self.assertTrue(trs_file.file_handle.closed)
		self.assertTrue(trs_file.handle.closed)

if __name__ == '__main__':
	unittest.main()
