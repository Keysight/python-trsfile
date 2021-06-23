import numpy

from trsfile.parametermap import TraceParameterMap
from trsfile.common import Header, SampleCoding

class Trace:
	"""The :py:obj:`Trace` class behaves like a :py:obj:`list`
	object were each item in the list is a sample of the trace.

	When a :py:obj:`Trace` is initialized the samples are (optionally) converted to a
	:py:class:`numpy.array` depending on the current type of the samples and the
	provided :py:obj:`sample_coding`.
	"""

	def __init__(self, sample_coding, samples, parameters=TraceParameterMap(), title='trace', headers={}):
		self.title = title
		self.parameters = parameters
		if not type(self.parameters) is TraceParameterMap:
			raise TypeError('Trace parameter data must be supplied as a TraceParameterMap')

		# Obtain sample coding
		if not isinstance(sample_coding, SampleCoding):
			raise TypeError('Trace requires sample_coding to be of type \'SampleCoding\'')
		self.sample_coding = sample_coding

		# Read in the sample and cast them automatically to the correct type
		# which is always a numpy.array with a specific dtype as indicated in sample_coding
		if isinstance(samples, numpy.ndarray):
			# Check if we need to convert the type of the numpy array
			if samples.dtype == sample_coding.format:
				self.samples = samples
			else:
				self.samples = samples.astype(sample_coding.format)
		else:
			if type(samples) in [bytes, bytearray, str]:
				self.samples = numpy.frombuffer(samples, dtype=self.sample_coding.format)
			else:
				self.samples = numpy.array(samples, dtype=self.sample_coding.format)

		# Optional headers to add meta support to data slicing (get_input etc)
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

	def get_input(self):
		if self.parameters['INPUT']:
			return self.parameters['INPUT'].value
		if self.parameters['LEGACY_DATA'] is None \
				or Header.INPUT_OFFSET not in self.headers \
				or Header.INPUT_LENGTH not in self.headers:
			return None
		return self.__subdata(self.headers[Header.INPUT_OFFSET], self.headers[Header.INPUT_LENGTH])

	def get_output(self):
		if self.parameters['OUTPUT']:
			return self.parameters['OUTPUT'].value
		if self.parameters['LEGACY_DATA'] is None \
				or Header.OUTPUT_OFFSET not in self.headers \
				or Header.OUTPUT_LENGTH not in self.headers:
			return None
		return self.__subdata(self.headers[Header.OUTPUT_OFFSET], self.headers[Header.OUTPUT_LENGTH])

	def get_key(self):
		if self.parameters['KEY']:
			return self.parameters['KEY'].value
		if self.parameters['LEGACY_DATA'] is None \
				or Header.KEY_OFFSET not in self.headers \
				or Header.KEY_LENGTH not in self.headers:
			return None
		return self.__subdata(self.headers[Header.KEY_OFFSET], self.headers[Header.KEY_LENGTH])

	def __subdata(self, offset, length):
		return self.parameters['LEGACY_DATA'].value[offset : offset + length]

	def __repr__(self):
		return '<Trace {0:s}: {1:d} samples, {2:d} parameters>'.format(self.title.strip(), len(self.samples),
																	   len(self.parameters))

	def __eq__(self, other):
		"""Compares two traces for equivalence"""
		if isinstance(other, Trace):
			return \
				self.title == other.title and \
				self.parameters == other.parameters and \
				self.sample_coding == other.sample_coding and \
				numpy.array_equal(self.samples, other.samples) and \
				self.headers == other.headers
		return False
