#include "snes_loader_platform.h"
#include "cores.h"
#include "tc_launch_trace.h"
#include "tc_transition_trace.h"
#include "tc_snes_sd_guard.h"
#include "ui16_crt.h"
#include "ui16_crt_defaults_reader.h"
#include "ui16_crt_restore_reader.h"
#include "ui16_rom_id_reader.h"
#include "ui16_osd.h"
extern "C" {
#include "sdh_sdcard.h"
status_t __wrap_SDH_ReadMultiBlocks(uint8_t *, uint32_t, uint16_t, uint32_t);
}

#include <algorithm>
#include <cassert>
#include <cctype>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <memory>

namespace {
constexpr auto path = "sd:/snes/synthetic.sfc";
constexpr std::size_t header_offset = 0x7fc0;
constexpr std::size_t rom_size = 65536;
std::array<unsigned char, rom_size> rom{};
std::vector<unsigned char> sent;
bool file_open = false, loading = false;
unsigned rom_opens = 0, rom_closes = 0, defaults_opens = 0, resets = 0;
unsigned save_calls = 0, negotiated_loads = 0;
std::string scenario;
std::uint32_t config = 0;

void make_rom() {
    for (std::size_t i = 0; i < rom.size(); ++i) rom[i] = static_cast<unsigned char>(i * 37 + 11);
    auto *header = rom.data() + header_offset;
    std::fill_n(header, 64, 0);
    std::fill_n(header, 21, 'G');
    header[23] = 6;
    header[28] = 0x12;
    header[29] = 0x34;
    header[30] = 0xed;
    header[31] = 0xcb;
    header[61] = 0x80;
}

bool save(const Ui16RomIdentity &, const Ui16CrtSettings &, bool) {
    ++save_calls;
    return false;
}

void check(Menu &menu, int row, const std::string &expected) {
    ui16_osd_capture_begin();
    menu.render();
    ui16_osd_capture_end();
    std::string line(ui16_osd_canvas().cells.data() + row * 32, 32);
    const auto last = line.find_last_not_of(' ');
    line.resize(last == std::string::npos ? 0 : last + 1);
    assert(line == expected);
}
}

bool core_running = false;
FIL fcore{};
alignas(64) unsigned char fbuf[8192];

char *strcasestr(const char *text, const char *part) {
    for (const char *p = text; *p; ++p) {
        std::size_t i = 0;
        while (part[i] && p[i] && std::tolower(static_cast<unsigned char>(part[i])) ==
               std::tolower(static_cast<unsigned char>(p[i]))) ++i;
        if (!part[i]) return const_cast<char *>(p);
    }
    return nullptr;
}

extern "C" status_t __real_SDH_ReadMultiBlocks(uint8_t *, uint32_t, uint16_t, uint32_t) { return Status_Timeout; }
extern "C" status_t __real_SDH_WriteMultiBlocks(uint8_t *, uint32_t, uint16_t, uint32_t) { assert(false); return 1; }
extern "C" void SDH_DisableIntSource(uint32_t) { assert(tc_snes_sd_faulted()); }
extern "C" void SDH_Reset() { assert(tc_snes_sd_faulted()); ++resets; }

extern "C" FRESULT f_open(FIL *file, const char *name, unsigned char mode) {
    assert(file == &fcore && !file_open && mode == FA_READ);
    if (std::string(name) == "sd:/crt/defaults.tsv") { ++defaults_opens; return FR_NO_FILE; }
    if (scenario == "nominal" && std::string(name).find("sd:/crt/02-") == 0) return FR_NO_FILE;
    assert(std::string(name) == path); // An invalid identity must never open an individual record.
    ++rom_opens;
    if (scenario == "rom-load-fails" && rom_opens == 2) return FR_NO_FILE;
    file_open = true;
    file->position = 0;
    file->size = rom.size();
    return FR_OK;
}

extern "C" FRESULT f_lseek(FIL *file, FSIZE_t at) {
    assert(file == &fcore && file_open);
    file->position = std::min(at, rom.size());
    return FR_OK;
}

extern "C" FRESULT f_read(FIL *file, void *data, UINT size, UINT *count) {
    assert(file == &fcore && file_open && data == fbuf);
    *count = 0;
    if (scenario == "sd-timeout") {
        assert(__wrap_SDH_ReadMultiBlocks(fbuf, 0, 512, 1) == Status_SDH_TransferFailed);
        return FR_DISK_ERR;
    }
    *count = static_cast<UINT>(std::min<std::size_t>(size, file->size - file->position));
    std::memcpy(data, rom.data() + file->position, *count);
    file->position += *count;
    return FR_OK;
}

extern "C" FRESULT f_close(FIL *file) {
    assert(file == &fcore && file_open);
    file_open = false;
    ++rom_closes;
    // Host FatFs shim does not declare FR_INT_ERR (value 2 in SDK FatFs).
    return (scenario == "id-close-error" || scenario == "rom-load-fails") && rom_closes == 1 ? 2 : FR_OK;
}

void send_fbuf_data(std::uint16_t size) {
    assert(loading && !core_running);
    sent.insert(sent.end(), fbuf, fbuf + size);
}
void set_loading_state(int state) { loading = state != 0; }

