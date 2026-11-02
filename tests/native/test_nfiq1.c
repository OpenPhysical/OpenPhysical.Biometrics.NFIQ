/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "munit.h"
#include "op_nfiq1.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static MunitResult blank(const MunitParameter p[], void *d) {
  (void)p;
  (void)d;
  uint8_t pixels[128 * 128];
  char path[2048];
  snprintf(path, sizeof path, "%s/negative/featureless.gray8", NFIQ_FIXTURES);
  FILE *image = fopen(path, "rb");
  munit_assert_not_null(image);
  munit_assert_size(fread(pixels, 1, sizeof pixels, image), ==, sizeof pixels);
  fclose(image);
  int32_t q, s, e;
  float c;
  munit_assert_int(
      op_nfiq1_assess(pixels, sizeof pixels, 128, 128, 500, &q, &c, &s, &e), ==,
      0);
  munit_assert_int(q, ==, 5);
  munit_assert_int(s, ==, 2);
  munit_assert_float(c, ==, 1.0f);
  return MUNIT_OK;
}
static MunitResult invalid(const MunitParameter p[], void *d) {
  (void)p;
  (void)d;
  int32_t q, s, e;
  float c;
  uint8_t b = 0;
  const int invalid_dimensions[][2] = {
      {63, 64}, {64, 63}, {0, 64}, {64, 0}, {-1, 64}, {64, -1},
      {2049, 64}, {64, 2049}, {INT32_MAX, INT32_MAX}, {65536, 65536}};
  for (size_t index = 0; index < sizeof invalid_dimensions / sizeof invalid_dimensions[0]; index++) {
    q = s = e = -1;
    c = -1;
    munit_assert_int(op_nfiq1_assess(&b, 1, invalid_dimensions[index][0],
                                   invalid_dimensions[index][1], 500, &q, &c, &s, &e), ==, 1);
    munit_assert_int(q, ==, 0);
    munit_assert_int(s, ==, 0);
    munit_assert_int(e, ==, 0);
    munit_assert_float(c, ==, 0);
  }
  munit_assert_int(op_nfiq1_assess(&b, 4096, 64, 64, 0, &q, &c, &s, &e), ==, 1);
  munit_assert_int(op_nfiq1_assess(&b, 4096, 64, 64, 1000, &q, &c, &s, &e), ==, 1);
  munit_assert_int(op_nfiq1_assess(NULL, 4096, 64, 64, 500, &q, &c, &s, &e), ==, 1);
  munit_assert_int(op_nfiq1_assess(&b, INT32_MAX, 2048, 2048, 500, &q, &c, &s, &e), ==, 1);
  char path[2048];
  snprintf(path, sizeof path, "%s/negative/truncated.gray8", NFIQ_FIXTURES);
  FILE *image = fopen(path, "rb");
  munit_assert_not_null(image);
  uint8_t truncated[2];
  munit_assert_size(fread(truncated, 1, sizeof truncated, image), ==,
                    sizeof truncated);
  fclose(image);
  munit_assert_int(op_nfiq1_assess(truncated, sizeof truncated, 128, 128, 500,
                                   &q, &c, &s, &e),
                   ==, 1);
  return MUNIT_OK;
}
static MunitResult reference(const MunitParameter p[], void *d) {
  (void)p;
  (void)d;
  char path[2048], name[128];
  int expected_status, expected_quality;
  float expected_confidence;
  snprintf(path, sizeof path, "%s/nfiq1-reference.tsv", NFIQ_FIXTURES);
  FILE *cases = fopen(path, "r");
  munit_assert_not_null(cases);
  unsigned char *pixels = malloc(512 * 512);
  munit_assert_not_null(pixels);
  while (fscanf(cases, "%127s %d %d %f", name, &expected_status,
                &expected_quality, &expected_confidence) == 4) {
    snprintf(path, sizeof path, "%s/%s", NFIQ_FIXTURES, name);
    FILE *image = fopen(path, "rb");
    munit_assert_not_null(image);
    munit_assert_size(fread(pixels, 1, 512 * 512, image), ==, 512 * 512);
    fclose(image);
    int32_t q, status, error;
    float confidence;
    munit_assert_int(op_nfiq1_assess(pixels, 512 * 512, 512, 512, 500, &q,
                                     &confidence, &status, &error),
                     ==, 0);
    munit_assert_int(q, ==, expected_quality);
    munit_assert_int(status, ==, expected_status);
    munit_assert_double(fabs((double)confidence - expected_confidence), <,
                        0.000001);
  }
  fclose(cases);
  snprintf(path, sizeof path, "%s/nfiq1-release.tsv", NFIQ_FIXTURES);
  cases = fopen(path, "r");
  munit_assert_not_null(cases);
  int width, height;
  while (fscanf(cases, "%127s %d %d %d %d %f", name, &width, &height,
                &expected_status, &expected_quality,
                &expected_confidence) == 6) {
    free(pixels);
    pixels = malloc((size_t)width * height);
    munit_assert_not_null(pixels);
    snprintf(path, sizeof path, "%s/%s", NFIQ_FIXTURES, name);
    FILE *image = fopen(path, "rb");
    munit_assert_not_null(image);
    munit_assert_size(fread(pixels, 1, (size_t)width * height, image), ==,
                      ((size_t)width * height));
    fclose(image);
    int32_t q, status, error;
    float confidence;
    munit_assert_int(op_nfiq1_assess(pixels, (size_t)width * height, width, height, 500,
                                     &q, &confidence, &status, &error),
                     ==, 0);
    munit_assert_int(q, ==, expected_quality);
    munit_assert_int(status, ==, expected_status);
    munit_assert_double(fabs((double)confidence - expected_confidence), <,
                        0.000001);
  }
  free(pixels);
  fclose(cases);
  return MUNIT_OK;
}
static MunitResult allocation(const MunitParameter p[], void *d) {
  (void)p;
  (void)d;
  char path[2048];
  snprintf(path, sizeof path, "%s/f0005_03.gray8", NFIQ_FIXTURES);
  FILE *image = fopen(path, "rb");
  munit_assert_not_null(image);
  uint8_t *pixels = munit_malloc(512 * 512);
  munit_assert_size(fread(pixels, 1, 512 * 512, image), ==, 512 * 512);
  fclose(image);
  int32_t quality, assessment, error;
  float confidence;
  op_nfiq1_test_fail_after(-1);
  munit_assert_int(op_nfiq1_assess(pixels, 512 * 512, 512, 512, 500,
                                 &quality, &confidence, &assessment, &error), ==, 0);
  munit_assert_int(assessment, ==, 0);
  const int total = op_nfiq1_test_allocation_attempts();
  munit_assert_int(total, >, 1024);
  const int expected_quality = quality;
  const int expected_assessment = assessment;
  const float expected_confidence = confidence;
  /* This real capture reaches the classifier. Cover early, middle, and final
   * allocation requests without hard-coding a compiler-specific allocation count. */
  const int failures[] = {0, 1, 8, 32, 128, 1024, total / 2, total - 1};
  for (size_t index = 0; index < sizeof failures / sizeof failures[0]; index++) {
    quality = assessment = error = -1;
    confidence = -1;
    op_nfiq1_test_fail_after(failures[index]);
    munit_assert_int(op_nfiq1_assess(pixels, 512 * 512, 512, 512, 500,
                                   &quality, &confidence, &assessment, &error), ==, 2);
    munit_assert_int(error, ==, -10000);
    munit_assert_int(quality, ==, 0);
    munit_assert_int(assessment, ==, 0);
    munit_assert_float(confidence, ==, 0);
    munit_assert_int(op_nfiq1_test_allocation_attempts(), ==, failures[index] + 1);
    munit_assert_int(op_nfiq1_test_live_allocations(), ==, 0);

    /* A failure must leave the next complete classification unchanged. */
    op_nfiq1_test_fail_after(-1);
    munit_assert_int(op_nfiq1_assess(pixels, 512 * 512, 512, 512, 500,
                                   &quality, &confidence, &assessment, &error), ==, 0);
    munit_assert_int(quality, ==, expected_quality);
    munit_assert_int(assessment, ==, expected_assessment);
    munit_assert_float(confidence, ==, expected_confidence);
    munit_assert_int(error, ==, 0);
    munit_assert_int(op_nfiq1_test_live_allocations(), ==, 0);
  }
  /* The first failure index beyond all requests must complete successfully. */
  op_nfiq1_test_fail_after(total);
  munit_assert_int(op_nfiq1_assess(pixels, 512 * 512, 512, 512, 500,
                                 &quality, &confidence, &assessment, &error), ==, 0);
  munit_assert_int(op_nfiq1_test_allocation_attempts(), ==, total);
  munit_assert_int(quality, ==, expected_quality);
  munit_assert_int(assessment, ==, expected_assessment);
  munit_assert_float(confidence, ==, expected_confidence);
  munit_assert_int(error, ==, 0);
  munit_assert_int(op_nfiq1_test_live_allocations(), ==, 0);
  op_nfiq1_test_fail_after(-1);
  free(pixels);
  return MUNIT_OK;
}
static MunitTest tests[] = {
    {"/allocation", allocation, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {"/reference", reference, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {"/blank", blank, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {"/invalid", invalid, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {NULL, NULL, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL}};
int main(int argc, char **argv) {
  MunitSuite suite = {"/nfiq1", tests, NULL, 1, MUNIT_SUITE_OPTION_NONE};
  return munit_suite_main(&suite, NULL, argc, argv);
}
