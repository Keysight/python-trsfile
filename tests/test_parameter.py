from io import BytesIO
from unittest import TestCase

from numpy import ndarray, int16, array, int32, int64, single, double, uint8, int8, uint16

from trsfile.traceparameter import BooleanArrayParameter, ByteArrayParameter, DoubleArrayParameter, FloatArrayParameter, \
    IntegerArrayParameter, ShortArrayParameter, LongArrayParameter, StringParameter


class TestParameter(TestCase):
    def test_bool_parameter(self):
        serialized_param = b'\x01\x00\x01'
        param1 = BooleanArrayParameter([True, False, True])
        self.assertEqual(serialized_param, param1.serialize())
        self.assertEqual(BooleanArrayParameter.deserialize(BytesIO(serialized_param), 3), param1)
        param2 = BooleanArrayParameter(ndarray(shape=[3], dtype=bool,
                                               buffer=array([bool(val) for val in [True, False, True]])))
        self.assertEqual(param1, param2)

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

        with self.assertWarns(UserWarning):
            param2 = ByteArrayParameter(ndarray(shape=[2, 2, 4], dtype=uint8,
                                                buffer=array([uint8(val) for val in int_data])))
        self.assertEqual(param1, param2)

        param2 = ByteArrayParameter(bytearray(int_data))
        self.assertEqual(param1, param2)

        param3 = ByteArrayParameter(bytes(int_data))
        self.assertEqual(param1, param3)

        with self.assertRaises(TypeError):
            ByteArrayParameter([0, '1'])
        with self.assertRaises(TypeError):
            ByteArrayParameter([bytes([0, 1, 2, 3]), bytes([4, 5, 6, 7])])
        with self.assertRaises(OverflowError):
            ByteArrayParameter(ndarray(shape=[16], dtype=int8, buffer=array(int_data, dtype=int8)))
        with self.assertRaises(TypeError):
            ByteArrayParameter(ndarray(shape=[16], dtype=uint16, buffer=array(int_data, dtype=uint16)))
        with self.assertRaises(ValueError):
            ByteArrayParameter([])
        with self.assertRaises(ValueError):
            ByteArrayParameter(ndarray(shape=[0], dtype=uint8, buffer=array([])))
        with self.assertRaises(TypeError):
            ByteArrayParameter([0, 1, 2, -1])
        with self.assertRaises(TypeError):
            ByteArrayParameter([0, 1, 2, 256])

    def test_double_parameter(self):
        serialized_param = b'\x00\x00\x00\x00\x00\x00\xe0\xbf\x00\x00\x00\x00\x00\x00\xe0\x3f' \
                           b'\x00\x00\x00\x00\x80\x84\x2e\x41'
        param1 = DoubleArrayParameter([-0.5, 0.5, 1e6])
        self.assertEqual(serialized_param, param1.serialize())
        self.assertEqual(DoubleArrayParameter.deserialize(BytesIO(serialized_param), 3), param1)

        param2 = DoubleArrayParameter(ndarray(shape=[3], dtype=double, buffer=array([-0.5, 0.5, 1e6])))
        self.assertEqual(param1, param2)

        # an array of only integers is still a valid value of a DoubleArrayParameter
        param1 = DoubleArrayParameter([-1, 2, 1000000])
        param2 = DoubleArrayParameter([-1, 2.0, 1e6])
        self.assertEqual(param1, param2)
        with self.assertWarns(UserWarning):
            param1 = DoubleArrayParameter(ndarray(shape=[1, 3], dtype=int32,
                                                  buffer=array([int32(val) for val in [-1, 2, 1000000]])))
        self.assertEqual(param1, param2)

        with self.assertWarns(UserWarning):
            param1 = DoubleArrayParameter(ndarray(shape=[1, 3], dtype=int64,
                                                  buffer=array([int64(val) for val in [-1, 2, 10000000000]])))
        param2 = DoubleArrayParameter([-1, 2.0, 1e10])
        self.assertEqual(param1, param2)

        # a float array parameter is not the same as a double array parameter
        param1 = FloatArrayParameter([1, 2.0, 1e6])
        param2 = DoubleArrayParameter([1, 2.0, 1e6])
        self.assertNotEqual(param1, param2)

        with self.assertRaises(TypeError):
            DoubleArrayParameter([0.5, -0.5, 'NaN'])
        with self.assertRaises(TypeError):
            DoubleArrayParameter(ndarray(shape=[3], dtype=single,
                                         buffer=array([single(val) for val in [-0.5, 0.5, 1e6]])))
        with self.assertRaises(TypeError):
            DoubleArrayParameter(0.5)
        with self.assertRaises(ValueError):
            DoubleArrayParameter([])
        with self.assertRaises(ValueError):
            IntegerArrayParameter(ndarray(shape=[0], dtype=double, buffer=array([])))

    def test_float_parameter(self):
        serialized_param = b'\x00\x00\x00\xbf\x00\x00\x00\x3f\x00\x24\x74\x49'
        param1 = FloatArrayParameter([-0.5, 0.5, 1e6])
        self.assertEqual(serialized_param, param1.serialize())
        self.assertEqual(FloatArrayParameter.deserialize(BytesIO(serialized_param), 3), param1)

        param2 = FloatArrayParameter(ndarray(shape=[3], dtype=single,
                                             buffer=array([single(val) for val in [-0.5, 0.5, 1e6]])))
        self.assertEqual(param1, param2)

        # an array of only integers is still a valid value of a FloatArrayParameter
        param1 = FloatArrayParameter([-1, 2, 1000000])
        param2 = FloatArrayParameter([-1, 2.0, 1e6])
        self.assertEqual(param1, param2)

        with self.assertWarns(UserWarning):
            param1 = FloatArrayParameter(ndarray(shape=[1, 3], dtype=int32,
                                                 buffer=array([int32(val) for val in [-1, 2, 1000000]])))
        self.assertEqual(param1, param2)

        with self.assertWarns(UserWarning):
            param1 = FloatArrayParameter(ndarray(shape=[1, 3], dtype=int64,
                                                 buffer=array([int64(val) for val in [-1, 2, 10000000000]])))
        param2 = FloatArrayParameter([-1, 2.0, 1e10])
        self.assertEqual(param1, param2)

        with self.assertRaises(TypeError):
            FloatArrayParameter([0.5, -0.5, 'NaN'])
        with self.assertRaises(TypeError):
            FloatArrayParameter(ndarray(shape=[3], dtype=double,
                                        buffer=array([double(val) for val in [-0.5, 0.5, 1e6]])))
        with self.assertRaises(TypeError):
            FloatArrayParameter(0.5)
        with self.assertRaises(ValueError):
            FloatArrayParameter([])
        with self.assertRaises(ValueError):
            IntegerArrayParameter(ndarray(shape=[0], dtype=single, buffer=array([])))

    def test_integer_parameter(self):
        serialized_param = b'\xff\xff\xff\xff\x01\x00\x00\x00\xff\xff\xff\x7f\x00\x00\x00\x80'
        param1 = IntegerArrayParameter([-1, 1, 0x7fffffff, -0x80000000])
        self.assertEqual(serialized_param, param1.serialize())
        self.assertEqual(IntegerArrayParameter.deserialize(BytesIO(serialized_param), 4), param1)

        with self.assertWarns(UserWarning):
            param2 = IntegerArrayParameter(ndarray(shape=[2, 2], dtype=int32,
                                                   buffer=array([int32(val) for val in [-1, 1, 0x7fffffff, -0x80000000]])))
        self.assertEqual(param1, param2)

        # a short array parameter is not the same as an int array parameter
        param1 = ShortArrayParameter([0, 1, -1, 255, 256, -32768, 32767])
        param2 = IntegerArrayParameter([0, 1, -1, 255, 256, -32768, 32767])
        self.assertNotEqual(param1, param2)

        # verify that an integer array parameter based on a ndarray filled with int16s works
        param1 = IntegerArrayParameter(ndarray(shape=[7], dtype=int16,
                                               buffer=array([int16(val) for val in [0, 1, -1, 255, 256, -32768, 32767]])))
        self.assertEqual(param1, param2)

        with self.assertRaises(TypeError):
            IntegerArrayParameter([1, 256, 1.0])
        with self.assertRaises(TypeError):
            IntegerArrayParameter(ndarray(shape=[4], dtype=int64,
                                          buffer=array([int64(val) for val in [-1, 1, 0x7fffffffffffffff, -0x8000000000000000]])))
        with self.assertRaises(ValueError):
            IntegerArrayParameter(ndarray(shape=[0], dtype=int32, buffer=array([])))
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
        param1= LongArrayParameter([-1, 1, 0x7fffffffffffffff, -0x8000000000000000])
        self.assertEqual(serialized_param, param1.serialize())
        self.assertEqual(LongArrayParameter.deserialize(BytesIO(serialized_param), 4), param1)

        with self.assertWarns(UserWarning):
            param2 = LongArrayParameter(ndarray(shape=[2, 2], dtype=int64,
                                                buffer=array([int64(val) for val in [-1, 1, 0x7fffffffffffffff, -0x8000000000000000]])))
        self.assertEqual(param1, param2)

        # an int array parameter is not the same as a long array parameter
        param1 = IntegerArrayParameter([-1, 1, 0x7fffffff, -0x80000000])
        param2 = LongArrayParameter([-1, 1, 0x7fffffff, -0x80000000])
        self.assertNotEqual(param1, param2)

        # verify that a long array parameter based on a ndarray filled with int32s works
        with self.assertWarns(UserWarning):
            param1 = LongArrayParameter(ndarray(shape=[1, 4], dtype=int32,
                                                buffer=array([int32(val) for val in [-1, 1, 0x7fffffff, -0x80000000]])))
        self.assertEqual(param1, param2)

        with self.assertRaises(TypeError):
            LongArrayParameter([1, 256, 1.0])
        with self.assertRaises(TypeError):
            LongArrayParameter(1)
        with self.assertRaises(ValueError):
            LongArrayParameter([])
        with self.assertRaises(ValueError):
            LongArrayParameter(ndarray(shape=[0], dtype=int64, buffer=array([])))

    def test_short_parameter(self):
        serialized_param = b'\x00\x00\x01\x00\xff\xff\xff\x00\x00\x01\x00\x80\xff\x7f'
        param1 = ShortArrayParameter([0, 1, -1, 255, 256, -32768, 32767])
        self.assertEqual(serialized_param, param1.serialize())
        self.assertEqual(ShortArrayParameter.deserialize(BytesIO(serialized_param), 7), param1)

        param2 = ShortArrayParameter(ndarray(shape=[7], dtype=int16,
                                             buffer=array([int16(val) for val in [0, 1, -1, 255, 256, -32768, 32767]])))
        self.assertEqual(param1, param2)

        with self.assertRaises(TypeError):
            ShortArrayParameter([1, 256, 1.0])
        with self.assertRaises(TypeError):
            ShortArrayParameter(ndarray(shape=[4], dtype=int32,
                                        buffer=array([int32(val) for val in [-1, 1, 0x7fffffff, -0x80000000]])))
        with self.assertRaises(ValueError):
            ShortArrayParameter(ndarray(shape=[0], dtype=int16, buffer=array([])))
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
