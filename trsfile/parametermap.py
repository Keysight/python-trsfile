from collections import OrderedDict
from io import BytesIO

from trsfile.traceparameter import TraceSetParameter, TraceParameter
from trsfile.utils import encode_as_short, read_parameter_name, read_short

UTF_8 = 'utf-8'


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
            out.extend(encode_as_short(len(name)))
            out.extend(name.encode(UTF_8))
            out.extend(value.serialize())
        return bytes(out)
