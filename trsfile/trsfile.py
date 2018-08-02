import os
import mmap
import struct
import numpy

from .trace import Trace
from .common import Header, SampleCoding

class TrsFile:
	handle = None
	file_handle = None
	temp_folder = None
	headers = {}

	# All our magic function to support easy usage of the Trs file format
	def __init__(self, path):
		self.path = path

		self.file_handle = open(path, 'rb', 0) # Disable buffering
		self.handle = mmap.mmap(self.file_handle.fileno(), 0, access = mmap.ACCESS_READ)

		self.__initialize_headers()

	def __del__(self):
		# Sanity close, no harm from calling twice, but we do expect user calling close!
		self.close()

	def __iter__(self):
		""" reset pointer """
		self.iterator_index = -1
		return self

	def __next__(self):
		self.iterator_index = self.iterator_index + 1

		if self.iterator_index >= len(self):
			raise StopIteration
		return self[self.iterator_index]

	def __enter__(self):
		"""Called when entering a `with` block"""
		if self.handle is None or self.handle.closed:
			raise ValueError('I/O operation on closed file')
		return self

	def __exit__(self, *args):
		"""Called when exiting a `with` block"""
		self.close()

	def __repr__(self):
		return repr([self[i] for i in range(0, len(self))])

	def __len__(self):
		"""Returns the total number of traces"""
		return self.headers[Header.NUMBER_TRACES] if Header.NUMBER_TRACES in self.headers else 0

	def __delitem__(self, index):
		raise TypeError('cannot modify existing trace set')

	def __setitem__(self, index, trace):
		raise TypeError('cannot modify existing trace set')

	def __getitem__(self, index):
		# check for slicing
		if isinstance(index, slice):
			# No bounds checking when using slices, that's how python rolls!
			r = range(*index.indices(self.headers[Header.NUMBER_TRACES]))
		else:
			# Wrap around for negative indexes
			if index < 0:
				index = index % self.headers[Header.NUMBER_TRACES]

			# Check if we are still in bounds
			if index >= self.headers[Header.NUMBER_TRACES]:
				raise IndexError('list index out of range')

			r = range(index, index + 1)

		# Now read in all traces
		traces = []
		for i in r:
			# Seek to the beginning of the trace
			self.handle.seek(self.data_offset + i * self.trace_length)

			# Read the title
			if Header.TITLE_SPACE in self.headers:
				title = self.handle.read(self.headers[Header.TITLE_SPACE]).decode('utf-8')
			else:
				title = Header.TRACE_TITLE.default

			# Read data
			if Header.LENGTH_DATA in self.headers:
				data = self.handle.read(self.headers[Header.LENGTH_DATA])
			else:
				data = bytes(Header.LENGTH_DATA.default)

			# Read all the samples
			samples = numpy.frombuffer(self.handle.read(self.trace_length), self.headers[Header.SAMPLE_CODING].format, self.headers[Header.NUMBER_SAMPLES])

			traces.append(Trace(self.headers[Header.SAMPLE_CODING], samples, data, title, self.headers))

		# Return the select item(s)
		if isinstance(index, slice):
			return traces
		else:
			# Earlier logic should ensure traces contains one element!
			return traces[0]

	def save(self):
		raise TypeError('cannot save existing trace set')

	def append(self, trace):
		raise TypeError('cannot modify existing trace set')

	def extend(self, traces):
		raise TypeError('cannot modify existing trace set')

	def insert(self, index, trace):
		raise TypeError('cannot modify existing trace set')

	def reverse(self):
		return self[::-1]

	def close(self):
		"""Closes the open file handle if it is opened"""

		if self.file_handle is not None and not self.file_handle.closed:
			self.file_handle.close()
		if self.handle is not None and not self.handle.closed:
			self.handle.close()

	def __initialize_headers(self):
		"""Read all internal headers from the file"""
		self.headers = {}

		# Add default headers and values if new
		self.handle.seek(0)

		# Parse all headers until the TRACE_BLOCK
		while Header.TRACE_BLOCK not in self.headers:
			# Obtain the Tag
			tag = self.handle.read(1)[0]

			# Obtain the Length
			tag_length = self.handle.read(1)[0]

			if (tag_length & 0x80) != 0:
				tag_length = int.from_bytes(self.handle.read(tag_length & 0x7F), 'little')

			# Obtain the Value
			tag_value = self.handle.read(tag_length) if tag_length > 0 else None

			# Interpreter it
			header = None
			if Header.has_value(tag):
				header = Header(tag)
				if header.type is int:
					tag_value = int.from_bytes(tag_value, 'little')
				elif header.type is float:
					tag_value, = struct.unpack('<f', tag_value)
				elif header.type is bool:
					tag_value, = struct.unpack('<?', tag_value)
				elif header.type is str:
					tag_value = tag_value.decode('utf-8')
				elif header.type is SampleCoding:
					tag_value = SampleCoding(tag_value[0])
			else:
				print('Warning: tag {tag:02X} is not supported by the library, please let us know.'.format(tag=tag))

			self.headers[tag if header is None else header] = tag_value

		# Pre-compute some static information based on headers
		self.data_offset = self.handle.tell()
		self.sample_length = self.headers[Header.NUMBER_SAMPLES] * self.headers[Header.SAMPLE_CODING].size
		self.trace_length = self.sample_length + self.headers.get(Header.LENGTH_DATA, 0) + self.headers.get(Header.TITLE_SPACE, 0)

		# Sanity: Check if we have all mandatory headers, if not, throw an error if we are in reading mode!
		if not Header.get_mandatory().issubset(self.headers):
			raise IOError('trace set does not contain all mandatory headers')

		# Sanity: Check if the file has the proper size
		self.handle.seek(0, os.SEEK_END)
		file_size = self.handle.tell()
		if file_size != self.data_offset + self.headers[Header.NUMBER_TRACES] * self.trace_length:
			raise IOError('trace set has an unexpected length')
