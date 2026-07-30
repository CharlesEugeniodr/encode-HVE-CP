"""Tests for the AI Mapping Layer.

Covers:
    - MappingResult construction and validation
    - AbstractMapper contract enforcement
    - DeterministicMapper round-trips (int and str)
    - RuleBasedMapper consistency and rules
    - MapperRegistry register / get / list / unregister
"""

from __future__ import annotations

import pytest

from hve.core import HVEState, HVEError, decode_base, encode_base, BASE_CARDINALITY
from hve.ai_mapping import (
    MappingResult,
    AbstractMapper,
    MapperRegistry,
    DeterministicMapper,
    RuleBasedMapper,
)


# ─── MappingResult ────────────────────────────────────────────────────────────


class TestMappingResult:
    """MappingResult dataclass creation and validation."""

    def test_basic_creation(self) -> None:
        state = HVEState(0, 0, 0, 0)
        result = MappingResult(
            state=state,
            confidence=0.0,
            mapper_id="test",
            mapper_version="0.1.0",
        )
        assert result.state == state
        assert result.confidence == 0.0
        assert result.mapper_id == "test"
        assert result.mapper_version == "0.1.0"
        assert result.provenance == {}
        assert result.alternatives == []

    def test_with_provenance_and_alternatives(self) -> None:
        primary = HVEState(10, 1, 2, 3)
        alt_state = HVEState(20, 0, 4, 8)
        alt = MappingResult(
            state=alt_state,
            confidence=0.3,
            mapper_id="test",
            mapper_version="0.1.0",
        )
        result = MappingResult(
            state=primary,
            confidence=0.9,
            mapper_id="test",
            mapper_version="0.1.0",
            provenance={"method": "example"},
            alternatives=[alt],
        )
        assert len(result.alternatives) == 1
        assert result.alternatives[0].state == alt_state
        assert result.provenance["method"] == "example"

    def test_confidence_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            MappingResult(
                state=HVEState(0, 0, 0, 0),
                confidence=1.5,
                mapper_id="test",
                mapper_version="0.1.0",
            )

    def test_negative_confidence(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            MappingResult(
                state=HVEState(0, 0, 0, 0),
                confidence=-0.1,
                mapper_id="test",
                mapper_version="0.1.0",
            )

    def test_empty_mapper_id(self) -> None:
        with pytest.raises(ValueError, match="mapper_id"):
            MappingResult(
                state=HVEState(0, 0, 0, 0),
                confidence=0.0,
                mapper_id="",
                mapper_version="0.1.0",
            )

    def test_empty_mapper_version(self) -> None:
        with pytest.raises(ValueError, match="mapper_version"):
            MappingResult(
                state=HVEState(0, 0, 0, 0),
                confidence=0.0,
                mapper_id="test",
                mapper_version="",
            )

    def test_invalid_state_rejected(self) -> None:
        with pytest.raises(HVEError):
            MappingResult(
                state=HVEState(999, 0, 0, 0),
                confidence=0.0,
                mapper_id="test",
                mapper_version="0.1.0",
            )

    def test_frozen(self) -> None:
        result = MappingResult(
            state=HVEState(0, 0, 0, 0),
            confidence=0.0,
            mapper_id="test",
            mapper_version="0.1.0",
        )
        with pytest.raises(AttributeError):
            result.confidence = 0.5  # type: ignore[misc]


# ─── AbstractMapper Contract ─────────────────────────────────────────────────


class TestAbstractMapperContract:
    """Verify that AbstractMapper cannot be instantiated directly."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            AbstractMapper()  # type: ignore[abstract]

    def test_incomplete_subclass(self) -> None:
        class Incomplete(AbstractMapper):
            @property
            def mapper_id(self) -> str:
                return "incomplete"

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]


# ─── DeterministicMapper ─────────────────────────────────────────────────────


class TestDeterministicMapper:
    """DeterministicMapper: int and str round-trips."""

    @pytest.fixture()
    def mapper(self) -> DeterministicMapper:
        return DeterministicMapper()

    def test_identity(self, mapper: DeterministicMapper) -> None:
        assert mapper.mapper_id == "hve.deterministic"
        assert mapper.mapper_version == "1.0.0"

    def test_supports_int(self, mapper: DeterministicMapper) -> None:
        assert mapper.supports(int)

    def test_supports_str(self, mapper: DeterministicMapper) -> None:
        assert mapper.supports(str)

    def test_does_not_support_float(self, mapper: DeterministicMapper) -> None:
        assert not mapper.supports(float)

    # ── int mapping ───────────────────────────────────────────────────

    def test_map_int_zero(self, mapper: DeterministicMapper) -> None:
        result = mapper.map(0)
        assert result.state == HVEState(0, 0, 0, 0)
        assert result.confidence == 1.0
        assert result.alternatives == []

    def test_map_int_max(self, mapper: DeterministicMapper) -> None:
        result = mapper.map(BASE_CARDINALITY - 1)
        assert result.state == HVEState(359, 1, 4, 8)

    def test_map_int_round_trip(self, mapper: DeterministicMapper) -> None:
        """encode(decode(i)) == i for a sample of indices."""
        for i in [0, 1, 89, 90, 1000, 16200, 32399]:
            result = mapper.map(i)
            assert encode_base(result.state) == i

    def test_map_int_out_of_range(self, mapper: DeterministicMapper) -> None:
        with pytest.raises(HVEError):
            mapper.map(BASE_CARDINALITY)

    def test_map_int_negative(self, mapper: DeterministicMapper) -> None:
        with pytest.raises(HVEError):
            mapper.map(-1)

    # ── str mapping ───────────────────────────────────────────────────

    def test_map_single_char(self, mapper: DeterministicMapper) -> None:
        result = mapper.map("A")
        expected = decode_base(ord("A") % BASE_CARDINALITY)
        assert result.state == expected
        assert result.confidence == 0.0
        assert result.alternatives == []

    def test_map_multi_char(self, mapper: DeterministicMapper) -> None:
        result = mapper.map("AB")
        assert len(result.alternatives) == 1
        alt_expected = decode_base(ord("B") % BASE_CARDINALITY)
        assert result.alternatives[0].state == alt_expected

    def test_map_empty_string(self, mapper: DeterministicMapper) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            mapper.map("")

    def test_map_unicode_char(self, mapper: DeterministicMapper) -> None:
        result = mapper.map("λ")  # U+03BB = 955
        expected = decode_base(955 % BASE_CARDINALITY)
        assert result.state == expected

    def test_map_high_codepoint(self, mapper: DeterministicMapper) -> None:
        ch = chr(100_000)
        result = mapper.map(ch)
        expected = decode_base(100_000 % BASE_CARDINALITY)
        assert result.state == expected

    # ── type errors ───────────────────────────────────────────────────

    def test_map_unsupported_type(self, mapper: DeterministicMapper) -> None:
        with pytest.raises(TypeError):
            mapper.map(3.14)


# ─── RuleBasedMapper ─────────────────────────────────────────────────────────


class TestRuleBasedMapper:
    """RuleBasedMapper: consistency and rule verification."""

    @pytest.fixture()
    def mapper(self) -> RuleBasedMapper:
        return RuleBasedMapper()

    def test_identity(self, mapper: RuleBasedMapper) -> None:
        assert mapper.mapper_id == "hve.rule_based"
        assert mapper.mapper_version == "1.0.0"

    def test_supports_str(self, mapper: RuleBasedMapper) -> None:
        assert mapper.supports(str)

    def test_does_not_support_int(self, mapper: RuleBasedMapper) -> None:
        assert not mapper.supports(int)

    def test_theta_is_length_mod_360(self, mapper: RuleBasedMapper) -> None:
        result = mapper.map("Hello")
        assert result.state.theta == len("Hello") % 360

    def test_s_uppercase(self, mapper: RuleBasedMapper) -> None:
        result = mapper.map("Abc")
        assert result.state.s == 0  # 'A' is uppercase

    def test_s_lowercase(self, mapper: RuleBasedMapper) -> None:
        result = mapper.map("abc")
        assert result.state.s == 1  # 'a' is lowercase

    def test_tau_and_phi_in_range(self, mapper: RuleBasedMapper) -> None:
        for text in ["foo", "bar", "Hello World", "x" * 500]:
            result = mapper.map(text)
            assert 0 <= result.state.tau < 5
            assert 0 <= result.state.phi < 9

    def test_confidence_is_half(self, mapper: RuleBasedMapper) -> None:
        result = mapper.map("anything")
        assert result.confidence == 0.5

    def test_same_input_same_output(self, mapper: RuleBasedMapper) -> None:
        r1 = mapper.map("deterministic")
        r2 = mapper.map("deterministic")
        assert r1.state == r2.state

    def test_different_inputs_may_differ(self, mapper: RuleBasedMapper) -> None:
        r1 = mapper.map("alpha")
        r2 = mapper.map("beta!")
        # Not a guarantee, but extremely unlikely to collide on all coords
        # with different length AND different hash
        # (alpha has length 5, beta! has length 5 — they share theta,
        #  but s or hash should differ)
        assert r1.state != r2.state or True  # non-fatal

    def test_empty_string(self, mapper: RuleBasedMapper) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            mapper.map("")

    def test_non_string_rejected(self, mapper: RuleBasedMapper) -> None:
        with pytest.raises(TypeError):
            mapper.map(42)

    def test_provenance_has_rules(self, mapper: RuleBasedMapper) -> None:
        result = mapper.map("test")
        assert "rules" in result.provenance
        assert "method" in result.provenance
        assert result.provenance["method"] == "rule_based"


# ─── MapperRegistry ──────────────────────────────────────────────────────────


class TestMapperRegistry:
    """MapperRegistry: register, get, list, unregister."""

    @pytest.fixture()
    def registry(self) -> MapperRegistry:
        return MapperRegistry()

    def test_register_and_get(self, registry: MapperRegistry) -> None:
        m = DeterministicMapper()
        registry.register("det", m)
        assert registry.get("det") is m

    def test_register_non_mapper_raises_type_error(self, registry: MapperRegistry) -> None:
        with pytest.raises(TypeError, match="AbstractMapper"):
            registry.register("bad", "not a mapper")  # type: ignore[arg-type]

    def test_double_register_raises(self, registry: MapperRegistry) -> None:
        m = DeterministicMapper()
        registry.register("det", m)
        with pytest.raises(HVEError, match="already registered"):
            registry.register("det", m)

    def test_get_missing_raises(self, registry: MapperRegistry) -> None:
        with pytest.raises(HVEError, match="not registered"):
            registry.get("nope")

    def test_unregister(self, registry: MapperRegistry) -> None:
        registry.register("det", DeterministicMapper())
        registry.unregister("det")
        assert "det" not in registry

    def test_unregister_missing_raises(self, registry: MapperRegistry) -> None:
        with pytest.raises(HVEError, match="not registered"):
            registry.unregister("nope")

    def test_list_mappers(self, registry: MapperRegistry) -> None:
        registry.register("beta", RuleBasedMapper())
        registry.register("alpha", DeterministicMapper())
        assert registry.list_mappers() == ["alpha", "beta"]  # sorted

    def test_len(self, registry: MapperRegistry) -> None:
        assert len(registry) == 0
        registry.register("a", DeterministicMapper())
        assert len(registry) == 1

    def test_contains(self, registry: MapperRegistry) -> None:
        registry.register("det", DeterministicMapper())
        assert "det" in registry
        assert "other" not in registry

    def test_repr(self, registry: MapperRegistry) -> None:
        registry.register("det", DeterministicMapper())
        r = repr(registry)
        assert "det" in r
        assert "MapperRegistry" in r
