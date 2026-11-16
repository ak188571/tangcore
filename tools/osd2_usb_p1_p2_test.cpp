#include "menu_manager.h"
#include "ui16_browser.h"
#include "ui16_crt.h"
#include "ui16_navigation.h"
#include "ui16_osd.h"
#include "ui16_osd_menu.h"

#include <array>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <iterator>
#include <memory>
#include <string>
#include <vector>

namespace {
constexpr std::uint16_t START = 0x0008;
constexpr std::uint16_t SELECT = 0x0004;
constexpr std::uint16_t LEFT = 0x0040;
constexpr std::uint16_t B = 0x0001;

struct UsbPoll {
    std::uint16_t p1;
    std::uint16_t p2;
};

constexpr UsbPoll polls[] = {
    {0, 0}, {0, UI16_BUTTON_DOWN}, {0, START},
    {0, UI16_BUTTON_BACK}, {0, 0},
    {START, 0}, {0, B}, {UI16_BUTTON_DOWN, B}, {0, 0},
    {0, B}, {UI16_BUTTON_BACK, B},
};

using TextRam = std::array<char, 32 * 28>;
TextRam screen;
std::vector<TextRam> visible_before_poll;
std::size_t next_poll = 0;
unsigned x = 0, y = 0;
std::uint32_t config = 0;
std::uint64_t now = 0;
}

int overlay_enabled = 1;
int critical_depth = 0;
void enter_critical() { ++critical_depth; }
void leave_critical() { --critical_depth; }
void fpga_tx_header(int command, int size) { assert(command == 0x12 && size == 1); }
void fpga_tx_byte(std::uint8_t) {}
std::uint32_t get_core_config() { return config; }
void set_core_config(std::uint32_t value) { config = value; }
std::uint64_t bflb_mtimer_get_time_ms() { return now; }
void delay(unsigned ms) { now += ms; }
int overlay_on() { return overlay_enabled; }
void overlay(int enabled) { overlay_enabled = enabled; }
void overlay_osd_capture_begin() { ui16_osd_capture_begin(); }
void overlay_osd_capture_end() { ui16_osd_capture_end(); }
void overlay_osd_window(unsigned, unsigned, unsigned, unsigned) {}
void dprint(const char *, ...) {}
std::uint8_t key_input() { return 0; }
void command_console() {}

void get_joypad_states(std::uint16_t *j1, std::uint16_t *j2, std::uint16_t *h1, std::uint16_t *h2) {
    assert(next_poll < std::size(polls));
    visible_before_poll.push_back(screen);
    const auto poll = polls[next_poll++];
    *j1 = poll.p1;
    *j2 = poll.p2;
    *h1 = *h2 = 0;
}

void overlay_clear() {
    if (!ui16_osd_capture_clear()) screen.fill(' ');
}

void overlay_cursor(int column, int row) {
    if (!ui16_osd_capture_cursor(column, row)) {
        x = column;
        y = row;
    }
}

void overlay_printf(const char *format, ...) {
    char text[128];
    va_list args;
    va_start(args, format);
    std::vsnprintf(text, sizeof(text), format, args);
    va_end(args);
    if (ui16_osd_capture_text(text)) return;
    for (const char *p = text; *p; ++p) {
        assert(x < 32 && y < 28);
        screen[y * 32 + x++] = *p;
    }
}

int main() {
    assert(ui16_osd_request(SELECT | LEFT, 0) == Ui16GameOsd::Crt);
    screen.fill(' ');
    ui16_crt_new_session();
    push_menu(std::unique_ptr<Menu>(ui16_create_crt_menu(true, true)));
    ui16_osd_menu_input_loop(false, "CRT SETTINGS", true);
    assert(next_poll == std::size(polls) && !overlay_enabled);

    const auto &compact = visible_before_poll[0];
    assert(std::string(compact.data(), compact.size()).find("START:INFO") != std::string::npos);
    for (std::size_t i = 1; i <= 5; ++i) assert(visible_before_poll[i] == compact);

    const auto &details = visible_before_poll[6];
    assert(std::string(details.data(), details.size()).find("START:HIDE") != std::string::npos);
    for (std::size_t i = 7; i < std::size(polls); ++i) assert(visible_before_poll[i] == details);
    assert(config == 0 && critical_depth == 0);
    menu_clear();

    std::puts("PASS: P2 directions, START and BACK leave OSD2 unchanged; P1 opens info; all-up unlocks the menu; P1 closes with P2 held.");
}
