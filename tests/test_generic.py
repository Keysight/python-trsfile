import unittest
import trsfile
from os.path import dirname, abspath

class TestGeneric(unittest.TestCase):
	def test_open(self):
		with trsfile.open(dirname(abspath(__file__)) + '/data/90x500xfloat.trs', engine='TrsEngine') as trs_file:
			self.assertIsInstance(trs_file, trsfile.TraceSet)
			self.assertIsInstance(trs_file.engine, trsfile.Engine)
			self.assertIsInstance(trs_file.engine, trsfile.TrsEngine)

			# Assume both handles to be not closed
			self.assertFalse(trs_file.is_closed())

	def test_close(self):
		trs_file = trsfile.open(dirname(abspath(__file__)) + '/data/90x500xfloat.trs', engine='TrsEngine')
		self.assertIsInstance(trs_file, trsfile.TraceSet)
		self.assertIsInstance(trs_file.engine, trsfile.Engine)
		self.assertIsInstance(trs_file.engine, trsfile.TrsEngine)
		trs_file.close()

		# Assume both handles to be closed
		self.assertTrue(trs_file.is_closed())

if __name__ == '__main__':
	unittest.main()
