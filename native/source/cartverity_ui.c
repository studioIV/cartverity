/* SPDX-License-Identifier: MIT */
#include "cartverity_ui.h"
#include <stdio.h>
#include <stdarg.h>

#define RGB565(r,g,b) ((((uint32_t)(r)>>3)<<11)|(((uint32_t)(g)>>2)<<5)|((uint32_t)(b)>>3))
#define BG RGB565(10,17,29)
#define PANEL RGB565(24,37,55)
#define WHITE RGB565(234,242,250)
#define MUTED RGB565(145,164,187)
#define ACCENT RGB565(64,220,188)
#define AMBER RGB565(255,195,82)
#define RED RGB565(255,110,115)

static void text(const CvPainter *p, int screen, int x, int y, uint32_t color,
                 const char *format, ...) {
    char buffer[160];
    va_list args; va_start(args, format);
    vsnprintf(buffer, sizeof(buffer), format, args); va_end(args);
    p->text(p->context, screen, x, y, color, buffer);
}
static void bar(const CvPainter *p, int y, int percent, uint32_t color) {
    p->rect(p->context, CV_SCREEN_TOP, 12, y, 376, 14, PANEL);
    if (percent > 0) p->rect(p->context, CV_SCREEN_TOP, 14, y+2,
        (372 * percent)/100, 10, color);
}
static void digest(const CvPainter *p, const uint8_t *hash, int complete, int y) {
    char hex[41]; const char *digits = "0123456789ABCDEF";
    if (!complete) { text(p, 1, 12, y, MUTED, "Incomplete"); return; }
    for (unsigned i = 0; i < 20; ++i) {
        hex[i*2] = digits[hash[i] >> 4]; hex[i*2+1] = digits[hash[i]&15];
    }
    hex[40] = 0;
    text(p, 1, 12, y, WHITE, "%.20s", hex);
    text(p, 1, 12, y+14, WHITE, "%.20s", hex+20);
}

