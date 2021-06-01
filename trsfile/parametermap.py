from collections import OrderedDict
from io import BytesIO

from traceparameter import TraceSetParameter, TraceParameter
from utils import encode_as_short


class TraceSetParameterMap(OrderedDict):
    def __setitem__(self, key, value):
        if not type(key) is str:
            raise TypeError('The key for an item in a TraceSetParameterMap must be of type \'str\'.')
        if not isinstance(value, TraceParameter) or type(value) is TraceSetParameter:
            raise TypeError('The value for a TraceSetParameterMap entry must be a specific subclass'
                            ' of TraceParameter (e.g. ByteArrayParameter).')
        super().__setitem__(key, value)

    @staticmethod
    def deserialize(raw: BytesIO):
        result = TraceSetParameterMap()
        number_of_entries = int.from_bytes(raw.read(2), 'little')
        for i in range(number_of_entries):
            name = TraceSetParameterMap.get_parameter_name(raw)
            value = TraceSetParameter.deserialize(raw)
            result[name] = value
        return result

    @staticmethod
    def get_parameter_name(raw):
        name_length = int.from_bytes(raw.read(2), 'little')
        name = raw.read(name_length).decode()
        return name

    def serialize(self):
        out = bytearray()
        number_of_entries = len(self)
        out.extend(encode_as_short(number_of_entries))
        for name, value in self.items():
            out.extend(encode_as_short(len(name)))
            out.extend(name.encode())
            out.extend(value.serialize())
        return bytes(out)