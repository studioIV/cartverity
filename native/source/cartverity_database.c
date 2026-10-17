/* SPDX-License-Identifier: MIT */
#include "cartverity_database.h"
#include "cartverity_scan.h"
#include <string.h>
static uint32_t read32(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static int clean_string(const uint8_t *p, unsigned size) {
    unsigned i = 0;
    if (!p[0]) return 0;
    while (i < size && p[i]) { if (p[i] < 32 || p[i] > 126) return 0; ++i; }
    if (i == size) return 0;
    while (i < size) if (p[i++]) return 0;
    return 1;
}
static int key_compare(const uint8_t *a, const uint8_t *b) {
    const int order = memcmp(a, b, 20);
    if (order) return order;
    const uint32_t as = read32(a+20), bs = read32(b+20);
    return as < bs ? -1 : as != bs;
}
int cv_db_validate(const uint8_t *data, size_t size, CvDatabase *out) {
    if (!out) return 0;
    memset(out, 0, sizeof(*out));
    if (!data || size < CV_DB_HEADER || size > CV_DB_MAX_SIZE || memcmp(data, "CVDB0001", 8)) return 0;
    const uint32_t count = read32(data+8);
    if (!count || count > CV_DB_MAX_RECORDS || read32(data+12) != CV_DB_RECORD || read32(data+20) ||
        size != CV_DB_HEADER + (size_t)count * CV_DB_RECORD || !clean_string(data+24, 80) ||
        !clean_string(data+104, 48) || !clean_string(data+184, 72)) return 0;
    const uint8_t zero[4] = {0};
    uint32_t crc = cv_crc32(0xFFFFFFFFu, data, 16);
    crc = cv_crc32(crc, zero, 4);
    crc = cv_crc32(crc, data+20, (uint32_t)size-20) ^ 0xFFFFFFFFu;
    if (crc != read32(data+16)) return 0;
    for (uint32_t i = 0; i < count; ++i) {
        const uint8_t *record = data + CV_DB_HEADER + i*CV_DB_RECORD;
        const uint32_t length = read32(record+20);
        if (length < 512 || length > CV_MAX_ROM || (length & (length-1)) ||
            !clean_string(record+24, 128) || (i && key_compare(record-CV_DB_RECORD, record) >= 0)) return 0;
        for (unsigned j = 152; j < 160; ++j) if (record[j]) return 0;
    }
    out->data = data; out->count = count;
    out->source = (const char*)data+24; out->version = (const char*)data+104;
    out->dat_sha256 = data+152; out->url = (const char*)data+184;
    return 1;
}
const char *cv_db_find(const CvDatabase *db, const uint8_t digest[20], uint32_t size) {
    if (!db || !db->data || !digest) return NULL;
    uint32_t low = 0, high = db->count;
    while (low < high) {
        const uint32_t mid = low + (high-low)/2;
        const uint8_t *record = db->data + CV_DB_HEADER + mid*CV_DB_RECORD;
        int order = memcmp(digest, record, 20);
        if (!order) { const uint32_t length = read32(record+20); order = size < length ? -1 : size != length; }
        if (order > 0) low = mid+1;
        else if (order < 0) high = mid;
        else return (const char*)record+24;
    }
    return NULL;
}
