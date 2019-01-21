from ..common import Header

class Engine:
	read_only = False

	def __init__(self, path, mode = 'x', **options):
		raise NotImplementedError('Implement \'__init__\' for the storage engine')

	def close(self):
		raise NotImplementedError('Implement \'close\' for the storage engine')

	def length(self):
		raise NotImplementedError('Implement \'length\' for the storage engine')

	def is_closed(self):
		raise NotImplementedError('Implement \'is_closed\' for the storage engine')

	def is_read_only(self):
		return self.read_only

	# Functions that are optionally implemented
	def del_traces(self, index):
		raise TypeError('Cannot remove traces with this storage engine')

	def set_traces(self, index, traces):
		raise TypeError('Cannot change traces with this storage engine')

	def get_traces(self, index):
		raise TypeError('Cannot get traces with this storage engine')

	# The headers as defined by the TRS specifications
	def update_headers(self, headers):
		"""Updates zero or more headers of this TRS file, returns True on change"""
		if self.is_read_only():
			raise TypeError('Cannot modify trace set, it is (opened) read-only')

		# Early return
		if headers is None:
			return []

		if not isinstance(headers, dict) or any([not isinstance(header, Header) for header in self.headers]):
			raise TypeError('All headers have to be of type \'Header\'')

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
		"""Updates one single header, returns true on change"""
		return self.update_headers({header: value})
