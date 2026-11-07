"""Render actual before/after C++ OSD frames with the existing FPGA font; no ROM/device access."""
from pathlib import Path
import hashlib,json,os,re,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];FW=ROOT/'firmware-bl616';OUT=ROOT/'verification/osd2-compact-20261107'
OUT.mkdir(parents=True,exist_ok=True);BUILD=FW/'build-ui16-host/osd2-compact-preview';BUILD.mkdir(parents=True,exist_ok=True)
BASELINE='8f05446158d005eae095839aa2f494021adb700d'
source=BUILD/'preview.cpp'
source.write_text(r'''
#include "ui16_crt.h"
#include "ui16_osd.h"
#include "menu_manager.h"
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <fstream>
#include <memory>
static std::uint32_t config=0;
void enter_critical(){}void leave_critical(){}
std::uint32_t get_core_config(){return config;}void set_core_config(std::uint32_t v){config=v;}
std::uint64_t bflb_mtimer_get_time_ms(){return 0;}
void fpga_tx_header(int,int){}
void overlay_clear(){ui16_osd_capture_clear();}
void overlay_cursor(int x,int y){ui16_osd_capture_cursor(x,y);}
void overlay_printf(const char *format,...){char s[256];va_list args;va_start(args,format);std::vsnprintf(s,sizeof(s),format,args);va_end(args);ui16_osd_capture_text(s);}
bool save(const Ui16RomIdentity &,const Ui16CrtSettings &,bool){return true;}
static void dump(Menu &menu,const char *path){
    ui16_osd_capture_begin();menu.render();ui16_osd_capture_end();int top=0,width=menu.osd_width();
    const auto f=ui16_osd_layout(ui16_osd_canvas(),menu.get_options(),0,top,width,Ui16OsdPosition::TopRight,true,"CRT SETTINGS"
#ifndef OSD_BEFORE
        ,menu.osd_style()
#endif
    );
    std::ofstream out(path);assert(out);out<<"{\"x\":"<<f.x<<",\"y\":"<<f.y<<",\"width\":"<<f.width<<",\"height\":"<<f.height<<",\"cells\":[";
    for(unsigned y=0;y<28;++y){if(y)out<<",";out<<"\"";for(unsigned x=0;x<32;++x){char c=f.cells[y*32+x];if(c=='\\'||c=='\"')out<<'\\';out<<c;}out<<"\"";}out<<"]}\n";
}
int main(int argc,char **argv){
    assert(argc>=2);Ui16RomIdentity id{true,Ui16RomVolume::Sd,2,0x232bb5b8,2097152};
    Ui16CrtRestore user{Ui16CrtReadState::User,{true,{true,1,3}}};
    ui16_crt_snes_session({},id,user,save,{});std::unique_ptr<Menu> menu(ui16_create_crt_menu(true,true));
    ui16_crt_accept_status(config);menu->on_tick(0);dump(*menu,argv[1]);
#ifndef OSD_BEFORE
    assert(argc==3&&menu->on_info());dump(*menu,argv[2]);
#endif
}
''',encoding='utf-8',newline='\n')
old=BUILD/'before';old.mkdir(exist_ok=True)
for name in ['ui16_crt.cpp','ui16_crt.h','ui16_osd.cpp','ui16_osd.h','menu_manager.h']:
    (old/name).write_bytes(subprocess.check_output(['git','-C',str(FW),'show',BASELINE+':ui/'+name]))
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;C:/msys64/usr/bin;'+env['PATH']
compiler='C:/msys64/ucrt64/bin/g++.exe'
for before in [True,False]:
    directory=old if before else FW/'ui';exe=BUILD/('before.exe' if before else 'after.exe')
    command=[compiler,'-BC:/msys64/ucrt64/bin/','-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-DUI16_SYSTEM_MENU',
             '-I'+str(directory),'-I'+str(FW/'tests/ui16'),'-I'+str(FW/'ui'),str(source),str(directory/'ui16_crt.cpp'),str(directory/'ui16_osd.cpp'),'-o',str(exe)]
    if before:command.append('-DOSD_BEFORE')
    with (OUT/('preview-before.log' if before else 'preview-after.log')).open('wb') as log:
        subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        args=[str(exe),str(OUT/('before-frame.json' if before else 'compact-frame.json'))]
        if not before:args.append(str(OUT/'info-frame.json'))
        subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
frames={name:json.loads((OUT/(name+'-frame.json')).read_text()) for name in ['before','compact','info']}
assert (frames['before']['width'],frames['before']['height'])==(26,17)
assert (frames['compact']['width'],frames['compact']['height'])==(16,10)
assert (frames['info']['width'],frames['info']['height'])==(24,17)
font_source=ROOT/'snestang/src/font.vh'
font=[int(x,16) for x in re.findall(r"8'h([0-9a-fA-F]{2})",font_source.read_text())];assert len(font)==128*8
font_label=ImageFont.truetype('D:/Users/foobaris/AppData/Local/Microsoft/Windows/Fonts/NotoSansCJKjp-Regular.otf',23)
def render(frame,name):
    bg=Image.new('RGB',(1280,720),(25,27,34));draw=ImageDraw.Draw(bg)
    for y in range(0,720,60):
        for x in range(160,1120,60):
            draw.rectangle((x,y,x+59,y+59),fill=(45+((x//60)%4)*14,53+((y//60)%4)*12,69+((x//60+y//60)%3)*12))
    layer=Image.new('RGBA',(256,224),(0,0,0,0));pixels=layer.load()
    for row in range(frame['y'],frame['y']+frame['height']):
        for col in range(frame['x'],frame['x']+frame['width']):
            character=ord(frame['cells'][row][col]);assert character<128
            for gy in range(8):
                for gx in range(8):pixels[col*8+gx,row*8+gy]=(255,255,132,255) if font[character*8+gy]&(1<<gx) else (0,0,0,255)
    scaled=layer.resize((960,720),Image.Resampling.NEAREST);bg.paste(scaled,(160,0),scaled)
    bg.save(OUT/(name+'.png'));return bg
images={name:render(frame,name) for name,frame in frames.items()}
comparison=Image.new('RGB',(1440,470),(244,245,247));draw=ImageDraw.Draw(comparison)
draw.text((20,8),'BEFORE 26 x 17 cells',font=font_label,fill=(20,24,32));draw.text((740,8),'COMPACT 16 x 10 cells',font=font_label,fill=(20,24,32))
for index,name in enumerate(['before','compact']):comparison.paste(images[name].resize((720,405),Image.Resampling.NEAREST),(index*720,44))
comparison.save(OUT/'comparison.png')
report=dict(baseline_firmware_commit=BASELINE,actual_production_Cpp_frames=True,existing_FPGA_font_sha256=hashlib.sha256(font_source.read_bytes()).hexdigest(),normal_before_cells=[26,17],normal_after_cells=[16,10],optional_info_cells=[24,17],normal_window_area_reduction_percent=round((1-160/442)*100,2),background='Synthetic; not a hardware screenshot or ROM image',hardware_verified=False)
(OUT/'preview.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
