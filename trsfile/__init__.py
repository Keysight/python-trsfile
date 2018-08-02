"""
The defactor trace set (.trs files) library for reading
Riscure Inspector trace files.
"""

name        = "trsfile"
__version__ = '0.1.1'
__author__  = 'Kevin Valk'
__contact__ =  'valk@riscure.com'
__all__     = ['trs_open', 'trs_create', 'Trace', 'SampleCoding', 'Header', 'TracePadding']

from .trace import Trace
from .common import Header, SampleCoding, TracePadding
from .trsfile import TrsFile
from .trsfile_mutable import TrsFileMutable

def open(path):
	return trs_open(path)

def create(path, padding_mode = TracePadding.PAD, force_overwrite = False):
	return trs_create(path, padding_mode, force_overwrite)

def trs_open(path):
	return TrsFile(path)

def trs_create(path, padding_mode = TracePadding.PAD, force_overwrite = False):
	return TrsFileMutable(path, padding_mode, force_overwrite)
