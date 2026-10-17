/* SPDX-License-Identifier: MIT
 * CartVerity native adapter for the pinned GodMode9 release.
 * Only fixed 0:/ SD log paths are opened for writing. No cart/save/NAND writers.
 */
#include "cartverity_app.h"
#include "cartverity_scan.h"
#include "cartverity_ui.h"
#include "godmode.h"
#include "ui.h"
#include "hid.h"
#include "fs.h"
#include "gamecart.h"
#include "nand.h"
#include "sha.h"
#include "timer.h"
#include "rtc.h"
#include "language.h"
#include "entrypoints.h"
#include "power.h"
#include <stdarg.h>

#define CV_VERSION "0.2.0-alpha.3"
#define CV_OUTPUT "0:/gm9/out/dscheck"
#define CV_PIXELS ((400u+320u)*240u)
static CvSettings settings = {1, 2, 0, 0};
static uint16_t *frame, *previous_frame;
static bool frame_valid;

static uint16_t *screen_buffer(int screen) {
    return frame + (screen == CV_SCREEN_TOP ? 0 : 400*240);
}

typedef struct {
    CartData *cart;
    uint8_t header[512];
    uint32_t card_id;
    uint32_t total;
    uint64_t timer;
    uint64_t last_draw;
    CvView view;
    CvResult result;
    FIL log;
    bool log_open;
    bool log_ok;
    bool finished;
    char reference_path[160];
    uint8_t reference[20];
} CvSession;

static void paint_rect(void *unused, int screen, int x, int y, int w, int h, uint32_t color) {
    (void)unused;
    const int width = screen == CV_SCREEN_TOP ? 400 : 320;
    if (x < 0 || y < 0 || w <= 0 || h <= 0 || x+w > width || y+h > 240) return;
    DrawRectangle(screen_buffer(screen), x, y, w, h, color);
}
static void paint_text(void *unused, int screen, int x, int y, uint32_t color, const char *value) {
    (void)unused;
    const int width = screen == CV_SCREEN_TOP ? 400 : 320;
    if (x < 0 || y < 0 || y+(int)GetFontHeight() > 240) return;
    /* DrawString identifies width by a hardware framebuffer address. Render
       glyphs explicitly so our RAM top-screen buffer retains its 400px width. */
    while (*value && x+(int)GetFontWidth() <= width) {
        DrawCharacter(screen_buffer(screen), (unsigned char)*value++, x, y, color, COLOR_TRANSPARENT);
        x += GetFontWidth();
    }
}
static const CvPainter painter = {NULL, paint_rect, paint_text};
static void draw(CvSession *s) {
    s->view.settings = &settings;
    cv_draw(&painter, &s->view);
    cv_present(TOP_SCREEN, previous_frame, frame, 400*240, !frame_valid);
    cv_present(BOT_SCREEN, previous_frame+400*240, frame+400*240, 320*240, !frame_valid);
    frame_valid = true;
}

static void configure(CvSession *s) {
    s->view.stage = CV_STAGE_SETTINGS;
    s->view.selected_setting = 0;
    draw(s);
    for (;;) {
        while (HID_ReadState() & BUTTON_ANY) {}
        const u32 keys = InputWait(0);
        if (keys & (BUTTON_B | BUTTON_Y)) return;
        if (keys & BUTTON_UP) s->view.selected_setting = (s->view.selected_setting + 3) % 4;
        if (keys & BUTTON_DOWN) s->view.selected_setting = (s->view.selected_setting + 1) % 4;
        if (keys & BUTTON_LEFT) cv_setting_change(&settings, s->view.selected_setting, -1);
        if (keys & (BUTTON_RIGHT | BUTTON_A)) cv_setting_change(&settings, s->view.selected_setting, 1);
        if (keys & BUTTON_X) settings = (CvSettings){1, 2, 0, 0};
        SetScreenBrightness(cv_brightness(&settings));
        draw(s);
    }
}

