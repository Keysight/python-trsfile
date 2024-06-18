from __future__ import annotations

import struct
import warnings
from abc import ABC, abstractmethod
from enum import Enum
from io import BytesIO
from typing import Any

import numpy
from numpy import ndarray, integer, uint8, double, single

from trsfile.utils import encode_as_short, read_short

UTF_8 = 'utf-8'
BYTE_MIN = 0
BYTE_MAX = 255
SHORT_MIN = -2**15
SHORT_MAX = 2**15-1
INT_MIN = -2**31
INT_MAX = 2**31-1


class TraceParameter(ABC):
    _expected_type_string = "None"

    @staticmethod
    @abstractmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        pass

    @abstractmethod
    def serialize(self) -> bytes:
        pass

    @staticmethod
    @abstractmethod
    def _has_expected_type(value: Any) -> bool:
        pass

    def __init__(self, value):
        if type(value) is ndarray and len(value.shape) > 1:
            warnings.warn("Flatting multi-dimensional ndarray before adding it to trace parameter.\n"
                          "Information about dimensions of this ndarray will be lost.")
            value = value.flatten()
        if value is None or ((type(value) is list or type(value) is ndarray) and len(value) <= 0):
            raise ValueError('The value for a TraceParameter cannot be empty')
        if not type(self)._has_expected_type(value):
            raise TypeError(f'A {type(self).__name__} must have a value of type "{type(self)._expected_type_string}"'
                            f', but it has a type of {type(value)}')
        self.value = value

    def __len__(self):
        return len(self.value)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        if len(self.value) != len(other.value):
            return False
        # return true only if both parameter value arrays contain the same elements in the same order,
        # regardless of whether it is an ndarray or a list
        return all(this_val == that_val for (this_val, that_val) in zip(self.value, other.value))

    def __str__(self):
        return str(self.value)


class TraceSetParameter:
    @staticmethod
    def deserialize(io_bytes: BytesIO) -> TraceSetParameter:
        param_type = ParameterType(io_bytes.read(1)[0])
        param_length = read_short(io_bytes)
        return param_type.param_class.deserialize(io_bytes, param_length)


class BooleanArrayParameter(TraceParameter):
    _expected_type_string = "List[bool] or ndarray[bool]"

    def __len__(self):
        return len(bytes(self.value))

    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int) -> BooleanArrayParameter:
        raw_values = io_bytes.read(ParameterType.BOOL.byte_size * param_length)
        param_value = [bool(x) for x in list(raw_values)]
        return BooleanArrayParameter(param_value)

    def serialize(self) -> bytes:
        out = bytearray()
        out.extend(bytes(self.value))
        return bytes(out)

    @staticmethod
    def _has_expected_type(value: Any) -> bool:
        if type(value) is list:
            return all(isinstance(elem, bool) for elem in value)
        elif type(value) is ndarray:
            return all(isinstance(elem, numpy.bool) for elem in value)
        return False


class ByteArrayParameter(TraceParameter):
    _expected_type_string = f"bytearray, bytes, List[int], or ndarray[integer], where the int values are in range({BYTE_MIN}, {BYTE_MAX + 1})"

    def __len__(self):
        return len(bytes(self.value))

    def __eq__(self, other):
        return isinstance(other, ByteArrayParameter) and bytearray(self.value) == bytearray(other.value)

    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        param_value = list(io_bytes.read(ParameterType.BYTE.byte_size * param_length))
        return ByteArrayParameter(param_value)

    def __str__(self):
        return '0x' + bytes(self.value).hex().upper() if self.value else ''

    def serialize(self):
        out = bytearray()
        out.extend(bytes(self.value))
        return bytes(out)

    @staticmethod
    def _has_expected_type(value: Any) -> bool:
        if type(value) is bytes or type(value) is bytearray:
            return True
        if type(value) is list:
            return all(isinstance(elem, int) and BYTE_MIN <= elem <= BYTE_MAX for elem in value)
        elif type(value) is ndarray:
            return all(isinstance(elem, uint8) for elem in value)
        return False


class DoubleArrayParameter(TraceParameter):
    _expected_type_string = "List[float/int] or ndarray[double/integer]"

    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int) -> DoubleArrayParameter:
        param_value = [struct.unpack('<d', io_bytes.read(ParameterType.DOUBLE.byte_size))[0] for i in range(param_length)]
        return DoubleArrayParameter(param_value)

    def serialize(self) -> bytes:
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<d', x))
        return bytes(out)

    @staticmethod
    def _has_expected_type(value: Any) -> bool:
        if type(value) is list:
            return all(isinstance(elem, (float, int)) for elem in value)
        elif type(value) is ndarray:
            return all(isinstance(elem, (double, integer)) for elem in value)
        return False


class FloatArrayParameter(TraceParameter):
    _expected_type_string = "List[float/int] or ndarray[single/integer]"

    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int) -> FloatArrayParameter:
        param_value = [struct.unpack('<f', io_bytes.read(ParameterType.FLOAT.byte_size))[0] for i in range(param_length)]
        return FloatArrayParameter(param_value)

    def serialize(self) -> bytes:
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<f', x))
        return bytes(out)

    @staticmethod
    def _has_expected_type(value: Any) -> bool:
        if type(value) is list:
            return all(isinstance(elem, (float, int)) for elem in value)
        elif type(value) is ndarray:
            return all(isinstance(elem, (single, integer)) for elem in value)
        return False


