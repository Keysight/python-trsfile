from trsfile.common import Header

class Engine:
	read_only = False

	def __init__(self, path, mode = 'x', **options):
		"""Initializes a storage engine for the specified format.

		:param path: relative or absolute path to the file
		:param mode: in which mode to open the file (r, w, a, x)
		:param **options: options that this engine supports, the Engine specifies
			which options are supported.
		:type path: str
		:type mode: str
		:type **options: dict(str, any)
		"""
		raise NotImplementedError('Implement \'__init__\' for the storage engine')

	def close(self):
		"""Closes the file backing the trace set. It also could perform the
		final writes to synchronize the file with the trace set.

		:returns: None
		"""
		raise NotImplementedError('Implement \'close\' for the storage engine')

	def length(self):
		"""Returns the total number of traces

		:returns: total number of traces
		:rtype: int
		"""
		raise NotImplementedError('Implement \'length\' for the storage engine')

	def is_closed(self):
		"""Returns if the file backing the trace set is closed

		:returns: True if the file is closed, otherwise False
		:rtype: boolean
		"""
		raise NotImplementedError('Implement \'is_closed\' for the storage engine')

	def is_read_only(self):
		"""Returns if the trace set is read-only

		:returns: True if the file is read-only, otherwise False
		:rtype: boolean
		"""
		return self.read_only

	# Functions that are optionally implemented
	def del_traces(self, index):
		"""Deletes zero or more traces from the trace set

		:param index: the slice or index that specifies which traces to delete
		:type index: slice, int
		:returns: None
		"""
		raise TypeError('Cannot remove traces with this storage engine')

	def set_traces(self, index, traces):
		"""Inserts zero or more traces into the trace set

		:param index: the slice or index that specifies were to insert traces
		:param traces: zero or more traces to insert into the trace set
		:type index: slice, int
		:type traces: Trace, list[Trace]
		:returns: None
		"""
		raise TypeError('Cannot change traces with this storage engine')

	def get_traces(self, index):
		"""Retrieves zero or more traces from the trace set

		:param index: the slice or index that specifies which traces to get
		:type index: slice, int
		:returns: a list of zero or more traces from the trace set
		:rtype: Trace, list[Trace]
		"""
		raise TypeError('Cannot get traces with this storage engine')

	# The headers as defined by the TRS specifications
	def update_headers(self, headers):
		"""Updates zero or more headers

		:param headers: dictionary of header, value pairs to update
		:type headers: dict(Header, any)
		:returns: a list of the headers that changed
		:rtype: list[Header]
		"""
		# Early return
		if headers is None:
			return []

		if self.is_read_only():
			raise TypeError('Cannot modify trace set, it is (opened) read-only')

		if not isinstance(headers, dict) or any([not isinstance(header, Header) for header in self.headers]):
			raise TypeError('All headers have to be of type \'Header\'')

		# TODO: We can test the header type here, do we want to?

		# Only update headers that are changed
		changed_headers = {}
		for header, value in headers.items():
			if header in self.headers and value == self.headers[header]:
				continue
			changed_headers[header] = value

		# Do nothing if nothing has changed
		if len(changed_headers) <= 0:
			return []

		# Update internally the headers
		self.headers.update(changed_headers)

		# Notify that headers have been changed
		return changed_headers

	def update_header(self, header, value):
		"""Updates one specific header

		:param header: header to update
		:param value: value of the header to update
		:type header: Header
		:type value: any
		:returns: a list of the headers that changed
		:rtype: list[Header]
		"""
		return self.update_headers({header: value})
