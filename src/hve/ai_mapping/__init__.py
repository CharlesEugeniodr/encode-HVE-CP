"""HVE AI Mapping Layer — extensible mapper framework.

This sub-package defines the contract for mapping arbitrary data into the
HVE state space, plus two reference implementations:

* :class:`DeterministicMapper` — exact, reversible encoding.
* :class:`RuleBasedMapper` — demonstration rule-driven encoding.

No trained ML model is included.  Third-party mappers should subclass
:class:`AbstractMapper` and register with :class:`MapperRegistry`.
"""

from __future__ import annotations

from hve.ai_mapping.result import MappingResult
from hve.ai_mapping.interfaces import AbstractMapper
from hve.ai_mapping.registry import MapperRegistry
from hve.ai_mapping.deterministic_mapper import DeterministicMapper
from hve.ai_mapping.rule_based_mapper import RuleBasedMapper

__all__ = [
    "MappingResult",
    "AbstractMapper",
    "MapperRegistry",
    "DeterministicMapper",
    "RuleBasedMapper",
]