static void encode_hex(const uint8_t *bytes, unsigned size, char *out) {
    static const char digits[] = "0123456789ABCDEF";
    for (unsigned i = 0; i < size; ++i) {
        out[i*2] = digits[bytes[i] >> 4]; out[i*2+1] = digits[bytes[i] & 15];
    }
    out[size*2] = 0;
}
static bool directory(const char *path) {
    FILINFO info;
    const FRESULT result = fvx_stat(path, &info);
    if (result == FR_OK) return (info.fattrib & AM_DIR) != 0;
    return (result == FR_NO_FILE || result == FR_NO_PATH) && fvx_mkdir(path) == FR_OK;
}
static bool log_line(CvSession *s, const char *format, ...) {
    char text[512];
    if (!s->log_open || !s->log_ok) return false;
    va_list args; va_start(args, format);
    const int size = vsnprintf(text, sizeof(text)-1, format, args); va_end(args);
    if (size < 0 || size >= (int)sizeof(text)-1) return (s->log_ok = false);
    text[size] = '\n'; UINT written = 0;
    if (fvx_write(&s->log, text, (UINT)size+1, &written) != FR_OK || written != (UINT)size+1)
        s->log_ok = false;
    return s->log_ok;
}
static bool log_open(CvSession *s) {
    if (!directory("0:/gm9") || !directory("0:/gm9/out") || !directory(CV_OUTPUT)) return false;
    DsTime now = {0}; get_dstime(&now);
    for (unsigned suffix = 0; suffix < 10000; ++suffix) {
        snprintf(s->view.log_path, sizeof(s->view.log_path),
            CV_OUTPUT "/native_%02X%02X%02X_%02X%02X%02X_%04u.txt",
            (unsigned)now.bcd_Y, (unsigned)now.bcd_M, (unsigned)now.bcd_D,
            (unsigned)now.bcd_h, (unsigned)now.bcd_m, (unsigned)now.bcd_s, suffix);
        FRESULT result = fvx_open(&s->log, s->view.log_path, FA_WRITE | FA_CREATE_NEW);
        if (result == FR_EXIST) continue;
        if (result != FR_OK) return false;
        s->log_open = s->log_ok = true;
        return true;
    }
    return false;
}
static void log_close(CvSession *s) {
    if (!s->log_open) return;
    if (fvx_sync(&s->log) != FR_OK) s->log_ok = false;
    if (fvx_close(&s->log) != FR_OK) s->log_ok = false;
    s->log_open = false;
    s->view.log_saved = s->log_ok && s->finished;
}
static bool error(CvSession *s, const char *message) {
    s->view.stage = CV_STAGE_ERROR;
    snprintf(s->view.detail, sizeof(s->view.detail), "%s", message);
    draw(s);
    return false;
}

static bool discover(CvSession *s) {
    s->result.status = CV_READY;
    s->view.pass = 1;
    s->view.stage = CV_STAGE_READY;
    s->view.result = &s->result;
    strcpy(s->view.name, "Waiting for a DS cartridge");
    if (!InitSDCardFS()) return error(s, "Console SD is not available.");
    if (!CART_STATE || InitCartRead(s->cart) != 0)
        return error(s, "Could not initialize the cartridge.");
    if (!(s->cart->cart_type & CART_NTR) || (s->cart->cart_type & CART_TWL) ||
        s->cart->header[0x12] != 0 || s->cart->save_type == CARD_SAVE_RETAIL_NAND)
        return error(s, "Requires a standard DS ROM cartridge.");
    if (!s->cart->cart_size || s->cart->cart_size > CV_MAX_ROM || s->cart->cart_size % 512)
        return error(s, "Unsupported ROM size (max 512 MiB).");
    memcpy(s->header, s->cart->header, sizeof(s->header));
    s->card_id = s->cart->cart_id;
    s->view.total = s->total = (uint32_t)s->cart->cart_size;
    for (unsigned i = 0; i < 12; ++i) {
        uint8_t c = s->header[i];
        s->view.name[i] = c >= 32 && c < 127 ? (char)c : ' ';
    }
    s->view.name[12] = 0;
    for (unsigned i = 0; i < 4; ++i) {
        uint8_t c = s->header[0x0C+i];
        s->view.game_code[i] = c >= 32 && c < 127 ? (char)c : '?';
    }
    s->view.game_code[4] = 0;
    s->view.revision = s->header[0x1E];
    char stem[32]; GetCartName(stem, s->cart);
    snprintf(s->reference_path, sizeof(s->reference_path),
        "0:/gm9/support/dscheck/%s.nds.sha1", stem);
    FIL reference; FILINFO info;
    FRESULT result = settings.reference == 2 ? FR_NO_FILE : fvx_stat(s->reference_path, &info);
    if (result == FR_NO_FILE || result == FR_NO_PATH) {
        if (settings.reference == 1) return error(s, "A reference is required. Add its file.");
        strcpy(s->view.detail, settings.reference == 2 ? "Reference comparison disabled." : "Ready. No known-good reference.");
    } else {
        if (result != FR_OK || (info.fattrib & AM_DIR) || info.fsize != 20)
            return error(s, "Reference must be 20 binary bytes.");
        if (fvx_open(&reference, s->reference_path, FA_READ) != FR_OK)
            return error(s, "Reference could not be opened.");
        UINT got = 0;
        bool ok = fvx_read(&reference, s->reference, 20, &got) == FR_OK && got == 20;
        if (fvx_close(&reference) != FR_OK) ok = false;
        if (!ok) return error(s, "Reference could not be read.");
        s->view.reference_present = 1;
        strcpy(s->view.detail, "Ready. Compare supplied reference.");
    }
    draw(s);
    return true;
}

