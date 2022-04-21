import copy
import numbers

from trsfile.standardparameters import StandardTraceSetParameters, StandardTraceParameters
from trsfile.traceparameter import TraceSetParameter, TraceParameter, TraceParameterDefinition, ParameterType, \
    BooleanArrayParameter, ByteArrayParameter, StringParameter, DoubleArrayParameter, IntegerArrayParameter, \
    LongArrayParameter, ShortArrayParameter
from trsfile.utils import *

UTF_8 = 'utf-8'
SHORT_MIN = -2**15
SHORT_MAX = 2**15-1
INT_MIN = -2**31
INT_MAX = 2**31-1

class ParameterMapUtil:
    # A placeholder for integers that are actually shorts
    class ShortType(numbers.Rational):
        pass

    # A placeholder for integers that are actually longs
    class LongType(numbers.Rational):
        pass

    TYPE_TO_PARAMETER = {
        ShortType: ShortArrayParameter,
        int: IntegerArrayParameter,
        LongType: LongArrayParameter,
        float: DoubleArrayParameter,
        str: StringParameter,
        bool: BooleanArrayParameter,
        bytes: ByteArrayParameter,
        bytearray: ByteArrayParameter
    }

    _RATIONAL_TYPES_PRIORITY = [
        float,
        LongType,
        int,
        ShortType
    ]

    SUPPORTED_TYPES = [
        ShortType,
        int,
        LongType,
        float,
        str,
        bool,
        bytes,
        bytearray,
        list
    ]

    LISTABLE_TYPES = [
        ShortType,
        int,
        LongType,
        float,
        bool
    ]

    @staticmethod
    def _get_type(value):
        result = type(value)
        # python doesn't differentiate between 32 bit and 64 bit ints, so we have to do it ourselves
        if result is int and (value > INT_MAX or value < INT_MIN):
            result = ParameterMapUtil.LongType
        elif result is int and (SHORT_MIN <= value <= SHORT_MAX):
            result = ParameterMapUtil.ShortType
        if result not in ParameterMapUtil.SUPPORTED_TYPES:
            raise TypeError(f"Unsupported type for a value of a trace(Set) parameter: {result}.")
        return result

    @staticmethod
    def _highest_priority_rational_type(type1, type2):
        for rational_type in ParameterMapUtil._RATIONAL_TYPES_PRIORITY:
            if type1 == rational_type or type2 == rational_type:
                return rational_type

    @staticmethod
    def _get_type_of_list_elems(input_list):
        """Get the shared type of the elements in a list, with the goal to use that list as the value of a
        Trace(Set) parameter.
        Raises errors if elements don't share a type, or if lists of the found type may not be used as values
        of Trace(Set) parameters"""
        result_type = None

        for elem in input_list:
            elem_type = ParameterMapUtil._get_type(elem)
            if result_type is not None and elem_type != result_type:
                # Types of array elements may only vary if they are all rational numbers
                if elem_type in ParameterMapUtil._RATIONAL_TYPES_PRIORITY \
                        and result_type in ParameterMapUtil._RATIONAL_TYPES_PRIORITY:
                    result_type = ParameterMapUtil._highest_priority_rational_type(elem_type, result_type)
                else:
                    raise TypeError("A list that is used as Trace(set) parameter must have elements that share a type")
            else:
                result_type = elem_type

        if result_type not in ParameterMapUtil.LISTABLE_TYPES:
            raise TypeError(f"Lists of the {result_type} type are not supported as values of trace(set) parameters")

        return result_type

    @staticmethod
    def get_typed_parameter(param_value):
        value_type = ParameterMapUtil._get_type(param_value)
        if value_type == list:
            value_type = ParameterMapUtil._get_type_of_list_elems(param_value)
        return ParameterMapUtil.TYPE_TO_PARAMETER[value_type]

    @staticmethod
    def to_list_if_listable(value):
        return [value] if type(value) in ParameterMapUtil.LISTABLE_TYPES else value


class LockableDict(StringKeyOrderedDict):
    def __init__(self, seq=None, **kwargs):
        if seq is None:
            seq = {}
        self._is_locked = False
        super().__init__(seq, **kwargs)

    def _stop_if_locked(self):
        if self._is_locked:
            raise TypeError(f'Cannot modify a {type(self).__name__} object after it has been written into a trs file')

    def __delitem__(self, key):
        self._stop_if_locked()
        super().__delitem__(key)

    def __copy__(self):
        result = type(self)({key: value for (key, value) in self.items()})
        result._is_locked = self._is_locked
        return result

    def __deepcopy__(self, memo):
        return type(self)({copy.deepcopy(key): copy.deepcopy(value) for (key, value) in self.items()})

    def copy(self):
        result = type(self)(super().copy())
        result._is_locked = self._is_locked
        return result

    def pop(self, key):
        self._stop_if_locked()
        super().pop(key)

    def popitem(self, last=True):
        self._stop_if_locked()
        super().popitem(last)

    def clear(self):
        self._stop_if_locked()
        super().clear()

    def move_to_end(self, key, last=True):
        self._stop_if_locked()
        super().move_to_end(key, last)

    def lock_content(self):
        self._is_locked = True


