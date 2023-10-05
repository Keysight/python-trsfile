from __future__ import annotations
import copy
import numbers
import warnings
from typing import Any, Union, List, Dict

from trsfile.compatibility import alias, aliased
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

    ParameterValueType = Union[int, float, bool, List[int], List[float], List[bool], bytes, bytearray, str]
    StrictParameterValueType = Union[List[int], List[float], List[bool], bytes, bytearray, str]


    @staticmethod
    def _get_type(value):
        result = type(value)
        # python doesn't differentiate between 16 bit, 32 bit and 64 bit ints, so we have to do it ourselves
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
        # If neither input type is a rational type, raise an error.
        # This should never happen, as type-checking is done before this function is called
        raise TypeError(f"Cannot create a Number array from elements of types {type1.__name__} and {type2.__name__}")

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
    def get_typed_parameter(param_value: ParameterValueType) -> type:
        """Get the subclass of TraceParameter needed to hold a given value
        Throws an error if the value cannot be stored in any TraceParameter subclass"""
        value_type = ParameterMapUtil._get_type(param_value)
        if value_type == list:
            value_type = ParameterMapUtil._get_type_of_list_elems(param_value)
        return ParameterMapUtil.TYPE_TO_PARAMETER[value_type]

    @staticmethod
    def to_list_if_listable(value: ParameterValueType) -> StrictParameterValueType:
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


