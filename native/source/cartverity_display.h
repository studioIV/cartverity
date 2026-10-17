/* SPDX-License-Identifier: MIT */
#ifndef CARTVERITY_DISPLAY_H
#define CARTVERITY_DISPLAY_H
#include <stdint.h>
#include <stddef.h>
/* Publish only changed RGB565 pixels. Drawing is completed in RAM first.
   Returns the number of hardware pixels written. Not a VBlank page flip. */
size_t cv_present(uint16_t *target, uint16_t *previous, const uint16_t *next,
                  size_t pixels, int force);
typedef struct {
    unsigned refresh, brightness, reference, result_page;
} CvSettings;
unsigned cv_refresh_ms(const CvSettings *settings);
int cv_brightness(const CvSettings *settings);
void cv_setting_change(CvSettings *settings, unsigned row, int direction);
#endif
