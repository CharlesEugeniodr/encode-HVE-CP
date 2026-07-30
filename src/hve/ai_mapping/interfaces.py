"""AI Mapping Layer — abstract mapper interface.

Every mapper—deterministic, rule-based, or ML-based—must subclass
:class:`AbstractMapper` and implement its four abstract members.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from hve.ai_mapping.result import MappingResult


class AbstractMapper(ABC):
    """Base contract for all HVE mappers.

    Subclasses provide a concrete ``map`` that transforms arbitrary input
    data into one or more :class:`MappingResult` instances, and a
    ``supports`` predicate that advertises which input types the mapper
    can handle.
    """

    # ── Identity ──────────────────────────────────────────────────────

    @property
    @abstractmethod
    def mapper_id(self) -> str:
        """Globally unique identifier for this mapper (e.g. ``'hve.deterministic'``)."""
        ...

    @property
    @abstractmethod
    def mapper_version(self) -> str:
        """Semantic version string for this mapper (e.g. ``'1.0.0'``)."""
        ...

    # ── Core API ──────────────────────────────────────────────────────

    @abstractmethod
    def map(self, input_data: Any, **kwargs: Any) -> MappingResult:
        """Map *input_data* to an HVE state.

        Args:
            input_data: The datum to encode.
            **kwargs: Mapper-specific options.

        Returns:
            A :class:`MappingResult` with the primary state, confidence,
            provenance, and any alternatives.

        Raises:
            HVEError: If the input cannot be mapped.
            TypeError: If the input type is not supported.
        """
        ...

    @abstractmethod
    def supports(self, input_type: type) -> bool:
        """Return ``True`` if this mapper can handle *input_type*.

        Args:
            input_type: The Python type to check.

        Returns:
            Whether the mapper accepts that type.
        """
        ...