@aliased
class TraceSetParameterMap(LockableDict):
    default_values = {
        StandardTraceSetParameters.DISPLAY_HINT_X_LABEL: "",
        StandardTraceSetParameters.DISPLAY_HINT_Y_LABEL: "",
        StandardTraceSetParameters.DISPLAY_HINT_NUM_TRACES_SHOWN: 1,
        StandardTraceSetParameters.DISPLAY_HINT_TRACES_OVERLAP: False,
        StandardTraceSetParameters.DISPLAY_HINT_USE_LOG_SCALE: False,
        StandardTraceSetParameters.X_OFFSET: 0,
        StandardTraceSetParameters.TRACE_OFFSET: 0,
        StandardTraceSetParameters.X_SCALE: 1.0,
        StandardTraceSetParameters.Y_SCALE: 1.0
    }

    def __setitem__(self, key: str, value: Union[TraceParameter, TraceSetParameter]):
        if not isinstance(value, TraceParameter) or type(value) is TraceSetParameter:
            raise TypeError('The value for a TraceSetParameterMap entry must be a specific subclass'
                            ' of TraceParameter (e.g. ByteArrayParameter).')
        self._stop_if_locked()
        super().__setitem__(key, value)

    @alias("add")
    def add_parameter(self, name: str, value: ParameterMapUtil.ParameterValueType) -> TraceSetParameterMap:
        """Add a trace set parameter with a given name and value.
        If the name matches the identifier of a standard trace set parameter,
        then the value's type should be the type that standard trace set parameter expects.
        If the parameter already exists within the map, it will be overwritten.

        :param name:  The name of the parameter that will be added
        :param value: The value of the parameter. If the name matches that of a standard trace set parameter, it is
                      recommended that the type of the value matches that of standard trace set parameter. Otherwise,
                      valid types are: int, float, bool, List[int], List[float], List[bool], bytes, bytearray or str
        :return:      This TraceSetParameterMap after adding the new parameter"""
        try:
            std_param = StandardTraceSetParameters.from_identifier(name)
            typed_param = std_param.parameter_type.param_class
            self[std_param.identifier] = typed_param(ParameterMapUtil.to_list_if_listable(value))
            return self
        # if no std_param can be found, a ValueError is raised,
        # if adding the trace parameter to the map fails, a TypeError is raised
        except (ValueError, TypeError) as e:
            if isinstance(e, TypeError):
                warnings.warn("Adding a trace set parameter with a name that matches a standard set trace parameter, "
                              "but with a type that doesn't match that standard trace set parameter.\nThis may lead to "
                              "unexpected behavior when displaying this traceset or processing it in Inspector")
            typed_param = ParameterMapUtil.get_typed_parameter(value)
            self[name] = typed_param(ParameterMapUtil.to_list_if_listable(value))

    def add_standard_parameter(self, std_trace_set_param: StandardTraceSetParameters,
                               value: ParameterMapUtil.ParameterValueType) -> TraceSetParameterMap:
        """Add a standard trace set parameter with a given value.
        If the parameter already exists within the map, it will be overwritten.

        :param std_trace_set_param: The standard trace set parameter that will be added
        :param value:               The value of the parameter. The type this value must have depends on
                                    the standard trace set parameter.
        :return:                    This TraceSetParameterMap after adding the new standard parameter"""
        typed_param = std_trace_set_param.parameter_type.param_class
        self[std_trace_set_param.identifier] = typed_param(ParameterMapUtil.to_list_if_listable(value))
        return self

    def fill_from_headers(self, headers: Dict['Header', Any]) -> TraceSetParameterMap:
        """Add to this trace set parameter map all data that is in the header
        and for which standard trace set parameters exist.
        Data that already exists in the map will not be overwritten.

        :param headers: The headers dictionary from which data will be copied into the trace set parameter map
        :return:        This TraceSetParameterMap after adding the parameters based on the headers"""
        for header_tag, value in headers.items():
            std_param = header_tag.equivalent_std_param
            if std_param is not None and std_param.identifier not in self:
                self.add_standard_parameter(std_param, value)

    def add_defaults(self) -> TraceSetParameterMap:
        """If specific standard trace set parameters don't exist yet in the map, add them with default values
         :return: This TraceSetParameterMap after adding the default parameters"""
        for key, value in TraceSetParameterMap.default_values.items():
            if key.identifier not in self:
                self.add_standard_parameter(key, value)

    @staticmethod
    def deserialize(raw: BytesIO) -> TraceSetParameterMap:
        result = TraceSetParameterMap()
        number_of_entries = read_short(raw)
        for _ in range(number_of_entries):
            name = read_parameter_name(raw)
            value = TraceSetParameter.deserialize(raw)
            result[name] = value
        return result

    def serialize(self) -> bytes:
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

    def __setitem__(self, key: str, value: TraceParameterDefinition):
        if type(value) is not TraceParameterDefinition:
            raise TypeError('The value for an entry in a TraceParameterDefinitionMap must be of '
                            'type TraceParameterDefinition')
        self._stop_if_locked()
        super().__setitem__(key, value)

    def insert_std(self, name: str, size: int, offset: int) -> TraceParameterDefinitionMap:
        """Insert a trace parameter definition of a StandardTraceParameter into this map in a specified location. If
        the given offset would put the new TraceParameter in the middle of a parameter already present in the map, the
        offset is increased to put the new parameter after that existing one instead. Any parameters already present
        in the map that have a greater or equal offset than the new parameter, have their offset increased to make space
        for the new parameter.

        :param name:   The name of the TraceParameter for which to add a definition. This name must match that of a
                       StandardTraceParameter
        :param size:   The size of the TraceParameter, in number of elements
        :param offset: The offset of the TraceParameter, in bytes
        :return:       This TraceParameterDefinition map after adding the new definition
        """
        try:
            type = StandardTraceParameters.from_identifier(name).parameter_type
            return self.insert(name, type, size, offset)
        except ValueError:
            raise ValueError(f"No StandardTraceParameter found with name '{name}'. Either use the 'insert' method or "
                             f"correct the name to match a standard trace parameter.")

    def insert(self, name: str, type: ParameterType, size: int, offset: int) -> TraceParameterDefinitionMap:
        """Insert a trace parameter definition into this map in a specified location. If the given offset would put the
        new TraceParameter in the middle of a parameter already present in the map, the offset is increased to put the
        new parameter after that existing one instead. Any parameters already present in the map that have a greater
        or equal offset than the new parameter, have their offset increased to make space for the new parameter.

        :param name:   The name of the TraceParameter for which to add a definition
        :param type:   The type of the TraceParameter for which to add a definition
        :param size:   The size of the TraceParameter, in number of elements
        :param offset: The offset of the TraceParameter, in bytes
        :return:       This TraceParameterDefinition map after adding the new definition
        """
        self._stop_if_locked()
        params_to_move_back = []
        for key, param in self.items():
            if param.offset >= offset:
                param.offset += size * type.byte_size
                params_to_move_back.append(key)
            elif param.offset + param.length * param.param_type.byte_size > offset:
                offset = param.offset + param.length * param.param_type.byte_size
                warnings.warn("Given offset would put a parameter inside another trace parameter.\n"
                              f"Increased the offset of the inserted parameter definition to {offset} to prevent this.")

        new_definition = TraceParameterDefinition(type, size, offset)
        self.__setitem__(name, new_definition)
        for param in params_to_move_back:
            self.move_to_end(param)
        return self

    def append_std(self, name: str, size: int) -> TraceParameterDefinitionMap:
        """Append a trace parameter definition of a StandardTraceParameter to this map. The parameter wil be added after
       all parameter definitions already in the map.

       :param name: The name of the TraceParameter for which to add a definition. This name must match that of a
                    StandardTraceParameter
       :param size: The size of the TraceParameter, in number of elements
       :return:     This TraceParameterDefinition map after adding the new definition"""
        try:
            type = StandardTraceParameters.from_identifier(name).parameter_type
            return self.append(name, type, size)
        except ValueError:
            raise ValueError(f"No StandardTraceParameter found with name '{name}'. Either use the 'append' method or "
                             f"correct the name to match a standard trace parameter.")

    def append(self, name: str, type: ParameterType, size: int) -> TraceParameterDefinitionMap:
        """Append a trace parameter definition to this map. The parameter wil be added after all parameter definitions
        already in the map.

        :param name: The name of the TraceParameter for which to add a definition
        :param type: The type of the TraceParameter for which to add a definition
        :param size: The size of the TraceParameter, in number of elements
        :return:     This TraceParameterDefinition map after adding the new definition"""
        new_definition = TraceParameterDefinition(type, size, self.get_total_size())
        self.__setitem__(name, new_definition)
        return self

    @staticmethod
    def deserialize(raw: BytesIO) -> TraceParameterDefinitionMap:
        result = TraceParameterDefinitionMap()
        number_of_entries = read_short(raw)
        for _ in range(number_of_entries):
            name = read_parameter_name(raw)
            value = TraceParameterDefinition.deserialize(raw)
            result[name] = value
        return result

    def serialize(self) -> bytearray:
        out = bytearray()
        out.extend(encode_as_short(len(self)))
        for name, value in self.items():
            encoded_name = name.encode(UTF_8)
            out.extend(encode_as_short(len(encoded_name)))
            out.extend(encoded_name)
            out.extend(value.serialize())
        return out

    @staticmethod
    def from_trace_parameter_map(trace_parameters: TraceParameterMap) -> TraceParameterDefinitionMap:
        """Create a trace parameters definition map from a trace parameter map.

        :param trace_parameters: The trace parameter map from which the definitions will be deduced

        :return:                 A parameter definition map that described the metadata of the input trace parameter map"""
        if isinstance(trace_parameters, RawTraceData):
            warnings.warn("Creating a trace parameter definition map from raw trace data.\nThis is not recommended, "
                          "as it will not add any meta information about the trace data.\nEither manually define a "
                          "TraceParameterDefinitionMap for the traceset or make sure the first trace you add to the "
                          "traceset has a proper TraceParameterMap")

        offset = 0
        result = TraceParameterDefinitionMap()
        for key, trace_param in trace_parameters.items():
            size = len(trace_param)
            param_type = ParameterType.from_class(type(trace_param))
            result[key] = TraceParameterDefinition(param_type, size, offset)
            offset += size * param_type.byte_size
        return result


