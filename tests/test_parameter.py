from io import BytesIO
from unittest import TestCase

from trsfile.traceparameter import BooleanArrayParameter, ByteArrayParameter, DoubleArrayParameter, FloatArrayParameter, \
    IntegerArrayParameter, ShortArrayParameter, LongArrayParameter, StringParameter


class TestParameter(TestCase):
    def test_bool_parameter(self):
        serialized_param = b'\x01\x00\x01'
        param = BooleanArrayParameter([True, False, True])
        self.assertEqual(serialized_param, param.serialize())
        self.assertEqual(BooleanArrayParameter.deserialize(BytesIO(serialized_param), 3), param)

        with self.assertRaises(TypeError):
            BooleanArrayParameter(True)
        with self.assertRaises(ValueError):
            BooleanArrayParameter([])
        with self.assertRaises(TypeError):
            BooleanArrayParameter([True, False, 1])

    def test_byte_parameter(self):
        serialized_param = bytes.fromhex('cafebabedeadbeef0102030405060708')
        int_data = [0xCA, 0xFE, 0xBA, 0xBE, 0xDE, 0xAD, 0xBE, 0xEF, 1, 2, 3, 4, 5, 6, 7, 8]

        param1 = ByteArrayParameter(int_data)
        self.assertEqual(serialized_param, param1.serialize())
        self.assertEqual(ByteArrayParameter.deserialize(BytesIO(serialized_param), 16), param1)

        param2 = ByteArrayParameter(bytearray(int_data))
        self.assertEqual(param1, param2)

        param3 = ByteArrayParameter(bytes(int_data))
        self.assertEqual(param1, param3)

        with self.assertRaises(TypeError):
            ByteArrayParameter([0, '1'])
        with self.assertRaises(TypeError):
            ByteArrayParameter([bytes([0, 1, 2, 3]), bytes([4, 5, 6, 7])])
        with self.assertRaises(ValueError):
            ByteArrayParameter([])
        with self.assertRaises(TypeError):
            ByteArrayParameter([0, 1, 2, -1])
        with self.assertRaises(TypeError):
            ByteArrayParameter([0, 1, 2, 256])

    def test_double_parameter(self):
        serialized_param = b'\x00\x00\x00\x00\x00\x00\xe0\xbf\x00\x00\x00\x00\x00\x00\xe0\x3f' \
                           b'\x00\x00\x00\x00\x80\x84\x2e\x41'
        param = DoubleArrayParameter([-0.5, 0.5, 1e6])
        self.assertEqual(serialized_param, param.serialize())
        self.assertEqual(DoubleArrayParameter.deserialize(BytesIO(serialized_param), 3), param)

        # an array of only integers is still a valid value of a DoubleArrayParameter
        param1 = DoubleArrayParameter([1, 2, 1000000])
        param2 = DoubleArrayParameter([1, 2.0, 1e6])
        self.assertEqual(param1, param2)

        # a float array parameter is not the same as a double array parameter
        param1 = FloatArrayParameter([1, 2.0, 1e6])
        param2 = DoubleArrayParameter([1, 2.0, 1e6])
        self.assertNotEqual(param1, param2)

        with self.assertRaises(TypeError):
            DoubleArrayParameter([0.5, -0.5, 'NaN'])
        with self.assertRaises(TypeError):
            DoubleArrayParameter(0.5)
        with self.assertRaises(ValueError):
            DoubleArrayParameter([])

    def test_float_parameter(self):
        serialized_param = b'\x00\x00\x00\xbf\x00\x00\x00\x3f\x00\x24\x74\x49'
        param = FloatArrayParameter([-0.5, 0.5, 1e6])
        self.assertEqual(serialized_param, param.serialize())
        self.assertEqual(FloatArrayParameter.deserialize(BytesIO(serialized_param), 3), param)

        # an array of only integers is still a valid value of a FloatArrayParameter
        param1 = FloatArrayParameter([1, 2, 1000000])
        param2 = FloatArrayParameter([1, 2.0, 1e6])
        self.assertEqual(param1, param2)

        with self.assertRaises(TypeError):
            FloatArrayParameter([0.5, -0.5, 'NaN'])
        with self.assertRaises(TypeError):
            FloatArrayParameter(0.5)
        with self.assertRaises(ValueError):
            FloatArrayParameter([])

    def test_integer_parameter(self):
        serialized_param = b'\xff\xff\xff\xff\x01\x00\x00\x00\xff\xff\xff\x7f\x00\x00\x00\x80'
        param = IntegerArrayParameter([-1, 1, 0x7fffffff, -0x80000000])
        self.assertEqual(serialized_param, param.serialize())
        self.assertEqual(IntegerArrayParameter.deserialize(BytesIO(serialized_param), 4), param)

        # a short array parameter is not the same as an int array parameter
        param1 = ShortArrayParameter([0, 1, -1, 255, 256, -32768, 32767])
        param2 = IntegerArrayParameter([0, 1, -1, 255, 256, -32768, 32767])
        self.assertNotEqual(param1, param2)

        with self.assertRaises(TypeError):
            IntegerArrayParameter([1, 256, 1.0])
        with self.assertRaises(TypeError):
            IntegerArrayParameter(1)
        with self.assertRaises(ValueError):
            IntegerArrayParameter([])
        with self.assertRaises(TypeError):
            IntegerArrayParameter([-1, 1, 0x80000000, -0x80000000])
        with self.assertRaises(TypeError):
            IntegerArrayParameter([-1, 1, 0x7fffffff, -0x80000001])

    def test_long_parameter(self):
        serialized_param = b'\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00' \
                           b'\xff\xff\xff\xff\xff\xff\xff\x7f\x00\x00\x00\x00\x00\x00\x00\x80'
        param = LongArrayParameter([-1, 1, 0x7fffffffffffffff, -0x8000000000000000])
        self.assertEqual(serialized_param, param.serialize())
        self.assertEqual(LongArrayParameter.deserialize(BytesIO(serialized_param), 4), param)

        # an int array parameter is not the same as a long array parameter
        param1 = IntegerArrayParameter([-1, 1, 0x7fffffff, -0x80000000])
        param2 = LongArrayParameter([-1, 1, 0x7fffffff, -0x80000000])
        self.assertNotEqual(param1, param2)

        with self.assertRaises(TypeError):
            LongArrayParameter([1, 256, 1.0])
        with self.assertRaises(TypeError):
            LongArrayParameter(1)
        with self.assertRaises(ValueError):
            LongArrayParameter([])

    def test_short_parameter(self):
        serialized_param = b'\x00\x00\x01\x00\xff\xff\xff\x00\x00\x01\x00\x80\xff\x7f'
        param = ShortArrayParameter([0, 1, -1, 255, 256, -32768, 32767])
        self.assertEqual(serialized_param, param.serialize())
        self.assertEqual(ShortArrayParameter.deserialize(BytesIO(serialized_param), 7), param)

        with self.assertRaises(TypeError):
            ShortArrayParameter([1, 256, 1.0])
        with self.assertRaises(TypeError):
            ShortArrayParameter(1)
        with self.assertRaises(ValueError):
            ShortArrayParameter([])
        with self.assertRaises(TypeError):
            ShortArrayParameter([-1, 1, 32768, -32768])
        with self.assertRaises(TypeError):
            ShortArrayParameter([-1, 1, 32767, -32769])

    def test_string_parameter(self):
        serialized_param = b'The quick brown fox jumped over the lazy dog.'
        param = StringParameter('The quick brown fox jumped over the lazy dog.')
        self.assertEqual(serialized_param, param.serialize())
        self.assertEqual(StringParameter.deserialize(BytesIO(serialized_param), 45), param)

        serialized_param = b'\xe4\xbd\xa0\xe5\xa5\xbd\xef\xbc\x8c\xe4\xb8\x96\xe7\x95\x8c'
        param = StringParameter('你好，世界')
        self.assertEqual(serialized_param, param.serialize())
        self.assertEqual(StringParameter.deserialize(BytesIO(serialized_param), 15), param)

        with self.assertRaises(TypeError):
            StringParameter(['The', 'quick', 'brown', 'fox', 'jumped', 'over', 'the', 'lazy', 'dog'])
        with self.assertRaises(ValueError):
            StringParameter(None)


