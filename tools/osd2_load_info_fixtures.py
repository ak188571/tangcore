"""Pure, bounded SNES fixtures. No media access or device operations."""
import struct
import zlib

A = 'crt/02-232bb5b8-0000000000200000.a'
B = 'crt/02-232bb5b8-0000000000200000.b'
D = 'crt/defaults.tsv'
TARGETS = (A, B, D)

def record(kind, generation, value):
    data = bytearray(32)
    data[:8] = b'CRT1' + bytes([1, 2, kind, 0])
    struct.pack_into('<IQ', data, 8, 0x232bb5b8, 2097152)
    data[20] = value
    struct.pack_into('<I', data, 24, generation)
    return crc(data)

def crc(data):
    data = bytearray(data)
    struct.pack_into('<I', data, 28, zlib.crc32(data[:28]) & 0xffffffff)
    return bytes(data)

def profiles(a, b):
    # Only a known, freshly backed-up baseline may be used by the installer.
    assert a == record(1, 7, 0) and b == record(0, 6, 1), 'Actual records differ; preserve and inspect'
    bad_a = bytearray(a); bad_a[28] ^= 1
    bad_b = bytearray(b); bad_b[28] ^= 1
    future = bytearray(a); future[4] = 2
    return {
        'system': {A: a, B: bytes(bad_b), D: b'system\tcrt_v1\n*\t1:1:3\nsnes\t1:2:1\n'},
        'global': {A: bytes(bad_a), B: bytes(bad_b), D: b'system\tcrt_v1\n*\t1:1:3\n'},
        'errors': {A: crc(future), B: b, D: b'system\tcrt_v1\n*\t1:1:3\nsnes\t1:4:0\n'},
    }
