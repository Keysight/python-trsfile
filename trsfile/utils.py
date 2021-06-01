import struct


def encode_as_short(value):
    # TODO convert to little endian
    return struct.pack('>h', value)
