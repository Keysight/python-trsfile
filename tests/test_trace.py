import unittest
import trsfile
import binascii
from os.path import dirname, abspath

from trsfile.parametermap import TraceParameterMap
from trsfile.traceparameter import ByteArrayParameter


class TestTrsFile(unittest.TestCase):
	def setUp(self):
		self.trs_file = trsfile.open(dirname(abspath(__file__)) + '/data/90x500xfloat.trs', engine='TrsEngine')

	def tearDown(self):
		self.trs_file.close()

	def test_iterator(self):
		"""Check if we can iterate over the samples"""
		i = 0
		for samples in self.trs_file[0]:
			i += 1
		self.assertEqual(i, len(self.trs_file[0]))

	def test_data(self):
		self.assertEqual(self.trs_file[0].parameters,
						 TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(
							 binascii.unhexlify('43B94E34D3A221B27640C5AD87FBE5DF'))}))

	def test_title(self):
		self.assertEqual(self.trs_file[0].title, 'Clipped trace')

	def test_equality(self):
		self.assertEqual(self.trs_file[0], self.trs_file[0])
		self.assertNotEqual(self.trs_file[0], self.trs_file[1])


if __name__ == '__main__':
	unittest.main()
