/* SPDX-License-Identifier: MIT */
#include "cartverity_ui.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

#define RGB565(r,g,b) ((((uint32_t)(r)>>3)<<11)|(((uint32_t)(g)>>2)<<5)|((uint32_t)(b)>>3))
#define BG RGB565(8,13,27)
#define PANEL RGB565(21,32,55)
#define FOOTER RGB565(28,43,69)
#define WHITE RGB565(243,248,255)
#define MUTED RGB565(167,186,213)
#define CYAN RGB565(76,211,255)
#define BLUE RGB565(100,173,255)
#define GREEN RGB565(91,240,170)
#define PURPLE RGB565(199,158,255)
#define AMBER RGB565(255,204,87)
#define RED RGB565(255,119,145)
#define GREEN_BG RGB565(12,53,45)
#define AMBER_BG RGB565(55,42,24)
#define RED_BG RGB565(57,25,43)

static void text(const CvPainter *p, int screen, int x, int y, uint32_t color,
                 const char *format, ...) {
    char buffer[160];
    va_list args; va_start(args, format);
    vsnprintf(buffer, sizeof(buffer), format, args); va_end(args);
    p->text(p->context, screen, x, y, color, buffer);
}
static void large(const CvPainter *p, int screen, int x, int y, uint32_t color, const char *value) {
    if (p->text_scaled) p->text_scaled(p->context, screen, x, y, color, 2, value);
    else p->text(p->context, screen, x, y, color, value);
}
static void panel(const CvPainter *p, int screen, int x, int y, int w, int h, uint32_t color) {
    p->rect(p->context, screen, x, y, w, h, color);
}
static void bar(const CvPainter *p, int y, unsigned percent, uint32_t color) {
    if (percent > 100) percent = 100;
    panel(p, 0, 12, y, 376, 14, PANEL);
    if (percent) panel(p, 0, 14, y+2, (int)(372*percent/100), 10, color);
}
static void key(const CvPainter *p, int x, int y, const char *name, const char *action, uint32_t color) {
    const int width = strlen(name) > 1 ? 50 : 18;
    panel(p, 1, x, y, width, 16, color);
    /* The pinned font is 6x10. Padding also accommodates the 8px bounds check. */
    text(p, 1, x+(width-(int)strlen(name)*6)/2, y+3, BG, "%s", name);
    text(p, 1, x+width+8, y+3, WHITE, "%s", action);
}
static void controls(const CvPainter *p, const CvView *v) {
    panel(p, 1, 0, 174, 320, 66, FOOTER);
    panel(p, 1, 0, 174, 320, 2, BLUE);
    if (v->stage == CV_STAGE_SCANNING) {
        key(p, 12, 184, "B", "Cancel scan", RED);
        text(p, 1, 12, 210, MUTED, "Current read finishes first.");
        text(p, 1, 12, 226, MUTED, "PHYSICAL BUTTON");
    } else if (v->stage == CV_STAGE_SETTINGS) {
        key(p, 12, 182, "D-PAD", "Select / change", BLUE);
        key(p, 12, 202, "X", "Defaults", CYAN);
        key(p, 164, 202, "B", "Back", RED);
        key(p, 12, 222, "A", "Change value", GREEN);
        key(p, 164, 222, "Y", "Back", PURPLE);
    } else {
        key(p, 12, 182, "A", v->stage == CV_STAGE_RESULT ? "Back to ready" :
            v->stage == CV_STAGE_ERROR ? "Retry" : "Start scan", GREEN);
        if (v->stage == CV_STAGE_RESULT) key(p, 164, 182, "X", "Next page", CYAN);
        key(p, 12, 202, "Y", "Settings", PURPLE);
        key(p, 164, 202, "B", "Power off", RED);
        key(p, 12, 222, "START", "Reboot", MUTED);
        text(p, 1, 164, 225, MUTED, "PHYSICAL KEYS");
    }
}
static void heading(const CvPainter *p, const char *value, unsigned page) {
    text(p, 1, 12, 12, CYAN, "%s", value);
    if (page) text(p, 1, 276, 12, MUTED, "%u/4", page);
}

