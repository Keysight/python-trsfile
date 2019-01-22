"""
The defactor trace set (.trs files) library for reading
Riscure Inspector trace files.
"""

name        = "trsfile"
__version__ = '0.2.0'
__author__  = 'Kevin Valk'
__contact__ =  'valk@riscure.com'
__all__     = [
	'trs_open', 'Trace', 'TraceSet', 'SampleCoding', 'Header', 'TracePadding', \
	'Engine', 'TrsEngine', 'FileEngine',
]

from .trace import Trace
from .common import Header, SampleCoding, TracePadding
from .trace_set import TraceSet
from .engine.engine import Engine

# All our engines
from .engine.trs import TrsEngine
from .engine.file import FileEngine

def trs_open(path, mode = 'r', **options):
	"""Reads, modifies or creates a :py:obj:`TraceSet` with a specific storage
	engine (defaults to :py:obj:`TrsEngine`).

	:param path: path to the file or directory
	:param mode: mode how to open the file or directory (same as the default
		Python :py:obj:`open`)
	:param options: zero or more options that are passed down to the
		:py:obj:`TraceSet` and the storage engine. Available options can be found
		in the different storage engines. The storage engine can be selected with
		:code:`engine = 'TrsEngine'` (default value).
	:type path: str
	:type mode: str
	:type options: dict(str, any)
	:returns: instance of a new or initialized :py:obj:`TraceSet`
	:rtype: TraceSet
	"""
	return TraceSet(path, mode, **options)

open = trs_open
