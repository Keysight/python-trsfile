import struct


def encode_as_short(value):
    return struct.pack('<h', value)
