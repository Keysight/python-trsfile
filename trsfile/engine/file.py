import shutil
import time
import numpy
import pickle
from pathlib import Path

from trsfile.common import Header, SampleCoding
from trsfile.engine.engine import Engine
from trsfile.parametermap import TraceParameterMap
from trsfile.trace import Trace
from trsfile.traceparameter import ByteArrayParameter


class FileEngine(Engine):
	"""
	This engine tries to save traces to disk in the most versatile and simple
	manner available. No known tools support this file format and serve only as
	an intermediate step to later convert it to a supported format.

	This is can be useful when the trace length (number of samples) varies as
	this is often not supported in trace files.

	After acquisition, the file can be converted to the proper format with the
	correct padding mode.

	This engine supports the following options:

	+--------------+-----------------------------------------------------------+
	| Option       | Description                                               |
	+==============+===========================================================+
	| headers      | Dictionary containing zero or more headers, see           |
	|              | :py:class:`trsfile.common.Header`                         |
	+--------------+-----------------------------------------------------------+
	"""

	INFO_FILE = 'traceset.pickle'

	def __get_trace_path(self, i, name):
		return (self.path / '{0:d}.{1:s}'.format(i, name))

	def __init__(self, path, mode = 'x', **options):
		# Defaults
		self.path = Path(path)
		self.headers = {}
		self.read_only = False

		# Shadow list of traces in files
		self.shadow_trace_index = -1
		self.shadow_traces = []

		# Parse the mode
		if mode == 'r':
			"""r = open for reading"""
			if not self.path.is_dir() or not (self.path / self.INFO_FILE).is_file():
				raise FileNotFoundError('Path \'{0:s}\' does not point to a tmp trace set'.format(path))

			# Load the headers
			with (self.path / self.INFO_FILE).open('rb') as f:
				self.headers = pickle.load(f)

			# Initialize the shadow_traces list
			self.shadow_traces = sorted([int(trace_path.stem) for trace_path in self.path.glob('*.samples')])
			self.shadow_trace_index = max(self.shadow_traces) + 1

			self.read_only = True

		elif mode == 'w':
			"""open for writing, truncating the file first"""

			# Remove the directory if it exists
			if self.path.is_dir():
				shutil.rmtree(str(self.path), True)

				# Wait until it is removed
				try:
					while self.path.is_dir():
						time.sleep(0.001)
				except:
					pass

			# Create the temporary folder and initialize this class
			self.path.mkdir()
			self.__initialize_headers()

		elif mode == 'x':
			"""open for exclusive creation, failing if the file already exists (default)"""
			if self.path.is_dir():
				raise FileExistsError('Trace set already exists at path \'{0:s}\''.format(str(self.path)))

			# Create the temporary folder and initialize this class
			self.path.mkdir()
			self.__initialize_headers()

		elif mode == 'a':
			"""a = open for writing, appending to the end of the file if it exists"""
			if self.path.is_dir() and (self.path / self.INFO_FILE).is_file():
				# Load the headers
				with (self.path / self.INFO_FILE).open('rb') as f:
					self.headers = pickle.load(f)

				# Initialize the shadow_traces list
				self.shadow_traces = sorted([int(trace_path.stem) for trace_path in self.path.glob('*.samples')])
				self.shadow_trace_index = max(self.shadow_traces) + 1
			else:
				# Create the temporary folder and initialize this class
				self.path.mkdir()
				self.__initialize_headers()

		else:
			raise ValueError('invalid mode: \'{0:s}\''.format(mode))

		# Update the headers
		headers = options.get('headers', None)
		if self.is_read_only() and headers is not None:
			raise ValueError('Cannot add headers when opening in read-only mode')
		elif headers is not None:
			self.update_headers(headers)

	def __initialize_headers(self):
		headers = {}

		# Let's support dynamic sample coding depending on the trace
		headers[Header.SAMPLE_CODING] = None

		# Add any mandatory headers that are missing
		for header in Header.get_mandatory():
			if not header in headers:
				headers[header] = header.default

		# Store these default headers
		self.update_headers(headers)

	def update_headers(self, headers):
		changed_headers = super().update_headers(headers)
		if len(changed_headers) > 0:
			# Dump all headers to disk
			with (self.path / self.INFO_FILE).open('wb') as f:
				pickle.dump(self.headers, f)

	def is_closed(self):
		return not self.path.is_dir() or not (self.path / self.INFO_FILE).is_file()

	def length(self):
		return len(self.shadow_traces)

	def del_traces(self, index):
		# Remove the shadow traces and with that check if indexes are correct
		exception = None
		try:
			indices = self.shadow_traces[index]
			del self.shadow_traces[index]

			if not isinstance(index, slice):
				indices = [indices]
		except IndexError as err:
			exception = err

		# Do we have an exception, re-raise
		if exception is not None:
			raise IndexError(exception)

		# Delete all traces on the file system
		for trace_index in indices:
			for category in ['title', 'data', 'samples']:
				path = self.__get_trace_path(trace_index, category)
				if path.is_file():
					path.unlink()

	def get_traces(self, index):
		# Try access, and re-raise if wrong for fancy indexing errors
		try:
			indices = self.shadow_traces[index]
			if not isinstance(index, slice):
				indices = [indices]
		except IndexError as exception:
			raise IndexError(exception)

		# Now obtain all requested traces from file
		traces = []
		for i in indices:
			# Read the samples
			path = self.__get_trace_path(i, 'samples')
			if path.is_file():
				with path.open('rb') as tmp_file:
					# First byte is always sample coding
					sample_coding = SampleCoding(tmp_file.read(1)[0])
					samples = numpy.fromfile(tmp_file, sample_coding.format, -1)
			else:
				raise IOError('Unable to read samples from trace {0:d}'.format(i))

			# Title
			path = self.__get_trace_path(i, 'title')
			if path.is_file():
				with path.open('rb') as tmp_file:
					title = tmp_file.read().decode('utf-8')
			else:
				title = Header.TRACE_TITLE.default

			# Read the data
			path = self.__get_trace_path(i, 'data')
			if path.is_file():
				with path.open('rb') as tmp_file:
					data = tmp_file.read()
			else:
				data = b''

			parameters = TraceParameterMap()
			if data:
				parameters['LEGACY_DATA'] = ByteArrayParameter(data)
			# Create trace and make sure headers point to our dict
			traces.append(Trace(sample_coding, samples, parameters, title, self.headers))

		return traces

	def set_traces(self, index, traces):
		# Make sure we have iterable traces
		if isinstance(traces, Trace):
			traces = [traces]

		# Get all traces that we are going to remove
		try:
			indices = self.shadow_traces[index]
			if not isinstance(index, slice):
				indices = [indices]
		except IndexError as exception:
			raise IndexError(exception)

		# Remove the traces from disk only to keep storage lean and mean
		for trace_index in indices:
			for category in ['title', 'data', 'samples']:
				path = self.__get_trace_path(trace_index, category)
				if path.is_file():
					path.unlink()

		# Store all traces with the next sequence numbers and keep these numbers as a list
		new_traces = []
		for trace in traces:
			self.shadow_trace_index += 1
			new_traces.append(self.shadow_trace_index)

			# Save the trace data
			# Write the title as ascii
			with self.__get_trace_path(self.shadow_trace_index, 'title').open('wb') as tmp_file:
				tmp_file.write(trace.title if not isinstance(trace.title, str) else trace.title.encode('utf-8'))

			# Write the data file
			if trace.parameters is not None and len(trace.parameters) > 0:
				with open(self.__get_trace_path(self.shadow_trace_index, 'data'), 'wb') as tmp_file:
					tmp_file.write(trace.parameters.serialize())

			# Write the sample file
			with open(self.__get_trace_path(self.shadow_trace_index, 'samples'), 'wb') as tmp_file:
				tmp_file.write(bytes([trace.sample_coding.value]))
				trace.samples.tofile(tmp_file)

		# Now we just assign the new_traces however, the slicing works
		if isinstance(index, slice):
			self.shadow_traces[index] = new_traces
		else:
			if len(new_traces) != 1:
				raise TypeError('assigning multiple new traces to single trace')
			self.shadow_traces[index] = new_traces[0]

	def close(self):
		# We do not need to close anything :)
		pass
