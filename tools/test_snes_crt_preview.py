"""Exercise the unchanged S3a UI with both SNES effect capabilities, without editing firmware sources."""
from pathlib import Path
import json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
FW=ROOT/'firmware-bl616';OUT=ROOT/'verification/snes-crt-stage3b-20261106'
build=FW/'build-ui16-host';build.mkdir(exist_ok=True)
source=(FW/'tests/ui16/crt_test.cpp').read_text(encoding='utf-8')
marker='    assert(preview->on_close()&&config==preserved&&saves==saves_before_preview);\n'
assert source.count(marker)==1
extra='''
    // S3b advertises both effects but still owns no storage actions.
    for(unsigned value=0;value<32;value++){
        ui16_crt_preview_session();preview.reset(ui16_create_crt_menu(true,true));
        assert((preview->get_options()==std::vector<int>{3,4,5}));
        if(value&1)assert(preview->on_adjust(0,1));
        for(unsigned n=0;n<((value>>1)&3);n++)assert(preview->on_adjust(1,1));
        for(unsigned n=0;n<((value>>3)&3);n++)assert(preview->on_adjust(2,1));
        assert(config==(preserved|(value<<16)));
        assert(!preview->on_choose(3)&&!preview->on_choose(4)&&saves==saves_before_preview);
        ui16_crt_accept_status(config);now+=300;assert(preview->on_tick(now));
        ui16_osd_capture_begin();preview->render();ui16_osd_capture_end();
        const auto &frame=ui16_osd_canvas().cells;
        assert(std::string(frame.data(),32).find("SNES CRT PREVIEW")!=std::string::npos);
        assert(std::string(frame.data()+5*32,32).find("NOT YET")==std::string::npos);
        for(int row:{1,6,8,11})assert(std::string(frame.data()+row*32,32).find("UNAVAILABLE")!=std::string::npos);
        assert(std::string(frame.data()+7*32,32).find("FRAME ACK")!=std::string::npos);
        assert(preview->on_close()&&config==preserved&&saves==saves_before_preview);
    }
    std::puts("SNES S3b unchanged UI PASS: 32 settings, both advertised effects, scan selectable, SAVE/RESET unavailable, frame ACK and cancel to OFF");
'''
(build/'crt_snes_s3b_test.cpp').write_text(source.replace(marker,marker+extra),encoding='utf-8')
script=(FW/'tools/ui16/test_crt.sh').read_text(encoding='utf-8')
script=script.replace('cd "$(dirname "$0")/../.."','cd -- "'+FW.as_posix()+'"')
script=script.replace('tests/ui16/crt_test.cpp','build-ui16-host/crt_snes_s3b_test.cpp')
script=script.replace('-o build-ui16-host/crt_test','-o build-ui16-host/crt_snes_s3b_test')
script=script.replace('./build-ui16-host/crt_test','./build-ui16-host/crt_snes_s3b_test')
path=build/'test_crt_snes_s3b.sh';path.write_text(script,encoding='utf-8')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;C:/msys64/usr/bin;'+env['PATH']
command=['C:/msys64/usr/bin/bash.exe',path.as_posix()]
start=time.monotonic();OUT.mkdir(parents=True,exist_ok=True)
with (OUT/'host-snes-preview.log').open('wb') as log:
    result=subprocess.run(command,cwd=FW,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
(OUT/'ui-preview-tests.json').write_text(json.dumps(dict(exit_code=result.returncode,command=command,
    seconds=round(time.monotonic()-start,2),firmware_source_modified=False,settings_checked=32),indent=2)+'\n')
print((OUT/'host-snes-preview.log').read_text(errors='replace'))
raise SystemExit(result.returncode)
