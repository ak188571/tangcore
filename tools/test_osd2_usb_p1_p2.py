"""Compile and run the production UI16 menu tests against a firmware checkout."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--firmware', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cxx', default='g++')
    parser.add_argument('--cxxflag', action='append', default=[])
    args = parser.parse_args()
    firmware = args.firmware.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sources = [
        'ui/ui16_crt.cpp', 'ui/ui16_osd.cpp', 'ui/ui16_osd_menu.cpp',
        'ui/ui16_navigation.cpp', 'ui/menu_manager.cpp',
    ]
    probes = [
        ('firmware_crt_test', firmware / 'tests/ui16/crt_test.cpp'),
        ('p1_p2_menu_test', Path(__file__).with_name('osd2_usb_p1_p2_test.cpp').resolve()),
    ]
    result = {}
    for name, test in probes:
        executable = output / f'{name}.exe'
        command = [args.cxx, *args.cxxflag, '-std=c++17', '-DUI16_SYSTEM_MENU',
                   '-Itests/ui16', '-Iui', '-Iutils', str(test), *sources, '-o', str(executable)]
        subprocess.run(command, cwd=firmware, check=True)
        run = subprocess.run([str(executable)], check=True, capture_output=True, text=True)
        print(run.stdout, end='')
        result[name] = {'passed': True, 'stdout': run.stdout}
    result['production_source_sha256'] = {
        source: hashlib.sha256((firmware / source).read_bytes()).hexdigest() for source in sources
    }
    (output / 'pc-result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
