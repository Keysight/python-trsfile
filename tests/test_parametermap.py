from io import BytesIO
from unittest import TestCase

from trsfile.parametermap import TraceSetParameterMap, TraceParameterDefinitionMap, TraceParameterMap
from trsfile.traceparameter import *


class TestTraceSetParameterMap(TestCase):
    SERIALIZED_MAP = b'\x09\x00' \
                     b'\x06\x00param1\x31\x05\x00\x01\x00\x00\x01\x01' \
                     b'\x06\x00param2\x01\x06\x00\x00\x01\x7f\x80\xfe\xff' \
                     b'\x06\x00param3\x02\x07\x00\x00\x00\x01\x00\xff\xff\xff\x00\x00\x01\x00\x80\xff\x7f' \
                     b'\x06\x00param4\x04\x04\x00\xff\xff\xff\xff\x01\x00\x00\x00\xff\xff\xff\x7f\x00\x00\x00\x80' \
                     b'\x06\x00param5\x08\x04\x00\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00' \
                     b'\xff\xff\xff\xff\xff\xff\xff\x7f\x00\x00\x00\x00\x00\x00\x00\x80' \
                     b'\x06\x00param6\x14\x03\x00\x00\x00\x00\xbf\x00\x00\x00\x3f\x00\x24\x74\x49' \
                     b'\x06\x00param7\x18\x03\x00\x00\x00\x00\x00\x00\x00\xe0\xbf\x00\x00\x00\x00\x00\x00\xe0\x3f' \
                     b'\x00\x00\x00\x00\x80\x84\x2e\x41' \
                     b'\x06\x00param8\x20\x2d\x00The quick brown fox jumped over the lazy dog.' \
                     b'\x06\x00\xe4\xb8\xad\xe6\x96\x87\x20\x0f\x00\xe4\xbd\xa0\xe5\xa5\xbd\xef\xbc\x8c\xe4\xb8' \
                     b'\x96\xe7\x95\x8c'

    @staticmethod
    def create_tracesetparametermap() -> TraceSetParameterMap:
        result = TraceSetParameterMap()
        result['param1'] = BooleanArrayParameter([True, False, False, True, True])
        result['param2'] = ByteArrayParameter([0, 1, 127, 128, 254, 255])
        result['param3'] = ShortArrayParameter([0, 1, -1, 255, 256, -32768, 32767])
        result['param4'] = IntegerArrayParameter([-1, 1, 0x7fffffff, -0x80000000])
        result['param5'] = LongArrayParameter([-1, 1, 0x7fffffffffffffff, -0x8000000000000000])
        result['param6'] = FloatArrayParameter([-0.5, 0.5, 1e6])
        result['param7'] = DoubleArrayParameter([-0.5, 0.5, 1e6])
        result['param8'] = StringParameter('The quick brown fox jumped over the lazy dog.')
        result['中文'] = StringParameter('你好，世界')
        return result

    def test_deserialize(self):
        map = TraceSetParameterMap.deserialize(BytesIO(self.SERIALIZED_MAP))
        deserialized = self.create_tracesetparametermap()
        self.assertDictEqual(map, deserialized)

    def test_serialize(self):
        map = self.create_tracesetparametermap()
        serialized = map.serialize()
        self.assertEqual(serialized, self.SERIALIZED_MAP)


class TestTraceParameterDefinitionMap(TestCase):
    SERIALIZED_DEFINITION = b'\x03\x00' \
                            b'\x05\x00INPUT\x01\x10\x00\x00\x00' \
                            b'\x05\x00TITLE\x20\x0d\x00\x10\x00' \
                            b'\x06\x00\xe4\xb8\xad\xe6\x96\x87\x20\x0f\x00\x1d\x00'

    @staticmethod
    def create_parameterdefinitionmap() -> TraceParameterDefinitionMap:
        map = TraceParameterDefinitionMap()
        map['INPUT'] = TraceParameterDefinition(ParameterType.BYTE, 16, 0)
        map['TITLE'] = TraceParameterDefinition(ParameterType.STRING, 13, 16)
        map['中文'] = TraceParameterDefinition(ParameterType.STRING, 15, 29)
        return map

    def test_get_total_size(self):
        size = self.create_parameterdefinitionmap().get_total_size()
        self.assertEqual(size, 44)

    def test_deserialize(self):
        self.assertDictEqual(TraceParameterDefinitionMap.deserialize(BytesIO(self.SERIALIZED_DEFINITION)),
                             self.create_parameterdefinitionmap())

    def test_serialize(self):
        self.assertEqual(self.create_parameterdefinitionmap().serialize(),
                         self.SERIALIZED_DEFINITION)


class TestTraceParameterMap(TestCase):
    CAFEBABE = bytes.fromhex('cafebabedeadbeef0102030405060708')
    SERIALIZED_MAP = CAFEBABE + \
                     b'Hello, world!' \
                     b'\xe4\xbd\xa0\xe5\xa5\xbd\xef\xbc\x8c\xe4\xb8\x96\xe7\x95\x8c'

    @staticmethod
    def create_parametermap() -> TraceParameterMap:
        map = TraceParameterMap()
        map['INPUT'] = ByteArrayParameter(list(TestTraceParameterMap.CAFEBABE))
        map['TITLE'] = StringParameter('Hello, world!')
        map['中文'] = StringParameter('你好，世界')
        return map

    def test_deserialize(self):
        self.assertDictEqual(
            TraceParameterMap.deserialize(self.SERIALIZED_MAP,
                                          TestTraceParameterDefinitionMap.create_parameterdefinitionmap()),
            self.create_parametermap())

    def test_serialize(self):
        self.assertEqual(self.SERIALIZED_MAP, self.create_parametermap().serialize())
