"""Verify committed firmware inputs, actual SDH wrapper linkage and SDK ownership evidence."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1];FW=ROOT/'firmware-bl616';OUT=ROOT/'verification/osd2-load-info-20261107'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
build=load(OUT/'firmware-build.json');assert build['build_inputs_unchanged']
assert not git(FW,'status','--porcelain').strip()
assert git(FW,'rev-parse','HEAD').decode().strip()==build['source_commit']
for name,digest in build['production_sha256'].items():
    assert sha(FW/name)==digest,name
    assert (FW/name).read_bytes().replace(b'\r\n',b'\n')==git(FW,'show','HEAD:'+name).replace(b'\r\n',b'\n'),name
assert len(load(OUT/'tests.json'))==16 and all(x['exit_code']==0 for x in load(OUT/'tests.json'))
sdk=Path(re.search(r'bouffalo_sdk_DIR:PATH=(.+)',(FW/'build-snes-crt-stage5-load-info/CMakeCache.txt').read_text()).group(1)).parent
paths=['bsp/common/sdcard/sdh_sdcard.c','bsp/common/sdcard/sdh_sdcard.h','drivers/soc/bl616/std/src/bl616_sdh.c',
       'components/fs/fatfs/port/fatfs_sdh_sdcard.c','components/fs/fatfs/port/fatfs_usbh.c','components/fs/fatfs/ffconf.h']
sdk_hashes={name:sha(sdk/name) for name in paths}
toolchain=Path('D:/Users/foobaris/Documents/Gowin/tangcore/xuantie-gcc-riscv-v2.6.1-windows-x86_64/bin')
elf=FW/'build-snes-crt-stage5-load-info/build_out/tangcore_bl616.elf'
disassembly={}
for function,target in [('MMC_disk_read','__wrap_SDH_ReadMultiBlocks'),('MMC_disk_write','__wrap_SDH_WriteMultiBlocks')]:
    text=subprocess.check_output([str(toolchain/'riscv64-unknown-elf-objdump.exe'),'-d','--disassemble='+function,str(elf)],text=True)
    assert '<'+target+'>' in text,function
    disassembly[function]=text
    (OUT/(function+'.disassembly.txt')).write_text(text,encoding='utf-8')
assert '#define FF_FS_REENTRANT 0' in (FW/'fatfs_conf_user.h').read_text()
assert '#define FF_FS_LOCK 0' in (FW/'fatfs_conf_user.h').read_text()
sn=load(ROOT/'verification/snes-crt-stage3b-20261106/final-source.json')['source_commits']
for name in ['snestang','nestang','monitor']:
    assert git(ROOT/name,'rev-parse','HEAD').decode().strip()==sn[name]
    assert not git(ROOT/name,'status','--porcelain').strip()
report=dict(source_commit=build['source_commit'],branch=build['branch'],production_files_checked=len(build['production_sha256']),
    production_inputs_match_commit_and_build=True,firmware_bytes=build['bytes'],firmware_sha256=build['sha256'],
    retained_snes_commit=sn['snestang'],retained_snes_image_sha256='bcc879e4f6da1194b8fa43edb487f71ac13c8b6037086558a42b6fa80b0dc429',
    nes_monitor_and_snes_sources_unchanged=True,sdk_source_hashes=sdk_hashes,actual_fatfs_calls_wrappers=True,
    fatfs_reentrant=False,fatfs_lock=0,sd_fault_policy='Only a SNES SD scope changes error handling: mask transfer interrupts, wait for controller reset, latch SD I/O off until power cycle. Other scopes retain SDK return values.',
    fault_tests='Host substitutes verify call order; physical SD faults and USB-storage DMA are not claimed as tested.',
    system2_raw_copier512_crc_reference=dict(plain='ee1ebc69',copier512='8541f1dc',reference='Python zlib'),hardware_status='pending')
(OUT/'final-source.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='sdk_source_hashes'},indent=2))
