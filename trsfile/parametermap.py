from io import BytesIO

from trsfile.traceparameter import TraceSetParameter, TraceParameter, TraceParameterDefinition, ParameterType
from trsfile.utils import *

UTF_8 = 'utf-8'


class TraceSetParameterMap(StringKeyOrderedDict):
    def __setitem__(self, key, value):
        if not isinstance(value, TraceParameter) or type(value) is TraceSetParameter:
            raise TypeError('The value for a TraceSetParameterMap entry must be a specific subclass'
                            ' of TraceParameter (e.g. ByteArrayParameter).')
        super().__setitem__(key, value)

    @staticmethod
    def deserialize(raw: BytesIO):
        result = TraceSetParameterMap()
        number_of_entries = read_short(raw)
        for i in range(number_of_entries):
            name = read_parameter_name(raw)
            value = TraceSetParameter.deserialize(raw)
            result[name] = value
        return result

    def serialize(self):
        out = bytearray()
        number_of_entries = len(self)
        out.extend(encode_as_short(number_of_entries))
        for name, param in self.items():
            encoded_name = name.encode(UTF_8)
            out.extend(encode_as_short(len(encoded_name)))
            out.extend(encoded_name)

            param_type = ParameterType.from_class(type(param))
            out.append(param_type.value)
            serialized_value = param.serialize()
            length = len(serialized_value) if param_type is ParameterType.STRING else len(param.value)
            out.extend(encode_as_short(length))

            out.extend(serialized_value)
        return bytes(out)


class TraceParameterDefinitionMap(StringKeyOrderedDict):
    def get_total_size(self) -> int:
        total = 0
        for param in self.values():
            total += param.length * param.param_type.byte_size
        return total

    def __setitem__(self, key, value):
        if type(value) is not TraceParameterDefinition:
            raise TypeError('The value for an entry in a TraceParameterDefinitionMap must be of '
                            'type TraceParameterDefinition')
        super().__setitem__(key, value)

    @staticmethod
    def deserialize(raw: BytesIO):
        result = TraceParameterDefinitionMap()
        number_of_entries = read_short(raw)
        for i in range(number_of_entries):
            name = read_parameter_name(raw)
            value = TraceParameterDefinition.deserialize(raw)
            result[name] = value
        return result

    def serialize(self):
        out = bytearray()
        out.extend(encode_as_short(len(self)))
        for name, value in self.items():
            encoded_name = name.encode(UTF_8)
            out.extend(encode_as_short(len(encoded_name)))
            out.extend(encoded_name)
            out.extend(value.serialize())
        return out


class TraceParameterMap(StringKeyOrderedDict):
    def __setitem__(self, key, value):
        if not isinstance(value, TraceParameter):
            raise TypeError('The value for a TraceParameterMap entry must be a specific subclass'
                            ' of TraceParameter (e.g. ByteArrayParameter).')
        super().__setitem__(key, value)

    @staticmethod
    def deserialize(raw: bytes, definitions: TraceParameterDefinitionMap):
        io_bytes = BytesIO(raw)
        result = TraceParameterMap()
        for key, val in definitions.items():
            io_bytes.seek(val.offset)
            param = val.param_type.param_class.deserialize(io_bytes, val.length)
            result[key] = param
        return result

    def serialize(self):
        out = bytearray()
        for val in self.values():
            out.extend(val.serialize())
        return out
