/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "munit.h"
#include "op_nfiq2.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
extern void op_nfiq2_test_fail_feature_allocation(void);
static MunitResult invalid(const MunitParameter p[], void *d) {
  (void)p;
  (void)d;
  int32_t score = 7, error;
  uint8_t pixels = 0;
  munit_assert_int(
      op_nfiq2_assess(NULL, &pixels, 1, 1, 1, 500, 0, &score, &error), ==, 1);
  munit_assert_int(score, ==, 0);
  return MUNIT_OK;
}
static MunitResult model(const MunitParameter p[], void *d) {
  (void)p;
  (void)d;
  void *ctx = NULL;
  int32_t error;
  munit_assert_int(op_nfiq2_create(&ctx, &error), ==, 0);
  munit_assert_not_null(ctx);
  op_nfiq2_destroy(ctx);
  return MUNIT_OK;
}
static MunitResult reference(const MunitParameter p[], void *d) {
  (void)p;
  (void)d;
  char path[2048], name[128];
  int expected_status, expected, expected_error;
  snprintf(path, sizeof path, "%s/nfiq2-reference.tsv", NFIQ_FIXTURES);
  FILE *cases = fopen(path, "r");
  munit_assert_not_null(cases);
  void *ctx = NULL;
  int32_t error;
  munit_assert_int(op_nfiq2_create(&ctx, &error), ==, 0);
  unsigned char *pixels = malloc(512 * 512);
  munit_assert_not_null(pixels);
  while (fscanf(cases, "%127s %d %d %d", name, &expected_status, &expected,
                &expected_error) == 4) {
    snprintf(path, sizeof path, "%s/%s", NFIQ_FIXTURES, name);
    FILE *image = fopen(path, "rb");
    munit_assert_not_null(image);
    munit_assert_size(fread(pixels, 1, 512 * 512, image), ==, 512 * 512);
    fclose(image);
    int32_t score;
    munit_assert_int(op_nfiq2_assess(ctx, pixels, 512 * 512, 512, 512, 500, 0,
                                     &score, &error),
                     ==, expected_status);
    munit_assert_int(score, ==, expected);
    munit_assert_int(error, ==, expected_error);
  }
  fclose(cases);
  snprintf(path, sizeof path, "%s/nfiq2-release.tsv", NFIQ_FIXTURES);
  cases = fopen(path, "r");
  munit_assert_not_null(cases);
  int width, height;
  while (fscanf(cases, "%127s %d %d %d %d %d", name, &width, &height,
                &expected_status, &expected, &expected_error) == 6) {
    snprintf(path, sizeof path, "%s/%s", NFIQ_FIXTURES, name);
    FILE *image = fopen(path, "rb");
    munit_assert_not_null(image);
    munit_assert_size(fread(pixels, 1, (size_t)width * height, image), ==,
                      ((size_t)width * height));
    fclose(image);
    int32_t score;
    munit_assert_int(op_nfiq2_assess(ctx, pixels, (size_t)width * height, width, height,
                                     500, 0, &score, &error),
                     ==, expected_status);
    munit_assert_int(score, ==, expected);
    munit_assert_int(error, ==, expected_error);
  }
  free(pixels);
  fclose(cases);
  op_nfiq2_destroy(ctx);
  return MUNIT_OK;
}
static MunitResult failure_classification(const MunitParameter p[], void *d) {
  (void)p; (void)d;
  void *ctx = NULL;
  int32_t error, score;
  uint8_t pixels[64 * 64] = {0};
  munit_assert_int(op_nfiq2_create(&ctx, &error), ==, 0);
  op_nfiq2_test_fail_feature_allocation();
  munit_assert_int(op_nfiq2_assess(ctx, pixels, sizeof pixels, 64, 64, 500, 0, &score, &error), ==, 5);
  munit_assert_int(error, ==, 0);
  munit_assert_int(score, ==, 0);
  munit_assert_int(op_nfiq2_assess(ctx, NULL, sizeof pixels, 64, 64, 500, 0, &score, &error), ==, 1);
  munit_assert_int(error, ==, -1);
  op_nfiq2_destroy(ctx);
  return MUNIT_OK;
}
static MunitResult argument_boundaries(const MunitParameter p[], void *d) {
  (void)p; (void)d;
  void *ctx = NULL;
  int32_t error, score;
  uint8_t pixels[64 * 64] = {0};
  const int bad[] = {-1, 0, 63, 2049, INT_MAX};
  munit_assert_int(op_nfiq2_create(&ctx, &error), ==, 0);
  for (size_t i = 0; i < sizeof bad / sizeof bad[0]; ++i) {
    munit_assert_int(op_nfiq2_assess(ctx, pixels, sizeof pixels, bad[i], 64, 500, 0, &score, &error), ==, 1);
    munit_assert_int(op_nfiq2_assess(ctx, pixels, sizeof pixels, 64, bad[i], 500, 0, &score, &error), ==, 1);
  }
  munit_assert_int(op_nfiq2_assess(ctx, pixels, INT_MAX, INT_MAX, INT_MAX, 500, 0, &score, &error), ==, 1);
  const int lengths[] = {-1, 0, 4095, 4097};
  for (size_t i = 0; i < sizeof lengths / sizeof lengths[0]; ++i)
    munit_assert_int(op_nfiq2_assess(ctx, pixels, lengths[i], 64, 64, 500, 0, &score, &error), ==, 1);
  const int fingers[] = {-1, 11, 255};
  for (size_t i = 0; i < sizeof fingers / sizeof fingers[0]; ++i)
    munit_assert_int(op_nfiq2_assess(ctx, pixels, sizeof pixels, 64, 64, 500, fingers[i], &score, &error), ==, 1);
  const int resolutions[] = {0, 499, 501};
  for (size_t i = 0; i < sizeof resolutions / sizeof resolutions[0]; ++i)
    munit_assert_int(op_nfiq2_assess(ctx, pixels, sizeof pixels, 64, 64, resolutions[i], 0, &score, &error), ==, 1);
  for (int finger = 0; finger <= 10; finger += 10) {
    munit_assert_int(op_nfiq2_assess(ctx, pixels, sizeof pixels, 64, 64, 500, finger, &score, &error), !=, 1);
  }
  op_nfiq2_destroy(ctx);
  return MUNIT_OK;
}
static MunitResult effective_dimensions(const MunitParameter p[], void *d) {
  (void)p; (void)d;
  void *ctx = NULL;
  int32_t error, score;
  munit_assert_int(op_nfiq2_create(&ctx, &error), ==, 0);
  uint8_t *pixels = malloc(2048 * 2048);
  munit_assert_not_null(pixels);
  const int sizes[][2] = {{800,1000}, {801,1000}, {800,1001}, {900,900}, {1024,600}, {2048,2048}, {64,64}, {100,100}};
  for (size_t i = 0; i < sizeof sizes / sizeof sizes[0]; ++i) {
    int width = sizes[i][0], height = sizes[i][1];
    for (int j = 0; j < (size_t)width * height; ++j) pixels[j] = j % 2 ? 64 : 0;
    int status = op_nfiq2_assess(ctx, pixels, (size_t)width * height, width, height, 500, 0, &score, &error);
    if (width > 800 || height > 1000) {
      munit_assert_int(status, ==, 3);
      munit_assert_int(error, ==, 14);
    } else {
      munit_assert_int(status, !=, 1);
      munit_assert_int(error, !=, 14);
    }
  }
  /* White padding is intentionally allowed before the upstream margin trim. */
  memset(pixels, 255, 1024 * 1200);
  char path[2048];
  snprintf(path, sizeof path, "%s/f0005_03.gray8", NFIQ_FIXTURES);
  FILE *image = fopen(path, "rb");
  munit_assert_not_null(image);
  for (int y = 0; y < 512; ++y)
    munit_assert_size(fread(pixels + (y + 300) * 1024 + 256, 1, 512, image), ==, 512);
  fclose(image);
  munit_assert_int(op_nfiq2_assess(ctx, pixels, 1024 * 1200, 1024, 1200, 500, 0, &score, &error), ==, 0);
  munit_assert_int(score, ==, 67);
  free(pixels);
  op_nfiq2_destroy(ctx);
  return MUNIT_OK;
}
static MunitTest tests[] = {
    {"/failure-classification", failure_classification, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {"/argument-boundaries", argument_boundaries, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {"/effective-dimensions", effective_dimensions, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {"/reference", reference, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {"/invalid", invalid, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {"/model", model, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL},
    {NULL, NULL, NULL, NULL, MUNIT_TEST_OPTION_NONE, NULL}};
int main(int argc, char **argv) {
  MunitSuite suite = {"/nfiq2", tests, NULL, 1, MUNIT_SUITE_OPTION_NONE};
  return munit_suite_main(&suite, NULL, argc, argv);
}
