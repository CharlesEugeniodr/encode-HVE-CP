"""Tests for the canonical state table module.

Covers:
    - Exhaustive round-trip validation (all 32,400 states)
    - State lookup by index
    - Index lookup by state
    - Table generation structure
    - Canonical summary statistics
"""

from __future__ import annotations

import pytest

from hve.core import HVEState, HVEError, BASE_CARDINALITY, RESERVED_WORDS, decode_base, encode_base
from hve.canonical import (
    generate_canonical_table,
    get_state,
    get_index,
    validate_canonical_table,
    canonical_table_summary,
)


# ─── Exhaustive Validation ───────────────────────────────────────────────────


class TestValidateCanonicalTable:
    """Exhaustive round-trip verification."""

    def test_all_valid_no_failures(self) -> None:
        valid, reserved, failures = validate_canonical_table()
        assert valid == BASE_CARDINALITY
        assert reserved == RESERVED_WORDS
        assert failures == 0

    def test_counts_match_cardinalities(self) -> None:
        valid, reserved, failures = validate_canonical_table()
        assert valid == 32_400
        assert reserved == 368


# ─── Table Generation ────────────────────────────────────────────────────────


class TestGenerateCanonicalTable:
    """generate_canonical_table structure and content."""

    def test_table_length(self) -> None:
        table = generate_canonical_table()
        assert len(table) == BASE_CARDINALITY

    def test_first_entry(self) -> None:
        table = generate_canonical_table()
        first = table[0]
        assert first == {
            "index": 0,
            "theta": 0,
            "s": 0,
            "tau": 0,
            "phi": 0,
            "sigma": 1,
        }

    def test_last_entry(self) -> None:
        table = generate_canonical_table()
        last = table[-1]
        assert last == {
            "index": 32_399,
            "theta": 359,
            "s": 1,
            "tau": 4,
            "phi": 8,
            "sigma": -1,
        }

    def test_all_entries_have_required_keys(self) -> None:
        table = generate_canonical_table()
        required = {"index", "theta", "s", "tau", "phi", "sigma"}
        for entry in table:
            assert required.issubset(entry.keys())

    def test_indices_are_sequential(self) -> None:
        table = generate_canonical_table()
        for i, entry in enumerate(table):
            assert entry["index"] == i

    def test_sigma_matches_s(self) -> None:
        table = generate_canonical_table()
        for entry in table:
            expected_sigma = 1 if entry["s"] == 0 else -1
            assert entry["sigma"] == expected_sigma


# ─── State Lookup ────────────────────────────────────────────────────────────


class TestGetState:
    """get_state convenience function."""

    def test_identity(self) -> None:
        assert get_state(0) == HVEState(0, 0, 0, 0)

    def test_max_index(self) -> None:
        assert get_state(32_399) == HVEState(359, 1, 4, 8)

    def test_matches_decode_base(self) -> None:
        for idx in [0, 1, 45, 90, 100, 1000, 16200, 32399]:
            assert get_state(idx) == decode_base(idx)

    def test_invalid_index(self) -> None:
        with pytest.raises(HVEError):
            get_state(32_400)

    def test_negative_index(self) -> None:
        with pytest.raises(HVEError):
            get_state(-1)


# ─── Index Lookup ────────────────────────────────────────────────────────────


class TestGetIndex:
    """get_index convenience function."""

    def test_identity(self) -> None:
        assert get_index(HVEState(0, 0, 0, 0)) == 0

    def test_max_state(self) -> None:
        assert get_index(HVEState(359, 1, 4, 8)) == 32_399

    def test_matches_encode_base(self) -> None:
        for idx in [0, 1, 45, 90, 100, 1000, 16200, 32399]:
            state = decode_base(idx)
            assert get_index(state) == encode_base(state)

    def test_round_trip(self) -> None:
        """get_index(get_state(i)) == i for all sampled indices."""
        for idx in range(0, BASE_CARDINALITY, 1000):
            assert get_index(get_state(idx)) == idx


# ─── Summary ─────────────────────────────────────────────────────────────────


class TestCanonicalTableSummary:
    """canonical_table_summary content."""

    def test_total_states(self) -> None:
        summary = canonical_table_summary()
        assert summary["total_states"] == 32_400

    def test_ranges(self) -> None:
        summary = canonical_table_summary()
        assert summary["theta_range"] == [0, 359]
        assert summary["s_values"] == [0, 1]
        assert summary["tau_range"] == [0, 4]
        assert summary["phi_range"] == [0, 8]

    def test_reserved_words(self) -> None:
        summary = canonical_table_summary()
        assert summary["reserved_words"] == 368

    def test_word_bits(self) -> None:
        summary = canonical_table_summary()
        assert summary["word_bits"] == 15

    def test_validation_clean(self) -> None:
        summary = canonical_table_summary()
        v = summary["validation"]
        assert v["valid"] == 32_400
        assert v["reserved_verified"] == 368
        assert v["failures"] == 0
