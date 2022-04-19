import os
import unittest
from os.path import abspath, dirname

from numpy import random

import trsfile
from trsfile import Header, SampleCoding, Trace, TracePadding


class TestHeader(unittest.TestCase):
    # These tests apply to creating a new traceset file:
    file_name = dirname(abspath(__file__)) + '/data/90x500xfloat_trsv2.trs'

    def setUp(self):
        self.trs_file = trsfile.open(self.file_name, engine='TrsEngine', mode='w', padding_mode=TracePadding.AUTO)

    def tearDown(self):
        self.trs_file.close()
        os.remove(self.file_name)

    def test_header_append(self):
        # Retrieve the header size and traceblock location before the append
        start_traceblock_offset = self.trs_file.engine.traceblock_offset
        start_traceblock_tuple = self.trs_file.engine.header_locations[Header.TRACE_BLOCK]
        self.assertEqual(start_traceblock_tuple[0], start_traceblock_offset)

        # Add data into the header and verify that the traceblock location changes
        self.trs_file.update_header(Header.TRS_VERSION, 1)
        updated_traceblock_offset = self.trs_file.engine.traceblock_offset
        updated_traceblock_tuple = self.trs_file.engine.header_locations[Header.TRACE_BLOCK]
        self.assertEqual(updated_traceblock_tuple[0], updated_traceblock_offset)
        self.assertEqual(start_traceblock_offset + 3, updated_traceblock_offset)


    def test_header_append_error(self):
        # Assert that after trace data has been added into the traceset, the header can not be appended any longer
        trace = Trace(SampleCoding.BYTE, random.randint(255, size=1000))
        self.trs_file.append(trace)
        with self.assertRaises(IOError):
            self.trs_file.update_header(Header.TRS_VERSION, 1)