static int begin_pass(void *opaque, unsigned pass) {
    CvSession *s = opaque;
    (void)pass;
    /* Reacquire the header/secure-area caches before each pass. This is still
       the normalized GodMode9 view, not an electrical or physical-cell test. */
    if (!CART_STATE || InitCartRead(s->cart) != 0) {
        strcpy(s->view.detail, "Cartridge initialization failed."); return 0;
    }
    if (s->cart->cart_id != s->card_id || s->cart->cart_size != s->total ||
        memcmp(s->header, s->cart->header, sizeof(s->header))) {
        strcpy(s->view.detail, "Cartridge identity/header changed."); return 0;
    }
    SetSecureAreaEncryption(false);
    return 1;
}
static int read_block(void *opaque, uint32_t offset, uint8_t *data, uint32_t size) {
    CvSession *s = opaque;
    if (!CART_STATE || ReadCartBytes(data, offset, size, s->cart, true) != 0 || !CART_STATE) {
        strcpy(s->view.detail, "Cartridge read failed or was removed."); return -1;
    }
    /* The lower-level DS bus API has no detailed per-sector status. */
    return (int)size;
}
static void hash_begin(void *opaque) { (void)opaque; sha_init(SHA1_MODE); }
static void hash_update(void *opaque, const uint8_t *data, uint32_t size) {
    (void)opaque; sha_update(data, size);
}
static void hash_end(void *opaque, uint8_t digest[20]) {
    (void)opaque;
    /* sha_get uses word transfers. CvResult's byte arrays need not be aligned. */
    alignas(16) u32 aligned_hash[8] = {0};
    sha_get(aligned_hash);
    memcpy(digest, aligned_hash, 20);
}
static int progress(void *opaque, unsigned pass, uint32_t done, const CvResult *result) {
    CvSession *s = opaque;
    const uint64_t ms = timer_msec(s->timer);
    s->view.pass = pass; s->view.done = done; s->view.elapsed_ms = ms;
    s->view.result = result;
    if (ms >= s->last_draw + cv_refresh_ms(&settings) || !done || done == s->total) {
        draw(s); s->last_draw = ms;
    }
    return !CheckButton(BUTTON_B);
}

