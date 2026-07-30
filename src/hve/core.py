"""HVE-720 BASE — core bijection, finite group, and validation.

Mathematical foundation:
    G = Z_360 × Z_2 × Z_5 × Z_9
    |G| = 360 × 2 × 5 × 9 = 32,400

Bijection (mixed-radix encoding):
    E(θ, s, τ, φ) = (((θ · 2 + s) · 5 + τ) · 9 + φ)

Addressing:
    15-bit words → [0, 32399] valid, [32400, 32767] reserved.
"""

from __future__ import annotations

from dataclasses import dataclass

# ─── Constants ────────────────────────────────────────────────────────────────

THETA_CARDINALITY: int = 360
S_CARDINALITY: int = 2
TAU_CARDINALITY: int = 5
PHI_CARDINALITY: int = 9

BASE_CARDINALITY: int = THETA_CARDINALITY * S_CARDINALITY * TAU_CARDINALITY * PHI_CARDINALITY  # 32,400
BASE_WORD_BITS: int = 15
BASE_WORD_CAPACITY: int = 1 << BASE_WORD_BITS  # 32,768
RESERVED_WORDS: int = BASE_WORD_CAPACITY - BASE_CARDINALITY  # 368


# ─── Exceptions ───────────────────────────────────────────────────────────────

class HVEError(ValueError):
    """Raised when an HVE value or operation violates the profile."""


# ─── Types ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class HVEState:
    """A state in the HVE-720 group G = Z_360 × Z_2 × Z_5 × Z_9.

    Attributes:
        theta: Angular position in [0, 359].
        s: Polarity index in {0, 1}.  (σ = (-1)^s, so s=0 → σ=+1, s=1 → σ=-1)
        tau: Auxiliary coordinate in [0, 4].
        phi: Auxiliary coordinate in [0, 8].
    """

    theta: int
    s: int
    tau: int
    phi: int

    def __post_init__(self) -> None:
        # Allow construction without validation for internal use;
        # explicit validate_state() is the public gate.
        pass


# ─── Validation ───────────────────────────────────────────────────────────────

def validate_state(state: HVEState) -> None:
    """Validate that *state* has coordinates within the canonical ranges.

    Raises:
        HVEError: If any coordinate is out of range.
    """
    if not (0 <= state.theta < THETA_CARDINALITY):
        raise HVEError(f"theta must be in [0, {THETA_CARDINALITY - 1}], got {state.theta}")
    if not (0 <= state.s < S_CARDINALITY):
        raise HVEError(f"s must be in {{0, 1}}, got {state.s}")
    if not (0 <= state.tau < TAU_CARDINALITY):
        raise HVEError(f"tau must be in [0, {TAU_CARDINALITY - 1}], got {state.tau}")
    if not (0 <= state.phi < PHI_CARDINALITY):
        raise HVEError(f"phi must be in [0, {PHI_CARDINALITY - 1}], got {state.phi}")


def validate_index(index: int) -> None:
    """Validate that *index* is a valid BASE-720 index in [0, 32399].

    Raises:
        HVEError: If *index* is outside the valid range or falls in the
                  reserved interval [32400, 32767].
    """
    if not (0 <= index < BASE_CARDINALITY):
        if BASE_CARDINALITY <= index < BASE_WORD_CAPACITY:
            raise HVEError(
                f"index {index} belongs to the reserved interval "
                f"[{BASE_CARDINALITY}, {BASE_WORD_CAPACITY - 1}]"
            )
        raise HVEError(f"index must be in [0, {BASE_CARDINALITY - 1}], got {index}")


# ─── Bijection ────────────────────────────────────────────────────────────────

def encode_base(state: HVEState) -> int:
    """Encode an HVE state to its unique 15-bit BASE index.

    Uses the mixed-radix formula:
        index = (((θ · 2 + s) · 5 + τ) · 9 + φ)

    Args:
        state: A valid HVE state.

    Returns:
        An integer index in [0, 32399].

    Raises:
        HVEError: If the state coordinates are invalid.
    """
    validate_state(state)
    index = (((state.theta * S_CARDINALITY + state.s) * TAU_CARDINALITY + state.tau) * PHI_CARDINALITY + state.phi)
    return index


def decode_base(index: int) -> HVEState:
    """Decode a 15-bit BASE index back to its unique HVE state.

    Uses successive Euclidean division:
        φ = index mod 9
        τ = (index / 9) mod 5
        s = (index / 45) mod 2
        θ = index / 90

    Args:
        index: A valid BASE index in [0, 32399].

    Returns:
        The corresponding HVE state.

    Raises:
        HVEError: If the index is outside the valid range.
    """
    validate_index(index)
    phi = index % PHI_CARDINALITY
    q1 = index // PHI_CARDINALITY
    tau = q1 % TAU_CARDINALITY
    q2 = q1 // TAU_CARDINALITY
    s = q2 % S_CARDINALITY
    theta = q2 // S_CARDINALITY
    return HVEState(theta, s, tau, phi)


# ─── Finite Group Operations ─────────────────────────────────────────────────

def group_identity() -> HVEState:
    """Return the identity element of the group G.

    Returns:
        HVEState(0, 0, 0, 0)
    """
    return HVEState(0, 0, 0, 0)


def group_add(a: HVEState, b: HVEState) -> HVEState:
    """Compute the group sum a ⊕ b in G = Z_360 × Z_2 × Z_5 × Z_9.

    Component-wise modular addition.

    Args:
        a: First operand.
        b: Second operand.

    Returns:
        The group sum.

    Raises:
        HVEError: If either operand is invalid.
    """
    validate_state(a)
    validate_state(b)
    return HVEState(
        (a.theta + b.theta) % THETA_CARDINALITY,
        (a.s + b.s) % S_CARDINALITY,
        (a.tau + b.tau) % TAU_CARDINALITY,
        (a.phi + b.phi) % PHI_CARDINALITY,
    )


def group_inverse(a: HVEState) -> HVEState:
    """Compute the group inverse ⊖a in G.

    Component-wise modular negation.

    Args:
        a: The operand.

    Returns:
        The additive inverse such that a ⊕ inverse(a) = identity.

    Raises:
        HVEError: If the operand is invalid.
    """
    validate_state(a)
    return HVEState(
        (-a.theta) % THETA_CARDINALITY,
        (-a.s) % S_CARDINALITY,
        (-a.tau) % TAU_CARDINALITY,
        (-a.phi) % PHI_CARDINALITY,
    )


# ─── Sigma Conversion ────────────────────────────────────────────────────────

def sigma_to_s(sigma: int) -> int:
    """Convert polarity σ ∈ {+1, -1} to index s ∈ {0, 1}."""
    if sigma == 1:
        return 0
    if sigma == -1:
        return 1
    raise HVEError("sigma must be +1 or -1")


def s_to_sigma(s: int) -> int:
    """Convert index s ∈ {0, 1} to polarity σ ∈ {+1, -1}."""
    if s == 0:
        return 1
    if s == 1:
        return -1
    raise HVEError("s must be 0 or 1")