void cv_draw(const CvPainter *p, const CvView *v) {
    if (!p || !p->rect || !p->text || !v || !v->result) return;
    const CvResult *r = v->result;
    CvMetrics m = cv_metrics(v->total, v->pass, v->done, v->elapsed_ms);
    p->rect(p->context, 0, 0, 0, 400, 240, BG);
    p->rect(p->context, 1, 0, 0, 320, 240, BG);
    text(p, 0, 12, 10, ACCENT, "CARTVERITY");
    text(p, 0, 12, 26, MUTED, "READ-ONLY / NDS INTEGRITY");
    p->rect(p->context, 0, 12, 43, 376, 1, PANEL);
    text(p, 0, 12, 54, WHITE, "%.36s", v->name);
    text(p, 0, 12, 71, MUTED, "%.4s  REV %02X   %lu MiB", v->game_code,
        v->revision, (unsigned long)(v->total / CV_REGION_SIZE));
    text(p, 0, 12, 93, WHITE, "OVERALL                       %3u%%", m.overall_percent);
    bar(p, 109, (int)m.overall_percent, ACCENT);
    text(p, 0, 12, 132, WHITE, "PASS %u / 2                    %3u%%", v->pass, m.pass_percent);
    bar(p, 148, (int)m.pass_percent, ACCENT);
    text(p, 0, 12, 170, WHITE, "Read %lu / %lu MiB this pass",
        (unsigned long)(v->done / CV_REGION_SIZE), (unsigned long)(v->total / CV_REGION_SIZE));
    const uint64_t speed = m.bytes_per_second * 100 / CV_REGION_SIZE;
    if (m.eta_known)
        text(p, 0, 12, 186, MUTED, "%llu.%02llu MiB/s   ETA %02llu:%02llu",
            (unsigned long long)(speed/100), (unsigned long long)(speed%100),
            (unsigned long long)(m.eta_seconds/60), (unsigned long long)(m.eta_seconds%60));
    else text(p, 0, 12, 186, MUTED, "Speed --   ETA --");
    text(p, 0, 12, 202, MUTED, "Elapsed %02llu:%02llu   Regions %lu/%lu",
        (unsigned long long)(v->elapsed_ms/60000), (unsigned long long)((v->elapsed_ms/1000)%60),
        (unsigned long)r->regions_compared,
        (unsigned long)((v->total+CV_REGION_SIZE-1)/CV_REGION_SIZE));
    text(p, 0, 12, 218, r->regions_changed ? RED : MUTED,
        "Changed: %lu   Region size: 1 MiB", (unsigned long)r->regions_changed);

    if (v->stage == CV_STAGE_RESULT && v->page == 1) {
        text(p, 1, 12, 12, ACCENT, "SHA-1 FINGERPRINTS");
        text(p, 1, 12, 38, MUTED, "Pass 1"); digest(p, r->digest[0], r->complete[0], 54);
        text(p, 1, 12, 94, MUTED, "Pass 2"); digest(p, r->digest[1], r->complete[1], 110);
        text(p, 1, 12, 163, MUTED, "Reference: %s", v->reference_present ? "supplied" : "absent");
        text(p, 1, 12, 213, WHITE, "X  Next page");
        return;
    }
    if (v->stage == CV_STAGE_RESULT && v->page == 2) {
        text(p, 1, 12, 12, ACCENT, "SAVED REPORT");
        text(p, 1, 12, 40, v->log_saved ? WHITE : RED, v->log_saved ? "Log saved to SD:" : "Log may be incomplete:");
        /* Fixed-width wrapping works with the bundled <=8px font. */
        for (unsigned i = 0; v->log_path[i] && i < 160; i += 32)
            text(p, 1, 12, 64+(int)(i/32)*16, WHITE, "%.32s", v->log_path+i);
        text(p, 1, 12, 180, MUTED, "No ROM dump was saved.");
        text(p, 1, 12, 213, WHITE, "X  Back to result");
        return;
    }
    const char *title = "READY TO CHECK";
    uint32_t title_color = ACCENT;
    if (v->stage == CV_STAGE_SCANNING) title = "CHECKING CARTRIDGE";
    else if (v->stage == CV_STAGE_ERROR) { title = "CANNOT START"; title_color = RED; }
    else if (v->stage == CV_STAGE_RESULT) {
        title_color = AMBER;
        switch (r->status) {
        case CV_CONSISTENT: title = "READS CONSISTENT"; break;
        case CV_REFERENCE_MATCH: title = "REFERENCE MATCH"; title_color = ACCENT; break;
        case CV_REFERENCE_MISMATCH: title = "REFERENCE DIFFERS"; title_color = RED; break;
        case CV_INCONSISTENT: title = "READS DIFFER"; title_color = RED; break;
        case CV_CANCELLED: title = "SCAN CANCELLED"; break;
        default: title = "SCAN INCOMPLETE"; title_color = RED; break;
        }
    }
    text(p, 1, 12, 12, title_color, "%s", title);
    if (v->stage == CV_STAGE_SCANNING) {
        text(p, 1, 12, 40, WHITE, "B  Cancel scan");
        text(p, 1, 12, 65, MUTED, "Keep cartridge inserted.");
        text(p, 1, 12, 92, WHITE, "Reference: %s", v->reference_present ? "supplied" : "absent");
        text(p, 1, 12, 122, MUTED, v->pass == 1 ? "Collecting region baseline." : "Comparing logical regions.");
        text(p, 1, 12, 150, MUTED, "No cartridge or save writes.");
    } else {
        text(p, 1, 12, 40, WHITE, v->stage == CV_STAGE_RESULT ? "A  Scan again   X  Details" : "A  Start / retry scan");
        text(p, 1, 12, 57, WHITE, "B  Power off   START  Reboot");
        text(p, 1, 12, 88, MUTED, "%.36s", v->detail);
        text(p, 1, 12, 106, MUTED, "Reference: %s", v->reference_present ? "supplied (unverified)" : "not supplied");
        if (v->stage == CV_STAGE_RESULT)
            text(p, 1, 12, 134, v->log_saved ? ACCENT : RED,
                 v->log_saved ? "SD log saved." : "SD LOG FAILED.");
    }
    text(p, 1, 12, 177, MUTED, "Consistency alone does not");
    text(p, 1, 12, 191, MUTED, "establish known-good data.");
    text(p, 1, 12, 222, MUTED, "v0.2.0-alpha.1 / experimental");
}
