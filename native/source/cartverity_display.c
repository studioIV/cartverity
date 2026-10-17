/* SPDX-License-Identifier: MIT */
#include "cartverity_display.h"
size_t cv_present(uint16_t *target, uint16_t *previous, const uint16_t *next,
                  size_t pixels, int force) {
    if (!target || !previous || !next) return 0;
    size_t written = 0;
    for (size_t i = 0; i < pixels; ++i) {
        if (force || previous[i] != next[i]) {
            target[i] = next[i];
            previous[i] = next[i];
            ++written;
        }
    }
    return written;
}
unsigned cv_refresh_ms(const CvSettings *s) {
    static const unsigned values[] = {100, 250, 500, 1000};
    return values[s && s->refresh < 4 ? s->refresh : 1];
}
int cv_brightness(const CvSettings *s) {
    static const int values[] = {-1, 40, 110, 170, 210};
    return values[s && s->brightness < 5 ? s->brightness : 2];
}
void cv_setting_change(CvSettings *s, unsigned row, int direction) {
    if (!s || row > 3 || !direction) return;
    unsigned *value = row == 0 ? &s->refresh : row == 1 ? &s->brightness
                    : row == 2 ? &s->reference : &s->result_page;
    unsigned count = row == 0 ? 4 : row == 1 ? 5 : 3;
    *value = (*value % count + (direction > 0 ? 1 : count-1)) % count;
}
