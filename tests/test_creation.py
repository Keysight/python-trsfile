import os
import trsfile
import time
import tempfile
import unittest
import math
import shutil

from trsfile import Trace, SampleCoding, Header, TracePadding
from trsfile.parametermap import TraceParameterMap, TraceParameterDefinitionMap, TraceSetParameterMap, RawTraceData
from trsfile.standardparameters import StandardTraceSetParameters
from trsfile.traceparameter import ByteArrayParameter, TraceParameterDefinition, ParameterType, StringParameter, \
    IntegerArrayParameter, BooleanArrayParameter, FloatArrayParameter


def get_sample(x):
    return math.sin(0.5 * x) * 1000


class TestCreation(unittest.TestCase):

    def setUp(self):
        # We want a tmp file name in a safe way
        fd, self.tmp_path = tempfile.mkstemp(prefix='trsfile_')

        # However, some tests require the file to not yet exist
        os.close(fd)
        os.remove(self.tmp_path)

        # Small guard for windows to prevent some weird race conditions...
        time.sleep(0.01)

    def tearDown(self):
        # Perform any cleanup of the file
        try:
            if os.path.isfile(self.tmp_path):
                os.remove(self.tmp_path)
            elif os.path.isdir(self.tmp_path):
                shutil.rmtree(self.tmp_path, True)
                time.sleep(0.01)
        except FileNotFoundError:
            pass

    def test_write(self):
        trace_count = 100
        sample_count = 1000

        try:
            with trsfile.open(self.tmp_path, 'w', headers = {
                    Header.LABEL_X: 'Testing X',
                    Header.LABEL_Y: 'Testing Y',
                    Header.DESCRIPTION: 'Testing trace creation',
                }, padding_mode = TracePadding.AUTO) as trs_traces:
                trs_traces.extend([
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * sample_count,
                        TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(i.to_bytes(8, byteorder='big'))})
                    )
                    for i in range(0, trace_count)]
                )
        except Exception as e:
            self.fail('Exception occurred: ' + str(e))

    def test_defaults(self):
        trace_count = 100
        sample_count = 1000

        default_trace_set_parameters = TraceSetParameterMap({
            'DISPLAY_HINT:X_LABEL': StringParameter(""),
            'DISPLAY_HINT:Y_LABEL': StringParameter(""),
            'DISPLAY_HINT:NUM_TRACES_SHOWN': IntegerArrayParameter([1]),
            'DISPLAY_HINT:TRACES_OVERLAP': BooleanArrayParameter([False]),
            'DISPLAY_HINT:USE_LOG_SCALE': BooleanArrayParameter([False]),
            'X_OFFSET': IntegerArrayParameter([0]),
            'TRACE_OFFSET': IntegerArrayParameter([0]),
            'X_SCALE': FloatArrayParameter([1.0]),
            'Y_SCALE': FloatArrayParameter([1.0])
        })

        try:
            with trsfile.open(self.tmp_path, 'w') as trs_traces:
                trs_traces.extend([
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * sample_count,
                        TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(i.to_bytes(8, byteorder='big'))})
                    )
                    for i in range(0, trace_count)]
                )
                headers = trs_traces.get_headers()
                expected_definitions = TraceParameterDefinitionMap(
                    {'LEGACY_DATA': TraceParameterDefinition(ParameterType.BYTE, 8, 0)})
                self.assertDictEqual(headers[Header.TRACE_PARAMETER_DEFINITIONS], expected_definitions)
                self.assertDictEqual(headers[Header.TRACE_SET_PARAMETERS], default_trace_set_parameters)
                self.assertEqual(headers[Header.TRS_VERSION], 2)
        except Exception as e:
            self.fail('Exception occurred: ' + str(e))

    def test_header_to_trace_set_params(self):
        """Verify that every header tag is converted correctly into the equivalent trace set parameter"""
        trace_count = 100
        sample_count = 1000

        try:
            with trsfile.open(self.tmp_path, 'w', headers={
                Header.LABEL_X: "s",
                Header.LABEL_Y: "V",
                Header.OFFSET_X: 100,
                Header.SCALE_X: 1.1,
                Header.SCALE_Y: 0.9,
                Header.TRACE_OFFSET: 200,
                Header.LOGARITHMIC_SCALE: False,
                Header.ACQUISITION_RANGE_OF_SCOPE: 1.0,
                Header.ACQUISITION_COUPLING_OF_SCOPE: 2,
                Header.ACQUISITION_OFFSET_OF_SCOPE: 3.0,
                Header.ACQUISITION_INPUT_IMPEDANCE: 4.0,
                Header.ACQUISITION_DEVICE_ID: '5',
                Header.ACQUISITION_TYPE_FILTER: 6,
                Header.ACQUISITION_FREQUENCY_FILTER: 7.0,
                Header.ACQUISITION_RANGE_FILTER: 8.0,
                Header.EXTERNAL_CLOCK_USED: True,
                Header.EXTERNAL_CLOCK_THRESHOLD: 9.0,
                Header.EXTERNAL_CLOCK_MULTIPLIER: 10,
                Header.EXTERNAL_CLOCK_PHASE_SHIFT: 11,
                Header.EXTERNAL_CLOCK_RESAMPLER_MASK: 12,
                Header.EXTERNAL_CLOCK_RESAMPLER_ENABLED: False,
                Header.EXTERNAL_CLOCK_FREQUENCY: 13.0,
                Header.EXTERNAL_CLOCK_BASE: 14,
                Header.NUMBER_VIEW: 15,
                Header.TRACE_OVERLAP: True,
                Header.NUMBER_OF_ENABLED_CHANNELS: 16,
                Header.NUMBER_OF_USED_OSCILLOSCOPES: 17,
                Header.XY_SCAN_WIDTH: 18,
                Header.XY_SCAN_HEIGHT: 19,
                Header.XY_MEASUREMENTS_PER_SPOT: 20,
            }) as trs_traces:
                trs_traces.extend([
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * sample_count,
                        TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(i.to_bytes(8, byteorder='big'))})
                    )
                    for i in range(0, trace_count)]
                )
                expected_trace_set_parameters = TraceSetParameterMap()
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.DISPLAY_HINT_X_LABEL, "s")
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.DISPLAY_HINT_Y_LABEL, "V")
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.X_OFFSET, 100)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.X_SCALE, 1.1)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.Y_SCALE, 0.9)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.TRACE_OFFSET, 200)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.DISPLAY_HINT_USE_LOG_SCALE, False)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_OSCILLOSCOPE_RANGE, 1.0)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_OSCILLOSCOPE_COUPLING, 2)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_OSCILLOSCOPE_OFFSET, 3.0)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_OSCILLOSCOPE_INPUT_IMPEDANCE, 4.0)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_OSCILLOSCOPE_DEVICE_IDENTIFIER, '5')
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_FILTER_TYPE, 6)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_FILTER_FREQUENCY, 7.0)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_FILTER_RANGE, 8.0)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_EXT_CLK_ENABLED, True)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_EXT_CLK_THRESHOLD, 9.0)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_EXT_CLK_MULTIPLIER, 10)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_EXT_CLK_PHASESHIFT, 11)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_EXT_CLK_RESAMPLER_MASK, 12)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_EXT_CLK_RESAMPLER_MASK_ENABLED, False)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_EXT_CLK_FREQUENCY, 13.0)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_ICWAVES_EXT_CLK_TIMEBASE, 14)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.DISPLAY_HINT_NUM_TRACES_SHOWN, 15)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.DISPLAY_HINT_TRACES_OVERLAP, True)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_OSCILLOSCOPE_ACTIVE_CHANNEL_COUNT, 16)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_OSCILLOSCOPE_COUNT, 17)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_XYZ_GRID_COUNT_X, 18)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_XYZ_GRID_COUNT_Y, 19)
                expected_trace_set_parameters.add_standard_parameter(StandardTraceSetParameters.SETUP_XYZ_MEASUREMENTS_PER_SPOT, 20)
                self.assertDictEqual(trs_traces.get_headers()[Header.TRACE_SET_PARAMETERS], expected_trace_set_parameters)
        except Exception as e:
            self.fail('Exception occurred: ' + str(e))

    def test_write_different_trace_sizes(self):
        trace_count = 100
        sample_count = 1000

        with trsfile.open(self.tmp_path, 'w', padding_mode=TracePadding.AUTO) as trs_traces:
            trs_traces.extend([
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    RawTraceData(i.to_bytes(8, byteorder='big'))
                )
                for i in range(0, trace_count)]
            )

    def test_write_closed(self):
        trace_count = 100
        sample_count = 1000

        with trsfile.open(self.tmp_path, 'w', padding_mode=TracePadding.AUTO) as trs_traces:
            trs_traces.extend([
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(i.to_bytes(8, byteorder='big'))})
                )
                for i in range(0, trace_count)]
            )

        # Should raise an "ValueError: I/O operation on closed trace set"
        with self.assertRaises(ValueError):
            print(trs_traces)

    def test_write_different_trace_sizes(self):
        trace_count = 100
        sample_count = 1000

        with trsfile.open(self.tmp_path, 'w', padding_mode=TracePadding.AUTO) as trs_traces:
            trs_traces.extend([
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(i.to_bytes(8, byteorder='big'))})
                )
                for i in range(0, trace_count)]
            )
            with self.assertRaises(TypeError):
                # The length is incorrect
                # Should raise a Type error: The parameters of trace #0 do not match the trace set's definitions.
                trs_traces.extend([
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * sample_count,
                        TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(bytes.fromhex('cafebabedeadbeef0102030405060708'))})
                    )]
                )
            with self.assertRaises(TypeError):
                # The name is incorrect
                # Should raise a Type error: The parameters of trace #1 do not match the trace set's definitions.
                trs_traces.extend([
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * sample_count,
                        TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(bytes.fromhex('0102030405060708'))})
                    ),
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * sample_count,
                        TraceParameterMap({'NEW_DATA': ByteArrayParameter(bytes.fromhex('0102030405060708'))})
                    )]
                )
            with self.assertRaises(TypeError):
                # The type is incorrect
                # Should raise a Type error: The parameters of trace #0 do not match the trace set's definitions.
                trs_traces.extend([
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * sample_count,
                        TraceParameterMap({'LEGACY_DATA': IntegerArrayParameter([42, 74])})
                    )]
                )

        with trsfile.open(self.tmp_path, 'w', padding_mode=TracePadding.AUTO) as trs_traces:
            trs_traces.extend([
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    TraceParameterMap()
                )
                for i in range(0, trace_count)]
            )
            with self.assertRaises(TypeError):
                # The length, data and name are incorrect
                # Should raise a Type error: The parameters of trace #0 do not match the trace set's definitions.
                trs_traces.extend([
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * sample_count,
                        TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(bytes.fromhex('cafebabedeadbeef0102030405060708'))})
                    )]
                )

    def test_read(self):
        trace_count = 100
        sample_count = 1000

        original_traces = [
                Trace(
                    SampleCoding.FLOAT,
                    [get_sample(i) for i in range(0, sample_count)],
                    TraceParameterMap()
                )
                for i in range(0, trace_count)
            ]

        # Create a trace
        with trsfile.open(self.tmp_path, 'w', headers = {
                Header.LABEL_X: 'Testing X',
                Header.LABEL_Y: 'Testing Y',
                Header.DESCRIPTION: 'Testing trace creation',
            }, padding_mode = TracePadding.AUTO
            ) as trs_traces:

            trs_traces.extend(original_traces)

            # Make sure length is equal
            self.assertEqual(len(original_traces), len(trs_traces))

        # Read the trace and check if everything is good
        with trsfile.open(self.tmp_path, 'r') as trs_traces:
            # Check if lengths are still good :)
            self.assertEqual(len(original_traces), len(trs_traces))

            # Check if every trace is saved correctly
            for original_trace, trs_trace in zip(trs_traces, original_traces):
                self.assertEqual(original_trace, trs_trace)

    def test_read_non_existing(self):
        with self.assertRaises(FileNotFoundError):
            with trsfile.open(self.tmp_path, 'r') as trs_traces:
                pass

    def test_append(self):
        trace_count = 100
        sample_count = 1000

        # Append to a non-existing file, behaves same as normal "write"
        with trsfile.open(self.tmp_path, 'a', padding_mode=TracePadding.AUTO) as trs_traces:
            self.assertEqual(len(trs_traces), 0)

            # Extend the trace file with 100 traces with each 1000 samples
            trs_traces.extend([
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(i.to_bytes(8, byteorder='big'))})
                )
                for i in range(0, trace_count)]
            )

            self.assertEqual(len(trs_traces), trace_count)

        # Now open and close for a few times while adding some number of traces
        expected_length = trace_count
        for t in range(0, 10):

            trace_count = (t + 1) * 10

            with trsfile.open(self.tmp_path, 'a', padding_mode=TracePadding.AUTO) as trs_traces:
                self.assertEqual(len(trs_traces), expected_length)

                # Extend the trace file with 100 traces with each 1000 samples
                trs_traces.extend([
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * sample_count,
                        raw_data=i.to_bytes(8, byteorder='big')
                    )
                    for i in range(0, trace_count)]
                )

                expected_length += trace_count
                self.assertEqual(len(trs_traces), expected_length)

    def test_exclusive(self):
        trace_count = 100
        sample_count = 1000

        # Write to file exclusively
        with trsfile.open(self.tmp_path, 'x', padding_mode=TracePadding.AUTO) as trs_traces:
            self.assertEqual(len(trs_traces), 0)

            # Extend the trace file with 100 traces with each 1000 samples
            trs_traces.extend([
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(i.to_bytes(8, byteorder='big'))})
                )
                for i in range(0, trace_count)]
            )

            self.assertEqual(len(trs_traces), trace_count)

        # Now try again (this should throw an exception)
        with self.assertRaises(FileExistsError):
            with trsfile.open(self.tmp_path, 'x') as trs_traces:
                self.assertEqual(len(trs_traces), trace_count)


    def test_extend(self):
        trace_count = 100
        sample_count = 1000

        with trsfile.open(self.tmp_path, 'w', padding_mode=TracePadding.AUTO) as trs_traces:
            # Extend empty list
            trs_traces.extend([])
            self.assertEqual(len(trs_traces), 0)

            # Extend non empty list
            trs_traces.extend([
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(bytes(8))})
                )
                ]
            )
            self.assertEqual(len(trs_traces), 1)

            # Extend non empty list
            trs_traces.extend([
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(i.to_bytes(8, byteorder='big'))})
                )
                for i in range(0, trace_count)]
            )
            self.assertEqual(len(trs_traces), trace_count + 1)

    def test_padding_none(self):
        sample_count = 1000

        with trsfile.open(
            self.tmp_path,
            'w',
            padding_mode = TracePadding.NONE,
            headers = {
                Header.NUMBER_SAMPLES: sample_count,
                Header.LENGTH_DATA: 8,
                Header.SAMPLE_CODING: SampleCoding.FLOAT
            }
            ) as trs_traces:
            # This is the length of the trace
            trs_traces.extend(
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(bytes(8))})
                )
            )

            # Length is smaller
            with self.assertRaises(ValueError):
                trs_traces.extend(
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * (sample_count - 1),
                        TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(b'\x10' * 8)})
                    )
                )
            self.assertEqual(len(trs_traces), 1)

            # Length is bigger
            with self.assertRaises(ValueError):
                trs_traces.extend(
                    Trace(
                        SampleCoding.FLOAT,
                        [0] * (sample_count + 1),
                        TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(b'\x01' * 8)})
                    )
                )
            self.assertEqual(len(trs_traces), 1)

            # Length is equal
            trs_traces.extend(
                Trace(
                    SampleCoding.FLOAT,
                    [0] * sample_count,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(bytes(8))})
                )
            )
            self.assertEqual(len(trs_traces), 2)

    def test_padding(self):
        trace_count = 100
        sample_count = 1000
        fmt = SampleCoding.FLOAT

        with trsfile.open(self.tmp_path, 'w', padding_mode=TracePadding.AUTO) as trs_traces:
            # This is the length everything should be padded/clipped to
            trs_traces.extend(
                Trace(
                    fmt,
                    b'\xDE' * (sample_count * fmt.size),
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(bytes(8))})
                )
            )

            # Padding mode
            trs_traces.extend([
                Trace(
                    fmt,
                    b'\xDE' * (sample_count + i) * fmt.size,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(abs(i).to_bytes(8, byteorder='big'))})
                )
                for i in range(0, -trace_count, -1)]
            )

            # Clipping mode
            trs_traces.extend([
                Trace(
                    fmt,
                    b'\xDE' * (sample_count + i) * fmt.size,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(i.to_bytes(8, byteorder='big'))})
                )
                for i in range(0, trace_count)]
            )

        with trsfile.open(self.tmp_path, 'r') as trs_traces:
            self.assertEqual(len(trs_traces), trace_count * 2 + 1)

            # Check that all traces are of the same size
            for trs_trace in trs_traces:
                self.assertEqual(len(trs_trace), sample_count)

            # Check that all padding is zero
            for i, trs_trace in enumerate(trs_traces[1:101]):
                # Difficult case :)
                if i == 0:
                    continue

                for si, sample in enumerate(trs_trace[-i:]):
                    self.assertEqual(sample, 0.0 if fmt == SampleCoding.FLOAT else 0, str(i))

                # Test that this is indeed not zero
                self.assertNotEqual(trs_trace[-i - 1], 0)


if __name__ == '__main__':
    unittest.main()

