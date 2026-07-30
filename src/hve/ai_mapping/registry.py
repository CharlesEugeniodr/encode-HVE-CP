"""AI Mapping Layer — mapper registry.

The :class:`MapperRegistry` is a lightweight service-locator that lets
callers discover and retrieve mappers by name at runtime.
"""

from __future__ import annotations

from hve.core import HVEError
from hve.ai_mapping.interfaces import AbstractMapper


class MapperRegistry:
    """Named registry of :class:`AbstractMapper` instances.

    Example::

        registry = MapperRegistry()
        registry.register("deterministic", DeterministicMapper())
        mapper = registry.get("deterministic")
    """

    def __init__(self) -> None:
        self._mappers: dict[str, AbstractMapper] = {}

    # ── Mutators ──────────────────────────────────────────────────────

    def register(self, name: str, mapper: AbstractMapper) -> None:
        """Register *mapper* under *name*.

        Args:
            name: A unique registry key.
            mapper: The mapper instance to register.

        Raises:
            HVEError: If *name* is already registered.
            TypeError: If *mapper* is not an :class:`AbstractMapper`.
        """
        if not isinstance(mapper, AbstractMapper):
            raise TypeError(
                f"mapper must be an AbstractMapper, got {type(mapper).__name__}"
            )
        if name in self._mappers:
            raise HVEError(f"mapper '{name}' is already registered")
        self._mappers[name] = mapper

    def unregister(self, name: str) -> None:
        """Remove the mapper registered under *name*.

        Args:
            name: The registry key to remove.

        Raises:
            HVEError: If *name* is not registered.
        """
        if name not in self._mappers:
            raise HVEError(f"mapper '{name}' is not registered")
        del self._mappers[name]

    # ── Queries ───────────────────────────────────────────────────────

    def get(self, name: str) -> AbstractMapper:
        """Retrieve the mapper registered under *name*.

        Args:
            name: The registry key.

        Returns:
            The :class:`AbstractMapper` instance.

        Raises:
            HVEError: If *name* is not registered.
        """
        if name not in self._mappers:
            raise HVEError(f"mapper '{name}' is not registered")
        return self._mappers[name]

    def list_mappers(self) -> list[str]:
        """Return an alphabetically sorted list of registered mapper names.

        Returns:
            List of registry keys.
        """
        return sorted(self._mappers)

    def __len__(self) -> int:
        return len(self._mappers)

    def __contains__(self, name: str) -> bool:
        return name in self._mappers

    def __repr__(self) -> str:
        names = ", ".join(self.list_mappers())
        return f"MapperRegistry([{names}])"
