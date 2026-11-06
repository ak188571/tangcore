"""Record S3b RTL regressions and compatibility of the unchanged UI firmware."""
from pathlib import Path
import json,os,subprocess,time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'verification/snes-crt-stage3b-20261106'
env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
env['PATH']='C:/msys64/ucrt64/bin;C:/msys64/usr/bin;'+env['PATH']
bash='C:/msys64/usr/bin/bash.exe'
commands=[
    ('host-crt',[bash,'tools/ui16/test_crt.sh'],ROOT/'firmware-bl616'),
    ('snes-scan-rtl',[bash,'tests/crt/test_stage3b.sh'],ROOT/'snestang'),
    ('snes-s3a-compatibility',[bash,'tests/crt/test_stage3a.sh'],ROOT/'snestang'),
    ('snes-s1-compatibility',[bash,'tests/crt/test_stage1.sh'],ROOT/'snestang'),
    ('snes-restart',[bash,'tools/test_osd1_restart.sh','snes'],ROOT),
]
OUT.mkdir(parents=True,exist_ok=True)
results=[]
for name,command,cwd in commands:
    start=time.monotonic()
    with (OUT/(name+'.log')).open('wb') as log:
        p=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    results.append(dict(name=name,command=command,exit_code=p.returncode,seconds=round(time.monotonic()-start,2)))
    (OUT/'tests.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(name,p.returncode,flush=True)
    if p.returncode:
        print((OUT/(name+'.log')).read_text(errors='replace')[-6000:])
        raise SystemExit(p.returncode)
