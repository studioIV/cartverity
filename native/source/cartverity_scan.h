/* SPDX-License-Identifier: MIT */
#ifndef CARTVERITY_SCAN_H
#define CARTVERITY_SCAN_H
#include <stdint.h>
#include <stddef.h>

#define CV_BLOCK_SIZE 32768u
#define CV_REGION_SIZE 1048576u
#define CV_MAX_REGIONS 512u
#define CV_MAX_ROM (CV_REGION_SIZE * CV_MAX_REGIONS)

typedef enum {
    CV_READY, CV_RUNNING, CV_CONSISTENT, CV_REFERENCE_MATCH,
    CV_REFERENCE_MISMATCH, CV_INCONSISTENT, CV_CANCELLED,
    CV_READ_ERROR, CV_SHORT_READ, CV_INVALID
} CvStatus;

typedef struct {
    CvStatus status;
    uint32_t bytes[2];
    uint8_t complete[2];
    uint8_t digest[2][20];
    uint32_t regions_compared;
    uint32_t regions_changed;
    uint8_t changed[CV_MAX_REGIONS];
} CvResult;

typedef struct {
    void *context;
    int (*begin_pass)(void *, unsigned pass);
    /* Return the actual byte count, or a negative value for failure. */
    int (*read)(void *, uint32_t offset, uint8_t *, uint32_t size);
    void (*hash_begin)(void *);
    void (*hash_update)(void *, const uint8_t *, uint32_t);
    void (*hash_end)(void *, uint8_t digest[20]);
    /* Called before reading, after each block, and at each completed pass.
       Returning zero cancels. A null callback disables cancellation. */
    int (*progress)(void *, unsigned pass, uint32_t completed, const CvResult *);
} CvCallbacks;

/* Two full sequential SHA-1 passes; no file or hardware writes in this core.
   Caller owns a suitably aligned CV_BLOCK_SIZE-byte buffer and callbacks.
   CRC32 compares 1 MiB logical regions, not physical storage cells. */
void cv_scan(uint32_t total, uint8_t *buffer, const uint8_t *reference,
             const CvCallbacks *callbacks, CvResult *result);
uint32_t cv_crc32(uint32_t state, const uint8_t *data, uint32_t length);

typedef struct {
    unsigned pass_percent;
    unsigned overall_percent;
    uint32_t overall_bytes;
    uint64_t bytes_per_second;
    uint64_t eta_seconds;
    int eta_known;
} CvMetrics;
CvMetrics cv_metrics(uint32_t total, unsigned pass, uint32_t completed,
                     uint64_t elapsed_ms);
const char *cv_status_name(CvStatus status);
#endif
