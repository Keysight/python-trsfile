from io import BytesIO

from trsfile.traceparameter import TraceSetParameter, TraceParameter, TraceParameterDefinition
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
        for name, value in self.items():
            encoded_name = name.encode(UTF_8)
            out.extend(encode_as_short(len(encoded_name)))
            out.extend(encoded_name)
            out.extend(value.serialize())
        return bytes(out)


class TraceParameterDefinitionMap(StringKeyOrderedDict):
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
