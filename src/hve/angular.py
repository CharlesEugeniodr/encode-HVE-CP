"""Angular State Engine — discrete circular geometry on C₃₆₀.

Mathematical foundation:
    C₃₆₀ is the cycle graph on the cyclic group Z₃₆₀.  Every vertex is
    an integer in [0, 359] representing one degree of angular position.

    The geodesic (shortest-path) distance on C₃₆₀ is:
        δ(θ₁, θ₂) = min(|θ₁ − θ₂|, 360 − |θ₁ − θ₂|)

Multi-resolution addressing:
    BASE   — 1° resolution   (360 cells)           m = 1
    MICRO  — 0.001° resolution (360,000 cells)      m = 1,000
    NANO   — sub-µ° resolution (388,800,000 cells)  m = 1,080,000

The refinement factors are defined by the HVE specification:
    MICRO: 1,000 sub-cells per degree  →  |Z_{360·1000}| = 360,000
    NANO:  1,080 sub-cells per micro   →  |Z_{360·1000·1080}| = 388,800,000

Full group cardinalities:
    |G_BASE|  = 360 × 2 × 5 × 9 = 32,400
    |G_MICRO| = 360,000 × 2 × 5 × 9 = 32,400,000
    |G_NANO|  = 388,800,000 × 2 × 5 × 9 = 34,992,000,000
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Sequence

from hve.core import HVEError, THETA_CARDINALITY

# ─── Constants ────────────────────────────────────────────────────────────────

CYCLE_ORDER: int = THETA_CARDINALITY          # 360
HALF_CYCLE: int = CYCLE_ORDER // 2            # 180
DEFAULT_MICRO_DIVISIONS: int = 1_000
DEFAULT_NANO_DIVISIONS: int = 1_080

# Consistency asserts for hierarchical refinement
assert DEFAULT_MICRO_DIVISIONS == 1_000, "MICRO_FACTOR must be 1,000"
assert DEFAULT_NANO_DIVISIONS * DEFAULT_MICRO_DIVISIONS == 1_080_000, "NANO_TOTAL_FACTOR must be 1,080,000"



# ─── Types ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ShortestPath:
    """Result of a shortest-path query on C₃₆₀.

    Attributes:
        distance:         Geodesic distance δ(θ₁, θ₂).
        clockwise:        Steps to walk clockwise from θ₁ to θ₂.
        counterclockwise: Steps to walk counter-clockwise from θ₁ to θ₂.
        direction:        Which walk is shorter: 'cw', 'ccw', or 'antipodal'.
        arc:              Intermediate vertices on the shortest walk,
                          *excluding* the two endpoints.
    """

    distance: int
    clockwise: int
    counterclockwise: int
    direction: Literal["cw", "ccw", "antipodal"]
    arc: list[int]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _mod360(value: int) -> int:
    """Reduce *value* into [0, 359]."""
    return value % CYCLE_ORDER


# ─── Distance Metrics ────────────────────────────────────────────────────────

def circular_distance(theta1: int, theta2: int) -> int:
    """Geodesic distance on C₃₆₀.

    δ(θ₁, θ₂) = min(|θ₁ − θ₂|, 360 − |θ₁ − θ₂|)

    Args:
        theta1: First vertex in Z₃₆₀.
        theta2: Second vertex in Z₃₆₀.

    Returns:
        The shortest-path distance in [0, 180].
    """
    diff = abs(_mod360(theta1) - _mod360(theta2))
    return min(diff, CYCLE_ORDER - diff)


def normalized_distance(theta1: int, theta2: int) -> float:
    """Normalized geodesic distance on C₃₆₀.

    Returns δ(θ₁, θ₂) / 180, mapping [0, 180] → [0.0, 1.0].

    Args:
        theta1: First vertex in Z₃₆₀.
        theta2: Second vertex in Z₃₆₀.

    Returns:
        A float in [0.0, 1.0].
    """
    return circular_distance(theta1, theta2) / HALF_CYCLE


def geodesic_distance(theta1: int, theta2: int) -> int:
    """Alias for :func:`circular_distance`.

    Explicit name emphasising the discrete geodesic interpretation on C₃₆₀.
    """
    return circular_distance(theta1, theta2)


# ─── Path & Direction ────────────────────────────────────────────────────────

def shortest_path(theta1: int, theta2: int) -> ShortestPath:
    """Compute the shortest path between two vertices on C₃₆₀.

    Args:
        theta1: Start vertex in Z₃₆₀.
        theta2: End vertex in Z₃₆₀.

    Returns:
        A :class:`ShortestPath` dataclass.
    """
    t1 = _mod360(theta1)
    t2 = _mod360(theta2)

    cw = (t2 - t1) % CYCLE_ORDER       # clockwise steps
    ccw = (t1 - t2) % CYCLE_ORDER      # counter-clockwise steps
    dist = min(cw, ccw)

    if dist == HALF_CYCLE:
        direction: Literal["cw", "ccw", "antipodal"] = "antipodal"
    elif cw <= ccw:
        direction = "cw"
    else:
        direction = "ccw"

    # Build intermediate arc along the shorter walk.
    if direction in ("cw", "antipodal"):
        arc = [_mod360(t1 + i) for i in range(1, dist)]
    else:
        arc = [_mod360(t1 - i) for i in range(1, dist)]

    return ShortestPath(
        distance=dist,
        clockwise=cw,
        counterclockwise=ccw,
        direction=direction,
        arc=arc,
    )


# ─── Neighbourhood & Rotation ────────────────────────────────────────────────

def neighborhood(theta: int, radius: int) -> set[int]:
    """Return the closed r-neighbourhood N_r(θ) on C₃₆₀.

    N_r(θ) = {(θ − r) mod 360, …, (θ + r) mod 360}

    Args:
        theta:  Centre vertex.
        radius: Neighbourhood radius (non-negative).

    Returns:
        A set of vertices.

    Raises:
        HVEError: If *radius* is negative or ≥ HALF_CYCLE and would
                  cover the whole cycle.
    """
    if radius < 0:
        raise HVEError(f"radius must be non-negative, got {radius}")
    t = _mod360(theta)
    return {_mod360(t + d) for d in range(-radius, radius + 1)}


def rotate(theta: int, delta: int) -> int:
    """Rotate vertex θ by *delta* steps on C₃₆₀.

    Args:
        theta: Starting vertex.
        delta: Signed step count (positive = clockwise).

    Returns:
        The resulting vertex in [0, 359].
    """
    return _mod360(theta + delta)


# ─── Arc Operations ──────────────────────────────────────────────────────────

def circular_interval(start: int, end: int) -> list[int]:
    """Return the clockwise arc [start → end], inclusive of both endpoints.

    Args:
        start: Arc start vertex.
        end:   Arc end vertex.

    Returns:
        A list of vertices traversed clockwise from *start* to *end*.
    """
    s = _mod360(start)
    e = _mod360(end)
    length = (e - s) % CYCLE_ORDER
    return [_mod360(s + i) for i in range(length + 1)]


def arc_contains(start: int, end: int, theta: int) -> bool:
    """Test membership in the clockwise arc [start → end].

    Args:
        start: Arc start vertex.
        end:   Arc end vertex.
        theta: Query vertex.

    Returns:
        ``True`` iff θ lies on the clockwise arc from *start* to *end*
        (inclusive of both endpoints).
    """
    s = _mod360(start)
    e = _mod360(end)
    t = _mod360(theta)
    arc_len = (e - s) % CYCLE_ORDER
    offset = (t - s) % CYCLE_ORDER
    return offset <= arc_len


# ─── Circular Statistics ─────────────────────────────────────────────────────

def circular_center(thetas: Sequence[int]) -> float:
    """Compute the circular mean direction of a set of angles.

    Uses the atan2(mean(sin θ), mean(cos θ)) formula with angles
    converted to radians and the result converted back to degrees
    in [0, 360).

    Args:
        thetas: A non-empty sequence of integer angles.

    Returns:
        The circular mean in [0.0, 360.0).

    Raises:
        HVEError: If *thetas* is empty.
    """
    if not thetas:
        raise HVEError("circular_center requires at least one angle")

    sin_sum = sum(math.sin(math.radians(t)) for t in thetas)
    cos_sum = sum(math.cos(math.radians(t)) for t in thetas)
    mean_deg = math.degrees(math.atan2(sin_sum, cos_sum))
    return mean_deg % 360.0


def circular_mean(thetas: Sequence[int]) -> float:
    """Alias for :func:`circular_center`."""
    return circular_center(thetas)


# ─── Sector Grouping ─────────────────────────────────────────────────────────

def sector_group(thetas: Sequence[int], n_sectors: int) -> dict[int, list[int]]:
    """Partition angles into *n_sectors* equal sectors of C₃₆₀.

    Sector *k* spans the half-open interval [k·w, (k+1)·w) where
    w = 360 / n_sectors.

    Args:
        thetas:    A sequence of integer angles.
        n_sectors: Number of sectors (must evenly divide 360).

    Returns:
        A dict mapping sector index → list of angles in that sector.

    Raises:
        HVEError: If *n_sectors* does not evenly divide 360.
    """
    if CYCLE_ORDER % n_sectors != 0:
        raise HVEError(
            f"n_sectors must evenly divide {CYCLE_ORDER}, got {n_sectors}"
        )
    width = CYCLE_ORDER // n_sectors
    groups: dict[int, list[int]] = {k: [] for k in range(n_sectors)}
    for t in thetas:
        sector = _mod360(t) // width
        groups[sector].append(t)
    return groups


# ─── Multi-Resolution ─────────────────────────────────────────────────────────
#
# Architecture: hierarchical refinement.
#
#   MICRO_FACTOR        = 1,000  (sub-cells per degree)
#   NANO_PER_MICRO      = 1,080  (sub-cells per micro-cell)
#   NANO_TOTAL_FACTOR   = MICRO_FACTOR * NANO_PER_MICRO = 1,080,000
#
# Angular domains (theta axis only):
#   BASE:   Z_360              1° resolution
#   MICRO:  Z_360,000          0.001° resolution    (360 * 1,000)
#   NANO:   Z_388,800,000      sub-µ° resolution    (360 * 1,000 * 1,080)
#
# Full group cardinalities (angular * 2 * 5 * 9):
#   |G_BASE|  = 32,400
#   |G_MICRO| = 32,400,000
#   |G_NANO|  = 34,992,000,000
#
# Normative API: integer encode/decode.
# Float quantize functions: convenience only (use round, not truncation).
# ──────────────────────────────────────────────────────────────────────────────

MICRO_FACTOR: int = DEFAULT_MICRO_DIVISIONS        # 1,000 sub-cells/degree
NANO_PER_MICRO: int = DEFAULT_NANO_DIVISIONS        # 1,080 sub-cells/micro-cell
NANO_TOTAL_FACTOR: int = MICRO_FACTOR * NANO_PER_MICRO  # 1,080,000

_STATE_COFACTOR: int = 2 * 5 * 9                    # 90  (|Z_2 x Z_5 x Z_9|)


def quantize_base(theta: int) -> int:
    """Quantize to BASE resolution (1° cells).

    At BASE resolution every integer degree maps to itself.

    Args:
        theta: An integer angle.

    Returns:
        theta mod 360.
    """
    return _mod360(theta)


# ─── Cardinality Functions ────────────────────────────────────────────────────

def micro_angular_cardinality() -> int:
    """Return |Z_{360 * MICRO_FACTOR}| = 360,000."""
    return CYCLE_ORDER * MICRO_FACTOR


def nano_angular_cardinality() -> int:
    """Return |Z_{360 * NANO_TOTAL_FACTOR}| = 388,800,000."""
    return CYCLE_ORDER * NANO_TOTAL_FACTOR


def micro_state_cardinality() -> int:
    """Return |G_MICRO| = 360,000 * 90 = 32,400,000."""
    return micro_angular_cardinality() * _STATE_COFACTOR


def nano_state_cardinality() -> int:
    """Return |G_NANO| = 388,800,000 * 90 = 34,992,000,000."""
    return nano_angular_cardinality() * _STATE_COFACTOR


# Legacy aliases — accept optional factor overrides for backward compat.
def micro_cardinality(micro_divisions: int = MICRO_FACTOR) -> int:
    """Angular cardinality at MICRO level.  Prefer :func:`micro_angular_cardinality`."""
    return CYCLE_ORDER * micro_divisions


def nano_cardinality(
    micro_divisions: int = MICRO_FACTOR,
    nano_divisions: int = NANO_PER_MICRO,
) -> int:
    """Angular cardinality at NANO level.  Prefer :func:`nano_angular_cardinality`."""
    return CYCLE_ORDER * micro_divisions * nano_divisions


# ─── Normative Integer Encode / Decode ────────────────────────────────────────

def encode_micro(base_theta: int, micro_offset: int,
                 micro_divisions: int = MICRO_FACTOR) -> int:
    """Encode (base, micro) to a flat index in Z_{360 * m}.

    This is the **normative** MICRO API.

    Args:
        base_theta:      Integer degree in [0, 359].
        micro_offset:    Sub-cell offset in [0, micro_divisions - 1].
        micro_divisions: Sub-cells per degree (default 1,000).

    Returns:
        Integer index in [0, 360*m - 1].
    """
    b = _mod360(base_theta)
    if not (0 <= micro_offset < micro_divisions):
        raise HVEError(
            f"micro_offset must be in [0, {micro_divisions - 1}], "
            f"got {micro_offset}"
        )
    return b * micro_divisions + micro_offset


def decode_micro(flat_index: int,
                 micro_divisions: int = MICRO_FACTOR) -> tuple[int, int]:
    """Decode a flat MICRO index to (base_theta, micro_offset).

    Args:
        flat_index:      Integer in [0, 360*m - 1].
        micro_divisions: Sub-cells per degree (default 1,000).

    Returns:
        Tuple (base_theta, micro_offset).
    """
    card = CYCLE_ORDER * micro_divisions
    if not (0 <= flat_index < card):
        raise HVEError(f"micro index must be in [0, {card - 1}], got {flat_index}")
    base, offset = divmod(flat_index, micro_divisions)
    return (base, offset)


def encode_nano(base_theta: int, micro_offset: int, nano_offset: int,
                micro_divisions: int = MICRO_FACTOR,
                nano_divisions: int = NANO_PER_MICRO) -> int:
    """Encode (base, micro, nano) to a flat index in Z_{360 * m * n}.

    This is the **normative** NANO API.

    Composition: NANO_TOTAL_FACTOR = micro_divisions * nano_divisions = 1,080,000.
    Angular cardinality: 360 * 1,080,000 = 388,800,000.

    Args:
        base_theta:      Integer degree in [0, 359].
        micro_offset:    In [0, micro_divisions - 1].
        nano_offset:     In [0, nano_divisions - 1].
        micro_divisions: Sub-cells per degree (default 1,000).
        nano_divisions:  Sub-cells per micro-cell (default 1,080).

    Returns:
        Integer index in [0, 360*m*n - 1].
    """
    b = _mod360(base_theta)
    if not (0 <= micro_offset < micro_divisions):
        raise HVEError(
            f"micro_offset must be in [0, {micro_divisions - 1}], "
            f"got {micro_offset}"
        )
    if not (0 <= nano_offset < nano_divisions):
        raise HVEError(
            f"nano_offset must be in [0, {nano_divisions - 1}], "
            f"got {nano_offset}"
        )
    return (b * micro_divisions + micro_offset) * nano_divisions + nano_offset


def decode_nano(flat_index: int,
                micro_divisions: int = MICRO_FACTOR,
                nano_divisions: int = NANO_PER_MICRO) -> tuple[int, int, int]:
    """Decode a flat NANO index to (base_theta, micro_offset, nano_offset).

    Args:
        flat_index:      Integer in [0, 360*m*n - 1].
        micro_divisions: Sub-cells per degree (default 1,000).
        nano_divisions:  Sub-cells per micro-cell (default 1,080).

    Returns:
        Tuple (base_theta, micro_offset, nano_offset).
    """
    card = CYCLE_ORDER * micro_divisions * nano_divisions
    if not (0 <= flat_index < card):
        raise HVEError(f"nano index must be in [0, {card - 1}], got {flat_index}")
    micro_flat, nano_off = divmod(flat_index, nano_divisions)
    base, micro_off = divmod(micro_flat, micro_divisions)
    return (base, micro_off, nano_off)


# ─── Float Convenience (Non-Normative) ───────────────────────────────────────
#
# These accept float angles and produce integer tuples via round().
# For normative encoding, use encode_micro / encode_nano with integer args.
#
# IMPORTANT — Rounding semantics:
#   Python's round() uses banker's rounding (round-half-to-even), so values
#   exactly at x.5 boundaries may round differently than the "always round up"
#   school rule.  This is NOT part of the normative wire representation.
#
#   Convenience floating-point quantization follows the host language rounding
#   semantics and is not part of the normative wire representation.
#
#   For interoperability across Python, C, and other languages, normative
#   inputs must be received as:
#     - integer degree + integer tick; or
#     - decimal text processed with an expressly defined rounding rule.
# ──────────────────────────────────────────────────────────────────────────────

def quantize_micro(
    theta_precise: float,
    micro_divisions: int = MICRO_FACTOR,
) -> tuple[int, int]:
    """Quantize a float angle to MICRO resolution (non-normative convenience).

    Uses round() to avoid IEEE 754 truncation errors at boundaries.
    For normative encoding, use :func:`encode_micro` with integer arguments.

    Args:
        theta_precise:   A floating-point angle.
        micro_divisions: Sub-cells per degree (default 1,000).

    Returns:
        Tuple (base_theta, micro_offset) with integer values.
    """
    normalised = theta_precise % 360.0
    base = int(normalised)
    fractional = normalised - base
    tick = round(fractional * micro_divisions)
    # Handle overflow: round(0.9999... * 1000) could yield 1000
    if tick >= micro_divisions:
        base = (base + 1) % CYCLE_ORDER
        tick = 0
    return (base, tick)


def quantize_nano(
    theta_precise: float,
    micro_divisions: int = MICRO_FACTOR,
    nano_divisions: int = NANO_PER_MICRO,
) -> tuple[int, int, int]:
    """Quantize a float angle to NANO resolution (non-normative convenience).

    Uses round() at each level to avoid IEEE 754 truncation.
    For normative encoding, use :func:`encode_nano` with integer arguments.

    Args:
        theta_precise:   A floating-point angle.
        micro_divisions: Sub-cells per degree (default 1,000).
        nano_divisions:  Sub-cells per micro-cell (default 1,080).

    Returns:
        Tuple (base_theta, micro_offset, nano_offset) with integer values.
    """
    # Total ticks in the flat NANO domain
    total_factor = micro_divisions * nano_divisions
    normalised = theta_precise % 360.0
    flat_tick = round(normalised * total_factor)
    # Handle overflow at 360°
    if flat_tick >= CYCLE_ORDER * total_factor:
        flat_tick = 0
    # Decompose hierarchically
    micro_flat, nano_off = divmod(flat_tick, nano_divisions)
    base, micro_off = divmod(micro_flat, micro_divisions)
    return (base % CYCLE_ORDER, micro_off, nano_off)


# ─── Resolution Projection ───────────────────────────────────────────────────

_LEVEL_ORDER = {"base": 1, "micro": 2, "nano": 3}


def project_resolution(
    value: tuple,
    from_level: str,
    to_level: str,
) -> tuple:
    """Project an address between resolution levels.

    Supported levels: 'base', 'micro', 'nano'.

    *Downscaling* (higher to lower) truncates sub-cell offsets.
    *Upscaling* (lower to higher) pads with zero offsets.

    Args:
        value:      A tuple of length matching *from_level*.
        from_level: Source resolution level.
        to_level:   Target resolution level.

    Returns:
        A tuple of length matching *to_level*.

    Raises:
        HVEError: If level names are unknown or *value* length mismatches.
    """
    if from_level not in _LEVEL_ORDER:
        raise HVEError(f"unknown level '{from_level}', expected one of {list(_LEVEL_ORDER)}")
    if to_level not in _LEVEL_ORDER:
        raise HVEError(f"unknown level '{to_level}', expected one of {list(_LEVEL_ORDER)}")

    expected_len = _LEVEL_ORDER[from_level]
    if len(value) != expected_len:
        raise HVEError(
            f"'{from_level}' requires a {expected_len}-tuple, got length {len(value)}"
        )

    target_len = _LEVEL_ORDER[to_level]

    if target_len <= expected_len:
        # Truncate (downscale).
        return value[:target_len]

    # Pad with zeros (upscale).
    return value + (0,) * (target_len - expected_len)



def verify_hierarchy() -> None:
    """Run internal asserts to ensure hierarchical constants are correct.

    Called by tests to guarantee that modifications do not break the
    mathematical relationship between MICRO and NANO divisions.
    """
    assert DEFAULT_MICRO_DIVISIONS == 1_000
    assert DEFAULT_NANO_DIVISIONS * DEFAULT_MICRO_DIVISIONS == 1_080_000
