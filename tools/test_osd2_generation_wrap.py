"""Verify exact wrap fixtures and expected writes against production firmware.

All generated files stay in --output. No device or removable media access.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib


def record(value, generation):
    data = bytearray(32)
    data[:8] = b'CRT1' + bytes([1, 2, 0, 0])
    struct.pack_into('<IQ', data, 8, 0x232bb5b8, 0x200000)
    data[20] = value
    struct.pack_into('<I', data, 24, generation)
    struct.pack_into('<I', data, 28, zlib.crc32(data[:28]))
    return bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--firmware', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fw, out = args.firmware.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    fixtures = out / 'fixtures'
    profiles = {
        'initial': [('a', 19, 0xffffffff), ('b', 0, 0xfffffffe)],
        'after-first-save': [('a', 19, 0xffffffff), ('b', 18, 0)],
        'after-second-save': [('a', 19, 1), ('b', 18, 0)],
    }
    manifest = {}
    for profile, rows in profiles.items():
        manifest[profile] = {}
        for slot, value, generation in rows:
            name = 'crt/02-232bb5b8-0000000000200000.' + slot
            data = record(value, generation)
            path = fixtures / profile / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            manifest[profile][name] = dict(bytes=32, sha256=hashlib.sha256(data).hexdigest(),
                generation=generation, kind='USER', packed_value=value, crc_valid=True)
    exe = out / 'generation-wrap.exe'
    command = ['C:/msys64/ucrt64/bin/g++.exe', '-BC:/msys64/ucrt64/bin/', '-std=c++17',
               '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter', '-DUI16_SYSTEM_MENU',
               '-Itests/ui16', '-Iui', str(Path(__file__).with_name('osd2_generation_wrap_test.cpp')),
               'ui/ui16_crt.cpp', 'ui/ui16_osd.cpp', 'ui/ui16_crt_restore.cpp',
               'ui/ui16_crt_save.cpp', 'ui/ui16_crt_defaults.cpp', 'ui/ui16_rom_id.cpp',
               '-o', str(exe)]
    env = dict(os.environ)
    env['PATH'] = 'C:/msys64/ucrt64/bin;C:/msys64/usr/bin;' + env['PATH']
    subprocess.run(command, cwd=fw, env=env, check=True)
    run = subprocess.run([str(exe), str(fixtures)], cwd=fw, env=env, check=True,
                         capture_output=True, text=True)
    result = dict(passed=True, profiles=manifest, stdout=run.stdout,
        production_source_sha256={p: hashlib.sha256((fw / p).read_bytes()).hexdigest()
                                  for p in command if p.startswith('ui/')}, compiler_command=command)
    (out / 'pc-result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(run.stdout, end='')


if __name__ == '__main__':
    main()
