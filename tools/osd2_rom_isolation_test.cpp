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
static const std::string mario = "/crt/02-232bb5b8-0000000000200000";
static const std::string panel = "/crt/02-14d70786-0000000000100000";
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
        assert(mode==(FA_WRITE|FA_CREATE_ALWAYS)&&(path=="sd:"+mario+".b"||path=="sd:"+panel+".b"));
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
static Ui16CrtRestore expect_user(const Ui16RomIdentity &id, int slot,
                                   unsigned generation, const Ui16CrtSettings &settings) {
    const auto restored = read(id);
    assert(restored.state == Ui16CrtReadState::User && restored.override_value.present);
    assert(restored.selected_slot == slot && restored.generation == generation);
    assert(restored.override_value.settings == settings);
    return restored;
}

static void save_once(const Ui16RomIdentity &id, const Ui16CrtRestore &restored,
                      const Ui16CrtSettings &initial, const Ui16CrtSettings &final,
                      const char *initial_crt_line, const char *final_crt_line, const char *blur_line,
                      const char *scan_line, const char *rom_line) {
    const auto defaults = ui16_read_crt_defaults(2, "sd:snes/game.sfc", file, buffer.data(), buffer.size());
    assert(defaults.state == Ui16CrtDefaultsState::Missing);
    ui16_crt_snes_session({}, id, restored, save, defaults);
    assert(config == initial.merge(0));
    std::unique_ptr<Menu> menu(ui16_create_crt_menu(true, true));
    assert(menu->on_info());
    check(*menu, 0, initial_crt_line);
    check(*menu, 1, blur_line);
    check(*menu, 2, scan_line);
    check(*menu, 3, "SAVE OK");
    check(*menu, 5, "SAVE: SAVED");
    check(*menu, 6, "LOADED FROM: USER");
    check(*menu, 7, "SAVE READ: USER");
    check(*menu, 9, rom_line);
    assert(menu->on_adjust(0, 1) && config == final.merge(0));
    check(*menu, 3, "SAVE *");
    assert(!menu->on_choose(3));
    check(*menu, 0, final_crt_line);
    check(*menu, 1, blur_line);
    check(*menu, 2, scan_line);
    check(*menu, 3, "SAVE OK");
    check(*menu, 5, "SAVE: SAVED");
    check(*menu, 6, "LOADED FROM: USER");
    check(*menu, 7, "SAVE READ: USER");
    check(*menu, 9, rom_line);
    ui16_crt_accept_status(config);
    menu->on_tick(100);
    check(*menu, 8, "APPLY: FRAME ACK");
    assert(menu->on_close() && config == final.merge(0));
}

int main(int argc, char **argv) {
    assert(argc == 2 || argc == 3);
    const std::string directory = argv[1];
    const Ui16RomIdentity mario_id{true, Ui16RomVolume::Sd, 2, 0x232bb5b8, 2097152};
    const Ui16RomIdentity panel_id{true, Ui16RomVolume::Sd, 2, 0x14d70786, 1048576};
    const Ui16CrtSettings mario_initial{true, 1, 2}, mario_final{false, 1, 2};
    const Ui16CrtSettings panel_initial{false, 2, 1}, panel_final{true, 2, 1};
    const std::string ma = "sd:" + mario + ".a", mb = "sd:" + mario + ".b";
    const std::string pa = "sd:" + panel + ".a", pb = "sd:" + panel + ".b";
    if (argc == 3) {
        assert(std::string(argv[2]) == "--verify-records");
        for (const auto &name : {ma, mb, pa, pb}) files[name] = load(directory + name.substr(3));
        expect_user(mario_id, 1, 8, mario_final);
        expect_user(panel_id, 1, 21, panel_final);
        assert(writes == 0 && write_opens == 0 && !active);
        std::puts("PASS: actual post-run records select Mario b generation 8 OFF/WEAK/STD and Panel b generation 21 ON/STD/WEAK.");
        return 0;
    }
    for (const auto &name : {ma, mb, pa}) files[name] = load(directory + "/initial" + name.substr(3));
    const auto original_ma = files.at(ma);
    const auto original_pa = files.at(pa);
    const auto expected_mb = load(directory + "/after-both" + mario + ".b");
    const auto expected_pb = load(directory + "/after-both" + panel + ".b");
    save_once(mario_id, expect_user(mario_id, 0, 7, mario_initial), mario_initial, mario_final,
              "CRT   ON", "CRT   OFF", "BLUR WEAK", "SCAN STD", "ROM ID: 232bb5b8");
    assert(writes == 1 && write_targets == std::vector<std::string>{mb});
    assert(files.size() == 3 && files.at(ma) == original_ma && files.at(mb) == expected_mb && files.at(pa) == original_pa);
    save_once(panel_id, expect_user(panel_id, 0, 20, panel_initial), panel_initial, panel_final,
              "CRT   OFF", "CRT   ON", "BLUR STD", "SCAN WEAK", "ROM ID: 14d70786");
    const std::vector<std::string> expected_targets{mb, pb};
    assert(writes == 2 && syncs == 2 && write_opens == 2 && mkdirs == 2 && write_targets == expected_targets);
    assert(files.size() == 4 && files.at(ma) == original_ma && files.at(mb) == expected_mb);
    assert(files.at(pa) == original_pa && files.at(pb) == expected_pb && !active);
    expect_user(mario_id, 1, 8, mario_final);
    expect_user(panel_id, 1, 21, panel_final);
    std::puts("PASS: fresh session per ROM, isolated initial OSD settings, one SAVE per ROM, exact independent writes/CRC/generations and fresh parser readback. FRAME ACK is simulated.");
}
