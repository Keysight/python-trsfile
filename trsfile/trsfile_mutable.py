import os
import struct
import shutil
import numpy
import math

from .trace import Trace
from .common import Header, SampleCoding, TracePadding
from .trsfile import TrsFile

class TrsFileMutable(TrsFile):
	temp_folder = None
	is_saved = False

	def __init__(self, path, padding_mode = TracePadding.PAD, force_overwrite = False):
		# Check if trs file already exists, warn if it does
		if not force_overwrite and os.path.isfile(path):
			raise IOError('trs file already exists, use force_overwrite argument to overwrite.')

		self.path = path
		self.padding_mode = padding_mode

		# Shadow list of traces in files
		self.shadow_trace_index = -1
		self.shadow_traces = []

		# Create the temporary folder
		self.file_path, self.file_ext = os.path.splitext(self.path)
		if len(self.file_ext) <= 1:
			self.file_ext = '.trs'
		self.temp_folder = self.file_path + '.tmp'

		# Make sure to always start with a fresh start
		if os.path.isdir(self.temp_folder):
			shutil.rmtree(self.temp_folder, True)
		os.mkdir(self.temp_folder)

		self.__initialize_headers()

	def __del__(self):
		if self.temp_folder is not None and os.path.isdir(self.temp_folder):
			shutil.rmtree(self.temp_folder, True)

	def __enter__(self):
		"""Called when entering a `with` block"""

		if not os.path.isdir(self.temp_folder):
			raise ValueError('temp folder for traces does not exists')
		return self

	def __len__(self):
		"""Returns the total number of traces"""

		return len(self.shadow_traces)

	def __delitem__(self, index):
		self.is_saved = False
		# Remove the shadow traces and with that check if indexes are correct
		exception = None
		try:
			indices = self.shadow_traces[index]
			del self.shadow_traces[index]

			if not isinstance(index, slice):
				indices = [indices]
		except IndexError as err:
			exception = err

		# Delete all traces on the file system
		for trace_index in indices:
			for category in ['title', 'data', 'samples']:
				path = self.__get_temp_trace(trace_index, category)
				if os.path.isfile(path):
					os.remove(path)

		# Do we have an exception, re-raise
		if exception is not None:
			raise IndexError(exception)

	def __getitem__(self, index):
		self.is_saved = False
		traces = []

		# Try access, and re-raise if wrong for fancy indexing errors
		try:
			indices = self.shadow_traces[index]
			if not isinstance(index, slice):
				indices = [indices]
		except IndexError as exception:
			raise IndexError(exception)

		# Now obtain all requested traces from file
		for i in indices:
			samples = None

			# Read the samples
			path = self.__get_temp_trace(i, 'samples')
			if os.path.isfile(path):
				with open(path, 'rb') as tmp_file:
					# First byte is always sample coding
					sample_coding = SampleCoding(tmp_file.read(1)[0])
					samples = numpy.fromfile(tmp_file, sample_coding.format, -1)

			# Title
			path = self.__get_temp_trace(i, 'title')
			if os.path.isfile(path):
				with open(path, 'rb') as tmp_file:
					title = tmp_file.read().decode('utf-8')
			else:
				title = Header.TRACE_TITLE.default

			# Read the data
			path = self.__get_temp_trace(i, 'data')
			if os.path.isfile(path):
				with open(path, 'rb') as tmp_file:
					data = tmp_file.read()
			else:
				data = b''

			# Sanity check
			if samples is None:
				raise IOError('unable to read samples from trace {0:d}'.format(i))

			traces.append(Trace(sample_coding, samples, data, title, self.headers))

		# Return the list of traces, or single trace
		if isinstance(index, slice):
			return traces
		else:
			# Earlier logic should ensure traces contains one element!
			return traces[0]

	def __setitem__(self, index, traces):
		self.is_saved = False

		# Make sure we have iterable traces
		if isinstance(traces, Trace):
			traces = [traces]

		# Store all traces with the next sequence numbers and keep these numbers as a list
		new_traces = []
		for trace in traces:
			# Make sure we do not do something weird
			if not isinstance(trace, Trace):
				raise ValueError('the data added to the trace set is not of type Trace')

			self.shadow_trace_index += 1
			new_traces.append(self.shadow_trace_index)

			# Save the trace data
			# Write the title as ascii
			with open(self.__get_temp_trace(self.shadow_trace_index, 'title'), 'wb') as tmp_file:
				tmp_file.write(trace.title if not isinstance(trace.title, str) else trace.title.encode('utf-8'))

			# Write the data file
			if trace.data is not None and len(trace.data) > 0:
				with open(self.__get_temp_trace(self.shadow_trace_index, 'data'), 'wb') as tmp_file:
					tmp_file.write(trace.data)

			# Write the sample file
			with open(self.__get_temp_trace(self.shadow_trace_index, 'samples'), 'wb') as tmp_file:
				tmp_file.write(bytes([trace.sample_coding.value]))
				numpy.array(trace.samples).astype(trace.sample_coding.format).tofile(tmp_file)

		# Lets delete the files that we are replacing to prevent storage explosions
		try:
			indices = self.shadow_traces[index]
			if not isinstance(index, slice):
				indices = [indices]
		except IndexError as exception:
			raise IndexError(exception)

		for i in indices:
			for category in ['title', 'data', 'samples']:
				path = self.__get_temp_trace(i, category)
				if os.path.isfile(path):
					os.remove(path)

		# Now we just assign the new_traces however, the slicing works
		if isinstance(index, slice):
			self.shadow_traces[index] = new_traces
		else:
			if len(new_traces) != 1:
				raise TypeError('assigning multiple new traces to single trace')
			self.shadow_traces[index] = new_traces[0]

	def save(self, padding_mode = None):
		# Do not save twice, just a waste!
		if self.is_saved:
			return

		# Get argument or default
		padding_mode = self.padding_mode if padding_mode is None else padding_mode

		# Calculate some fields
		check_values = {}
		check_values[Header.NUMBER_SAMPLES] = set([len(trace) for trace in self])
		check_values[Header.SAMPLE_CODING]  = set([trace.sample_coding for trace in self])
		check_values[Header.LENGTH_DATA]    = set([len(trace.data) for trace in self])

		# Calculate headers based on shadow list
		for header in Header.get_mandatory():
			if not header in self.headers:
				self.headers[header] = header.default

		# Check padding mode
		if padding_mode == TracePadding.PAD:
			check_values[Header.NUMBER_SAMPLES] = [max(check_values[Header.NUMBER_SAMPLES])]
		elif padding_mode == TracePadding.TRUNCATE:
			check_values[Header.NUMBER_SAMPLES] = [min(check_values[Header.NUMBER_SAMPLES])]

		# Set the headers and make sure all traces share the common header settings
		self.headers[Header.NUMBER_TRACES]  = len(self)
		self.headers[Header.TITLE_SPACE]    = max([len(trace.title) for trace in self])
		for header, check_values in check_values.items():
			if len(check_values) != 1:
				raise TypeError('traces have different values for header {0:s}'.format(header.name))
			self.headers[header] = check_values.pop()

		# Save the file
		with open(self.path, 'wb') as trs_file:

			# Save the headers
			for header, value in self.headers.items():
				# Skip TRACE_BLOCK header as we write that last!
				if header == Header.TRACE_BLOCK:
					continue

				# Check if we have definitions for all headers
				if not isinstance(header, Header):
					# TODO: Make this proper
					print('Warning, can not write unknown header X')
					continue

				# Obtain the tag value
				if header.type is int:
					tag_value = value.to_bytes(header.length, 'little')
				elif header.type is float:
					tag_value = struct.pack('<f', value)
				elif header.type is bool:
					tag_value = struct.pack('<?', value)
				elif header.type is str:
					tag_value = value.encode('utf-8')
				elif header.type is SampleCoding:
					tag_value = value.value.to_bytes(1, 'little')
				elif header.type is bytes:
					tag_value = value
				else:
					print('Warning, missing bla, to bla', header, header.type)
					continue

				# Write the Tag
				trs_file.write(bytes([header.value]))

				# Write the Length
				tag_length = len(tag_value)
				if tag_length >= 0x80:
					tag_length_length = math.ceil(x.bit_length() / 8.0)
					trs_file.write(bytes([0x80 | tag_length_length]) + tag_length.to_bytes(tag_length_length, 'little'))
				else:
					trs_file.write(bytes([tag_length]))

				# Write the value
				trs_file.write(tag_value)

			# Save the TRACE_BLOCK
			trs_file.write(bytes([Header.TRACE_BLOCK.value, 0]))

			# Start saving all traces
			for trace in self:
				# Title and title padding
				title = trace.title.encode('utf-8')
				trs_file.write(title)
				if len(title) < self.headers[Header.TITLE_SPACE]:
					trs_file.write(bytes([0] * (self.headers[Header.TITLE_SPACE] - len(title))))

				# Data
				trs_file.write(trace.data)

				# Automatic truncate
				numpy.array(trace.samples[:self.headers[Header.NUMBER_SAMPLES]]) \
				.astype(self.headers[Header.SAMPLE_CODING].format).tofile(trs_file)

				# Add any required padding
				if len(trace.samples) < self.headers[Header.NUMBER_SAMPLES]:
					numpy.array([0] * (self.headers[Header.NUMBER_SAMPLES] - len(trace.samples))) \
					.astype(self.headers[Header.SAMPLE_CODING].format).tofile(trs_file)

		# Set save flag to true
		self.is_saved = True

	def close(self):
		# Make sure to save any changes if we are creating a trace file
		self.save()

	def append(self, trace):
		self[len(self):len(self)] = trace

	def extend(self, traces):
		self[len(self):len(self)] = traces

	def insert(self, index, trace):
		self[index:index] = [trace]

	def __get_temp_trace(self, i, name):
		return self.temp_folder + '/{0:d}.{1:s}'.format(i, name)

	def __initialize_headers(self):
		"""Read all internal headers from the file"""
		self.headers = {}
