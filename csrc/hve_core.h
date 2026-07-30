/*
 * hve_core.h — HVE-720 BASE portable C11 reference core.
 *
 * Bijection:  E(theta, s, tau, phi) = (((theta * 2 + s) * 5 + tau) * 9 + phi)
 * Group:      G = Z_360 x Z_2 x Z_5 x Z_9
 * |G| = 32,400 valid states in 15-bit words (368 reserved).
 *
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Charles de Paula Eugenio
 */

#ifndef HVE_CORE_H
#define HVE_CORE_H

#include <stdint.h>
#include <stdbool.h>

/* ── Constants ─────────────────────────────────────────────────────────── */

#define HVE_THETA_CARD  360
#define HVE_S_CARD      2
#define HVE_TAU_CARD    5
#define HVE_PHI_CARD    9
#define HVE_BASE_CARD   (HVE_THETA_CARD * HVE_S_CARD * HVE_TAU_CARD * HVE_PHI_CARD)  /* 32400 */
#define HVE_WORD_BITS   15
#define HVE_WORD_CAP    (1u << HVE_WORD_BITS)  /* 32768 */
#define HVE_RESERVED    (HVE_WORD_CAP - HVE_BASE_CARD)  /* 368 */

/* ── Types ─────────────────────────────────────────────────────────────── */

typedef struct {
    uint16_t theta;   /* [0, 359] */
    uint8_t  s;       /* {0, 1}   */
    uint8_t  tau;     /* [0, 4]   */
    uint8_t  phi;     /* [0, 8]   */
} hve_state_t;

typedef enum {
    HVE_OK = 0,
    HVE_ERR_THETA,
    HVE_ERR_S,
    HVE_ERR_TAU,
    HVE_ERR_PHI,
    HVE_ERR_INDEX,
    HVE_ERR_RESERVED,
} hve_error_t;

/* ── Validation ────────────────────────────────────────────────────────── */

static inline hve_error_t hve_validate_state(const hve_state_t *st)
{
    if (st->theta >= HVE_THETA_CARD) return HVE_ERR_THETA;
    if (st->s     >= HVE_S_CARD)     return HVE_ERR_S;
    if (st->tau   >= HVE_TAU_CARD)   return HVE_ERR_TAU;
    if (st->phi   >= HVE_PHI_CARD)   return HVE_ERR_PHI;
    return HVE_OK;
}

static inline hve_error_t hve_validate_index(uint16_t index)
{
    if (index >= HVE_WORD_CAP)  return HVE_ERR_INDEX;
    if (index >= HVE_BASE_CARD) return HVE_ERR_RESERVED;
    return HVE_OK;
}

/* ── Bijection ─────────────────────────────────────────────────────────── */

static inline hve_error_t hve_encode(const hve_state_t *st, uint16_t *out)
{
    hve_error_t err = hve_validate_state(st);
    if (err != HVE_OK) return err;
    *out = (uint16_t)(((st->theta * HVE_S_CARD + st->s) * HVE_TAU_CARD + st->tau)
                      * HVE_PHI_CARD + st->phi);
    return HVE_OK;
}

static inline hve_error_t hve_decode(uint16_t index, hve_state_t *out)
{
    hve_error_t err = hve_validate_index(index);
    if (err != HVE_OK) return err;
    uint16_t q;
    out->phi   = (uint8_t)(index % HVE_PHI_CARD);
    q          = index / HVE_PHI_CARD;
    out->tau   = (uint8_t)(q % HVE_TAU_CARD);
    q          = q / HVE_TAU_CARD;
    out->s     = (uint8_t)(q % HVE_S_CARD);
    out->theta = (uint16_t)(q / HVE_S_CARD);
    return HVE_OK;
}

/* ── Group operations ──────────────────────────────────────────────────── */

static inline hve_state_t hve_identity(void)
{
    hve_state_t e = {0, 0, 0, 0};
    return e;
}

static inline hve_state_t hve_add(hve_state_t a, hve_state_t b)
{
    hve_state_t r;
    r.theta = (a.theta + b.theta) % HVE_THETA_CARD;
    r.s     = (a.s     + b.s)     % HVE_S_CARD;
    r.tau   = (a.tau   + b.tau)   % HVE_TAU_CARD;
    r.phi   = (a.phi   + b.phi)   % HVE_PHI_CARD;
    return r;
}

static inline hve_state_t hve_inverse(hve_state_t a)
{
    hve_state_t r;
    r.theta = (HVE_THETA_CARD - a.theta) % HVE_THETA_CARD;
    r.s     = (HVE_S_CARD     - a.s)     % HVE_S_CARD;
    r.tau   = (HVE_TAU_CARD   - a.tau)   % HVE_TAU_CARD;
    r.phi   = (HVE_PHI_CARD   - a.phi)   % HVE_PHI_CARD;
    return r;
}

/* ── Circular distance on C_360 ────────────────────────────────────────── */

static inline uint16_t hve_circular_distance(uint16_t t1, uint16_t t2)
{
    uint16_t d = (t1 > t2) ? (t1 - t2) : (t2 - t1);
    return (d <= 180) ? d : (360 - d);
}

#endif /* HVE_CORE_H */
