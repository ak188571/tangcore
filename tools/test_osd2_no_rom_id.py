"""Exercise the production launch adapter, loader, card guard and OSD2 on a PC."""

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def compiler_path(path):
    """MSYS2 GCC does not accept Windows' extended-length path prefix."""
    name = str(path)
    if not name.startswith('\\\\?\\'):
        return name
    short = ctypes.create_unicode_buffer(32768)
    size = ctypes.windll.kernel32.GetShortPathNameW(name, short, len(short))
    if 0 < size < len(short):
        name = short.value
    if name.startswith('\\\\?\\UNC\\'):
        name = '\\\\' + name[8:]
    elif name.startswith('\\\\?\\'):
        name = name[4:]
    if len(name) >= 260:
        raise ValueError('Use a shorter path for the GCC build inputs or output directory')
    return name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--firmware', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--diagnostic', action='store_true')
    parser.add_argument('--compiler-bin', type=Path, default=Path('C:/msys64/ucrt64/bin'))
    args = parser.parse_args()
    firmware, out = args.firmware.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    main_file = (firmware / 'main.cpp').read_text(encoding='utf-8')
    match = re.search(r'^static bool ui16_hw_load_rom\(int id,const char \*path,void \*\)\n\{.*?^\}',
                      main_file, re.MULTILINE | re.DOTALL)
    if not match:
        raise RuntimeError('Could not extract the production launch adapter')
    adapter = out / 'load_adapter.inc'
    adapter.write_text(match.group(0) + '\n', encoding='utf-8')

    env = dict(os.environ)
    bin_dir = args.compiler_bin.resolve()
    env['PATH'] = str(bin_dir) + os.pathsep + env['PATH']
    compiler = [str(bin_dir / 'g++.exe'), '-B' + bin_dir.as_posix() + '/', '-std=c++17',
                '-DUI16_SYSTEM_MENU', '-DTC_ROM_UART', '-DBL616', '-Itests/ui16', '-Itests/storage',
                '-Iui', '-Icore', '-Iutils', '-Iusb', '-I', compiler_path(out)]
    if args.diagnostic:
        # The existing host-only FatFs shim omits the SDK enum's value 2.
        compiler += ['-DTC_DIAG_ROM_ID_CLOSE_FAILURE', '-DFR_INT_ERR=2']
    executable = out / 'no-rom-id-test.exe'
    sources = ['core/snes.cpp', 'ui/ui16_rom_id.cpp', 'ui/ui16_crt_restore.cpp',
               'ui/ui16_crt_defaults.cpp', 'ui/ui16_crt.cpp', 'ui/ui16_osd.cpp', 'utils/tc_snes_sd_guard.cpp']
    subprocess.run([*compiler, '-include', 'tests/ui16/snes_loader_platform.h',
                    compiler_path(Path(__file__).with_name('osd2_no_rom_id_test.cpp').resolve()), *sources,
                    '-o', compiler_path(out) + os.sep + executable.name], cwd=firmware, env=env, check=True)
    cases = ['diagnostic'] if args.diagnostic else ['nominal', 'id-close-error', 'sd-timeout', 'rom-load-fails']
    result = {}
    for case in cases:
        run = subprocess.run([compiler_path(executable), case], env=env, check=True,
                             stdout=subprocess.PIPE, text=True)
        result[case] = {'passed': True, 'stdout': run.stdout}
        print(run.stdout, end='')
    (out / 'result.json').write_text(json.dumps(dict(cases=result,
        production_source_sha256={p: hashlib.sha256((firmware / p).read_bytes()).hexdigest()
                                  for p in ['main.cpp', *sources]}), indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
