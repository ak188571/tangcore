#include "diskio.h"
#include "ui16_crt_save.h"
#include "ui16_crt_restore_reader.h"

#include <array>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <map>
#include <vector>

namespace {
constexpr std::size_t sector_bytes = 512;
constexpr LBA_t sectors = 98304;
constexpr auto volume = "sd:";
constexpr auto slot_a = "sd:/crt/02-232bb5b8-0000000000200000.a";
constexpr auto slot_b = "sd:/crt/02-232bb5b8-0000000000200000.b";
constexpr auto neighbour = "sd:/crt/untouched.txt";
constexpr Ui16RomIdentity identity{true, Ui16RomVolume::Sd, 2, 0x232bb5b8, 2097152};
constexpr Ui16CrtSettings older{true, 1, 2};
constexpr Ui16CrtSettings latest{true, 2, 1};
constexpr Ui16CrtSettings requested{false, 3, 2};
alignas(64) std::array<unsigned char, 8192> buffer;
std::vector<unsigned char> media(sectors * sector_bytes);

struct PowerCut {};
enum class Boundary { SectorWrite, Sync, SaveComplete };
bool trace_active = false;
std::size_t cut_at = 0;
std::vector<Boundary> trace;
LBA_t blocked_read = sectors;
bool record_read_sectors = false;
std::vector<LBA_t> read_sectors;
std::size_t completed_writes = 0;
std::size_t blocked_write_at = static_cast<std::size_t>(-1);
std::size_t torn_prefix_bytes = 0;
bool buffer_until_sync = false;
std::map<LBA_t, std::array<BYTE, sector_bytes>> pending;

void checkpoint(Boundary operation) {
    if (!trace_active) return;
    if (trace.size() == cut_at) throw PowerCut{};
    trace.push_back(operation);
}

void remount(FATFS &fs) {
    assert(f_mount(nullptr, volume, 0) == FR_OK);
    assert(f_mount(&fs, volume, 1) == FR_OK && fs.fs_type == FS_FAT32);
}

std::array<unsigned char, 32> read_record(const char *path) {
    std::array<unsigned char, 32> bytes{};
    FIL file{};
    UINT read = 0;
    assert(f_open(&file, path, FA_READ) == FR_OK);
    assert(f_size(&file) == bytes.size());
    assert(f_read(&file, bytes.data(), bytes.size(), &read) == FR_OK && read == bytes.size());
    assert(f_close(&file) == FR_OK);
    return bytes;
}

void create_neighbour() {
    FIL file{};
    UINT written = 0;
    const std::array<unsigned char, 32> known{0x1a, 0x3e, 0x77};
    assert(f_open(&file, neighbour, FA_WRITE | FA_CREATE_ALWAYS) == FR_OK);
    assert(f_write(&file, known.data(), known.size(), &written) == FR_OK && written == known.size());
    assert(f_close(&file) == FR_OK);
}

bool save(const Ui16CrtSettings &value) {
    FIL file{};
    return ui16_save_crt_override(identity, value, file, buffer.data(), buffer.size());
}

Ui16CrtRestore restore() {
    FIL file{};
    return ui16_read_crt_override(identity, file, buffer.data(), buffer.size());
}

const char *name(Boundary operation) {
    switch (operation) {
    case Boundary::SectorWrite: return "before_sector_write";
    case Boundary::Sync: return "before_device_sync";
    default: return "after_completed_save";
    }
}
}

extern "C" DSTATUS disk_initialize(BYTE drive) { return drive == DEV_SD ? 0 : STA_NOINIT; }
extern "C" DSTATUS disk_status(BYTE drive) { return disk_initialize(drive); }

extern "C" DRESULT disk_read(BYTE drive, BYTE *data, LBA_t first, UINT count) {
    assert(drive == DEV_SD && first < sectors && count <= sectors - first);
    if (record_read_sectors) {
        for (UINT offset = 0; offset < count; ++offset) read_sectors.push_back(first + offset);
    }
    if (blocked_read >= first && blocked_read - first < count) return RES_ERROR;
    for (UINT offset = 0; offset < count; ++offset) {
        const auto cached = pending.find(first + offset);
        const BYTE *source = cached == pending.end()
            ? media.data() + (first + offset) * sector_bytes : cached->second.data();
        std::memcpy(data + offset * sector_bytes, source, sector_bytes);
    }
    return RES_OK;
}

extern "C" DRESULT disk_write(BYTE drive, const BYTE *data, LBA_t first, UINT count) {
    assert(drive == DEV_SD && first < sectors && count <= sectors - first);
    for (UINT offset = 0; offset < count; ++offset) {
        auto *durable = media.data() + (first + offset) * sector_bytes;
        const auto *incoming = data + offset * sector_bytes;
        if (trace_active && trace.size() == cut_at && torn_prefix_bytes != 0) {
            std::memcpy(durable, incoming, torn_prefix_bytes);
        }
        checkpoint(Boundary::SectorWrite);
        if (completed_writes == blocked_write_at) return RES_ERROR;
        auto *destination = buffer_until_sync ? pending[first + offset].data() : durable;
        std::memcpy(destination, incoming, sector_bytes);
        ++completed_writes;
    }
    return RES_OK;
}