@aliased
class TraceParameterMap(StringKeyOrderedDict):
    def __setitem__(self, key: str, value: TraceParameter):
        if not isinstance(value, TraceParameter):
            raise TypeError('The value for a TraceParameterMap entry must be a specific subclass'
                            ' of TraceParameter (e.g. ByteArrayParameter).')
        super().__setitem__(key, value)

    @alias("add")
    def add_parameter(self, name: str, value: ParameterMapUtil.ParameterValueType) -> TraceParameterMap:
        """Add a trace parameter with a given name and value
        If the name matches the identifier of a standard trace parameter,
        then the value's type should be the type that standard trace parameter expects.
        If the parameter already exists within the map, it will be overwritten.

        :param name:  The name of the parameter that will be added
        :param value: The value of the parameter. If the name matches that of a standard trace parameter, it is
                      recommended that the type of the value matches that of standard trace set parameter. Otherwise,
                      valid types are: int, float, bool, List[int], List[float], List[bool], bytes, bytearray or str
        :return:      This map after adding the parameter"""
        try:
            std_param = StandardTraceParameters.from_identifier(name)
            typed_param = std_param.parameter_type.param_class
            self[std_param.identifier] = typed_param(ParameterMapUtil.to_list_if_listable(value))
        # if no std_param can be found, a ValueError is raised,
        # if adding the trace parameter to the map fails, a TypeError is raised
        except (TypeError, ValueError) as e:
            if isinstance(e, TypeError):
                warnings.warn("Adding a trace parameter with a name that matches a standard trace parameter, but with "
                              "a type that doesn't match that standard trace parameter.\nThis may lead to unexpected "
                              "behavior when displaying this traceset or processing this trace in Inspector")
            typed_param = ParameterMapUtil.get_typed_parameter(value)
            self[name] = typed_param(ParameterMapUtil.to_list_if_listable(value))
        return self

    def add_standard_parameter(self, std_trace_param: StandardTraceParameters,
                               value: ParameterMapUtil.ParameterValueType) -> TraceParameterMap:
        """Add a standard trace parameter with a given value.
        If the parameter already exists within the map, it will be overwritten.

        :param std_trace_param: The standard trace parameter that will be added
        :param value:           The value of the parameter. The type this value must have depends on
                                the standard trace parameter.
        :return:                This map after adding the parameter"""
        typed_param = std_trace_param.parameter_type.param_class
        self[std_trace_param.identifier] = typed_param(ParameterMapUtil.to_list_if_listable(value))
        return self

    @staticmethod
    def deserialize(raw: bytes, definitions: TraceParameterDefinitionMap) -> TraceParameterMap:
        io_bytes = BytesIO(raw)
        result = TraceParameterMap()
        for key, val in definitions.items():
            io_bytes.seek(val.offset)
            param = val.param_type.param_class.deserialize(io_bytes, val.length)
            result[key] = param
        return result

    def serialize(self) -> bytearray:
        out = bytearray()
        for val in self.values():
            out.extend(val.serialize())
        return out

    def matches(self, definitions: TraceParameterDefinitionMap) -> bool:
        """Test whether this TraceParameterMap matches the associated definitions

        :param definitions: The trace parameter definition map of the trs file to which the trace with this trace
                            parameter map will be added

        :return:            A boolean that is true if the trace parameter definitions match the metadata of the trace
                            parameter map"""
        match = True
        offset = 0
        matched_keys = []
        for key, value in self.items():
            if key not in definitions:
                match = False
            else:
                definition = definitions[key]
                matched_keys.append(key)
                # Confirm the length, type and offset are correct
                match = len(value) == definition.length
                match &= ParameterType.from_class(type(value)) == definition.param_type
                match &= definition.offset == offset
                offset += len(value) * definition.param_type.byte_size
            if not match:
                break
        match &= matched_keys == list(definitions.keys())
        return match


class RawTraceData(TraceParameterMap):
    def __init__(self, data: bytes):
        super().__init__()
        super().__setitem__("LEGACY_DATA", ByteArrayParameter(data))

    def __setitem__(self, key: str, value: TraceParameter):
        raise KeyError("Adding Trace Parameters into raw trace data is not allowed")

    def matches(self, definitions: TraceParameterDefinitionMap) -> bool:
        """Test whether this RawTraceData could be interpreted by given definitions

        :param definitions: The trace parameter definition map to check this raw trace data against

        :return:            A boolean that is true if the trace parameter definitions can interpret this raw trace data"""
        return definitions.get_total_size() == len(self["LEGACY_DATA"])
