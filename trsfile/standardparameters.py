from __future__ import annotations
from enum import Enum

from trsfile.traceparameter import ParameterType


class StandardTraceSetParameters(Enum):
    """While running modules on tracesets or displaying tracesets, Inspector or Inspector FI Python utilize
    TraceSetParameters with specific names and types to be present in those tracesets. This class denotes which trace
    set parameter names are reserved for use by Riscure programs, and the types they are expected to have"""
    
    def __new__(cls, tag: int, identifier: str, parameter_type: ParameterType):
        obj = object.__new__(cls)
        obj._value_ = tag
        obj.identifier = identifier
        obj.parameter_type = parameter_type
        return obj

    @staticmethod
    def from_identifier(identifier: str) -> StandardTraceSetParameters:
        for val in StandardTraceSetParameters:
            if identifier.lower() == val.identifier.lower() or identifier.lower() == val.name.lower():
                return val
        raise ValueError(f'{identifier} is not an identifier of a StandardTraceSetParameter')

    KEY = (0x01, 'KEY', ParameterType.BYTE)
    X_OFFSET = (0x02, 'X_OFFSET', ParameterType.INT)
    X_SCALE = (0x03, 'X_SCALE', ParameterType.FLOAT)
    Y_SCALE = (0x04, 'Y_SCALE', ParameterType.FLOAT)
    TRACE_OFFSET = (0x05, 'TRACE_OFFSET', ParameterType.INT)

    SETUP_OSCILLOSCOPE_RANGE = (0x10, 'SETUP:OSCILLOSCOPE:RANGE', ParameterType.FLOAT)
    SETUP_OSCILLOSCOPE_COUPLING = (0x11, 'SETUP:OSCILLOSCOPE:COUPLING', ParameterType.INT)
    SETUP_OSCILLOSCOPE_OFFSET = (0x12, 'SETUP:OSCILLOSCOPE:OFFSET', ParameterType.FLOAT)
    SETUP_OSCILLOSCOPE_INPUT_IMPEDANCE = (0x13, 'SETUP:OSCILLOSCOPE:INPUT_IMPEDANCE', ParameterType.FLOAT)
    SETUP_OSCILLOSCOPE_DEVICE_IDENTIFIER = (0x14, 'SETUP:OSCILLOSCOPE:DEVICE_ID', ParameterType.STRING)
    SETUP_OSCILLOSCOPE_ACTIVE_CHANNEL_COUNT = (0x15, 'SETUP:OSCILLOSCOPE:ACTIVE_CHANNEL_COUNT', ParameterType.INT)
    SETUP_OSCILLOSCOPE_COUNT = (0x16, 'SETUP:OSCILLOSCOPE:COUNT', ParameterType.INT)

    SETUP_ICWAVES_FILTER_TYPE = (0x20, 'SETUP:ICWAVES:FILTER:FREQUENCY', ParameterType.INT)
    SETUP_ICWAVES_FILTER_FREQUENCY = (0x21, 'SETUP:ICWAVES:FILTER:RANGE', ParameterType.FLOAT)
    SETUP_ICWAVES_FILTER_RANGE = (0x22, 'SETUP:ICWAVES:FILTER:TYPE', ParameterType.FLOAT)
    SETUP_ICWAVES_EXT_CLK_ENABLED = (0x23, 'SETUP:ICWAVES:EXT_CLK:ENABLED', ParameterType.BOOL)
    SETUP_ICWAVES_EXT_CLK_THRESHOLD = (0x24, 'SETUP:ICWAVES:EXT_CLK:THRESHOLD', ParameterType.FLOAT)
    SETUP_ICWAVES_EXT_CLK_MULTIPLIER = (0x25, 'SETUP:ICWAVES:EXT_CLK:MULTIPLIER', ParameterType.INT)
    SETUP_ICWAVES_EXT_CLK_PHASESHIFT = (0x26, 'SETUP:ICWAVES:EXT_CLK:PHASE_SHIFT', ParameterType.INT)
    SETUP_ICWAVES_EXT_CLK_RESAMPLER_MASK = (0x27, 'SETUP:ICWAVES:EXT_CLK:RESAMPLER_MASK', ParameterType.INT)
    SETUP_ICWAVES_EXT_CLK_RESAMPLER_MASK_ENABLED = (0x28, 'SETUP:ICWAVES:EXT_CLK:RESAMPLER_MASK_ENABLED', ParameterType.BOOL)
    SETUP_ICWAVES_EXT_CLK_FREQUENCY = (0x29, 'SETUP:ICWAVES:EXT_CLK:FREQUENCY', ParameterType.FLOAT)
    SETUP_ICWAVES_EXT_CLK_TIMEBASE = (0x2A, 'SETUP:ICWAVES:EXT_CLK:TIMEBASE', ParameterType.INT)

    SETUP_XYZ_GRID_COUNT_X = (0x30, 'SETUP:XYZ:GRID_COUNT_X', ParameterType.INT)
    SETUP_XYZ_GRID_COUNT_Y = (0x31, 'SETUP:XYZ:GRID_COUNT_Y', ParameterType.INT)
    SETUP_XYZ_MEASUREMENTS_PER_SPOT = (0x32, 'SETUP:XYZ:MEASUREMENTS_PER_SPOT', ParameterType.INT)
    SETUP_XYZ_REFERENCE_POINTS = (0x33, 'SETUP:XYZ:REFERENCE_POINTS', ParameterType.DOUBLE)

    DISPLAY_HINT_X_LABEL = (0x40, 'DISPLAY_HINT:X_LABEL', ParameterType.STRING)
    DISPLAY_HINT_Y_LABEL = (0x41, 'DISPLAY_HINT:Y_LABEL', ParameterType.STRING)
    DISPLAY_HINT_USE_LOG_SCALE = (0x42, 'DISPLAY_HINT:USE_LOG_SCALE', ParameterType.BOOL)
    DISPLAY_HINT_NUM_TRACES_SHOWN = (0x43, 'DISPLAY_HINT:NUM_TRACES_SHOWN', ParameterType.INT)
    DISPLAY_HINT_TRACES_OVERLAP = (0x44, 'DISPLAY_HINT:TRACES_OVERLAP', ParameterType.BOOL)

    TVLA_SET = (0x50, 'TVLA:SET', ParameterType.STRING)
    TVLA_CIPHER = (0x51, 'TVLA:CIPHER', ParameterType.STRING)