bool tc_rom_uart_capable() { return scenario == "diagnostic"; }
bool tc_rom_uart_load_snes(FIL &file, std::uint32_t off, std::uint32_t size, const std::uint8_t *header) {
    assert(off == 0 && size == rom.size() && header == fbuf);
    assert(std::equal(header, header + 64, rom.data() + header_offset));
    assert(f_lseek(&file, off) == FR_OK);
    for (unsigned at = 0; at < size; at += sizeof fbuf) {
        UINT read = 0;
        assert(f_read(&file, fbuf, sizeof fbuf, &read) == FR_OK && read == sizeof fbuf);
        assert(std::equal(fbuf, fbuf + read, rom.data() + at));
    }
    ++negotiated_loads;
    return true; // The host checks the transport input, not signals on the FPGA connection.
}

void delay(unsigned) {}
void overlay_status(const char *, ...) {}
void overlay_message(const char *, int) {}
void overlay(int state) { assert(state == 0 && core_running && !loading && !file_open); }
void enter_critical() {}
void leave_critical() {}
std::uint32_t get_core_config() { return config; }
void set_core_config(std::uint32_t value) { config = value; }
std::uint64_t bflb_mtimer_get_time_ms() { return 0; }
void fpga_tx_header(int, int) {}
void overlay_clear() { ui16_osd_capture_clear(); }
void overlay_cursor(int x, int y) { ui16_osd_capture_cursor(x, y); }
void overlay_printf(const char *format, ...) {
    char line[128];
    va_list args;
    va_start(args, format);
    std::vsnprintf(line, sizeof line, format, args);
    va_end(args);
    ui16_osd_capture_text(line);
}

static bool crt_stage1_capable = true, snes_crt_sd_session = false;
static Ui16RomIdentity crt_rom_identity;
static Ui16CrtRestore crt_restore;
static Ui16CrtDefaults crt_defaults;
constexpr UINT BLOCK_SIZE = sizeof fbuf;
struct TcStorageLease { explicit operator bool() const { return true; } };
core_info *find_core_by_id(uint16_t id) {
    static core_info snes{2, "SNES", "/snes", "snestang.bin", loadsnes, nullptr};
    return id == 2 ? &snes : nullptr;
}

// Generated verbatim from the inspected main.cpp by the test runner.
#include "load_adapter.inc"

int main(int argc, char **argv) {
    assert(argc == 2);
    scenario = argv[1];
    make_rom();
    const bool started = ui16_hw_load_rom(2, path, nullptr);
    if (scenario == "sd-timeout" || scenario == "rom-load-fails") {
        assert(!started && !core_running && !snes_crt_sd_session && !file_open);
        assert(!crt_rom_identity.valid && sent.empty());
        if (scenario == "sd-timeout") {
            assert(rom_opens == 1 && rom_closes == 1 && resets == 1 && tc_snes_sd_faulted());
            assert(defaults_opens == 0);
        } else assert(rom_opens == 2 && defaults_opens == 1 && resets == 0);
        std::printf("PASS %s: launch stops; no in-game OSD2 session.\n", scenario.c_str());
        return 0;
    }

    assert(started && core_running && snes_crt_sd_session && !file_open && !loading);
    assert(rom_opens == 2 && rom_closes == 2 && defaults_opens == 1 && !tc_snes_sd_faulted());
    if (scenario == "diagnostic") assert(negotiated_loads == 1 && sent.empty());
    else {
        assert(sent.size() == rom.size() + 64);
        assert(std::equal(sent.begin() + 64, sent.end(), rom.begin()));
    }
    if (scenario == "nominal") {
        assert(crt_rom_identity.valid && crt_rom_identity.size == rom.size());
        assert(crt_restore.state == Ui16CrtReadState::Missing);
        std::puts("PASS nominal: normal SD reads produce a ROM ID and the ROM loader succeeds.");
        return 0;
    }
    assert(scenario == "id-close-error" || scenario == "diagnostic");
    assert(!crt_rom_identity.valid && crt_restore.state == Ui16CrtReadState::NoId);
    ui16_crt_snes_session({}, crt_rom_identity, crt_restore, save, crt_defaults);
    std::unique_ptr<Menu> menu(ui16_create_crt_menu(true, true));
    check(*menu, 3, "SAVE N/A");
    check(*menu, 4, "RESET N/A");
    assert(menu->get_options() == std::vector<int>({0, 1, 2}));
    assert(menu->on_info());
    ui16_crt_accept_status(config);
    menu->on_tick(100);
    check(*menu, 5, "SAVE: READ ONLY");
    check(*menu, 6, "LOADED FROM: BUILT-IN");
    check(*menu, 7, "SAVE READ: NO ROM ID");
    check(*menu, 8, "APPLY: FRAME ACK");
    check(*menu, 9, "ROM ID: UNAVAILABLE");
    check(*menu, 10, "DEFAULTS: MISSING");
    assert(menu->on_adjust(0, 1) && config != 0);
    assert(!menu->on_choose(3) && !menu->on_choose(4) && save_calls == 0);
    assert(menu->on_close() && config == 0);
    if (scenario == "diagnostic") {
        const auto next = ui16_identify_rom(2, path, fcore, fbuf, sizeof fbuf);
        assert(next.valid && next.size == rom.size() && rom_closes == 3 && !file_open);
    }
    std::printf("PASS %s: ROM loader succeeds; NO ROM ID, READ ONLY, no SAVE/RESET, preview cancels.\n", scenario.c_str());
}
