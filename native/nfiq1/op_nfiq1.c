/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "op_nfiq1.h"
#include "op_alloc.h"
#ifdef _WIN32
#include <windows.h>
/* NBIS uses IGNORE for a minutia-processing flag. */
#undef IGNORE
static SRWLOCK mutex = SRWLOCK_INIT;
#define LOCK() AcquireSRWLockExclusive(&mutex)
#define UNLOCK() ReleaseSRWLockExclusive(&mutex)
#else
#include <pthread.h>
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
#define LOCK() pthread_mutex_lock(&mutex)
#define UNLOCK() pthread_mutex_unlock(&mutex)
#endif
#include <nfiq.h>
char *get_progname(void) { return "OpenPhysical.Biometrics.NFIQ1"; }
/* Legacy MLP functions report fatal conditions. The arena reclaims all owned
 * allocations at the C boundary, including objects left by partial failures. */
void fatalerr(char *a, char *b, char *c) {
  (void)a;
  (void)b;
  (void)c;
  longjmp(op_allocation_failure, 1);
}
void syserr(char *a, char *b, char *c) {
  (void)a;
  (void)b;
  (void)c;
  longjmp(op_allocation_failure, 1);
}
int32_t op_nfiq1_abi_version(void) { return 1; }
int32_t op_nfiq1_assess(const uint8_t *pixels, int32_t length, int32_t width,
                        int32_t height, int32_t dpi, int32_t *quality,
                        float *confidence, int32_t *assessment,
                        int32_t *error) {
  int flag = 0, ret;
  unsigned char *copy;
  void *pending;
  if (!quality || !confidence || !assessment || !error)
    return 1;
  *quality = 0;
  *confidence = 0;
  *assessment = 0;
  *error = 0;
  if (!pixels || width < 64 || height < 64 || width > 2048 || height > 2048 ||
      length != width * height || dpi != 500)
    return 1;
  LOCK();
  if (setjmp(op_allocation_failure)) {
    *quality = 0;
    *confidence = 0;
    *assessment = 0;
    *error = -10000;
    pending = op_detach_allocations();
    UNLOCK();
    op_release_detached(pending);
    return 2;
  }
  copy = malloc((size_t)length);
  memcpy(copy, pixels, (size_t)length);
  ret = comp_nfiq(quality, confidence, copy, width, height, 8, dpi, &flag);
  pending = op_detach_allocations();
  UNLOCK();
  op_release_detached(pending);
  if (ret < 0) {
    *error = ret;
    *quality = 0;
    *confidence = 0;
    return 3;
  }
  *assessment = ret;
  return 0;
}
#ifdef OP_NBIS_TESTING
void op_nfiq1_test_fail_after(int count) {
  LOCK();
  op_fail_allocation_after(count);
  UNLOCK();
}
int32_t op_nfiq1_test_allocation_attempts(void) {
  LOCK();
  int count = op_allocation_attempts();
  UNLOCK();
  return count;
}
int32_t op_nfiq1_test_live_allocations(void) {
  LOCK();
  int count = op_live_allocations();
  UNLOCK();
  return count;
}
#endif