class StandardTraceParameters(Enum):
    """While running modules, Inspector may expect TraceParameters with specific names and types to be present in the
    traces it runs on. This class denotes which trace parameter names are reserved for use by Riscure programs, and the
    types they are expected to have"""

    def __new__(cls, tag: int, identifier: str, parameter_type: ParameterType):
        obj = object.__new__(cls)
        obj._value_ = tag
        obj.identifier = identifier
        obj.parameter_type = parameter_type
        return obj

    @staticmethod
    def from_identifier(identifier: str) -> StandardTraceParameters:
        for val in StandardTraceParameters:
            if identifier.lower() == val.identifier.lower() or identifier.lower() == val.name.lower():
                return val
        raise ValueError('{} is not a name of a StandardTraceParameter'.format(identifier))

    INPUT = (0x01, 'INPUT', ParameterType.BYTE)
    OUTPUT = (0x02, 'OUTPUT', ParameterType.BYTE)
    KEY = (0x03, 'KEY', ParameterType.BYTE)

    TIMEOUT = (0x04, 'TIMEOUT', ParameterType.INT)
    UNKNOWN_IO_DATA = (0x05, 'UNKNOWN_IO_DATA', ParameterType.BYTE)

    CHANNEL_INDEX = (0x06, 'CHANNEL_INDEX', ParameterType.INT)
    PATTERN_TYPE = (0x07, 'PATTERN_TYPE', ParameterType.BYTE)

    TVLA_SET_INDEX = (0x08, 'TVLA:SET_INDEX', ParameterType.SHORT)

    XYZ_RELATIVE_POSITION = (0x09, 'XYZ:RELATIVE_POSITION', ParameterType.DOUBLE)

    SOURCE_TRACE_INDEX = (0x0A, 'SOURCE_TRACE_INDEX', ParameterType.INT)
    SOURCE_TRACE_SAMPLE_INDEX = (0x0B, 'SOURCE_TRACE_SAMPLE_INDEX', ParameterType.INT)

    FILTER_LOW_BOUND = (0x10, 'FILTER:LOW_BOUND', ParameterType.FLOAT)
    FILTER_HIGH_BOUND = (0x11, 'FILTER:HIGH_BOUND', ParameterType.FLOAT)
    FILTER_SEGMENTS_VALUES = (0x12, 'FILTER:SEGMENTS:VALUES', ParameterType.BYTE)
    FILTER_SEGMENTS_COUNT = (0x13, 'FILTER:SEGMENTS:COUNT', ParameterType.INT)