extern "C" DRESULT disk_ioctl(BYTE drive, BYTE command, void *value) {
    assert(drive == DEV_SD);
    switch (command) {
    case CTRL_SYNC:
        checkpoint(Boundary::Sync);
        for (const auto &entry : pending) {
            std::memcpy(media.data() + entry.first * sector_bytes, entry.second.data(), sector_bytes);
        }
        pending.clear();
        return RES_OK;
    case GET_SECTOR_COUNT: *static_cast<LBA_t *>(value) = sectors; return RES_OK;
    case GET_BLOCK_SIZE: *static_cast<DWORD *>(value) = 1; return RES_OK;
    default: return RES_PARERR;
    }
}

int main() {
    MKFS_PARM options{};
    options.fmt = FM_FAT32 | FM_SFD;
    options.n_fat = 2;
    options.au_size = sector_bytes;
    assert(f_mkfs(volume, &options, buffer.data(), buffer.size()) == FR_OK);
    FATFS setup{};
    remount(setup);
    assert(save(older) && save(latest));
    create_neighbour();
    assert(restore().generation == 2);
    const auto protected_b = read_record(slot_b);
    const auto protected_neighbour = read_record(neighbour);
    const auto baseline = media;

    cut_at = static_cast<std::size_t>(-1);
    trace_active = true;
    assert(save(requested));
    checkpoint(Boundary::SaveComplete);
    trace_active = false;
    const auto boundaries = trace;
    assert(boundaries.size() > 2);
    const auto complete_a = read_record(slot_a);
    assert(restore().generation == 3);

    const auto check_cut = [&](std::size_t cut, bool cached, std::size_t torn_bytes) {
        media = baseline;
        buffer_until_sync = cached;
        torn_prefix_bytes = torn_bytes;
        assert(pending.empty());
        FATFS trial{};
        remount(trial);
        trace.clear();
        cut_at = cut;
        trace_active = true;
        bool interrupted = false;
        try {
            assert(save(requested));
            checkpoint(Boundary::SaveComplete);
        } catch (const PowerCut &) {
            interrupted = true;
        }
        trace_active = false;
        assert(interrupted);

        // Reboot without closing the abandoned file or flushing the device cache.
        pending.clear();
        FATFS restarted{};
        remount(restarted);
        assert(read_record(slot_b) == protected_b && read_record(neighbour) == protected_neighbour);
        const auto selection = restore();
        assert(selection.override_value.present);
        if (selection.generation == 3) {
            assert(selection.selected_slot == 0 && selection.state == Ui16CrtReadState::User);
            assert(selection.override_value.settings == requested && read_record(slot_a) == complete_a);
        } else {
            assert(selection.generation == 2 && selection.selected_slot == 1);
            assert(selection.override_value.settings == latest);
            assert(selection.state == Ui16CrtReadState::User || selection.state == Ui16CrtReadState::Recovered);
        }
        std::printf("%s %zu %s partial_bytes=%zu selected=%c generation=%u state=%s\n",
                    cached ? "buffered" : torn_bytes ? "torn" : "direct", cut, name(boundaries[cut]), torn_bytes,
                    selection.selected_slot ? 'b' : 'a', selection.generation, ui16_crt_read_name(selection.state));
        assert(f_mount(nullptr, volume, 0) == FR_OK);
    };
    std::size_t torn_cases = 0;
    for (std::size_t cut = 0; cut < boundaries.size(); ++cut) {
        check_cut(cut, false, 0);
        check_cut(cut, true, 0);
        if (boundaries[cut] == Boundary::SectorWrite) {
            for (std::size_t bytes : {1u, 256u, 511u}) {
                check_cut(cut, false, bytes);
                ++torn_cases;
            }
        }
    }
    buffer_until_sync = false;
    torn_prefix_bytes = 0;
    std::printf("PASS: %zu direct, %zu buffered and %zu torn-sector cases on SDK FatFs FAT32; last good slot and neighbouring file survived every remount.\n",
                boundaries.size(), boundaries.size(), torn_cases);

    media = baseline;
    FATFS io{};
    remount(io);
    // Track the sector access during the latest record's data read, after its file is open.
    FIL file{};
    UINT transferred = 0;
    assert(f_open(&file, slot_b, FA_READ) == FR_OK);
    record_read_sectors = true;
    assert(f_read(&file, buffer.data(), 32, &transferred) == FR_OK && transferred == 32);
    record_read_sectors = false;
    assert(f_close(&file) == FR_OK && read_sectors.size() == 1);
    blocked_read = read_sectors.front();
    const auto before_error = completed_writes;
    const auto unreadable = restore();
    assert(unreadable.state == Ui16CrtReadState::Io && unreadable.selected_slot == -1);
    assert(!save(requested) && completed_writes == before_error && media == baseline);
    blocked_read = sectors;
    assert(restore().generation == 2);
    std::puts("PASS: latest slot sector read error yields READ ERROR and refuses SAVE before any disk write.");

    blocked_write_at = completed_writes + 2;
    assert(!save(requested) && completed_writes == blocked_write_at);
    blocked_write_at = static_cast<std::size_t>(-1);
    FATFS after_write_error{};
    remount(after_write_error);
    assert(read_record(slot_b) == protected_b && read_record(neighbour) == protected_neighbour);
    const auto recovered = restore();
    assert(recovered.selected_slot == 1 && recovered.generation == 2 && recovered.override_value.settings == latest);
    std::puts("PASS: disk write failure after two sector writes leaves the latest confirmed slot readable after remount.");
}
