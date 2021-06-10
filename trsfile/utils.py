import struct
from io import BytesIO

LITTLE_ENDIAN_ORDER = 'little'
UTF_8 = 'utf-8'


def encode_as_short(value):
    return struct.pack('<h', value)


def read_parameter_name(io_bytes: BytesIO):
    name_length = read_short(io_bytes)
    name = io_bytes.read(name_length).decode(UTF_8)
    return name


def read_short(io_bytes: BytesIO):
    number_of_entries = int.from_bytes(io_bytes.read(2), LITTLE_ENDIAN_ORDER)
    return number_of_entries
