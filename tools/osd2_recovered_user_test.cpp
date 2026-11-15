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
#include <memory>
#include <string>

static std::string directory;
static std::string bytes;
static bool active=false;
static unsigned mutation_attempts=0;
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
extern "C" FRESULT f_open(FIL *f,const char *path,unsigned char mode){
    assert(f==&file&&!active);
    if(mode!=FA_READ){++mutation_attempts;return FR_DISK_ERR;}
    assert(std::string(path).find("sd:/")==0);
    std::ifstream in(directory+'/'+std::string(path+4),std::ios::binary);
    if(!in)return FR_NO_FILE;
    bytes.assign(std::istreambuf_iterator<char>(in),{});
    active=true;f->size=bytes.size();return FR_OK;
}
extern "C" FRESULT f_read(FIL *f,void *out,UINT wanted,UINT *count){
    assert(f==&file&&active&&out==buffer.data());
    *count=static_cast<UINT>(std::min<std::size_t>(wanted,bytes.size()));
    std::memcpy(out,bytes.data(),*count);return FR_OK;
}
extern "C" FRESULT f_close(FIL *f){assert(f==&file&&active);active=false;return FR_OK;}
extern "C" FRESULT f_write(FIL *,const void *,UINT,UINT *){++mutation_attempts;return FR_DISK_ERR;}
extern "C" FRESULT f_sync(FIL *){++mutation_attempts;return FR_DISK_ERR;}
extern "C" FRESULT f_mkdir(const char *){++mutation_attempts;return FR_DISK_ERR;}
static bool save(const Ui16RomIdentity &id,const Ui16CrtSettings &value,bool reset){
    return ui16_save_crt_override(id,value,file,buffer.data(),buffer.size(),reset);
}
static void check(Menu &menu,int row,const std::string &expected){
    ui16_osd_capture_begin();menu.render();ui16_osd_capture_end();
    assert(std::string(ui16_osd_canvas().cells.data()+row*32,32).find(expected)!=std::string::npos);
}
int main(int argc,char **argv){
    assert(argc==2);directory=argv[1];
    const Ui16RomIdentity id{true,Ui16RomVolume::Sd,2,0x232bb5b8,2097152};
    const auto restored=ui16_read_crt_override(id,file,buffer.data(),buffer.size());
    assert(restored.state==Ui16CrtReadState::Recovered);
    assert(restored.override_value.present&&restored.selected_slot==1&&restored.generation==8);
    const Ui16CrtSettings expected{true,1,2};
    assert(restored.override_value.settings==expected);
    const auto defaults=ui16_read_crt_defaults(2,"sd:snes/game.sfc",file,buffer.data(),buffer.size());
    assert(defaults.state==Ui16CrtDefaultsState::Missing);
    ui16_crt_snes_session({},id,restored,save,defaults);assert(config==expected.merge(0));
    std::unique_ptr<Menu> menu(ui16_create_crt_menu(true,true));
    check(*menu,0,"CRT   ON");check(*menu,1,"BLUR WEAK");check(*menu,2,"SCAN STD");check(*menu,3,"SAVE OK");
    assert(menu->on_info());ui16_crt_accept_status(config);menu->on_tick(100);
    check(*menu,5,"SAVE: SAVED");check(*menu,6,"LOADED FROM: USER");
    check(*menu,7,"SAVE READ: RECOVERED");check(*menu,8,"APPLY: FRAME ACK");
    check(*menu,9,"ROM ID: 232bb5b8");check(*menu,10,"DEFAULTS: MISSING");
    assert(menu->on_adjust(0,1));check(*menu,0,"CRT   OFF");check(*menu,3,"SAVE *");check(*menu,5,"SAVE: UNSAVED");
    check(*menu,6,"LOADED FROM: USER");check(*menu,7,"SAVE READ: RECOVERED");
    ui16_crt_accept_status(config);menu->on_tick(200);check(*menu,8,"APPLY: FRAME ACK");
    assert(menu->on_close()&&config==expected.merge(0));
    menu.reset(ui16_create_crt_menu(true,true));assert(menu->on_info());
    ui16_crt_accept_status(config);menu->on_tick(300);
    check(*menu,0,"CRT   ON");check(*menu,1,"BLUR WEAK");check(*menu,2,"SCAN STD");
    check(*menu,3,"SAVE OK");check(*menu,5,"SAVE: SAVED");check(*menu,6,"LOADED FROM: USER");
    check(*menu,7,"SAVE READ: RECOVERED");check(*menu,8,"APPLY: FRAME ACK");
    assert(!active&&mutation_attempts==0);
    std::puts("PASS: exact fixtures select valid USER slot b generation 8 as RECOVERED despite CRC-bad slot a generation 9; ON/WEAK/STD overrides builtin OFF; SAVED, preview/cancel/reopen retain USER/RECOVERED; zero mkdir/write-open/write/sync attempts. FRAME ACK is simulated on PC.");
}
