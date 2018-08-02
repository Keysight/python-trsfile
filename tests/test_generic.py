import unittest
import trsfile
from os.path import dirname, abspath
from trsfile import TrsFile

class TestGeneric(unittest.TestCase):
	def test_open(self):
		with trsfile.open(dirname(abspath(__file__)) + '/data/90x500xfloat.trs') as trs_file:
			self.assertIsInstance(trs_file, TrsFile)

			# Assume both handles to be not closed
			self.assertFalse(trs_file.file_handle.closed)
			self.assertFalse(trs_file.handle.closed)

	def test_close(self):
		trs_file = trsfile.open(dirname(abspath(__file__)) + '/data/90x500xfloat.trs')
		self.assertIsInstance(trs_file, TrsFile)
		trs_file.close()

		# Assume both handles to be closed
		self.assertTrue(trs_file.file_handle.closed)
		self.assertTrue(trs_file.handle.closed)

if __name__ == '__main__':
	unittest.main()
