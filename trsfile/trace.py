import binascii

from .common import Header, SampleCoding

class Trace:
	"""
	Single trace
	"""

	def __init__(self, sample_coding : SampleCoding, samples, data = b'', title = 'trace', headers = {}):
		self.title = title
		self.data = data if data is not None else b''
		self.samples = samples
		self.sample_coding = sample_coding
		self.headers = headers

	def __len__(self):
		"""Returns the total number of samples in this trace"""
		return len(self.samples)

	def __iter__(self):
		""" reset pointer """
		self.iterator_index = -1
		return self

	def __next__(self):
		self.iterator_index = self.iterator_index + 1

		if self.iterator_index >= len(self):
			raise StopIteration
		return self[self.iterator_index]

	def __delitem__(self, index):
		del self.samples[index]

	def __setitem__(self, index, sample):
		self.samples[index] = sample

	def __getitem__(self, index):
		return self.samples[index]

	def get_input():
		if self.data is None or Header.INPUT_OFFSET not in self.headers or Header.INPUT_LENGTH not in self.headers:
			return None
		return self.__subdata(self.headers[Header.INPUT_OFFSET], self.headers[Header.INPUT_LENGTH])

	def get_output():
		if self.data is None or Header.OUTPUT_OFFSET not in self.headers or Header.OUTPUT_LENGTH not in self.headers:
			return None
		return self.__subdata(self.headers[Header.OUTPUT_OFFSET], self.headers[Header.OUTPUT_LENGTH])

	def get_key():
		if self.data is None or Header.KEY_OFFSET not in self.headers or Header.KEY_LENGTH not in self.headers:
			return None
		return self.__subdata(self.headers[Header.KEY_OFFSET], self.headers[Header.KEY_LENGTH])

	def __subdata(self, offset, length):
		return self.data[offset : offset + length]

	def __repr__(self):
		# Represent the data
		if len(self.data) >= 2:
			data = ', {0:02X}...{1:01X}'.format(self.data[0], self.data[-1])
		elif len(self.data) == 1:
			data = ', {0:02X}'.format(self.data[0])
		else:
			data = ''

		# Return the representation
		return '<Trace: {0:d}, {1:s}{2:s}>'.format(len(self.samples), self.title, data)
