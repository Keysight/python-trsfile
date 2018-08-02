import unittest
import trsfile
import os
import binascii
import numpy
from pathlib import Path
from trsfile import TrsFile, Header, SampleCoding

class TestTrsFile(unittest.TestCase):
	def setUp(self):
		self.trs_file = trsfile.open(Path(__file__).parent / 'data' / '90x500xfloat.trs')

	def tearDown(self):
		self.trs_file.close()

	def test_iterator(self):
		"""Check if we can iterate over the samples"""
		i = 0
		for samples in self.trs_file[0]:
			i += 1
		self.assertEqual(i, len(self.trs_file[0]))

	def test_data(self):
		self.assertEqual(self.trs_file[0].data, binascii.unhexlify('43B94E34D3A221B27640C5AD87FBE5DF'))

	def test_title(self):
		self.assertEqual(self.trs_file[0].title, 'Clipped trace')

if __name__ == '__main__':
	unittest.main()
