/* SPDX-License-Identifier: MIT */
#include "cartverity_scan.h"
#include <string.h>

uint32_t cv_crc32(uint32_t state, const uint8_t *data, uint32_t length) {
    /* Reflected IEEE CRC32; the caller initializes/finalizes with XOR FFFFFFFF.
       A nibble table keeps ROM/stack use small. SHA-1 is the final comparison. */
    static const uint32_t table[16] = {
        0x00000000u,0x1DB71064u,0x3B6E20C8u,0x26D930ACu,
        0x76DC4190u,0x6B6B51F4u,0x4DB26158u,0x5005713Cu,
        0xEDB88320u,0xF00F9344u,0xD6D6A3E8u,0xCB61B38Cu,
        0x9B64C2B0u,0x86D3D2D4u,0xA00AE278u,0xBDBDF21Cu
    };
    while (length--) {
        state ^= *data++;
        state = (state >> 4) ^ table[state & 15];
        state = (state >> 4) ^ table[state & 15];
    }
    return state;
}

void cv_scan(uint32_t total, uint8_t *buffer, const uint8_t *reference,
             const CvCallbacks *cb, CvResult *out) {
    if (!out) return;
    memset(out, 0, sizeof(*out));
    out->status = CV_INVALID;
    if (!total || total > CV_MAX_ROM || total % 512 || !buffer || !cb ||
        !cb->read || !cb->hash_begin || !cb->hash_update || !cb->hash_end)
        return;
    uint8_t expected[20];
    if (reference) memcpy(expected, reference, 20);
    uint32_t baseline[CV_MAX_REGIONS];
    out->status = CV_RUNNING;
    for (unsigned pass = 1; pass <= 2; ++pass) {
        if (cb->progress && !cb->progress(cb->context, pass, 0, out)) {
            out->status = CV_CANCELLED; return;
        }
        if (cb->begin_pass && !cb->begin_pass(cb->context, pass)) {
            out->status = CV_READ_ERROR; return;
        }
        cb->hash_begin(cb->context);
        uint32_t crc = 0xFFFFFFFFu;
        while (out->bytes[pass-1] < total) {
            const uint32_t offset = out->bytes[pass-1];
            const uint32_t count = total - offset < CV_BLOCK_SIZE
                ? total - offset : CV_BLOCK_SIZE;
            const int got = cb->read(cb->context, offset, buffer, count);
            if (got < 0) { out->status = CV_READ_ERROR; return; }
            if ((uint32_t)got != count) { out->status = CV_SHORT_READ; return; }
            cb->hash_update(cb->context, buffer, count);
            crc = cv_crc32(crc, buffer, count);
            out->bytes[pass-1] += count;
            const uint32_t done = out->bytes[pass-1];
            if (done % CV_REGION_SIZE == 0 || done == total) {
                const uint32_t index = (done - 1) / CV_REGION_SIZE;
                const uint32_t checksum = crc ^ 0xFFFFFFFFu;
                if (pass == 1) baseline[index] = checksum;
                else {
                    ++out->regions_compared;
                    if (baseline[index] != checksum) {
                        out->changed[index] = 1;
                        ++out->regions_changed;
                    }
                }
                crc = 0xFFFFFFFFu;
            }
            if (done == total) {
                cb->hash_end(cb->context, out->digest[pass-1]);
                out->complete[pass-1] = 1;
            }
            if (cb->progress && !cb->progress(cb->context, pass, done, out)) {
                out->status = CV_CANCELLED; return;
            }
        }
    }
    if (out->regions_changed || memcmp(out->digest[0], out->digest[1], 20))
        out->status = CV_INCONSISTENT;
    else if (!reference) out->status = CV_CONSISTENT;
    else if (memcmp(out->digest[0], expected, 20)) out->status = CV_REFERENCE_MISMATCH;
    else out->status = CV_REFERENCE_MATCH;
}

CvMetrics cv_metrics(uint32_t total, unsigned pass, uint32_t done, uint64_t ms) {
    CvMetrics m = {0};
    if (!total || total > CV_MAX_ROM || pass < 1 || pass > 2) return m;
    if (done > total) done = total;
    const uint64_t overall = (uint64_t)(pass - 1) * total + done;
    const uint64_t full = (uint64_t)total * 2;
    m.pass_percent = (unsigned)((uint64_t)done * 100 / total);
    m.overall_percent = (unsigned)(overall * 100 / full);
    m.overall_bytes = (uint32_t)overall;
    if (overall && ms) {
        m.bytes_per_second = overall * 1000 / ms;
        const uint64_t remaining = full - overall;
        if (ms <= UINT64_MAX / (remaining ? remaining : 1)) {
            const uint64_t remaining_ms = remaining * ms / overall;
            m.eta_seconds = remaining_ms / 1000 + (remaining_ms % 1000 != 0);
            m.eta_known = 1;
        }
    }
    return m;
}

const char *cv_status_name(CvStatus status) {
    static const char *names[] = {
        "READY", "RUNNING", "CONSISTENT_UNVERIFIED", "MATCHES_SUPPLIED_REFERENCE",
        "REFERENCE_MISMATCH", "INCONSISTENT_READS", "CANCELLED", "READ_ERROR",
        "SHORT_READ", "INVALID_INPUT", "MATCHES_DATABASE"
    };
    return (unsigned)status < sizeof(names)/sizeof(names[0]) ? names[status] : "UNKNOWN";
}
