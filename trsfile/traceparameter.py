import struct
from abc import ABC, abstractmethod
from enum import Enum
from io import BytesIO

from trsfile.utils import encode_as_short


class TraceParameter(ABC):
    @staticmethod
    @abstractmethod
    def deserialize(io_bytes: BytesIO):
        pass

    @abstractmethod
    def serialize(self) -> bytes:
        pass

    @staticmethod
    def get_parameter_length(io_bytes: BytesIO) -> int:
        return int.from_bytes(io_bytes.read(2), 'little')

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class TraceSetParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_type = ParameterType(io_bytes.read(1)[0])
        return param_type.param_class.deserialize(io_bytes)

    def serialize(self) -> bytes:
        pass


class BooleanArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_length = TraceParameter.get_parameter_length(io_bytes)
        raw_values = io_bytes.read(ParameterType.BOOL.byte_size * param_length)
        param_value = [bool(x) for x in list(raw_values)]
        return BooleanArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        out.append(ParameterType.BOOL.value)
        out.extend(encode_as_short(len(self.value)))
        out.extend(bytes(self.value))
        return bytes(out)


class ByteArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_length = TraceParameter.get_parameter_length(io_bytes)
        param_value = list(io_bytes.read(ParameterType.BYTE.byte_size * param_length))
        return ByteArrayParameter(param_value)

    def __str__(self):
        return '0x' + bytes(self.value).hex().upper() if self.value else ''

    def serialize(self):
        out = bytearray()
        out.append(ParameterType.BYTE.value)
        out.extend(encode_as_short(len(self.value)))
        out.extend(bytes(self.value))
        return bytes(out)


class DoubleArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_length = TraceParameter.get_parameter_length(io_bytes)
        param_value = list(struct.unpack('<d', io_bytes.read(ParameterType.DOUBLE.byte_size * param_length)))
        return DoubleArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        out.append(ParameterType.DOUBLE.value)
        out.extend(encode_as_short(len(self.value)))
        for x in self.value:
            out.extend(struct.pack('<d', x))
        return bytes(out)


class FloatArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_length = TraceParameter.get_parameter_length(io_bytes)
        param_value = list(struct.unpack('<f', io_bytes.read(ParameterType.FLOAT.byte_size * param_length)))
        return FloatArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        out.append(ParameterType.FLOAT.value)
        out.extend(encode_as_short(len(self.value)))
        for x in self.value:
            out.extend(struct.pack('<f', x))
        return bytes(out)


class IntegerArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_length = TraceParameter.get_parameter_length(io_bytes)
        param_value = [int.from_bytes(io_bytes.read(ParameterType.INT.byte_size), 'little') for i in range(param_length)]
        return IntegerArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        out.append(ParameterType.INT.value)
        out.extend(encode_as_short(len(self.value)))
        for x in self.value:
            out.extend(struct.pack('<i', x))
        return bytes(out)


class LongArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_length = TraceParameter.get_parameter_length(io_bytes)
        param_value = [int.from_bytes(io_bytes.read(ParameterType.LONG.byte_size), 'little') for i in range(param_length)]
        return LongArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        out.append(ParameterType.LONG.value)
        out.extend(encode_as_short(len(self.value)))
        for x in self.value:
            out.extend(struct.pack('<l', x))
        return bytes(out)


class ShortArrayParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_length = TraceParameter.get_parameter_length(io_bytes)
        param_value = [int.from_bytes(io_bytes.read(ParameterType.SHORT.byte_size), 'little') for i in range(param_length)]
        return ShortArrayParameter(param_value)

    def serialize(self):
        out = bytearray()
        out.append(ParameterType.SHORT.value)
        out.extend(encode_as_short(len(self.value)))
        for x in self.value:
            out.extend(struct.pack('<h', x))
        return bytes(out)


class StringParameter(TraceParameter):
    @staticmethod
    def deserialize(io_bytes: BytesIO):
        param_length = TraceParameter.get_parameter_length(io_bytes)
        param_value = io_bytes.read(ParameterType.BOOL.byte_size * param_length).decode()
        return StringParameter(param_value)

    def serialize(self):
        out = bytearray()
        out.append(ParameterType.STRING.value)
        encoded_string = self.value.encode()
        out.extend(encode_as_short(len(encoded_string)))
        out.extend(encoded_string)
        return bytes(out)


class ParameterType(Enum):
    def __new__(cls, tag, byte_size, param_class):
        obj = object.__new__(cls)
        obj._value_ = tag
        obj.byte_size = byte_size
        obj.param_class = param_class
        return obj

    BYTE   = (0x01, 1, ByteArrayParameter)
    SHORT  = (0x02, 2, ShortArrayParameter)
    INT    = (0x04, 4, IntegerArrayParameter)
    FLOAT  = (0x14, 4, FloatArrayParameter)
    LONG   = (0x08, 8, LongArrayParameter)
    DOUBLE = (0x18, 8, DoubleArrayParameter)
    STRING = (0x20, 1, StringParameter)
    BOOL   = (0x31, 1, BooleanArrayParameter)
