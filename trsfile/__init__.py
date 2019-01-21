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
	'Engine', 'TrsEngine', 'TmpEngine',
]

from .trace import Trace
from .common import Header, SampleCoding, TracePadding
from .trace_set import TraceSet
from .engine.engine import Engine

# All our engines
from .engine.trs import TrsEngine
from .engine.tmp import TmpEngine

def trs_open(path, mode = 'r', **options):
	return TraceSet(path, mode, **options)

open = trs_open
