"""Check source ownership, committed build inputs and resource deltas after S3b build."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];SNES=ROOT/'snestang'
OUT=ROOT/'verification/snes-crt-stage3b-20261106'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(data):return data.replace(b'\r\n',b'\n')
build=load(OUT/'fpga-build.json')
assert build['exit_code']==0 and build['tracked_files_unchanged'] and not any(build['timing'].values())
assert git(SNES,'rev-parse','HEAD').decode().strip()==build['source_head']
assert not git(SNES,'status','--porcelain').strip()
count=0
for name,digest in build['tracked_file_sha256'].items():
    assert sha(SNES/name)==digest,name
    listed=git(SNES,'ls-files','--',name).strip()
    if listed:
        assert normalized(git(SNES,'show','HEAD:'+name))==normalized((SNES/name).read_bytes()),name
        count+=1
heads={}
for name in ['firmware-bl616','snestang','nestang','monitor']:
    repo=ROOT/name
    assert git(repo,'branch','--show-current').decode().strip()=='tangcore-integrated'
    assert not git(repo,'status','--porcelain').strip(),name
    heads[name]=git(repo,'rev-parse','HEAD').decode().strip()
assert heads['firmware-bl616']=='3560c1b429a36fc35a02c840f8dcfeb7f8b4f7e5'
assert (SNES/'src/iosys/crt_filter.sv').read_bytes()==(ROOT/'nestang/src/iosys/crt_filter.sv').read_bytes()
baseline='ac7fe8f48ff1cf38af735198ae824bf0654f5ab5'
paths=git(SNES,'diff','--name-only',baseline,'HEAD').decode().splitlines()
assert set(paths)=={'src/snes2hdmi.v','src/iosys/iosys_bl616.v','src/snestang_console138k_usb_top.v',
    'tests/crt/tb_snes_crt_uart.sv','tests/crt/tb_snes_crt_scan_video.sv','tests/crt/test_stage3b.sh'}
top=git(SNES,'show',baseline+':src/snestang_console138k_usb_top.v')
assert normalized(top.replace(b'.CRT_BLUR(1)) s2h(',b'.CRT_BLUR(1), .CRT_SCAN(1)) s2h(').replace(
    b'.SUPPORT_BLUR(1)) iosys (',b'.SUPPORT_BLUR(1), .SUPPORT_SCAN(1)) iosys ('))==normalized((SNES/'src/snestang_console138k_usb_top.v').read_bytes())
old=git(SNES,'show',baseline+':src/snes2hdmi.v').decode()
new=(SNES/'src/snes2hdmi.v').read_text()
assert normalized(old.split('    // address calculation')[1].split('    // Frame-applied settings.')[0].encode())==normalized(new.split('    // address calculation')[1].split('    // Frame-applied settings.')[0].encode())
assert normalized(old.split('    // Data input')[1].split('    // Video')[0].encode())==normalized(new.split('    // Data input')[1].split('    // Video')[0].encode())
previous=load(ROOT/'verification/snes-crt-stage3a-20261106/final-source.json')
hexes={name:sha(SNES/name) for name in previous['root_hex_after_build_sha256']}
assert hexes==previous['root_hex_after_build_sha256']
resources=load(ROOT/'verification/snes-crt-stage3a-20261106/fpga-build.json')['synthesis_resources']
delta={key:build['synthesis_resources'][key]-value for key,value in resources.items()}
report=dict(source_commits=heads,build_inputs_unchanged_after_commit=True,
    committed_inputs_equal_after_eol_normalization=count,changed_snes_paths=paths,
    top_only_enables_scan_parameter=True,source_sampling_audio_and_scaler_counter_blocks_unchanged=True,
    filter_byte_identical_to_NES=True,root_hex_after_build_sha256=hexes,root_hex_equal_to_S3a=True,
    resource_delta_from_S3a=delta,shared_firmware_source_unchanged=True)
(OUT/'final-source.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('root_hex_after_build_sha256','changed_snes_paths')},indent=2))
