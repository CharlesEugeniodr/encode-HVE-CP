/*
 * hve_test.c — Exhaustive test for the HVE-720 C11 reference core.
 *
 * Tests:
 *   1. Exhaustive round-trip of all 32,400 valid states.
 *   2. Rejection of all 368 reserved 15-bit words.
 *   3. Group inverse yields identity for sample states.
 *   4. Circular distance wrap-around.
 *
 * Build:  cc -std=c11 -Wall -Wextra -Wpedantic -O2 -o hve_test hve_test.c
 * Run:    ./hve_test
 *
 * SPDX-License-Identifier: MIT
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hve_core.h"

static int failures = 0;

#define CHECK(cond, fmt, ...)                                  \
    do {                                                       \
        if (!(cond)) {                                         \
            fprintf(stderr, "FAIL: " fmt "\n", ##__VA_ARGS__); \
            failures++;                                        \
        }                                                      \
    } while (0)

static void test_exhaustive_roundtrip(void)
{
    /* Verify perfect round-trip for all 32,400 valid states. */
    int count = 0;
    uint8_t seen[HVE_BASE_CARD];
    memset(seen, 0, sizeof(seen));

    for (int theta = 0; theta < HVE_THETA_CARD; theta++) {
        for (int s = 0; s < HVE_S_CARD; s++) {
            for (int tau = 0; tau < HVE_TAU_CARD; tau++) {
                for (int phi = 0; phi < HVE_PHI_CARD; phi++) {
                    hve_state_t st = {
                        (uint16_t)theta, (uint8_t)s,
                        (uint8_t)tau, (uint8_t)phi
                    };
                    uint16_t idx;
                    hve_error_t err = hve_encode(&st, &idx);
                    CHECK(err == HVE_OK,
                          "encode(%d,%d,%d,%d) returned %d",
                          theta, s, tau, phi, err);
                    CHECK(idx < HVE_BASE_CARD,
                          "index %u out of range", idx);
                    CHECK(!seen[idx],
                          "duplicate index %u", idx);
                    seen[idx] = 1;

                    hve_state_t dec;
                    err = hve_decode(idx, &dec);
                    CHECK(err == HVE_OK,
                          "decode(%u) returned %d", idx, err);
                    CHECK(dec.theta == st.theta && dec.s == st.s &&
                          dec.tau == st.tau && dec.phi == st.phi,
                          "roundtrip mismatch at index %u", idx);
                    count++;
                }
            }
        }
    }
    CHECK(count == HVE_BASE_CARD,
          "expected %d states, got %d", HVE_BASE_CARD, count);
    printf("  Exhaustive round-trip: %d / %d\n", count, HVE_BASE_CARD);
}

static void test_reserved_words(void)
{
    /* Verify all 368 reserved indices are rejected. */
    int rejected = 0;
    for (uint16_t idx = HVE_BASE_CARD; idx < HVE_WORD_CAP; idx++) {
        hve_state_t dec;
        hve_error_t err = hve_decode(idx, &dec);
        CHECK(err == HVE_ERR_RESERVED,
              "reserved index %u not rejected", idx);
        rejected++;
    }
    CHECK(rejected == HVE_RESERVED,
          "expected %d rejections, got %d", HVE_RESERVED, rejected);
    printf("  Reserved words rejected: %d / %d\n", rejected, HVE_RESERVED);
}

static void test_group_inverse(void)
{
    /* a + inverse(a) = identity for several states. */
    hve_state_t identity = hve_identity();
    hve_state_t samples[] = {
        {  0, 0, 0, 0},
        {180, 1, 2, 4},
        {359, 1, 4, 8},
        {  1, 0, 0, 0},
    };
    int n = (int)(sizeof(samples) / sizeof(samples[0]));
    for (int i = 0; i < n; i++) {
        hve_state_t inv = hve_inverse(samples[i]);
        hve_state_t sum = hve_add(samples[i], inv);
        CHECK(sum.theta == identity.theta && sum.s == identity.s &&
              sum.tau == identity.tau && sum.phi == identity.phi,
              "inverse failed for sample %d", i);
    }
    printf("  Group inverse: %d / %d\n", n, n);
}

static void test_circular_distance(void)
{
    CHECK(hve_circular_distance(359, 0) == 1,
          "d(359,0) != 1");
    CHECK(hve_circular_distance(0, 180) == 180,
          "d(0,180) != 180");
    CHECK(hve_circular_distance(90, 270) == 180,
          "d(90,270) != 180");
    CHECK(hve_circular_distance(0, 0) == 0,
          "d(0,0) != 0");
    printf("  Circular distance: 4 / 4\n");
}

int main(void)
{
    printf("HVE-720 C11 Reference Core — Exhaustive Test\n");
    printf("=============================================\n");
    test_exhaustive_roundtrip();
    test_reserved_words();
    test_group_inverse();
    test_circular_distance();
    printf("=============================================\n");
    if (failures == 0) {
        printf("ALL TESTS PASSED\n");
        return 0;
    }
    printf("FAILURES: %d\n", failures);
    return 1;
}
