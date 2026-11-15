#include "ui16_crt.h"
#include "ui16_crt_save.h"
#include "ui16_crt_defaults_reader.h"
#include "ui16_osd.h"
#include "menu_manager.h"
#include <cassert>
#include <array>
#include <algorithm>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <map>
#include <memory>
#include <string>
#include <vector>

using Bytes=std::vector<unsigned char>;
static std::map<std::string,Bytes> files;
static const std::string prefix="sd:/crt/02-232bb5b8-0000000000200000";
static std::string path;
static bool active=false,writing=false;
static unsigned writes=0,syncs=0,mkdirs=0,write_opens=0;
static FIL file;
alignas(64) static std::array<unsigned char,8192> buffer;
static std::uint32_t config=0;
void enter_critical(){} void leave_critical(){}
std::uint32_t get_core_config(){return config;}
void set_core_config(std::uint32_t v){config=v;}
std::uint64_t bflb_mtimer_get_time_ms(){return 0;}
void fpga_tx_header(int,int){}
void overlay_clear(){ui16_osd_capture_clear();}
void overlay_cursor(int x,int y){ui16_osd_capture_cursor(x,y);}
void overlay_printf(const char *format,...){
    char s[256];va_list args;va_start(args,format);std::vsnprintf(s,sizeof(s),format,args);va_end(args);ui16_osd_capture_text(s);
}
extern "C" FRESULT f_open(FIL *f,const char *name,unsigned char mode){
    assert(f==&file&&!active);path=name;writing=(mode&FA_WRITE)!=0;
    if(writing){
        assert(mode==(FA_WRITE|FA_CREATE_ALWAYS)&&path==prefix+".a");
        ++write_opens;files[path].clear();
    }else{
        assert(mode==FA_READ);
        if(!files.count(path))return FR_NO_FILE;
    }
    active=true;f->position=0;f->size=files[path].size();return FR_OK;
}
extern "C" FRESULT f_read(FIL *f,void *out,UINT wanted,UINT *count){
    assert(f==&file&&active&&!writing&&out==buffer.data());
    *count=static_cast<UINT>(std::min<std::size_t>(wanted,files[path].size()));
    if(*count)std::memcpy(out,files[path].data(),*count);
    return FR_OK;
}
extern "C" FRESULT f_close(FIL *f){assert(f==&file&&active);active=false;return FR_OK;}
extern "C" FRESULT f_write(FIL *f,const void *data,UINT wanted,UINT *count){
    assert(f==&file&&active&&writing&&data==buffer.data()&&wanted==32);
    ++writes;*count=wanted;const auto *bytes=static_cast<const unsigned char *>(data);
    files[path]=Bytes(bytes,bytes+wanted);return FR_OK;
}
extern "C" FRESULT f_sync(FIL *f){assert(f==&file&&active&&writing);++syncs;return FR_OK;}
extern "C" FRESULT f_mkdir(const char *name){assert(!active&&std::string(name)=="sd:/crt");++mkdirs;return FR_EXIST;}
static bool save(const Ui16RomIdentity &id,const Ui16CrtSettings &value,bool reset){
    return ui16_save_crt_override(id,value,file,buffer.data(),buffer.size(),reset);
}
static void check(Menu &menu,int row,const std::string &expected){
    ui16_osd_capture_begin();menu.render();ui16_osd_capture_end();
    assert(std::string(ui16_osd_canvas().cells.data()+row*32,32).find(expected)!=std::string::npos);
}
int main(int argc,char **argv){
    assert(argc==2||argc==3);
    const Ui16RomIdentity id{true,Ui16RomVolume::Sd,2,0x232bb5b8,2097152};
    std::ifstream in(argv[1],std::ios::binary);assert(in);
    const Bytes expected{std::istreambuf_iterator<char>(in),{}};assert(expected.size()==32);
    if(argc==3){
        assert(std::string(argv[2])=="--verify-record");files[prefix+".a"]=expected;
        const auto read=ui16_read_crt_override(id,file,buffer.data(),buffer.size());
        assert(read.state==Ui16CrtReadState::User&&read.generation==1&&read.selected_slot==0);
        assert(read.override_value.present&&read.override_value.settings==Ui16CrtSettings({true,0,0}));
        assert(writes==0&&write_opens==0&&mkdirs==0&&syncs==0);
        std::puts("PASS: observed first-save record parsed as USER, generation 1, slot a, ON/OFF/OFF; no writes.");return 0;
    }
    const auto initial=ui16_read_crt_override(id,file,buffer.data(),buffer.size());
    assert(initial.state==Ui16CrtReadState::Missing&&!initial.override_value.present&&initial.selected_slot==-1);
    const auto defaults=ui16_read_crt_defaults(2,"sd:snes/game.sfc",file,buffer.data(),buffer.size());
    assert(defaults.state==Ui16CrtDefaultsState::Missing);
    ui16_crt_snes_session({},id,initial,save,defaults);assert(config==0);
    std::unique_ptr<Menu> menu(ui16_create_crt_menu(true,true));assert(menu->on_info());
    check(*menu,5,"SAVE: RECOMMENDED");check(*menu,6,"LOADED FROM: BUILT-IN");check(*menu,7,"SAVE READ: MISSING");
    assert(files.empty()&&writes==0&&mkdirs==0);
    assert(menu->on_adjust(0,1));check(*menu,3,"SAVE *");assert(!menu->on_choose(3));
    check(*menu,3,"SAVE OK");check(*menu,5,"SAVE: SAVED");
    check(*menu,6,"LOADED FROM: BUILT-IN");check(*menu,7,"SAVE READ: MISSING");
    ui16_crt_accept_status(config);menu->on_tick(100);check(*menu,8,"APPLY: FRAME ACK");
    assert(writes==1&&syncs==1&&write_opens==1&&mkdirs==1&&files.size()==1&&files.at(prefix+".a")==expected);
    const auto reread=ui16_read_crt_override(id,file,buffer.data(),buffer.size());
    assert(reread.state==Ui16CrtReadState::User&&reread.generation==1&&reread.selected_slot==0);
    assert(reread.override_value.settings==Ui16CrtSettings({true,0,0}));
    // Cancel a subsequent unsaved OFF preview to the newly saved ON value.
    assert(menu->on_adjust(0,1));assert(config==0);assert(menu->on_close());
    assert(config==Ui16CrtSettings({true,0,0}).merge(0));
    menu.reset(ui16_create_crt_menu(true,true));assert(menu->on_info());
    check(*menu,0,"CRT   ON");check(*menu,1,"BLUR OFF");check(*menu,2,"SCAN OFF");
    check(*menu,3,"SAVE OK");check(*menu,5,"SAVE: SAVED");check(*menu,7,"SAVE READ: MISSING");
    assert(writes==1&&files.size()==1&&files.at(prefix+".a")==expected&&!active);
    // Reload is PC-only coverage; hardware requires one SNES launch.
    ui16_crt_snes_session({},id,reread,save,defaults);
    menu.reset(ui16_create_crt_menu(true,true));assert(menu->on_info());
    check(*menu,6,"LOADED FROM: USER");check(*menu,7,"SAVE READ: USER");
    std::puts("PASS: MISSING; first SAVE writes exact USER generation-1 slot a once; SAVED retains load snapshot MISSING; cancel/reopen returns to saved ON; production re-read accepts USER. FRAME ACK and reload are simulated on PC.");
}
