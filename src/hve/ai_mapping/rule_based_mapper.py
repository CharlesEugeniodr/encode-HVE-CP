"""AI Mapping Layer — rule-based mapper.

:class:`RuleBasedMapper` is a demonstration mapper that converts strings
to HVE states using simple deterministic rules:

* **θ** — string length mod 360
* **s** — 0 if the first character is uppercase, 1 otherwise
* **τ** — string hash mod 5
* **φ** — string hash mod 9

This is *not* a trained model.  It serves as a reference implementation
showing how the :class:`AbstractMapper` contract works for rule-driven
encodings.
"""

from __future__ import annotations

import hashlib
from typing import Any

from hve.core import (
    HVEState,
    THETA_CARDINALITY,
    S_CARDINALITY,
    TAU_CARDINALITY,
    PHI_CARDINALITY,
)
from hve.ai_mapping.interfaces import AbstractMapper
from hve.ai_mapping.result import MappingResult


def _stable_hash(text: str) -> int:
    """Return a stable, platform-independent hash for *text*.

    Uses SHA-256 truncated to 8 bytes so the result is deterministic
    across Python invocations (unlike the built-in ``hash()``).
    """
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


class RuleBasedMapper(AbstractMapper):
    """Map strings to HVE states via structural rules.

    Rules:
        theta = len(text) % 360
        s     = 0 if text[0].isupper() else 1
        tau   = stable_hash(text) % 5
        phi   = stable_hash(text) % 9

    Examples::

        mapper = RuleBasedMapper()
        result = mapper.map("Hello")
        assert result.state.theta == 5       # len("Hello") % 360
        assert result.state.s == 0           # 'H'.isupper()
    """

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def mapper_id(self) -> str:
        return "hve.rule_based"

    @property
    def mapper_version(self) -> str:
        return "1.0.0"

    # ── Core API ──────────────────────────────────────────────────────

    def map(self, input_data: Any, **kwargs: Any) -> MappingResult:
        """Map a string to an HVE state using structural rules.

        Args:
            input_data: A non-empty ``str``.
            **kwargs: Unused.

        Returns:
            A :class:`MappingResult` with ``confidence=0.5`` (heuristic).

        Raises:
            TypeError: If *input_data* is not a ``str``.
            ValueError: If the string is empty.
        """
        if not isinstance(input_data, str):
            raise TypeError(
                f"RuleBasedMapper only supports str, got {type(input_data).__name__}"
            )
        if not input_data:
            raise ValueError("input string must be non-empty")

        h = _stable_hash(input_data)

        theta = len(input_data) % THETA_CARDINALITY
        s = 0 if input_data[0].isupper() else 1
        tau = h % TAU_CARDINALITY
        phi = h % PHI_CARDINALITY

        state = HVEState(theta, s, tau, phi)

        return MappingResult(
            state=state,
            confidence=0.5,
            mapper_id=self.mapper_id,
            mapper_version=self.mapper_version,
            provenance={
                "method": "rule_based",
                "rules": {
                    "theta": "len(input) % 360",
                    "s": "0 if input[0].isupper() else 1",
                    "tau": "sha256(input) % 5",
                    "phi": "sha256(input) % 9",
                },
                "input": input_data,
                "stable_hash": h,
            },
        )

    def supports(self, input_type: type) -> bool:
        """Return ``True`` for ``str``."""
        return input_type is str
