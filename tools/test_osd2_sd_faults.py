"""Run SNES CRT fault tests on a PC, with SDK FatFs backed by synthetic sectors."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


CASE = re.compile(
    r'(direct|buffered|torn) (\d+) (\w+) partial_bytes=(\d+) '
    r'selected=([ab]) generation=([23]) state=(USER|RECOVERED)'
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--firmware', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compiler-bin', type=Path, help='directory containing gcc and g++')
    args = parser.parse_args()
    firmware = args.firmware.resolve()
    fatfs = args.sdk.resolve() / 'components/fs/fatfs'
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    suffix = '.exe' if os.name == 'nt' else ''
    cc, cxx = 'gcc' + suffix, 'g++' + suffix
    compiler_flags = []
    if args.compiler_bin is not None:
        bin_dir = args.compiler_bin.resolve()
        cc, cxx = str(bin_dir / cc), str(bin_dir / cxx)
        compiler_flags = ['-B' + bin_dir.as_posix() + '/']
        env['PATH'] = str(bin_dir) + os.pathsep + env['PATH']

    def build(driver, flags, inputs, target):
        subprocess.run([driver, *compiler_flags, *flags, *map(str, inputs), '-o', str(target)],
                       cwd=firmware, env=env, check=True)

    def run(executable, *params):
        result = subprocess.run([str(executable), *params], env=env, check=True,
                                capture_output=True, text=True)
        print(result.stdout, end='')
        return result.stdout

    restore_sources = ['ui/ui16_crt_restore.cpp', 'ui/ui16_rom_id.cpp']
    save_sources = ['ui/ui16_crt_save.cpp', *restore_sources]
    flags = ['-std=c++17', '-DUI16_SYSTEM_MENU']
    test_flags = flags + ['-DTEST_CRT_SYSTEM=2', '-Itests/ui16', '-Iui']
    restore_exe = output / ('crt-restore' + suffix)
    save_exe = output / ('crt-save' + suffix)
    build(cxx, test_flags, ['tests/ui16/crt_restore_test.cpp', *restore_sources], restore_exe)
    build(cxx, test_flags, ['tests/ui16/crt_save_test.cpp', *save_sources], save_exe)
    restore_log, save_log = run(restore_exe), run(save_exe)
    guard_exe = output / ('sd-guard' + suffix)
    build(cxx, flags + ['-DBL616', '-Itests/storage', '-Iutils'],
          ['tests/storage/snes_sd_guard_test.cpp', 'utils/tc_snes_sd_guard.cpp'], guard_exe)
    guard_logs = {case: run(guard_exe, case) for case in ('legacy', 'success', 'read-timeout', 'write-error')}

    objects = []
    for source in ('ff', 'ffunicode'):
        obj = output / f'{source}.o'
        build(cc, ['-std=c11', '-fexceptions', '-include', 'stdint.h', '-I.','-c'],
              [fatfs / f'{source}.c'], obj)
        objects.append(obj)
    fatfs_exe = output / ('fatfs-interruption' + suffix)
    harness = Path(__file__).with_name('osd2_fatfs_interruption_test.cpp').resolve()
    build(cxx, flags + ['-include', 'stdint.h', '-I.', '-Iui', '-I', str(fatfs)],
          [harness, *save_sources, *objects], fatfs_exe)
    fatfs_log = run(fatfs_exe)
    rows = []
    for line in fatfs_log.splitlines():
        match = CASE.fullmatch(line)
        if match is not None:
            model, boundary, event, prefix, slot, generation, state = match.groups()
            rows.append(dict(model=model, boundary=int(boundary), event=event,
                             partial_bytes=int(prefix), selected_slot=slot,
                             selected_generation=int(generation), state=state))
    if len(rows) != 44 or len({(r['model'], r['boundary'], r['partial_bytes']) for r in rows}) != 44:
        raise RuntimeError('Unexpected number of reported FAT32 conditions')
    controls = sum(r['event'] == 'after_completed_save' for r in rows)
    read_refusal = 'refuses SAVE before any disk write' in fatfs_log
    write_recovery = 'disk write failure after two sector writes' in fatfs_log
    if controls != 2 or not (read_refusal and write_recovery):
        raise RuntimeError('Missing expected fault result')

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    result = dict(
        scope='PC-only; real SDK FatFs over synthetic sectors; no device access',
        hardware_trial_status='deferred', physical_power_loss_tested=False,
        compiler=subprocess.check_output([cxx, '--version'], env=env, text=True).splitlines()[0],
        firmware_source_sha256={path: sha(firmware / path) for path in [
            *save_sources, 'fatfs_conf_user.h', 'utils/tc_snes_sd_guard.cpp',
            'tests/ui16/crt_restore_test.cpp', 'tests/ui16/crt_save_test.cpp',
            'tests/storage/snes_sd_guard_test.cpp',
        ]},
        sdk_fatfs_source_sha256={path: sha(fatfs / path) for path in (
            'ff.c', 'ff.h', 'ffconf.h', 'ffunicode.c', 'diskio.h',
        )},
        host_restore=dict(passed=True, stdout=restore_log),
        host_save=dict(passed=True, stdout=save_log),
        host_sd_guard=dict(passed=True, stdout_by_case=guard_logs),
        fatfs=dict(passed=True, interruptions=len(rows) - controls, completed_controls=controls,
                   last_confirmed_record_and_neighbour_preserved=True,
                   read_error_refused_save_before_disk_write=read_refusal,
                   write_error_preserved_latest_confirmed_slot=write_recovery,
                   cases=rows),
    )
    (output / 'pc-result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