class TraceSetParameterMap(LockableDict):
    def __setitem__(self, key, value):
        if not isinstance(value, TraceParameter) or type(value) is TraceSetParameter:
            raise TypeError('The value for a TraceSetParameterMap entry must be a specific subclass'
                            ' of TraceParameter (e.g. ByteArrayParameter).')
        self._stop_if_locked()
        super().__setitem__(key, value)

    def add_parameter(self, name: str, value):
        """Add a trace set parameter with a given name and value.
        If the name matches the identifier of a standard trace set parameter,
        then the value's type should be the type that standard trace set parameter expects"""
        try:
            std_param = StandardTraceSetParameters.from_identifier(name)
            typed_param = std_param.parameter_type.param_class
        except TypeError:
            typed_param = ParameterMapUtil.get_typed_parameter(value)
        self[name] = typed_param(ParameterMapUtil.to_list_if_listable(value))

    def add_standard_parameter(self, std_trace_set_param: StandardTraceSetParameters, value):
        """Add a standard trace set parameter with a given value"""
        typed_param = std_trace_set_param.parameter_type.param_class
        self[std_trace_set_param.identifier] = typed_param(ParameterMapUtil.to_list_if_listable(value))

    @staticmethod
    def deserialize(raw: BytesIO):
        result = TraceSetParameterMap()
        number_of_entries = read_short(raw)
        for _ in range(number_of_entries):
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


class TraceParameterDefinitionMap(LockableDict):
    def get_total_size(self) -> int:
        total = 0
        for param in self.values():
            total += param.length * param.param_type.byte_size
        return total

    def __setitem__(self, key, value):
        if type(value) is not TraceParameterDefinition:
            raise TypeError('The value for an entry in a TraceParameterDefinitionMap must be of '
                            'type TraceParameterDefinition')
        self._stop_if_locked()
        super().__setitem__(key, value)

    @staticmethod
    def deserialize(raw: BytesIO):
        result = TraceParameterDefinitionMap()
        number_of_entries = read_short(raw)
        for _ in range(number_of_entries):
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

    @staticmethod
    def from_trace_parameter_map(trace_parameters):
        """Create a trace parameters definition map from a trace parameter map"""
        offset = 0
        result = TraceParameterDefinitionMap()
        for key, trace_param in trace_parameters.items():
            size = len(trace_param)
            param_type = ParameterType.from_class(type(trace_param))
            result[key] = TraceParameterDefinition(param_type, size, offset)
            offset += size * param_type.byte_size
        return result


class TraceParameterMap(StringKeyOrderedDict):
    def __setitem__(self, key, value):
        if not isinstance(value, TraceParameter):
            raise TypeError('The value for a TraceParameterMap entry must be a specific subclass'
                            ' of TraceParameter (e.g. ByteArrayParameter).')
        super().__setitem__(key, value)

    def add_parameter(self, name: str, value):
        """Add a trace parameter with a given name and value
        If the name matches the identifier of a standard trace parameter,
        then the value's type should be the type that standard trace parameter expects"""
        try:
            std_param = StandardTraceParameters.from_identifier(name)
            typed_param = std_param.parameter_type.param_class
        except TypeError:
            typed_param = ParameterMapUtil.get_typed_parameter(value)
        self[name] = typed_param(ParameterMapUtil.to_list_if_listable(value))

    def add_standard_parameter(self, std_trace_param: StandardTraceParameters, value):
        """Add a standard trace parameter with a given value"""
        typed_param = std_trace_param.parameter_type.param_class
        self[std_trace_param.identifier] = typed_param(ParameterMapUtil.to_list_if_listable(value))

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

    def matches(self, definitions: TraceParameterDefinitionMap) -> bool:
        """Test whether this TraceParameterMap matches the associated definitions"""
        match = True
        for key, definition in definitions.items():
            if key not in self:
                match = False
            else:
                match = len(self) == definition.length and ParameterType.from_class(type(self)) == definition.param_type
            if not match:
                break
        return match