class IntegerArrayParameter(TraceParameter):
    _expected_type_string = f"List[int] or ndarray[integer], where the int values are in range({INT_MIN}, {INT_MAX + 1})"

    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int) -> IntegerArrayParameter:
        param_value = [struct.unpack('<i', io_bytes.read(ParameterType.INT.byte_size))[0] for i in range(param_length)]
        return IntegerArrayParameter(param_value)

    def serialize(self) -> bytes:
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<i', x))
        return bytes(out)

    @staticmethod
    def _has_expected_type(value: Any) -> bool:
        if type(value) is list:
            return all(isinstance(elem, int) and INT_MIN <= elem <= INT_MAX for elem in value)
        elif type(value) is ndarray:
            return all(isinstance(elem, integer) and INT_MIN <= elem <= INT_MAX for elem in value)
        return False


class LongArrayParameter(TraceParameter):
    _expected_type_string = "List[int] or ndarray[integer]"

    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int) -> LongArrayParameter:
        param_value = [struct.unpack('<q', io_bytes.read(ParameterType.LONG.byte_size))[0] for i in range(param_length)]
        return LongArrayParameter(param_value)

    def serialize(self) -> bytes:
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<q', x))
        return bytes(out)

    @staticmethod
    def _has_expected_type(value: Any) -> bool:
        if type(value) is list:
            return all(isinstance(elem, int) for elem in value)
        elif type(value) is ndarray:
            return all(isinstance(elem, integer) for elem in value)
        return False


class ShortArrayParameter(TraceParameter):
    _expected_type_string = f"List[int] or ndarray[integer], where the int values are in range({SHORT_MIN}, {SHORT_MAX + 1})"

    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int) -> ShortArrayParameter:
        param_value = [struct.unpack('<h', io_bytes.read(ParameterType.SHORT.byte_size))[0] for i in range(param_length)]
        return ShortArrayParameter(param_value)

    def serialize(self) -> bytes:
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<h', x))
        return bytes(out)

    @staticmethod
    def _has_expected_type(value: Any) -> bool:
        if type(value) is list:
            return all(isinstance(elem, int) and SHORT_MIN <= elem <= SHORT_MAX for elem in value)
        elif type(value) is ndarray:
            return all(isinstance(elem, integer) and SHORT_MIN <= elem <= SHORT_MAX for elem in value)
        return False


class StringParameter(TraceParameter):
    _expected_type_string = "str"

    def __len__(self):
        return len(self.value.encode(UTF_8))

    def __eq__(self, other):
        return isinstance(other, StringParameter) and self.value.encode(UTF_8) == other.value.encode(UTF_8)

    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int) -> StringParameter:
        bytes_read = io_bytes.read(ParameterType.STRING.byte_size * param_length)
        param_value = bytes_read.decode(UTF_8)
        return StringParameter(param_value)

    def serialize(self) -> bytes:
        out = bytearray()
        encoded_string = self.value.encode(UTF_8)
        out.extend(encoded_string)
        return bytes(out)

    @staticmethod
    def _has_expected_type(value: Any) -> bool:
        return type(value) is str


class ParameterType(Enum):
    def __new__(cls, tag, byte_size, param_class):
        obj = object.__new__(cls)
        obj._value_ = tag
        obj.byte_size = byte_size
        obj.param_class = param_class
        return obj

    @staticmethod
    def from_class(cls):
        for val in ParameterType:
            if cls is val.param_class:
                return val
        raise TypeError('{} is not valid ParameterType class'.format(cls.__name__))

    BYTE   = (0x01, 1, ByteArrayParameter)
    SHORT  = (0x02, 2, ShortArrayParameter)
    INT    = (0x04, 4, IntegerArrayParameter)
    FLOAT  = (0x14, 4, FloatArrayParameter)
    LONG   = (0x08, 8, LongArrayParameter)
    DOUBLE = (0x18, 8, DoubleArrayParameter)
    STRING = (0x20, 1, StringParameter)
    BOOL   = (0x31, 1, BooleanArrayParameter)


class TraceParameterDefinition:
    def __init__(self, param_type: ParameterType, length: int, offset: int):
        self.param_type = param_type
        self.length = length
        self.offset = offset

    def __eq__(self, other):
        return self.param_type == other.param_type \
               and self.length == other.length \
               and self. offset == other.offset

    def __repr__(self):
        return '<TraceParameterDefinition: {} of length {} at offset {}>'.format(self.param_type.param_class.__name__,
                                                                                 self.length, self.offset)

    @staticmethod
    def deserialize(io_bytes: BytesIO) -> TraceParameterDefinition:
        param_type = ParameterType(io_bytes.read(1)[0])
        length = read_short(io_bytes)
        offset = read_short(io_bytes)
        return TraceParameterDefinition(param_type, length, offset)

    def serialize(self) -> bytearray:
        out = bytearray()
        out.append(self.param_type.value)
        out.extend(encode_as_short(self.length))
        out.extend(encode_as_short(self.offset))
        return out