typedef struct { const char *title, *note; uint32_t color, tint; int matched; } Verdict;
static Verdict verdict(const CvView *v) {
    switch (v->result->status) {
    case CV_DATABASE_MATCH: return (Verdict){"DATABASE MATCH", "Catalog SHA-1 and size agree.", GREEN, GREEN_BG, 1};
    case CV_REFERENCE_MATCH: return (Verdict){"REFERENCE MATCH", "Both reads match supplied SHA-1.", GREEN, GREEN_BG, 1};
    case CV_CONSISTENT: return (Verdict){"READS CONSISTENT", "UNVERIFIED - no reference match.", AMBER, AMBER_BG, 0};
    case CV_REFERENCE_MISMATCH: return (Verdict){"REFERENCE DIFFERS", "Check revision and reference format.", RED, RED_BG, 0};
    case CV_INCONSISTENT: return (Verdict){"READS DIFFER", "Read data differs between passes.", RED, RED_BG, 0};
    case CV_CANCELLED: return (Verdict){"SCAN CANCELLED", "Verification was not completed.", AMBER, AMBER_BG, 0};
    default: return (Verdict){"SCAN INCOMPLETE", "Read or initialization failed.", RED, RED_BG, 0};
    }
}
static int reads_agree(CvStatus status) {
    return status == CV_CONSISTENT || status == CV_REFERENCE_MATCH ||
        status == CV_REFERENCE_MISMATCH || status == CV_DATABASE_MATCH;
}
static void status_icon(const CvPainter *p, const Verdict *s) {
    if (s->matched) {
        for (int i = 0; i < 3; ++i) panel(p, 0, 25+i*4, 118+i*4, 5, 5, s->color);
        for (int i = 0; i < 5; ++i) panel(p, 0, 33+i*4, 126-i*4, 5, 5, s->color);
    } else {
        panel(p, 0, 35, 108, 5, 16, s->color);
        panel(p, 0, 35, 129, 5, 5, s->color);
    }
}
static void metric(const CvPainter *p, int x, int width, const char *label,
                   const char *value, uint32_t color) {
    panel(p, 0, x, 168, width, 54, PANEL);
    text(p, 0, x+8, 176, MUTED, "%s", label);
    large(p, 0, x+8, 194, color, value);
}
static void top(const CvPainter *p, const CvView *v, int result) {
    const CvResult *r = v->result;
    text(p, 0, 12, 10, CYAN, "CARTVERITY");
    text(p, 0, 300, 10, WHITE, "by studioIV");
    text(p, 0, 12, 27, MUTED, "READ-ONLY / v0.2.0-alpha.5");
    panel(p, 0, 12, 43, 376, 1, BLUE);
    const char *title = result && v->reference_title[0] ? v->reference_title : v->name;
    text(p, 0, 12, 54, WHITE, "%.*s%s", strlen(title)>46 ? 43 : 46, title,
        strlen(title)>46 ? "..." : "");
    text(p, 0, 12, 73, MUTED, "%.4s  REV %02X   %lu MiB", v->game_code,
        v->revision, (unsigned long)(v->total/CV_REGION_SIZE));
    if (result) {
        const Verdict s = verdict(v);
        panel(p, 0, 12, 92, 376, 64, s.tint);
        panel(p, 0, 12, 92, 4, 64, s.color);
        status_icon(p, &s);
        large(p, 0, 70, 103, s.color, s.title);
        text(p, 0, 70, 135, WHITE, "%s", s.note);
        char passes[24], regions[24], elapsed[32];
        snprintf(passes, sizeof(passes), "%u / 2", (unsigned)(!!r->complete[0]+!!r->complete[1]));
        snprintf(regions, sizeof(regions), "%lu/%lu", (unsigned long)r->regions_compared,
            (unsigned long)((v->total+CV_REGION_SIZE-1)/CV_REGION_SIZE));
        const uint64_t minutes = v->elapsed_ms/60000;
        if (minutes > 999) snprintf(elapsed, sizeof(elapsed), ">999m");
        else snprintf(elapsed, sizeof(elapsed), "%02u:%02u", (unsigned)minutes, (unsigned)((v->elapsed_ms/1000)%60));
        metric(p, 12, 118, "PASSES", passes, r->complete[0] && r->complete[1] ? WHITE : AMBER);
        metric(p, 140, 118, "REGIONS", regions, WHITE);
        metric(p, 268, 120, "ELAPSED", elapsed, WHITE);
        if (reads_agree(r->status) || r->status == CV_INCONSISTENT)
            text(p, 0, 12, 228, r->regions_changed ? RED : MUTED,
                "Changed regions: %lu", (unsigned long)r->regions_changed);
        else text(p, 0, 12, 228, AMBER, "Scan stopped - no final comparison");
        return;
    }
    const CvMetrics m = cv_metrics(v->total, v->pass, v->done, v->elapsed_ms);
    text(p, 0, 12, 96, WHITE, "OVERALL                       %3u%%", m.overall_percent);
    bar(p, 113, m.overall_percent, CYAN);
    text(p, 0, 12, 136, WHITE, "PASS %u / 2                    %3u%%", v->pass, m.pass_percent);
    bar(p, 153, m.pass_percent, PURPLE);
    text(p, 0, 12, 179, WHITE, "Read %lu / %lu MiB this pass", (unsigned long)(v->done/CV_REGION_SIZE),
        (unsigned long)(v->total/CV_REGION_SIZE));
    const uint64_t speed = m.bytes_per_second*100/CV_REGION_SIZE;
    if (m.eta_known) text(p, 0, 12, 195, MUTED, "%llu.%02llu MiB/s   ETA %02llu:%02llu",
        (unsigned long long)(speed/100), (unsigned long long)(speed%100),
        (unsigned long long)(m.eta_seconds/60), (unsigned long long)(m.eta_seconds%60));
    else text(p, 0, 12, 195, MUTED, "Speed --   ETA --");
    text(p, 0, 12, 211, MUTED, "Elapsed %02llu:%02llu   Regions %lu",
        (unsigned long long)(v->elapsed_ms/60000), (unsigned long long)((v->elapsed_ms/1000)%60),
        (unsigned long)r->regions_compared);
    text(p, 0, 12, 227, r->regions_changed ? RED : MUTED,
        "Changed: %lu   Logical regions: 1 MiB", (unsigned long)r->regions_changed);
}
static void digest(const CvPainter *p, const uint8_t *hash, int complete, int y) {
    char hex[41]; const char *digits = "0123456789ABCDEF";
    if (!complete) { text(p, 1, 22, y, AMBER, "Incomplete"); return; }
    for (unsigned i = 0; i < 20; ++i) { hex[i*2] = digits[hash[i]>>4]; hex[i*2+1] = digits[hash[i]&15]; }
    hex[40] = 0;
    text(p, 1, 22, y, WHITE, "%.20s", hex);
    text(p, 1, 22, y+14, WHITE, "%.20s", hex+20);
}
static void details(const CvPainter *p, const CvView *v, const char *reference) {
    const CvResult *r = v->result;
    if (v->page == 1) {
        heading(p, "SHA-1 FINGERPRINTS", 2);
        panel(p, 1, 12, 34, 296, 54, PANEL);
        text(p, 1, 22, 40, CYAN, "PASS 1"); digest(p, r->digest[0], r->complete[0], 54);
        panel(p, 1, 12, 96, 296, 54, PANEL);
        text(p, 1, 22, 102, PURPLE, "PASS 2"); digest(p, r->digest[1], r->complete[1], 116);
        text(p, 1, 12, 157, MUTED, "Reference: %s", reference);
    } else if (v->page == 2) {
        heading(p, "SD REPORT", 3);
        panel(p, 1, 12, 34, 296, 124, PANEL);
        text(p, 1, 22, 43, v->log_saved ? GREEN : RED, v->log_saved ? "Saved to SD" : "Report may be incomplete");
        for (unsigned i = 0; i < 160 && v->log_path[i]; i += 32)
            text(p, 1, 22, 65+(int)(i/32)*14, WHITE, "%.32s", v->log_path+i);
        text(p, 1, 12, 157, MUTED, "No ROM dump was saved.");
    } else if (v->page == 3) {
        heading(p, "REFERENCE SOURCE", 4);
        text(p, 1, 12, 35, WHITE, "%.36s", v->reference_source[0] ? v->reference_source : "No reference loaded.");
        text(p, 1, 12, 51, CYAN, v->reference_database ? "Version: %.26s" : "Per-game reference: %s",
            v->reference_database ? v->reference_version : reference);
        text(p, 1, 12, 74, WHITE, "%.36s", v->reference_title[0] ? v->reference_title : "Reference entry not established.");
        if (strlen(v->reference_title)>36) text(p, 1, 12, 88, WHITE, "%.36s", v->reference_title+36);
        text(p, 1, 12, 108, MUTED, "%.36s", v->reference_url[0] ? v->reference_url : "Source supplied by user.");
        if (v->reference_database) {
            text(p, 1, 12, 127, MUTED, "Original DAT SHA-256:");
            text(p, 1, 12, 142, WHITE, "%.32s", v->reference_dat_sha256);
            text(p, 1, 12, 156, WHITE, "%.32s", v->reference_dat_sha256+32);
        }
    } else {
        heading(p, "RESULT SUMMARY", 1);
        panel(p, 1, 12, 34, 296, 48, PANEL);
        text(p, 1, 22, 42, CYAN, "REFERENCE");
        const char *ref = "No reference compared";
        uint32_t color = AMBER;
        if (r->status == CV_DATABASE_MATCH) { ref = "Catalog SHA-1 + size matched"; color = GREEN; }
        else if (r->status == CV_REFERENCE_MATCH) { ref = "Supplied SHA-1 matched"; color = GREEN; }
        else if (r->status == CV_REFERENCE_MISMATCH) { ref = "Supplied reference differs"; color = RED; }
        else if (v->reference_database) ref = r->status == CV_CONSISTENT ? "No exact database match" : "Database not compared";
        else if (v->reference_present) ref = "Reference not compared";
        text(p, 1, 22, 61, color, "%s", ref);
        panel(p, 1, 12, 90, 296, 46, PANEL);
        text(p, 1, 22, 98, BLUE, "ROM READS");
        text(p, 1, 22, 116, WHITE, r->status == CV_INCONSISTENT ? "Two reads differed" :
            reads_agree(r->status) ? "Two complete reads agree" : "Comparison not completed");
        panel(p, 1, 12, 144, 296, 24, v->log_saved ? GREEN_BG : RED_BG);
        panel(p, 1, 12, 144, 4, 24, v->log_saved ? GREEN : RED);
        text(p, 1, 24, 151, v->log_saved ? GREEN : RED, v->log_saved ? "SD report saved" : "SD REPORT INCOMPLETE");
    }
}
static void settings_page(const CvPainter *p, const CvView *v) {
    const CvSettings *s = v->settings;
    static const char *brightness[] = {"Auto", "Low", "Medium", "High", "Maximum"};
    static const char *reference[] = {"Auto", "Require", "Ignore"};
    static const char *pages[] = {"Summary", "SHA-1", "SD report"};
    static const char *labels[] = {"Refresh", "Brightness", "Reference", "Result page"};
    heading(p, "SESSION SETTINGS", 0);
    for (unsigned i = 0; i < 4; ++i) {
        const int y = 38+(int)i*33;
        panel(p, 1, 12, y, 296, 27, i == v->selected_setting ? FOOTER : PANEL);
        if (i == v->selected_setting) panel(p, 1, 12, y, 4, 27, CYAN);
        text(p, 1, 24, y+8, i == v->selected_setting ? CYAN : WHITE, "%s", labels[i]);
        if (!i) text(p, 1, 186, y+8, WHITE, "%u ms", cv_refresh_ms(s));
        else text(p, 1, 186, y+8, WHITE, "%s", i == 1 ? brightness[s->brightness<5?s->brightness:2] :
            i == 2 ? reference[s->reference<3?s->reference:0] : pages[s->result_page<3?s->result_page:0]);
    }
}
void cv_draw(const CvPainter *p, const CvView *v) {
    if (!p || !p->rect || !p->text || !v || !v->result) return;
    panel(p, 0, 0, 0, 400, 240, BG);
    panel(p, 1, 0, 0, 320, 240, BG);
    const int result = v->stage == CV_STAGE_RESULT || (v->stage == CV_STAGE_SETTINGS &&
        v->result->status != CV_READY && v->result->status != CV_RUNNING);
    top(p, v, result);
    const char *reference = v->reference_database ? "database" : v->reference_present ? "sidecar" : "absent";
    if (v->stage == CV_STAGE_RESULT) details(p, v, reference);
    else if (v->stage == CV_STAGE_SETTINGS && v->settings) settings_page(p, v);
    else if (v->stage == CV_STAGE_SCANNING) {
        heading(p, "CHECKING CARTRIDGE", 0);
        panel(p, 1, 12, 36, 296, 60, PANEL);
        text(p, 1, 24, 48, CYAN, "PASS %u OF 2", v->pass);
        text(p, 1, 24, 69, WHITE, v->pass == 1 ? "Collecting region baseline" : "Comparing logical regions");
        text(p, 1, 12, 113, MUTED, "Reference: %s", reference);
        text(p, 1, 12, 135, WHITE, "Keep cartridge inserted.");
        text(p, 1, 12, 155, MUTED, "No cartridge or save writes.");
    } else {
        const int failed = v->stage == CV_STAGE_ERROR;
        heading(p, failed ? "CANNOT START" : "READY TO CHECK", 0);
        panel(p, 1, 12, 36, 296, 68, failed ? RED_BG : PANEL);
        panel(p, 1, 12, 36, 4, 68, failed ? RED : CYAN);
        if (failed) {
            text(p, 1, 24, 49, RED, "Check setup before scanning");
            text(p, 1, 24, 70, WHITE, "%.34s", v->detail);
            if (strlen(v->detail)>34) text(p, 1, 24, 84, WHITE, "%.34s", v->detail+34);
        } else {
            text(p, 1, 24, 49, CYAN, "FULL ROM CONSISTENCY");
            text(p, 1, 24, 70, WHITE, "2 passes / SHA-1 + region CRC32");
            text(p, 1, 24, 87, MUTED, "Reference: %s", reference);
        }
        text(p, 1, 12, 122, WHITE, "%.36s", failed ? "Correct the message, then retry." : v->detail);
        text(p, 1, 12, 144, MUTED, "Reports: gm9/out/dscheck/");
    }
    controls(p, v);
}
