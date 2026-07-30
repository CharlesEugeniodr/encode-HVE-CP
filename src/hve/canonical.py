"""HVE-720 Canonical State Table.

Provides generation, lookup, and validation of the complete set of
32,400 HVE states.  The table is computed at runtime from the bijection
defined in :mod:`hve.core`; no static data file is required.

Functions:
    generate_canonical_table  — all 32,400 states as dicts.
    get_state                 — index → HVEState shortcut.
    get_index                 — HVEState → index shortcut.
    validate_canonical_table  — exhaustive round-trip check.
    canonical_table_summary   — summary statistics.
"""

from __future__ import annotations

from hve.core import (
    HVEState,
    HVEError,
    BASE_CARDINALITY,
    RESERVED_WORDS,
    THETA_CARDINALITY,
    S_CARDINALITY,
    TAU_CARDINALITY,
    PHI_CARDINALITY,
    decode_base,
    encode_base,
    s_to_sigma,
    validate_index,
    validate_state,
)


# ─── Table Generation ────────────────────────────────────────────────────────

def generate_canonical_table() -> list[dict]:
    """Generate the complete canonical table of all 32,400 HVE states.

    Each entry is a dict with keys:
        index, theta, s, tau, phi, sigma

    Returns:
        A list of 32,400 state dictionaries, ordered by index.
    """
    table: list[dict] = []
    for idx in range(BASE_CARDINALITY):
        state = decode_base(idx)
        table.append({
            "index": idx,
            "theta": state.theta,
            "s": state.s,
            "tau": state.tau,
            "phi": state.phi,
            "sigma": s_to_sigma(state.s),
        })
    return table


# ─── Convenience Lookups ─────────────────────────────────────────────────────

def get_state(index: int) -> HVEState:
    """Shortcut: decode a BASE index to its canonical HVE state.

    Args:
        index: A valid BASE index in [0, 32399].

    Returns:
        The corresponding :class:`HVEState`.

    Raises:
        HVEError: If *index* is out of range.
    """
    return decode_base(index)


def get_index(state: HVEState) -> int:
    """Shortcut: encode an HVE state to its canonical BASE index.

    Args:
        state: A valid :class:`HVEState`.

    Returns:
        The integer index in [0, 32399].

    Raises:
        HVEError: If the state is invalid.
    """
    return encode_base(state)


# ─── Validation ──────────────────────────────────────────────────────────────

def validate_canonical_table() -> tuple[int, int, int]:
    """Exhaustively validate the canonical table via round-trip encoding.

    For every index *i* in [0, 32399]:
        1. Decode *i* to a state.
        2. Validate the state's coordinates.
        3. Re-encode the state and verify ``encode(decode(i)) == i``.

    Also verifies that reserved indices [32400, 32767] are correctly
    rejected by :func:`decode_base`.

    Returns:
        ``(valid_count, reserved_count, failure_count)``
        — ideally ``(32400, 368, 0)``.
    """
    valid = 0
    failures = 0

    for idx in range(BASE_CARDINALITY):
        try:
            state = decode_base(idx)
            validate_state(state)
            if encode_base(state) != idx:
                failures += 1
            else:
                valid += 1
        except Exception:
            failures += 1

    # Verify reserved range rejects
    reserved_ok = 0
    for idx in range(BASE_CARDINALITY, BASE_CARDINALITY + RESERVED_WORDS):
        try:
            decode_base(idx)
            failures += 1  # should have raised
        except HVEError:
            reserved_ok += 1
        except Exception:
            failures += 1

    return (valid, reserved_ok, failures)


def canonical_table_summary() -> dict:
    """Return summary statistics about the canonical table.

    Returns:
        A dict with keys:
            total_states, theta_range, s_values, tau_range, phi_range,
            reserved_words, word_bits, validation.
    """
    valid, reserved, failures = validate_canonical_table()
    return {
        "total_states": BASE_CARDINALITY,
        "theta_range": [0, THETA_CARDINALITY - 1],
        "s_values": [0, S_CARDINALITY - 1],
        "tau_range": [0, TAU_CARDINALITY - 1],
        "phi_range": [0, PHI_CARDINALITY - 1],
        "reserved_words": RESERVED_WORDS,
        "word_bits": 15,
        "validation": {
            "valid": valid,
            "reserved_verified": reserved,
            "failures": failures,
        },
    }
