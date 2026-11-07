"""Exercise exact deployment fixture bytes through production readers and UI."""
from pathlib import Path
import os, subprocess
from osd2_load_info_fixtures import profiles, record
ROOT=Path(__file__).resolve().parents[1];FW=ROOT/'firmware-bl616'
BUILD=FW/'build-ui16-host/load-info-profiles';BUILD.mkdir(parents=True,exist_ok=True)
for profile,files in profiles(record(1,7,0),record(0,6,1)).items():
    for name,data in files.items():
        dest=BUILD/profile/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;C:/msys64/usr/bin;'+env['PATH']
exe=BUILD/'profiles.exe'
cmd=['C:/msys64/ucrt64/bin/g++.exe','-BC:/msys64/ucrt64/bin/','-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-DUI16_SYSTEM_MENU','-Itests/ui16','-Iui',
     'tests/ui16/crt_load_profiles_test.cpp','ui/ui16_crt.cpp','ui/ui16_osd.cpp','ui/ui16_crt_restore.cpp','ui/ui16_crt_save.cpp','ui/ui16_crt_defaults.cpp','ui/ui16_rom_id.cpp','-o',str(exe)]
subprocess.run(cmd,cwd=FW,env=env,check=True)
subprocess.run([str(exe),str(BUILD)],cwd=FW,env=env,check=True)
