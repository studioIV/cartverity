/* SPDX-License-Identifier: MIT */
#ifndef CARTVERITY_UI_H
#define CARTVERITY_UI_H
#include "cartverity_scan.h"
#include "cartverity_display.h"

enum { CV_SCREEN_TOP, CV_SCREEN_BOTTOM };
enum { CV_STAGE_READY, CV_STAGE_SCANNING, CV_STAGE_RESULT, CV_STAGE_ERROR, CV_STAGE_SETTINGS };
typedef struct {
    void *context;
    void (*rect)(void *, int screen, int x, int y, int w, int h, uint32_t color);
    void (*text)(void *, int screen, int x, int y, uint32_t color, const char *text);
} CvPainter;

typedef struct {
    char name[40];
    char game_code[5];
    unsigned revision;
    uint32_t total;
    unsigned pass;
    uint32_t done;
    uint64_t elapsed_ms;
    unsigned stage;
    unsigned page;
    int reference_present;
    int log_saved;
    char detail[80];
    char log_path[192];
    const CvResult *result;
    const CvSettings *settings;
    unsigned selected_setting;
} CvView;

void cv_draw(const CvPainter *paint, const CvView *view);
#endif