static void scan(CvSession *s, uint8_t *buffer) {
    if (!log_open(s)) { error(s, "Cannot create a unique SD log."); return; }
    log_line(s, "format=cartverity-native/1");
    log_line(s, "state=INCOMPLETE");
    log_line(s, "version=" CV_VERSION);
    log_line(s, "godmode9_base=2.2.3");
    log_line(s, "display_refresh_ms=%u", cv_refresh_ms(&settings));
    log_line(s, "reference_policy=%s", settings.reference == 2 ? "IGNORE" : settings.reference == 1 ? "REQUIRE" : "AUTO");
    log_line(s, "rom_view=full_standard_nds");
    log_line(s, "game_code_hex=%02X%02X%02X%02X", (unsigned)s->header[12],
        (unsigned)s->header[13], (unsigned)s->header[14], (unsigned)s->header[15]);
    log_line(s, "revision_hex=%02X", s->view.revision);
    log_line(s, "rom_bytes=%lu", (unsigned long)s->total);
    log_line(s, "reference_path=%s", s->reference_path);
    log_line(s, "reference_state=%s", s->view.reference_present ? "SUPPLIED_UNAUTHENTICATED" : "NOT_PROVIDED");
    if (s->view.reference_present) {
        char hash[41]; encode_hex(s->reference, 20, hash); log_line(s, "reference_sha1=%s", hash);
    }
    log_line(s, "region_size=%u", CV_REGION_SIZE);
    log_line(s, "scope=normalized_ROM;reinitialize_each_pass;no_per_sector_fault_report");
    if (fvx_sync(&s->log) != FR_OK) s->log_ok = false;
    if (!s->log_ok) { log_close(s); error(s, "SD log failed before scanning."); return; }

    s->view.stage = CV_STAGE_SCANNING;
    s->timer = timer_start(); s->last_draw = 0;
    strcpy(s->view.detail, "Two full read passes.");
    const CvCallbacks callbacks = {s, begin_pass, read_block, hash_begin, hash_update, hash_end, progress};
    cv_scan(s->total, buffer, s->view.reference_present ? s->reference : NULL, &callbacks, &s->result);
    s->view.elapsed_ms = timer_msec(s->timer);
    s->view.result = &s->result;
    log_line(s, "result=%s", cv_status_name(s->result.status));
    for (unsigned i = 0; i < 2; ++i) {
        log_line(s, "pass%u_bytes=%lu", i+1, (unsigned long)s->result.bytes[i]);
        if (s->result.complete[i]) {
            char hash[41]; encode_hex(s->result.digest[i], 20, hash);
            log_line(s, "sha1_pass%u=%s", i+1, hash);
        }
    }
    log_line(s, "elapsed_ms=%llu", (unsigned long long)s->view.elapsed_ms);
    log_line(s, "regions_compared=%lu", (unsigned long)s->result.regions_compared);
    log_line(s, "regions_changed=%lu", (unsigned long)s->result.regions_changed);
    for (unsigned i = 0; i < CV_MAX_REGIONS; ++i)
        if (s->result.changed[i]) log_line(s, "changed_region_offset=%lu", (unsigned long)i*CV_REGION_SIZE);
    log_line(s, "read_detail=%s", s->view.detail);
    log_line(s, "state=COMPLETE");
    s->finished = true; log_close(s);
    s->view.stage = CV_STAGE_RESULT; s->view.page = settings.result_page;
    if (s->result.status == CV_CONSISTENT)
        strcpy(s->view.detail, "No known-good reference compared.");
    else if (s->result.status == CV_REFERENCE_MATCH)
        strcpy(s->view.detail, "Both reads match the supplied SHA-1.");
    else if (s->result.status == CV_REFERENCE_MISMATCH)
        strcpy(s->view.detail, "Check reference, revision and format.");
    else if (s->result.status == CV_INCONSISTENT)
        strcpy(s->view.detail, "Read data differs between passes.");
    else if (s->result.status == CV_CANCELLED)
        strcpy(s->view.detail, "Cancelled; partial progress logged.");
    draw(s);
}

u32 CartVerityMain(int entrypoint) {
    if (!SetFont(NULL, 0)) return GODMODE_EXIT_POWEROFF;
    SetLanguage(NULL, 0);
    InitSDCardFS();
    InitNandCrypto(entrypoint != ENTRY_B9S);
    SetScreenBrightness(cv_brightness(&settings));
    frame = malloc(CV_PIXELS * sizeof(*frame));
    previous_frame = malloc(CV_PIXELS * sizeof(*previous_frame));
    frame_valid = false;
    CvSession *s = calloc(1, sizeof(*s));
    CartData *cart = malloc(sizeof(*cart));
    uint8_t *buffer = malloc(CV_BLOCK_SIZE);
    u32 exit_mode = GODMODE_EXIT_POWEROFF;
    if (!s || !cart || !buffer || !frame || !previous_frame) {
        ShowPrompt(false, "CartVerity: out of memory.");
    } else {
        bool ready = false;
        for (;;) {
            memset(s, 0, sizeof(*s)); s->cart = cart;
            ready = discover(s);
            bool restart = false;
            while (!restart) {
                while (HID_ReadState() & BUTTON_ANY) {} // fresh button press
                const u32 keys = InputWait(0);
                if (keys & BUTTON_START) { exit_mode = GODMODE_EXIT_REBOOT; goto exit; }
                if (keys & BUTTON_B) goto exit;
                if (keys & BUTTON_Y) { configure(s); restart = true; continue; }
                if ((keys & BUTTON_X) && s->view.stage == CV_STAGE_RESULT) {
                    s->view.page = (s->view.page + 1) % 3; draw(s);
                }
                if (keys & BUTTON_A) {
                    if (!ready || s->view.stage != CV_STAGE_READY) restart = true;
                    else { scan(s, buffer); ready = false; }
                }
            }
        }
    }
exit:
    if (s && s->log_open) log_close(s);
    free(buffer); free(cart); free(s);
    free(frame); free(previous_frame);
    DeinitSDCardFS();
    return exit_mode;
}
