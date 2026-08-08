"""AI Mapping Layer — deterministic mapper.

:class:`DeterministicMapper` provides deterministic mappings in two modes:

* **int** — canonical table lookup: treated as a BASE index in [0, 32399],
  decoded directly via :func:`decode_base`.  This is a bijection with
  ``confidence=1.0`` and ``mapping_type='exact'``.

* **str** — modular projection: each character's Unicode codepoint is
  taken mod 32,400 and decoded.  This is a many-to-one surjection
  (codepoints u and u+32400 collide), so it uses ``confidence=0.0``
  and ``mapping_type='derived'`` with ``collision_policy='modulo_projection'``.
"""

from __future__ import annotations

from typing import Any

from hve.core import (
    HVEError,
    HVEState,
    BASE_CARDINALITY,
    decode_base,
    encode_base,
)

# LCG multiplier for spatial dispersion across the full HVE state space.
# Without this, ord(ch) % 32400 concentrates ASCII/Latin text in states 0-255.
_LCG_MULTIPLIER: int = 1_103_515_245

# Maximum number of alternative mappings to avoid unbounded memory allocation.
_MAX_ALTERNATIVES: int = 10
from hve.ai_mapping.interfaces import AbstractMapper
from hve.ai_mapping.result import MappingResult


class DeterministicMapper(AbstractMapper):
    """Map integers and Unicode codepoints deterministically to HVE states.

    This mapper never uses heuristics or learned weights.

    * ``map(int)`` — **canonical table lookup**, bijective, ``confidence=1.0``.
    * ``map(str)`` — **modular projection**, many-to-one, ``confidence=0.0``.

    Examples::

        mapper = DeterministicMapper()
        result = mapper.map(0)       # exact → HVEState(0, 0, 0, 0), conf=1.0
        result = mapper.map(32399)   # exact → HVEState(359, 1, 4, 8), conf=1.0
        result = mapper.map("A")     # derived → codepoint 65 mod 32400, conf=0.0
    """

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def mapper_id(self) -> str:
        return "hve.deterministic"

    @property
    def mapper_version(self) -> str:
        return "1.0.0"

    # ── Core API ──────────────────────────────────────────────────────

    def map(self, input_data: Any, **kwargs: Any) -> MappingResult:
        """Map *input_data* deterministically to an HVE state.

        Args:
            input_data: An ``int`` index in [0, 32399] or a non-empty ``str``.
            **kwargs: Unused.

        Returns:
            A :class:`MappingResult`.  ``confidence=1.0`` for int (exact),
            ``confidence=0.0`` for str (derived modular projection).

        Raises:
            TypeError: If *input_data* is not ``int`` or ``str``.
            HVEError: If an integer index is out of range.
            ValueError: If a string is empty.
        """
        if isinstance(input_data, int):
            return self._map_int(input_data)
        if isinstance(input_data, str):
            return self._map_str(input_data)
        raise TypeError(
            f"DeterministicMapper does not support {type(input_data).__name__}"
        )

    def supports(self, input_type: type) -> bool:
        """Return ``True`` for ``int`` and ``str``."""
        return input_type in (int, str)

    # ── Private helpers ───────────────────────────────────────────────

    def _map_int(self, index: int) -> MappingResult:
        """Canonical table lookup — bijective, confidence=1.0."""
        state = decode_base(index)
        return MappingResult(
            state=state,
            confidence=1.0,
            mapper_id=self.mapper_id,
            mapper_version=self.mapper_version,
            provenance={
                "method": "canonical_table_lookup",
                "input": index,
                "table_id": "hve720-canonical",
                "table_version": "1.0.0",
                "mapping_type": "exact",
            },
        )

    def _map_str(self, text: str) -> MappingResult:
        """Modular projection — many-to-one, confidence=0.0.

        Unicode codepoints are projected via mod BASE_CARDINALITY.
        This is surjective (u and u+32400 map to the same state),
        so confidence is 0.0 and mapping_type is 'derived'.

        The first character determines the primary state; subsequent
        characters produce ``alternatives``.

        Raises:
            ValueError: If *text* is empty.
        """
        if not text:
            raise ValueError("input string must be non-empty")

        def _char_to_state(ch: str) -> HVEState:
            return decode_base((ord(ch) * _LCG_MULTIPLIER) % BASE_CARDINALITY)

        def _char_provenance(ch: str) -> dict:
            return {
                "method": "unicode_codepoint_mod",
                "char": ch,
                "codepoint": ord(ch),
                "index": (ord(ch) * _LCG_MULTIPLIER) % BASE_CARDINALITY,
                "mapping_type": "derived",
                "collision_policy": "modulo_projection",
            }

        primary = _char_to_state(text[0])
        alternatives = [
            MappingResult(
                state=_char_to_state(ch),
                confidence=0.0,
                mapper_id=self.mapper_id,
                mapper_version=self.mapper_version,
                provenance=_char_provenance(ch),
            )
            for ch in text[1 : _MAX_ALTERNATIVES + 1]
        ]

        return MappingResult(
            state=primary,
            confidence=0.0,
            mapper_id=self.mapper_id,
            mapper_version=self.mapper_version,
            provenance=_char_provenance(text[0]),
            alternatives=alternatives,
        )

