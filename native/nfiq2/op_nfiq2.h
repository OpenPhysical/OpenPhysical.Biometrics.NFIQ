/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef OP_NFIQ2_H
#define OP_NFIQ2_H
#include <stdint.h>
#ifdef _WIN32
#define OP_EXPORT __declspec(dllexport)
#else
#define OP_EXPORT __attribute__((visibility("default")))
#endif
#ifdef __cplusplus
extern "C" {
#endif
/* Each context owns the pinned model. Callers keep all input/output buffers.
 * Status 0 success; 1 invalid input; 2 allocation; 3 algorithm; 4 model
 * failure; 5 unexpected native failure (including upstream UnknownError 0).
 * Error -1 means no upstream code; zero is the actual upstream UnknownError
 * when status is 5. Failure clears the score; success returns the actual
 * score from 0 through 100 and clears the error. Input dimensions
 * 64..2048 bound buffers; upstream trims white margins, then limits content
 * to 800 wide by 1000 high (status 3, error 14 if exceeded). */
OP_EXPORT int32_t op_nfiq2_abi_version(void);
OP_EXPORT int32_t op_nfiq2_create(void **context, int32_t *error);
OP_EXPORT void op_nfiq2_destroy(void *context);
OP_EXPORT int32_t op_nfiq2_assess(void *context, const uint8_t *pixels,
                                  int32_t length, int32_t width, int32_t height,
                                  int32_t dpi, int32_t finger, int32_t *score,
                                  int32_t *error);
#ifdef __cplusplus
}
#endif
#endif
