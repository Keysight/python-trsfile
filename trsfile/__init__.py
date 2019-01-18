"""
The defactor trace set (.trs files) library for reading
Riscure Inspector trace files.
"""

name        = "trsfile"
__version__ = '0.2.0'
__author__  = 'Kevin Valk'
__contact__ =  'valk@riscure.com'
__all__     = ['trs_open', 'Trace', 'SampleCoding', 'Header', 'TracePadding']

from .trace import Trace
from .common import Header, SampleCoding, TracePadding
from .trsfile import TrsFile
from .trsfile_mutable import TrsFileMutable

def trs_open(path, mode = 'r', **options):
	return TrsFile(path, mode, **options)

open = trs_open
