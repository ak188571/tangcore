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
static std::vector<std::string> write_targets;
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
        assert(mode==(FA_WRITE|FA_CREATE_ALWAYS)&&(path==prefix+".a"||path==prefix+".b"));
        write_targets.push_back(path);
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
static Bytes load(const std::string &path){
    std::ifstream in(path,std::ios::binary);assert(in);
    const Bytes data{std::istreambuf_iterator<char>(in),{}};assert(data.size()==32);return data;
}
static Ui16CrtRestore read(const Ui16RomIdentity &id){return ui16_read_crt_override(id,file,buffer.data(),buffer.size());}
int main(int argc,char **argv){
    assert(argc==2||argc==3);const std::string directory=argv[1];
    const Ui16RomIdentity id{true,Ui16RomVolume::Sd,2,0x232bb5b8,2097152};
    const std::string rel="/crt/02-232bb5b8-0000000000200000";
    if(argc==3){
        assert(std::string(argv[2])=="--verify-records");
        files[prefix+".a"]=load(directory+rel+".a");files[prefix+".b"]=load(directory+rel+".b");
        auto selected=read(id);
        assert(selected.state==Ui16CrtReadState::User&&selected.selected_slot==0&&selected.generation==1);
        assert(selected.override_value.present&&selected.override_value.settings==Ui16CrtSettings({true,1,2}));
        files.erase(prefix+".a");selected=read(id);
        assert(selected.state==Ui16CrtReadState::User&&selected.selected_slot==1&&selected.generation==0);
        assert(selected.override_value.present&&selected.override_value.settings==Ui16CrtSettings({false,1,2}));
        assert(writes==0&&syncs==0&&mkdirs==0&&write_opens==0);
        std::puts("PASS: actual final records select USER a generation 1 ON/WEAK/STD; remaining b independently parses as USER generation 0 OFF/WEAK/STD; no writes.");return 0;
    }
    files[prefix+".a"]=load(directory+"/initial"+rel+".a");
    files[prefix+".b"]=load(directory+"/initial"+rel+".b");
    const auto original_a=files[prefix+".a"];
    const auto expected_zero=load(directory+"/after-first-save"+rel+".b");
    const auto expected_one=load(directory+"/after-second-save"+rel+".a");
    const auto initial=read(id);
    assert(initial.state==Ui16CrtReadState::User&&initial.selected_slot==0&&initial.generation==0xffffffffu);
    const Ui16CrtSettings on{true,1,2},off{false,1,2};assert(initial.override_value.settings==on);
    const auto defaults=ui16_read_crt_defaults(2,"sd:snes/game.sfc",file,buffer.data(),buffer.size());
    assert(defaults.state==Ui16CrtDefaultsState::Missing);
    ui16_crt_snes_session({},id,initial,save,defaults);assert(config==on.merge(0));
    std::unique_ptr<Menu> menu(ui16_create_crt_menu(true,true));assert(menu->on_info());
    check(*menu,0,"CRT   ON");check(*menu,1,"BLUR WEAK");check(*menu,2,"SCAN STD");
    check(*menu,3,"SAVE OK");check(*menu,5,"SAVE: SAVED");check(*menu,6,"LOADED FROM: USER");check(*menu,7,"SAVE READ: USER");
    // First explicit edit and SAVE: FFFFFFFF -> 0 in the alternate slot b.
    assert(menu->on_adjust(0,1)&&config==off.merge(0));assert(!menu->on_choose(3));
    assert(writes==1&&syncs==1&&write_opens==1&&write_targets.back()==prefix+".b");
    assert(files[prefix+".a"]==original_a&&files[prefix+".b"]==expected_zero);
    auto selected=read(id);assert(selected.state==Ui16CrtReadState::User&&selected.selected_slot==1&&selected.generation==0);
    assert(selected.override_value.settings==off);
    check(*menu,3,"SAVE OK");check(*menu,5,"SAVE: SAVED");
    check(*menu,6,"LOADED FROM: USER");check(*menu,7,"SAVE READ: USER");
    // Second explicit edit forces production SAVE to re-read and select generation 0.
    assert(menu->on_adjust(0,1)&&config==on.merge(0));assert(!menu->on_choose(3));
    assert(writes==2&&syncs==2&&write_opens==2&&mkdirs==2&&write_targets.back()==prefix+".a");
    assert(files.size()==2&&files[prefix+".b"]==expected_zero&&files[prefix+".a"]==expected_one);
    selected=read(id);assert(selected.state==Ui16CrtReadState::User&&selected.selected_slot==0&&selected.generation==1);
    assert(selected.override_value.settings==on);
    check(*menu,3,"SAVE OK");check(*menu,5,"SAVE: SAVED");
    ui16_crt_accept_status(config);menu->on_tick(100);check(*menu,8,"APPLY: FRAME ACK");
    // Cancel subsequent unsaved OFF without creating another generation.
    assert(menu->on_adjust(0,1));assert(menu->on_close()&&config==on.merge(0));
    menu.reset(ui16_create_crt_menu(true,true));assert(menu->on_info());
    check(*menu,0,"CRT   ON");check(*menu,1,"BLUR WEAK");check(*menu,2,"SCAN STD");
    check(*menu,3,"SAVE OK");check(*menu,5,"SAVE: SAVED");check(*menu,6,"LOADED FROM: USER");check(*menu,7,"SAVE READ: USER");
    assert(writes==2&&files[prefix+".a"]==expected_one&&files[prefix+".b"]==expected_zero&&!active);
    std::puts("PASS: exact initial a FFFFFFFF / b FFFFFFFE; first SAVE writes b generation 0 and preserves a; generation 0 is selected over FFFFFFFF; second SAVE re-reads and writes a generation 1 preserving b; exact bytes, CRC, USER values, SAVED UI and cancel verified. FRAME ACK is simulated on PC.");
}
