import os
import mmap
import struct
import numpy
import copy

from trsfile.trace import Trace
from trsfile.common import Header, SampleCoding, TracePadding
from trsfile.engine.engine import Engine

class TrsEngine(Engine):
	"""
	This engine supports .trs files from Riscure as specified in the
	"Trace set coding" document in Inspector.

	This engine supports the following options:

	+--------------+-----------------------------------------------------------+
	| Option       | Description                                               |
	+==============+===========================================================+
	| headers      | Dictionary containing zero or more headers, see           |
	|              | :py:class:`trsfile.common.Header`                         |
	+--------------+-----------------------------------------------------------+
	| live_update  | Performs live update of the TRS file every N traces. True |
	|              | for updating after every trace and False for never.       |
	+--------------+-----------------------------------------------------------+
	| padding_mode | Padding mode to use. The supported values are:            |
	|              | :py:attr:`trsfile.common.TracePadding.NONE` (default)     |
	|              | :py:attr:`trsfile.common.TracePadding.AUTO`               |
	+--------------+-----------------------------------------------------------+
	"""

	def __init__(self, path, mode = 'x', **options):
		self.path = path if type(path) is str else str(path)
		self.handle = None
		self.file_handle = None

		self.data_offset = None
		self.sample_length = None
		self.trace_length = None

		self.is_mmap_synched = False

		# Initialize empty dictionaries
		self.headers = {}
		self.header_locations = {}

		# Get the options
		headers = options.get('headers', None)
		self.live_update = int(options.get('live_update', False))
		self.live_update_count = 0
		self.padding_mode = options.get('padding_mode', TracePadding.NONE)
		if not isinstance(self.padding_mode, TracePadding):
			raise TypeError('TrsFile requires padding_mode to be of type \'TracePadding\'')
		if self.padding_mode not in [TracePadding.NONE, TracePadding.AUTO]:
			raise ValueError('TrsFile only supports the padding mode NONE and AUTO')

		# Parse the mode
		if mode == 'r':
			"""r = open for reading"""
			if headers is not None:
				raise TypeError('Cannot change headers when reading TRS files.')

			if not os.path.isfile(self.path):
				raise FileNotFoundError('No TRS file: \'{0:s}\''.format(self.path))

			self.file_handle = open(self.path, 'rb')
			self.handle = mmap.mmap(self.file_handle.fileno(), 0, access = mmap.ACCESS_READ)
			self.read_only = True
			self.read_headers = True

		elif mode == 'w':
			"""open for writing, truncating the file first"""
			if headers is not None and any(not isinstance(header, Header) for header in headers):
				raise TypeError('Creation of TRS files requires passing Headers to the constructor.')

			# Sadly, to memory map we need a file with a minimum of length 1
			self.file_handle = open(self.path, 'wb')
			self.file_handle.write(b'\x00')
			self.file_handle.close()

			# Now we can open it properly
			self.file_handle = open(self.path, 'r+b')
			self.handle = mmap.mmap(self.file_handle.fileno(), 0, access = mmap.ACCESS_WRITE)

			self.read_only = False
			self.read_headers = False

		elif mode == 'x':
			"""open for exclusive creation, failing if the file already exists"""
			if headers is not None and any(not isinstance(header, Header) for header in headers):
				raise TypeError('Creation of TRS files requires passing Headers to the constructor.')

			if os.path.isfile(self.path):
				raise FileExistsError('TRS file exists: \'{0:s}\''.format(self.path))

			# Sadly, to memory map we need a file with a minimum of length 1
			self.file_handle = open(self.path, 'wb')
			self.file_handle.write(b'\x00')
			self.file_handle.close()

			self.file_handle = open(self.path, 'r+b')
			self.handle = mmap.mmap(self.file_handle.fileno(), 0, access = mmap.ACCESS_WRITE)
			self.read_only = False
			self.read_headers = False

		elif mode == 'a':
			"""a = open for writing, appending to the end of the file if it exists"""

			# Check if the file exists, if so, we read in the headers and that will be our LAW!
			if os.path.isfile(self.path):
				self.read_headers = True
			else:
				self.read_headers = False

				# We need to create an empty file
				# Sadly, to memory map we need a file with a minimum of length 1
				self.file_handle = open(self.path, 'wb')
				self.file_handle.write(b'\x00')
				self.file_handle.close()

			if self.read_headers and headers is not None:
				raise TypeError('Cannot change headers when reading TRS files.')
			elif not self.read_headers and headers is not None and any(not isinstance(header, Header) for header in headers):
				raise TypeError('Creation of TRS files requires passing instances of Headers to the constructor.')

			# NOTE: We are using r+b mode because we are essentially updating the file!
			self.file_handle = open(self.path, 'r+b')
			self.handle = mmap.mmap(self.file_handle.fileno(), 0, access = mmap.ACCESS_WRITE)
			self.read_only = False

		else:
			raise ValueError('invalid mode: \'{0:s}\''.format(mode))

		self.__initialize_headers(headers)

	def length(self):
		return self.headers.get(Header.NUMBER_TRACES, 0)

	def is_closed(self):
		return self.handle is None or self.handle.closed

	def set_traces(self, index, traces):
		# Make sure we have proper indexing
		if isinstance(index, slice):
			start, stop, step = index.indices(index.stop)
			indexes = range(start, max(stop, start + len(traces)), step)
		else:
			indexes = range(index, index + 1)

		# Check if we are appending traces directly to the end of the file
		if indexes.start > self.headers[Header.NUMBER_TRACES]:
			raise IndexError('No arbitrary indexing supported')

		# Make sure we have enough traces for every index
		if len(indexes) != len(traces):
			raise TypeError('The number of provided traces ({0:d}) have to be equal to the number of indexes ({1:d})'.format(len(traces), len(indexes)))

		# Early return
		if len(indexes) <= 0:
			return

		# Check if any of the following headers are NOT initialized:
		# - NUMBER_SAMPLES
		# - LENGTH_DATA
		# - TITLE_SPACE
		# For any of these uninitialized headers, check if all traces are the same
		# for these fields, and set them to that value.
		if self.padding_mode == TracePadding.AUTO:
			update_headers = {}
			if self.headers[Header.NUMBER_SAMPLES] is None:
				lengths = set([len(trace) for trace in traces])

				# Check padding mode on how we are going to do this
				update_headers[Header.NUMBER_SAMPLES] = max(lengths)

			if self.headers[Header.LENGTH_DATA] is None:
				if len(set([len(trace.data) for trace in traces])) > 1:
					raise TypeError('Traces have different data length, this is not supported in TRS files')
				update_headers[Header.LENGTH_DATA] = len(traces[0].data)

			if self.headers[Header.SAMPLE_CODING] is None:
				if len(set([trace.sample_coding for trace in traces])) > 1:
					raise TypeError('Traces have different sample coding, this is not supported in TRS files')
				update_headers[Header.SAMPLE_CODING] = traces[0].sample_coding

			if self.headers[Header.TITLE_SPACE] is None:
				update_headers[Header.TITLE_SPACE] = max([len(trace.title) for trace in traces])

			# Now update headers
			self.update_headers(update_headers)
		elif self.padding_mode == TracePadding.NONE:
			# We need to verify if all required headers are set, else throw an error
			required_headers = [Header.NUMBER_SAMPLES, Header.LENGTH_DATA, Header.SAMPLE_CODING, Header.TITLE_SPACE]
			missing_headers = [header for header in required_headers if header not in self.headers or self.headers[header] is None]
			if len(missing_headers) > 0:
				raise ValueError('The following headers are not set: ' + ', '.join([h.name for h in missing_headers]) + ', set these headers or use PaddingMode.AUTO')

		else:
			raise NotImplementedError('This padding mode is not supported')

		# Pre-compute some static information based on headers
		if self.sample_length is None:
			self.sample_length = self.headers[Header.NUMBER_SAMPLES] * self.headers[Header.SAMPLE_CODING].size
		if self.trace_length is None:
			self.trace_length = self.sample_length + self.headers.get(Header.LENGTH_DATA, 0) + self.headers.get(Header.TITLE_SPACE, 0)

		# Store all traces with the next sequence numbers and keep these numbers as a list
		for i, trace in zip(indexes, traces):
			# Update the trace headers to be a reference to our internal headers because that is how it is!
			trace.headers = self.headers

			# Check padding mode
			if self.padding_mode == TracePadding.NONE and len(trace) != self.headers[Header.NUMBER_SAMPLES]:
				raise ValueError('Trace has a different length from the expected length and padding mode is NONE')

			# Seek to the beginning of the trace (this automatically enables us to overwrite)
			self.file_handle.seek(self.data_offset + i * self.trace_length)

			# Title and title padding
			title = trace.title.strip().encode('utf-8')
			if len(title) > self.headers[Header.TITLE_SPACE]:
				raise TypeError('Trace title is longer than available title space')
			self.file_handle.write(title)
			if len(title) < self.headers[Header.TITLE_SPACE]:
				self.file_handle.write(bytes(self.headers[Header.TITLE_SPACE] - len(title)))

			# Data and data padding
			if self.padding_mode == TracePadding.NONE and len(trace.data) > self.headers[Header.LENGTH_DATA]:
				raise TypeError('Trace data is longer than available data space')
			self.file_handle.write(trace.data[0:self.headers[Header.LENGTH_DATA]])
			if len(trace.data) < self.headers[Header.LENGTH_DATA]:
				self.file_handle.write(bytes(self.headers[Header.LENGTH_DATA] - len(trace.data)))

			# Automatic truncate
			trace.samples[:self.headers[Header.NUMBER_SAMPLES]].tofile(self.file_handle)

			# Add any required padding
			length = (self.headers[Header.NUMBER_SAMPLES] - len(trace.samples)) * self.headers[Header.SAMPLE_CODING].size
			if length > 0:
				self.file_handle.write(length * b'\x00')

		# Write the new total number of traces
		# If you want to have live update, you can give this flag and have this
		# automatically write to the file
		new_number_traces = max(self.headers[Header.NUMBER_TRACES], max(indexes) + 1)
		if self.headers[Header.NUMBER_TRACES] < new_number_traces:
			self.is_mmap_synched = False
			self.live_update_count += len(traces)

			if self.live_update != 0 and self.live_update_count >= self.live_update:
				self.live_update_count = 0
				self.update_header(Header.NUMBER_TRACES, new_number_traces)

				# Force flush
				self.handle.flush()
				self.file_handle.flush()
				os.fsync(self.file_handle.fileno())
			else:
				self.headers[Header.NUMBER_TRACES] = new_number_traces

	def get_traces(self, index):
		# check for slicing
		if isinstance(index, slice):
			# No bounds checking when using slices, that's how python rolls!
			indexes = range(*index.indices(self.length()))
		else:
			# Wrap around for negative index
			if index < 0:
				index = index % self.length()

			# Check if we are still in bounds
			if index >= self.length():
				raise IndexError('List index out of range')

			indexes = range(index, index + 1)

		# We need to resize the mmap if we added something directly on the file handle
		# We do it here for optimization purposes, if you do not read, no resizing :)
		if not self.is_mmap_synched and not self.read_only:
			total_file_size = self.data_offset + (self.length() + 1) * self.trace_length
			if self.handle.size() < total_file_size:
				self.handle.resize(total_file_size)
			self.is_mmap_synched = True

		# Now read in all traces
		traces = []
		for i in indexes:
			# Seek to the beginning of the trace
			self.handle.seek(self.data_offset + i * self.trace_length)

			# Read the title
			if Header.TITLE_SPACE in self.headers:
				title = self.handle.read(self.headers[Header.TITLE_SPACE]).rstrip(b'\x00').decode('utf-8')
			else:
				title = ''     # No title

			# Read data
			if Header.LENGTH_DATA in self.headers:
				data = self.handle.read(self.headers[Header.LENGTH_DATA])
			else:
				data = bytes() # No data

			# Read all the samples
			samples = numpy.frombuffer(self.handle.read(self.trace_length), self.headers[Header.SAMPLE_CODING].format, self.headers[Header.NUMBER_SAMPLES])

			traces.append(Trace(self.headers[Header.SAMPLE_CODING], samples, data, title, self.headers))

		return traces

	def close(self):
		"""Closes the open file handle if it is opened"""

		# Close all handles
		if self.handle is not None and not self.handle.closed:
			# Make sure we write all headers to the file
			if not self.read_only:
				self.__write_headers({Header.NUMBER_TRACES: self.headers[Header.NUMBER_TRACES]})

			# Flush the mmap (according to docs this is important) and close
			self.handle.flush()
			self.handle.close()
		if self.file_handle is not None and not self.file_handle.closed:
			self.file_handle.close()

	def update_headers(self, headers):
		changed_headers = super().update_headers(headers)
		if len(changed_headers) > 0:
			self.__write_headers(changed_headers)

	def __initialize_headers(self, headers = None):
		"""Initialize the headers, this is done either by reading the headers from file or using headers given on creation"""
		if self.read_headers:
			self.__read_headers()
		else:
			self.__create_headers(headers)

	def __create_headers(self, headers):
		if headers is not None:
			self.headers = copy.deepcopy(headers)

		# Let's support dynamic sample coding depending on the trace
		if Header.SAMPLE_CODING not in self.headers:
			self.headers[Header.SAMPLE_CODING] = None

		# Add any mandatory headers that are missing
		for header in Header.get_mandatory():
			if not header in self.headers:
				self.headers[header] = header.default

		# Finally add some extra headers that are freaking useful if they are not provided
		# This is up for debate if somethings are missing
		if Header.TITLE_SPACE not in self.headers:
			self.headers[Header.TITLE_SPACE] = Header.TITLE_SPACE.default
		if Header.LENGTH_DATA not in self.headers:
			self.headers[Header.LENGTH_DATA] = None

		# Write the initial headers
		self.__write_headers()

	def __write_headers(self, headers = None):
		if headers is None:
			headers = self.headers

		# Check if we have any work to do
		if len(headers) <= 0:
			return

		# Save the headers
		for header, value in headers.items():
			# Skip TRACE_BLOCK header as we write that last!
			if header == Header.TRACE_BLOCK:
				continue

			# Check if we have definitions for all headers
			if not isinstance(header, Header):
				raise TypeError('Cannot write unknown header to trace set')

			# Obtain the tag value
			if header.type is int:
				tag_value = b'\xff' * header.length if value is None else value.to_bytes(header.length, 'little')
			elif header.type is float:
				tag_value = struct.pack('<f', 0.0 if value is None else value)
			elif header.type is bool:
				tag_value = struct.pack('<?', 0 if value is None else value)
			elif header.type is str:
				tag_value = value.encode('utf-8')
			elif header.type is SampleCoding:
				tag_value = b'\xff' if value is None else value.value.to_bytes(1, 'little')
			elif header.type is bytes:
				tag_value = value
			else:
				raise TypeError('Header has a type that can not be serialized')

			# The tag length is easy!
			tag_length = len(tag_value)

			# Store or reuse the header_locations
			if header in self.header_locations:
				if self.header_locations[header][1] != tag_length:
					raise TypeError('While updating a header, the length of the value changed which is not supported')

				# Update the TLV value
				offset = self.header_locations[header][0]
				self.handle[offset : offset + len(tag_value)] = tag_value
			else:
				# Construct the TLV
				tag = [header.value]
				if tag_length >= 0x80:
					tag_length_length = (tag_length.bit_length() // 8) + (1 if tag_length.bit_length() % 8 > 0 else 0)
					tag += bytes([0x80 | tag_length_length]) + tag_length.to_bytes(tag_length_length, 'little')
				else:
					tag += [tag_length]
				tag += tag_value

				# Store this index for future references
				if self.handle.size() < self.handle.tell() + len(tag):
					self.handle.resize(self.handle.tell() + len(tag))
				self.handle.write(bytes(tag))
				self.header_locations[header] = (self.handle.tell() - len(tag_value), tag_length)

		# Save the TRACE_BLOCK if not already saved
		if Header.TRACE_BLOCK not in self.header_locations:
			# Write the TRACE_BLOCK
			if self.handle.size() < self.handle.tell() + 2:
				self.handle.resize(self.handle.tell() + 2)
			self.handle.write(bytes([Header.TRACE_BLOCK.value, 0]))

			# Calculate offset
			self.data_offset = self.handle.tell()
			self.header_locations[Header.TRACE_BLOCK] = None
		elif self.data_offset is None:
			# This should never happen, but who knows?!
			raise NotImplementedError('Data offset is still None but TRACE_BLOCK TLV already in headers?!?!?!')

	def __read_headers(self):
		"""Read all internal headers from the file"""
		self.headers = {}
		self.header_locations = {}

		# Jump to the beginning of the file (should contain TLV)
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
			tag_value_index = self.handle.tell()
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
				raise NotImplementedError('Warning: tag {tag:02X} is not supported by the library, please submit an issue on Github.'.format(tag=tag))

			self.headers[tag if header is None else header] = tag_value
			self.header_locations[tag if header is None else header] = (tag_value_index, tag_length)

		# Sanity: Check if we have all mandatory headers, if not, throw an error if we are in reading mode!
		if not Header.get_mandatory().issubset(self.headers):
			raise IOError('TRS file does not contain all mandatory headers')

		# Pre-compute some static information based on headers
		self.data_offset = self.handle.tell()
		self.sample_length = self.headers[Header.NUMBER_SAMPLES] * self.headers[Header.SAMPLE_CODING].size
		self.trace_length = self.sample_length + self.headers.get(Header.LENGTH_DATA, 0) + self.headers.get(Header.TITLE_SPACE, 0)

		# Sanity: Check if the file has the proper size
		self.handle.seek(0, os.SEEK_END)
		file_size = self.handle.tell()
		if file_size != self.data_offset + self.headers[Header.NUMBER_TRACES] * self.trace_length:
			raise IOError('TRS file has an unexpected length')
