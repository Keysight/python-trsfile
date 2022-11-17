import copy
import os
import unittest
from os.path import abspath, dirname

from numpy import random

import trsfile
from trsfile import Header, SampleCoding, Trace, TracePadding
from trsfile.parametermap import TraceParameterDefinitionMap, TraceSetParameterMap
from trsfile.traceparameter import FloatArrayParameter, ParameterType, TraceParameterDefinition, StringParameter


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

    def test_trace_set_params_append_errors(self):
        trace_set_parameter_map = TraceSetParameterMap()
        trace_set_parameter_map["Y_SCALE"] = FloatArrayParameter([0.01])
        self.trs_file.update_header(Header.TRACE_SET_PARAMETERS, trace_set_parameter_map)

        # Verify that changing the TraceSetParameterMap after it has been used in the header is not allowed
        with self.assertRaises(TypeError):
            trace_set_parameter_map["X_SCALE"] = FloatArrayParameter([0.01])
        with self.assertRaises(TypeError):
            del trace_set_parameter_map["Y_SCALE"]
        with self.assertRaises(TypeError):
            trace_set_parameter_map.pop("Y_SCALE")
        with self.assertRaises(TypeError):
            trace_set_parameter_map.popitem()
        with self.assertRaises(TypeError):
            trace_set_parameter_map.clear()

        # Shallow copies still share references to the same trace set parameters as the original,
        # and should therefore not be modifiable if the original isn't
        with self.assertRaises(TypeError):
            shallow_copy = trace_set_parameter_map.copy()
            shallow_copy["X_SCALE"] = FloatArrayParameter([0.01])
        with self.assertRaises(TypeError):
            shallow_copy = copy.copy(trace_set_parameter_map)
            shallow_copy["X_SCALE"] = FloatArrayParameter([0.01])

        # Deep copies of the TraceSetParameterMap should both be modifiable
        deep_copy = copy.deepcopy(trace_set_parameter_map)
        deep_copy["X_SCALE"] = FloatArrayParameter([0.01])

        # Verify that setting the TraceSetParameterMap to one with a different length is not allowed
        with self.assertRaises(TypeError):
            new_trace_set_parameter_map = TraceSetParameterMap()
            new_trace_set_parameter_map["DESCRIPTION"] = StringParameter("Some text")
            self.trs_file.update_header(Header.TRACE_SET_PARAMETERS, new_trace_set_parameter_map)

    def test_trace_param_defs_append_errors(self):
        trace_parameter_definitions = TraceParameterDefinitionMap()
        self.trs_file.update_header(Header.TRACE_PARAMETER_DEFINITIONS, trace_parameter_definitions)

        # Verify that changing the TraceParameterDefinitionMap after it has been used in the header is not allowed
        with self.assertRaises(TypeError):
            trace_parameter_definitions["INPUT"] = TraceParameterDefinition(ParameterType.BYTE, 16, 0)

        # Verify that changing the TraceParameterDefinitionMap after it has been used in the header is not allowed
        with self.assertRaises(TypeError):
            trace_parameter_definitions["OUTPUT"] = TraceParameterDefinition(ParameterType.BYTE, 16, 16)
        with self.assertRaises(TypeError):
            del trace_parameter_definitions["INPUT"]
        with self.assertRaises(TypeError):
            trace_parameter_definitions.pop("INPUT")
        with self.assertRaises(TypeError):
            trace_parameter_definitions.popitem()
        with self.assertRaises(TypeError):
            trace_parameter_definitions.clear()
        with self.assertRaises(TypeError):
            trace_parameter_definitions.append('input', ParameterType.BYTE, 16)
        with self.assertRaises(TypeError):
            trace_parameter_definitions.insert('output', ParameterType.BYTE, 16, 0)

        # Shallow copies still share references to the same trace set parameters as the original,
        # and should therefore not be modifiable if the original isn't
        with self.assertRaises(TypeError):
            shallow_copy = trace_parameter_definitions.copy()
            shallow_copy["OUTPUT"] = TraceParameterDefinition(ParameterType.BYTE, 16, 16)
        with self.assertRaises(TypeError):
            shallow_copy = copy.copy(trace_parameter_definitions)
            shallow_copy["OUTPUT"] = TraceParameterDefinition(ParameterType.BYTE, 16, 16)

        # Deep copies of the TraceParameterDefinitionMap should both be modifiable
        deep_copy = copy.deepcopy(trace_parameter_definitions)
        deep_copy["OUTPUT"] = TraceParameterDefinition(ParameterType.BYTE, 16, 16)

        # Verify that setting the TraceParameterDefinitionMap to one with a different length is not allowed
        with self.assertRaises(TypeError):
            new_trace_parameter_definitions = TraceParameterDefinitionMap()
            new_trace_parameter_definitions["INPUT"] = TraceParameterDefinition(ParameterType.BYTE, 16, 0)
            new_trace_parameter_definitions["OUTPUT"] = TraceParameterDefinition(ParameterType.BYTE, 16, 16)
            self.trs_file.update_header(Header.TRACE_PARAMETER_DEFINITIONS, new_trace_parameter_definitions)

    def test_header_append_error(self):
        # Assert that after trace data has been added into the traceset, the header can not be appended any longer
        trace = Trace(SampleCoding.BYTE, random.randint(255, size=1000))
        self.trs_file.append(trace)
        with self.assertRaises(IOError):
            self.trs_file.update_header(Header.DESCRIPTION, "Some text")
