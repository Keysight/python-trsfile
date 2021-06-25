import struct
from abc import ABC, abstractmethod
from enum import Enum
from io import BytesIO

from trsfile.utils import encode_as_short, read_short

UTF_8 = 'utf-8'


class TraceParameter(ABC):
    @staticmethod
    @abstractmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        pass

    @abstractmethod
    def serialize(self) -> bytes:
        pass

    def __init__(self, value):
        if type(value) is not str and (value is None or len(value) <= 0):
            raise ValueError('The value for a TraceParameter cannot be empty')
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __str__(self):
        return str(self.value)


class TraceSetParameter:
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_type = ParameterType(io_bytes.read(1)[0])
        param_length = read_short(io_bytes)
        return param_type.param_class.deserialize(io_bytes, param_length)


class BooleanArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        raw_values = io_bytes.read(ParameterType.BOOL.byte_size * param_length)
        param_value = [bool(x) for x in list(raw_values)]
        return BooleanArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        out.extend(bytes(self.value))
        return bytes(out)


class ByteArrayParameter(TraceParameter):
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


class DoubleArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        param_value = [struct.unpack('<d', io_bytes.read(ParameterType.DOUBLE.byte_size))[0] for i in range(param_length)]
        return DoubleArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<d', x))
        return bytes(out)


class FloatArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        param_value = [struct.unpack('<f', io_bytes.read(ParameterType.FLOAT.byte_size))[0] for i in range(param_length)]
        return FloatArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<f', x))
        return bytes(out)


class IntegerArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        param_value = [struct.unpack('<i', io_bytes.read(ParameterType.INT.byte_size))[0] for i in range(param_length)]
        return IntegerArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<i', x))
        return bytes(out)


class LongArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        param_value = [struct.unpack('<q', io_bytes.read(ParameterType.LONG.byte_size))[0] for i in range(param_length)]
        return LongArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<q', x))
        return bytes(out)


class ShortArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        param_value = [struct.unpack('<h', io_bytes.read(ParameterType.SHORT.byte_size))[0] for i in range(param_length)]
        return ShortArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        for x in self.value:
            out.extend(struct.pack('<h', x))
        return bytes(out)


class StringParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO, param_length: int):
        bytes_read = io_bytes.read(ParameterType.STRING.byte_size * param_length)
        param_value = bytes_read.decode(UTF_8)
        return StringParameter(param_value)

    def serialize(self):
        out = bytearray()
        encoded_string = self.value.encode(UTF_8)
        out.extend(encoded_string)
        return bytes(out)


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
    def deserialize(io_bytes: BytesIO):
        param_type = ParameterType(io_bytes.read(1)[0])
        length = read_short(io_bytes)
        offset = read_short(io_bytes)
        return TraceParameterDefinition(param_type, length, offset)

    def serialize(self):
        out = bytearray()
        out.append(self.param_type.value)
        out.extend(encode_as_short(self.length))
        out.extend(encode_as_short(self.offset))
        return out
