"""Exhaustive tests for hve.core — BASE bijection, group operations, validation."""

import pytest

from hve.core import (
    HVEState,
    HVEError,
    encode_base,
    decode_base,
    group_add,
    group_inverse,
    group_identity,
    validate_state,
    validate_index,
    sigma_to_s,
    s_to_sigma,
    BASE_CARDINALITY,
    THETA_CARDINALITY,
    S_CARDINALITY,
    TAU_CARDINALITY,
    PHI_CARDINALITY,
    RESERVED_WORDS,
    BASE_WORD_CAPACITY,
)


# ─── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_cardinality_product(self):
        assert BASE_CARDINALITY == 360 * 2 * 5 * 9

    def test_reserved_words(self):
        assert BASE_WORD_CAPACITY - BASE_CARDINALITY == RESERVED_WORDS
        assert RESERVED_WORDS == 368

    def test_word_capacity(self):
        assert BASE_WORD_CAPACITY == 2**15
        assert BASE_WORD_CAPACITY == 32768


# ─── Validation ───────────────────────────────────────────────────────────────

class TestValidation:
    def test_valid_state(self):
        validate_state(HVEState(0, 0, 0, 0))
        validate_state(HVEState(359, 1, 4, 8))

    def test_theta_out_of_range(self):
        with pytest.raises(HVEError, match="theta"):
            validate_state(HVEState(360, 0, 0, 0))

    def test_s_out_of_range(self):
        with pytest.raises(HVEError, match="s"):
            validate_state(HVEState(0, 2, 0, 0))

    def test_tau_out_of_range(self):
        with pytest.raises(HVEError, match="tau"):
            validate_state(HVEState(0, 0, 5, 0))

    def test_phi_out_of_range(self):
        with pytest.raises(HVEError, match="phi"):
            validate_state(HVEState(0, 0, 0, 9))

    def test_negative_coordinates(self):
        with pytest.raises(HVEError):
            validate_state(HVEState(-1, 0, 0, 0))

    def test_valid_index(self):
        validate_index(0)
        validate_index(32399)

    def test_reserved_index(self):
        with pytest.raises(HVEError, match="reserved"):
            validate_index(32400)
        with pytest.raises(HVEError, match="reserved"):
            validate_index(32767)

    def test_index_out_of_range(self):
        with pytest.raises(HVEError):
            validate_index(-1)
        with pytest.raises(HVEError):
            validate_index(32768)


# ─── Exhaustive Bijection ─────────────────────────────────────────────────────

class TestExhaustiveBijection:
    def test_exhaustive_base_roundtrip(self):
        """Verify perfect round-trip for all 32,400 valid states."""
        seen = set()
        count = 0
        for theta in range(THETA_CARDINALITY):
            for s in range(S_CARDINALITY):
                for tau in range(TAU_CARDINALITY):
                    for phi in range(PHI_CARDINALITY):
                        state = HVEState(theta, s, tau, phi)
                        index = encode_base(state)
                        assert 0 <= index < BASE_CARDINALITY
                        assert index not in seen, f"duplicate index {index}"
                        seen.add(index)
                        decoded = decode_base(index)
                        assert decoded == state
                        count += 1
        assert count == BASE_CARDINALITY
        assert len(seen) == BASE_CARDINALITY

    def test_all_reserved_words_rejected(self):
        """Verify all 368 reserved indices are rejected."""
        rejected = 0
        for index in range(BASE_CARDINALITY, BASE_WORD_CAPACITY):
            with pytest.raises(HVEError):
                decode_base(index)
            rejected += 1
        assert rejected == RESERVED_WORDS


# ─── Specific Bijection Values ────────────────────────────────────────────────

class TestBijectionValues:
    def test_first_state(self):
        assert encode_base(HVEState(0, 0, 0, 0)) == 0

    def test_last_state(self):
        assert encode_base(HVEState(359, 1, 4, 8)) == 32399

    def test_known_values(self):
        # index = (((theta*2+s)*5+tau)*9+phi)
        assert encode_base(HVEState(0, 0, 0, 8)) == 8
        assert encode_base(HVEState(0, 1, 0, 0)) == 45
        assert encode_base(HVEState(123, 1, 2, 7)) == 11140

    def test_decode_boundary(self):
        state = decode_base(32399)
        assert state == HVEState(359, 1, 4, 8)

    def test_decode_zero(self):
        state = decode_base(0)
        assert state == HVEState(0, 0, 0, 0)


# ─── Group Operations ────────────────────────────────────────────────────────

class TestGroupOperations:
    def test_identity(self):
        e = group_identity()
        assert e == HVEState(0, 0, 0, 0)

    def test_identity_is_neutral(self):
        e = group_identity()
        a = HVEState(123, 1, 3, 7)
        assert group_add(a, e) == a
        assert group_add(e, a) == a

    def test_inverse_yields_identity(self):
        """a ⊕ (-a) = identity for sample states."""
        e = group_identity()
        samples = [
            HVEState(0, 0, 0, 0),
            HVEState(180, 1, 2, 4),
            HVEState(359, 1, 4, 8),
            HVEState(1, 0, 0, 0),
        ]
        for a in samples:
            inv = group_inverse(a)
            assert group_add(a, inv) == e

    def test_associativity_random(self):
        """(a ⊕ b) ⊕ c = a ⊕ (b ⊕ c) for deterministic pseudo-random triples."""
        rng_state = 0xC0FFEE42
        for _ in range(10000):
            # xorshift32
            rng_state ^= (rng_state << 13) & 0xFFFFFFFF
            rng_state ^= (rng_state >> 17)
            rng_state ^= (rng_state << 5) & 0xFFFFFFFF
            rng_state &= 0xFFFFFFFF
            a = HVEState(rng_state % 360, (rng_state >> 10) % 2,
                         (rng_state >> 11) % 5, (rng_state >> 14) % 9)
            rng_state ^= (rng_state << 13) & 0xFFFFFFFF
            rng_state ^= (rng_state >> 17)
            rng_state ^= (rng_state << 5) & 0xFFFFFFFF
            rng_state &= 0xFFFFFFFF
            b = HVEState(rng_state % 360, (rng_state >> 10) % 2,
                         (rng_state >> 11) % 5, (rng_state >> 14) % 9)
            rng_state ^= (rng_state << 13) & 0xFFFFFFFF
            rng_state ^= (rng_state >> 17)
            rng_state ^= (rng_state << 5) & 0xFFFFFFFF
            rng_state &= 0xFFFFFFFF
            c = HVEState(rng_state % 360, (rng_state >> 10) % 2,
                         (rng_state >> 11) % 5, (rng_state >> 14) % 9)
            left = group_add(group_add(a, b), c)
            right = group_add(a, group_add(b, c))
            assert left == right

    def test_commutativity(self):
        a = HVEState(100, 1, 3, 7)
        b = HVEState(200, 0, 2, 5)
        assert group_add(a, b) == group_add(b, a)


# ─── Sigma Conversion ────────────────────────────────────────────────────────

class TestSigma:
    def test_sigma_to_s(self):
        assert sigma_to_s(1) == 0
        assert sigma_to_s(-1) == 1

    def test_s_to_sigma(self):
        assert s_to_sigma(0) == 1
        assert s_to_sigma(1) == -1

    def test_invalid_sigma(self):
        with pytest.raises(HVEError):
            sigma_to_s(0)

    def test_invalid_s(self):
        with pytest.raises(HVEError):
            s_to_sigma(2)

    def test_roundtrip(self):
        assert s_to_sigma(sigma_to_s(1)) == 1
        assert s_to_sigma(sigma_to_s(-1)) == -1
