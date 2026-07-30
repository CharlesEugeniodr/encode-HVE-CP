"""HVE-χ Chromatic Engine — pointed color extension.

The chromatic space is the pointed set:
    C* = {NoColor} ∪ RGB
    |C*| = 1 + 2^24 = 16,777,217

The full HVE-χ cardinality is:
    |HVE-χ| = 32,400 × 16,777,217 = 543,581,830,800

Encoding:
    χ_index = base_index × |C*| + κ(color)

where κ: C* → [0, 16777216] maps:
    NoColor → 0
    RGB(r, g, b) → 1 + r·2^16 + g·2^8 + b
"""

from __future__ import annotations

from dataclasses import dataclass

from hve.core import (
    HVEState,
    HVEError,
    encode_base,
    decode_base,
    validate_state,
    BASE_CARDINALITY,
)

# ─── Constants ────────────────────────────────────────────────────────────────

COLOR_RGB_CARDINALITY: int = 1 << 24  # 16,777,216
COLOR_POINTED_CARDINALITY: int = COLOR_RGB_CARDINALITY + 1  # 16,777,217
CHI_CARDINALITY: int = BASE_CARDINALITY * COLOR_POINTED_CARDINALITY  # 543,581,830,800
CHI_MAX_INDEX: int = CHI_CARDINALITY - 1


# ─── Types ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class HVEColor:
    """A color in the HVE pointed chromatic space C*.

    The space distinguishes:
      - NoColor (present=False, r=g=b=0): absence of chromatic information.
      - RGB black (present=True, r=g=b=0): explicit black color.
      - Any other RGB (present=True, r/g/b in [0,255]).

    Attributes:
        present: Whether chromatic information exists.
        r: Red channel [0, 255].
        g: Green channel [0, 255].
        b: Blue channel [0, 255].
    """

    present: bool
    r: int = 0
    g: int = 0
    b: int = 0

    @staticmethod
    def no_color() -> HVEColor:
        """Create a NoColor instance (absence of chromatic information)."""
        return HVEColor(False, 0, 0, 0)

    @staticmethod
    def rgb(r: int, g: int, b: int) -> HVEColor:
        """Create an RGB color, validating channel ranges."""
        color = HVEColor(True, r, g, b)
        validate_color(color)
        return color


# ─── Validation ───────────────────────────────────────────────────────────────

def validate_color(color: HVEColor) -> None:
    """Validate a color in the pointed chromatic space.

    Rules:
      - r, g, b must each be in [0, 255].
      - If present is False (NoColor), then r, g, b must all be 0.

    Raises:
        HVEError: If the color violates any constraint.
    """
    for name, value in (("r", color.r), ("g", color.g), ("b", color.b)):
        if not (0 <= value <= 255):
            raise HVEError(f"{name} must be in [0, 255], got {value}")
    if not color.present and (color.r != 0 or color.g != 0 or color.b != 0):
        raise HVEError("NoColor requires r=g=b=0")


# ─── Kappa Mapping ────────────────────────────────────────────────────────────

def color_kappa(color: HVEColor) -> int:
    """Map a color to its index κ in the pointed chromatic space.

    κ(NoColor) = 0
    κ(RGB(r, g, b)) = 1 + r·2^16 + g·2^8 + b

    Args:
        color: A valid HVE color.

    Returns:
        An integer in [0, 16777216].

    Raises:
        HVEError: If the color is invalid.
    """
    validate_color(color)
    if not color.present:
        return 0
    return 1 + (color.r << 16) + (color.g << 8) + color.b


def color_kappa_inverse(kappa: int) -> HVEColor:
    """Map an index κ back to its color in the pointed chromatic space.

    Args:
        kappa: An index in [0, 16777216].

    Returns:
        The corresponding HVE color.

    Raises:
        HVEError: If kappa is out of range.
    """
    if not (0 <= kappa < COLOR_POINTED_CARDINALITY):
        raise HVEError(f"kappa must be in [0, {COLOR_POINTED_CARDINALITY - 1}], got {kappa}")
    if kappa == 0:
        return HVEColor.no_color()
    u = kappa - 1
    return HVEColor.rgb((u >> 16) & 0xFF, (u >> 8) & 0xFF, u & 0xFF)


# ─── HVE-χ Bijection ─────────────────────────────────────────────────────────

def encode_chi(state: HVEState, color: HVEColor) -> int:
    """Encode an HVE state with color to a monolithic HVE-χ index.

    χ_index = base_index × |C*| + κ(color)

    Args:
        state: A valid HVE state.
        color: A valid HVE color.

    Returns:
        An integer in [0, 543,581,830,799].

    Raises:
        HVEError: If state or color is invalid.
    """
    return encode_base(state) * COLOR_POINTED_CARDINALITY + color_kappa(color)


def decode_chi(index: int) -> tuple[HVEState, HVEColor]:
    """Decode a monolithic HVE-χ index back to state and color.

    Args:
        index: A valid HVE-χ index in [0, 543,581,830,799].

    Returns:
        A tuple (state, color).

    Raises:
        HVEError: If the index is outside the valid interval.
    """
    if not (0 <= index <= CHI_MAX_INDEX):
        raise HVEError(f"HVE-χ index must be in [0, {CHI_MAX_INDEX}], got {index}")
    base_index, kappa = divmod(index, COLOR_POINTED_CARDINALITY)
    return decode_base(base_index), color_kappa_inverse(kappa)
