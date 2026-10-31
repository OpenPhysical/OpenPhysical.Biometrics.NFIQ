/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef OP_NFIQ1_H
#define OP_NFIQ1_H
#include <stdint.h>
#ifdef _WIN32
#define OP_EXPORT __declspec(dllexport)
#else
#define OP_EXPORT __attribute__((visibility("default")))
#endif
/* ABI version is independent of the package version. All buffers remain
 * caller-owned. Status 0: assessed, 1: invalid input, 2: allocation failure, 3:
 * native failure. Assessment status 1/2 carries a valid quality class 5
 * (empty/too few minutiae). */
OP_EXPORT int32_t op_nfiq1_abi_version(void);
OP_EXPORT int32_t op_nfiq1_assess(const uint8_t *pixels, int32_t length,
                                  int32_t width, int32_t height, int32_t dpi,
                                  int32_t *quality, float *confidence,
                                  int32_t *assessment, int32_t *error);
#ifdef OP_NBIS_TESTING
OP_EXPORT void op_nfiq1_test_fail_after(int count);
/* Counters exist only in test builds, outside the release ABI. */
OP_EXPORT int32_t op_nfiq1_test_allocation_attempts(void);
OP_EXPORT int32_t op_nfiq1_test_live_allocations(void);
#endif
#endif
