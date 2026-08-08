"""AI Mapping Layer — result container.

A MappingResult captures the output of any mapper: the encoded HVE state,
confidence score, provenance metadata, and optional alternative mappings.
Deterministic mappers always emit confidence = 1.0 (exact table lookup).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hve.core import HVEState, validate_state


@dataclass(frozen=True, slots=True)
class MappingResult:
    """Immutable result produced by an :class:`AbstractMapper`.

    Attributes:
        state: The primary HVE state selected by the mapper.
        confidence: Confidence in the mapping, in [0.0, 1.0].
            Deterministic mappers use 1.0 (exact table lookup).
        mapper_id: Unique identifier of the mapper that produced this result.
        mapper_version: Semantic version of the mapper.
        provenance: Free-form metadata describing how the mapping was derived.
        alternatives: Ranked list of alternative mappings (may be empty).
    """

    state: HVEState
    confidence: float
    mapper_id: str
    mapper_version: str
    provenance: dict[str, Any] = field(default_factory=dict)
    alternatives: list[MappingResult] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_state(self.state)
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0.0, 1.0], got {self.confidence}"
            )
        if not self.mapper_id:
            raise ValueError("mapper_id must be a non-empty string")
        if not self.mapper_version:
            raise ValueError("mapper_version must be a non-empty string")
