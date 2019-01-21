import unittest
import trsfile
import numpy
from os.path import dirname, abspath
from trsfile import SampleCoding

class TestTrsFile(unittest.TestCase):
	def setUp(self):
		self.trs_file = trsfile.open(dirname(abspath(__file__)) + '/data/90x500xfloat.trs', engine='TrsEngine')

	def tearDown(self):
		self.trs_file.close()

	def test_length(self):
		"""Check if length is indeed equal to 90"""
		self.assertEqual(len(self.trs_file), 90)

	def test_sample_length(self):
		"""Check if sample length is indeed equal to 500"""
		self.assertEqual(len(self.trs_file[0]), 500)

	def test_sample_coding(self):
		"""Check if sample coding is indeed FLOAT"""
		self.assertEqual(self.trs_file[0].sample_coding, SampleCoding.FLOAT)

	def test_iterator(self):
		"""Check if we can iterate over the traces"""
		i = 0
		for trace in self.trs_file:
			i += 1
		self.assertEqual(i, len(self.trs_file))

	def test_read_only(self):
		"""Check if the TrsFile is read only"""
		with self.assertRaises(TypeError) as cm:
			self.trs_file[0] = None

		with self.assertRaises(TypeError) as cm:
			del self.trs_file[0]

	def test_slice(self):
		"""Check if we can slice the TrsFile file"""
		steps = 3
		traces = self.trs_file[::steps]
		self.assertEqual(len(traces), len(self.trs_file) // steps)

	def test_reverse(self):
		"""Check if reverse works"""
		for i, trace in zip(range(1, len(self.trs_file) + 1), self.trs_file.reverse()):
			self.assertTrue(numpy.array_equal(self.trs_file[len(self.trs_file) - i].samples, trace.samples))

if __name__ == '__main__':
	unittest.main()
