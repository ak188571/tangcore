"""Build SNES stage4b shared firmware artifacts without writing to the device or storage media."""
from pathlib import Path
import os,sys,json,subprocess,time,hashlib,ctypes
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent
OUT=ROOT/'verification/snes-crt-stage4b-20261106';OUT.mkdir(parents=True,exist_ok=True)
target=sys.argv[1]
source_repo=ROOT/'firmware-bl616'
production_names=[name for name in subprocess.check_output(['git','-C',str(source_repo),'ls-files'],text=True).splitlines()
    if not name.startswith(('tests/','tools/')) and Path(name).suffix in ('.cpp','.h','.txt')]
production_before={name:hashlib.sha256((source_repo/name).read_bytes()).hexdigest() for name in production_names}
env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',MSYSTEM='UCRT64')
env['PATH']=';'.join(['C:/msys64/ucrt64/bin','C:/msys64/usr/bin',env['PATH']])
steps=[]
def run(name,cmd,cwd):
    start=time.monotonic()
    with (OUT/(name+'.log')).open('wb') as log:
        p=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
    steps.append(dict(name=name,command=cmd,exit_code=p.returncode,seconds=round(time.monotonic()-start,2)))
    (OUT/(target+'-build.json')).write_text(json.dumps(dict(steps=steps,device_programming=False),indent=2)+'\n')
    print(name,p.returncode,flush=True)
    if p.returncode:print((OUT/(name+'.log')).read_text(errors='replace')[-5000:]);sys.exit(p.returncode)
if target=='firmware':
    repo=ROOT/'firmware-bl616';build=repo/'build-snes-crt-stage4b'
    previous=json.loads((BASE/'console138k-install-kit-20261101/build_result.json').read_text())
    cmd=previous['steps'][0]['command'][:]
    buf=ctypes.create_unicode_buffer(4096)
    assert ctypes.windll.kernel32.GetShortPathNameW(str(repo),buf,4096)
    cmd[cmd.index('-S')+1]=buf.value.replace('\\','/')
    cmd[cmd.index('-B')+1]=str(build)
    env['BL_SDK_BASE']=Path(json.loads((BASE/'build-results-20261101/firmware_result.json').read_text())['sdk_path']).as_posix()
    env['PATH']=';'.join([str(Path(cmd[0]).parent),r'D:/Users/foobaris/Documents/Gowin/tangcore/xuantie-gcc-riscv-v2.6.1-windows-x86_64/bin',env['PATH']])
    run('firmware-configure',cmd,repo)
    run('firmware-compile',[cmd[0],'--build',str(build),'--parallel','8'],repo)
    run('firmware-combine',[cmd[0],'--build',str(build),'--target','combine'],repo)
    artifact=build/'build_out/tangcore_bl616.bin'
else:
    repo=ROOT/('nestang' if target=='nes' else 'snestang')
    run(target+'-fpga',['C:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe','build_console138k_usb.tcl','console138k','ds2'],repo)
    artifact=repo/'impl/pnr'/('nestang_console138k_ds2.bin' if target=='nes' else 'snestang_console138k_ds2.bin')
record=dict(steps=steps,device_programming=False,artifact=str(artifact),bytes=artifact.stat().st_size,sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
record.update(source_commit=subprocess.check_output(['git','-C',str(source_repo),'rev-parse','HEAD'],text=True).strip(),
    branch=subprocess.check_output(['git','-C',str(source_repo),'branch','--show-current'],text=True).strip(),
    production_sha256=production_before,build_inputs_unchanged=production_before=={name:hashlib.sha256((source_repo/name).read_bytes()).hexdigest() for name in production_names})
assert record['build_inputs_unchanged'] and record['branch']=='tangcore-integrated'
if target=='firmware':assert record['bytes']<=0x40000
(OUT/(target+'-build.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
