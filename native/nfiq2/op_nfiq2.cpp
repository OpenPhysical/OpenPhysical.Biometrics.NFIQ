/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "op_nfiq2.h"
#include <atomic>
#include <mutex>
#include <new>
#include <nfiq2.hpp>
#include <opencv2/core.hpp>
#ifdef OP_NFIQ2_TESTING
static std::atomic<bool> fail_feature_allocation{false};
extern "C" OP_EXPORT void op_nfiq2_test_fail_feature_allocation(void) {
  fail_feature_allocation.store(true);
}
extern "C" void op_nfiq2_test_feature_allocation(void) {
  if (fail_feature_allocation.exchange(false))
    throw std::bad_alloc();
}
#endif
struct context {
  NFIQ2::Algorithm model;
  std::mutex mutex;
};
int32_t op_nfiq2_abi_version(void) { return 1; }
int32_t op_nfiq2_create(void **out, int32_t *error) {
  if (!out || !error)
    return 1;
  *out = nullptr;
  *error = -1;
  try {
    *out = new context();
    *error = 0;
    return 0;
  } catch (const std::bad_alloc &) {
    return 2;
  } catch (const NFIQ2::Exception &e) {
    *error = static_cast<int32_t>(e.getErrorCode());
    return e.getErrorCode() == NFIQ2::ErrorCode::UnknownError ? 5 : 4;
  } catch (...) {
    return 5;
  }
}
void op_nfiq2_destroy(void *p) { delete static_cast<context *>(p); }
int32_t op_nfiq2_assess(void *p, const uint8_t *pixels, int32_t length,
                        int32_t width, int32_t height, int32_t dpi,
                        int32_t finger, int32_t *score, int32_t *error) {
  if (!score || !error)
    return 1;
  *score = 0;
  *error = -1;
  if (!p || !pixels || width < 64 || height < 64 || width > 2048 ||
      height > 2048 ||
      static_cast<int64_t>(length) != static_cast<int64_t>(width) * height ||
      dpi != 500 || finger < 0 || finger > 10)
    return 1;
  try {
    auto &c = *static_cast<context *>(p);
    std::lock_guard<std::mutex> guard(c.mutex);
    NFIQ2::FingerprintImageData image(pixels, length, width, height,
                                      static_cast<uint8_t>(finger), 500);
    auto value = c.model.computeUnifiedQualityScore(image);
    if (value > 100)
      return 5;
    *score = static_cast<int32_t>(value);
    *error = 0;
    return 0;
  } catch (const std::bad_alloc &) {
    return 2;
  } catch (const NFIQ2::Exception &e) {
    *error = static_cast<int32_t>(e.getErrorCode());
    return e.getErrorCode() == NFIQ2::ErrorCode::UnknownError ? 5 : 3;
  } catch (const cv::Exception &) {
    return 5;
  } catch (...) {
    return 5;
  }
}
