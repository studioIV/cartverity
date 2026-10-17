/* SPDX-License-Identifier: MIT */
#ifndef CARTVERITY_DATABASE_H
#define CARTVERITY_DATABASE_H
#include <stdint.h>
#include <stddef.h>
#define CV_DB_HEADER 256u
#define CV_DB_RECORD 160u
#define CV_DB_MAX_RECORDS 30000u
#define CV_DB_MAX_SIZE (CV_DB_HEADER + CV_DB_RECORD * CV_DB_MAX_RECORDS)
typedef struct {
    const uint8_t *data;
    uint32_t count;
    const char *source, *version, *url;
    const uint8_t *dat_sha256;
} CvDatabase;
/* Buffers remain owned by caller. Validate once before any lookup. */
int cv_db_validate(const uint8_t *data, size_t size, CvDatabase *out);
const char *cv_db_find(const CvDatabase *db, const uint8_t digest[20], uint32_t size);
#endif
