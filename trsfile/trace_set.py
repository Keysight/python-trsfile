import os
import mmap
import struct
import numpy
import copy

from .trace import Trace
from .common import Header, SampleCoding, TracePadding
from .engine.engine import Engine

# All our engines
from .engine.trs import TrsEngine
from .engine.tmp import TmpEngine

engines = {
	'trsengine': TrsEngine,
	'tmpengine': TmpEngine,
}

class TraceSet:
	engine = None

	def __init__(self, path, mode = 'r', **options):
		# Get the storage engine if one is given, else default to TrsEngine
		engine = options.get('engine', TrsEngine)
		if 'engine' in options:
			del options['engine']

		# We also support engine to be passed as string, if so we need to eval
		if isinstance(engine, str):
			engine_name = engine.lower().rstrip('engine') + 'engine'
			if engine_name not in engines:
				raise ValueError('The storage engine does not exists')
			engine = engines[engine_name]

		# Check type
		if not issubclass(engine, Engine):
			raise TypeError('The storage engine has to be of type \'Engine\'')

		self.engine = engine(path, mode, **options)

	def __del__(self):
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
		if self.engine.is_closed():
			raise ValueError('I/O operation on closed file')
		return self

	def __exit__(self, *args):
		"""Called when exiting a `with` block"""
		self.close()

	def __repr__(self):
		if len(self) <= 0:
			return '<TraceSet (0), empty>'
		else:
			return '<TraceSet ({0:d}), {1:s}, ... ,{2:s}>'.format(len(self), repr(self[0]), repr(self[-1]))

	def __len__(self):
		return self.engine.length()

	def __delitem__(self, index):
		if self.engine.is_read_only():
			raise TypeError('Cannot modify trace set, it is (opened) read-only')

		return self.engine.del_traces(index)

	def __setitem__(self, index, traces):
		if self.engine.is_read_only():
			raise TypeError('Cannot modify trace set, it is (opened) read-only')

		# Make sure we have iterable traces
		if isinstance(traces, Trace):
			traces = [traces]

		# Make sure we only are setting traces
		if any(not isinstance(trace, Trace) for trace in traces):
			raise TypeError('All objects assigned to a trace set needs to be of type \'Trace\'')

		return self.engine.set_traces(index, traces)

	def __getitem__(self, index):
		traces = self.engine.get_traces(index)

		# Return the select item(s)
		if isinstance(index, slice):
			return traces
		else:
			# Earlier logic should ensure traces contains one element!
			return traces[0]

	def is_closed(self):
		return self.engine.is_closed()

	def close(self):
		if self.engine is not None:
			self.engine.close()

	def append(self, trace):
		if self.engine.is_read_only():
			raise TypeError('Cannot modify trace set, it is (opened) read-only')

		self[len(self):len(self)] = trace

	def extend(self, traces):
		if self.engine.is_read_only():
			raise TypeError('Cannot modify trace set, it is (opened) read-only')

		self[len(self):len(self)] = traces

	def insert(self, index, trace):
		if self.engine.is_read_only():
			raise TypeError('Cannot modify trace set, it is (opened) read-only')

		self.engine.insert(index, trace)

	def reverse(self):
		return self[::-1]

	def update_headers(self, headers):
		return self.engine.update_headers(headers)

	def update_header(self, header, value):
		return self.engine.update_header(header, value)

	def get_headers(self):
		return self.engine.headers

	def get_header(self, header):
		return self.engine.headers[header]

	def __eq__(self, other):
		"""Compares two trace sets to each other"""

		if not isinstance(other, TrsFile):
			return False

		if len(self) != len(other):
			return False

		# Not using any, because we want to stop as soon as a difference arises
		for self_trace, other_trace in zip(self, other):
			if self_trace != other_trace:
				return False

		return True
