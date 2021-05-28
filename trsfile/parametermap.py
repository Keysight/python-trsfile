from collections import OrderedDict
from io import BytesIO

from traceparameter import TraceSetParameter


class TraceSetParameterMap(OrderedDict):
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

