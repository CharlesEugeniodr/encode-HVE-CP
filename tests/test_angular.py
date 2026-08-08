"""Tests for hve.angular — discrete circular geometry on C₃₆₀."""

from __future__ import annotations

import math

import pytest

from hve.angular import (
    ShortestPath,
    arc_contains,
    circular_center,
    circular_distance,
    circular_interval,
    circular_mean,
    geodesic_distance,
    neighborhood,
    normalized_distance,
    project_resolution,
    quantize_base,
    quantize_micro,
    quantize_nano,
    rotate,
    sector_group,
    shortest_path,
)
from hve.core import HVEError


# ─── circular_distance ───────────────────────────────────────────────────────

class TestCircularDistance:
    """δ(θ₁, θ₂) = min(|θ₁−θ₂|, 360−|θ₁−θ₂|)."""

    def test_same_angle(self) -> None:
        assert circular_distance(0, 0) == 0
        assert circular_distance(180, 180) == 0

    def test_adjacent_across_zero(self) -> None:
        assert circular_distance(359, 0) == 1

    def test_diametrically_opposite(self) -> None:
        assert circular_distance(0, 180) == 180
        assert circular_distance(90, 270) == 180

    def test_symmetric(self) -> None:
        assert circular_distance(10, 350) == circular_distance(350, 10)

    def test_small_gap(self) -> None:
        assert circular_distance(5, 10) == 5

    def test_large_raw_gap_wraps(self) -> None:
        assert circular_distance(1, 359) == 2

    def test_quarter_turn(self) -> None:
        assert circular_distance(0, 90) == 90


# ─── normalized_distance ─────────────────────────────────────────────────────

class TestNormalizedDistance:
    """δ/180, result in [0, 1]."""

    def test_adjacent_across_zero(self) -> None:
        assert normalized_distance(359, 0) == pytest.approx(1 / 180)

    def test_max_distance(self) -> None:
        assert normalized_distance(0, 180) == pytest.approx(1.0)

    def test_zero_distance(self) -> None:
        assert normalized_distance(42, 42) == pytest.approx(0.0)


# ─── shortest_path ───────────────────────────────────────────────────────────

class TestShortestPath:
    """Path queries on C₃₆₀."""

    def test_clockwise_short(self) -> None:
        sp = shortest_path(0, 3)
        assert sp.distance == 3
        assert sp.clockwise == 3
        assert sp.counterclockwise == 357
        assert sp.direction == "cw"
        assert sp.arc == [1, 2]

    def test_counterclockwise_short(self) -> None:
        sp = shortest_path(3, 0)
        assert sp.distance == 3
        assert sp.direction == "ccw"
        assert sp.arc == [2, 1]

    def test_antipodal(self) -> None:
        sp = shortest_path(0, 180)
        assert sp.distance == 180
        assert sp.direction == "antipodal"

    def test_antipodal_ninety(self) -> None:
        sp = shortest_path(90, 270)
        assert sp.distance == 180
        assert sp.direction == "antipodal"

    def test_wrap_around_cw(self) -> None:
        sp = shortest_path(358, 2)
        assert sp.distance == 4
        assert sp.direction == "cw"
        assert sp.arc == [359, 0, 1]

    def test_same_point(self) -> None:
        sp = shortest_path(42, 42)
        assert sp.distance == 0
        assert sp.direction == "cw"
        assert sp.arc == []


# ─── neighborhood ─────────────────────────────────────────────────────────────

class TestNeighborhood:
    """Closed r-neighbourhood N_r(θ) on C₃₆₀."""

    def test_radius_one_at_zero(self) -> None:
        assert neighborhood(0, 1) == {359, 0, 1}

    def test_radius_two_near_boundary(self) -> None:
        assert neighborhood(358, 2) == {356, 357, 358, 359, 0}

    def test_radius_zero(self) -> None:
        assert neighborhood(100, 0) == {100}

    def test_negative_radius_raises(self) -> None:
        with pytest.raises(HVEError):
            neighborhood(0, -1)

    def test_radius_one_at_180(self) -> None:
        assert neighborhood(180, 1) == {179, 180, 181}


# ─── rotate ───────────────────────────────────────────────────────────────────

class TestRotate:
    """Rotation θ + δ (mod 360)."""

    def test_wrap_forward(self) -> None:
        assert rotate(359, 1) == 0

    def test_wrap_backward(self) -> None:
        assert rotate(0, -1) == 359

    def test_no_wrap(self) -> None:
        assert rotate(10, 5) == 15

    def test_full_rotation(self) -> None:
        assert rotate(42, 360) == 42

    def test_large_negative(self) -> None:
        assert rotate(0, -360) == 0


# ─── circular_interval ───────────────────────────────────────────────────────

class TestCircularInterval:
    """Clockwise arc [start → end]."""

    def test_wraps_through_zero(self) -> None:
        assert circular_interval(358, 2) == [358, 359, 0, 1, 2]

    def test_same_point(self) -> None:
        assert circular_interval(90, 90) == [90]

    def test_no_wrap(self) -> None:
        assert circular_interval(0, 4) == [0, 1, 2, 3, 4]

    def test_full_arc(self) -> None:
        result = circular_interval(0, 359)
        assert len(result) == 360
        assert result[0] == 0
        assert result[-1] == 359


# ─── arc_contains ─────────────────────────────────────────────────────────────

class TestArcContains:
    """Membership in the clockwise arc [start → end]."""

    def test_inside_no_wrap(self) -> None:
        assert arc_contains(10, 20, 15) is True

    def test_outside_no_wrap(self) -> None:
        assert arc_contains(10, 20, 25) is False

    def test_at_start(self) -> None:
        assert arc_contains(10, 20, 10) is True

    def test_at_end(self) -> None:
        assert arc_contains(10, 20, 20) is True

    def test_wrap_inside(self) -> None:
        assert arc_contains(350, 10, 0) is True

    def test_wrap_outside(self) -> None:
        assert arc_contains(350, 10, 180) is False


# ─── circular_mean / circular_center ─────────────────────────────────────────

class TestCircularMean:
    """Circular mean direction via atan2(Σ sin, Σ cos)."""

    def test_single_angle(self) -> None:
        assert circular_mean([90]) == pytest.approx(90.0)

    def test_symmetric_pair(self) -> None:
        # 350° and 10° → mean at 0° (which is ≡ 360° on the cycle)
        result = circular_mean([350, 10])
        assert result % 360.0 == pytest.approx(0.0, abs=0.5)

    def test_uniform_quadrants_raises(self) -> None:
        # [0, 90, 180, 270] — sin/cos sums ≈ 0, direction undefined
        with pytest.raises(HVEError, match="cancel out"):
            circular_mean([0, 90, 180, 270])

    def test_alias(self) -> None:
        angles = [30, 60]
        assert circular_center(angles) == circular_mean(angles)

    def test_empty_raises(self) -> None:
        with pytest.raises(HVEError):
            circular_center([])


# ─── sector_group ─────────────────────────────────────────────────────────────

class TestSectorGroup:
    """Partition angles into equal sectors."""

    def test_four_sectors(self) -> None:
        angles = list(range(360))
        groups = sector_group(angles, 4)
        assert len(groups) == 4
        for sector_idx in range(4):
            assert len(groups[sector_idx]) == 90

    def test_sector_assignment(self) -> None:
        groups = sector_group([0, 89, 90, 179, 180, 269, 270, 359], 4)
        assert 0 in groups[0]
        assert 89 in groups[0]
        assert 90 in groups[1]
        assert 180 in groups[2]
        assert 270 in groups[3]
        assert 359 in groups[3]

    def test_bad_sector_count_raises(self) -> None:
        with pytest.raises(HVEError):
            sector_group([0], 7)  # 360 % 7 ≠ 0


# ─── quantize_base ───────────────────────────────────────────────────────────

class TestQuantizeBase:
    """Identity quantization at 1° resolution."""

    def test_identity(self) -> None:
        assert quantize_base(42) == 42

    def test_wraps(self) -> None:
        assert quantize_base(360) == 0
        assert quantize_base(-1) == 359


# ─── quantize_micro ──────────────────────────────────────────────────────────

class TestQuantizeMicro:
    """0.001° resolution quantization (m=1000)."""

    def test_exact_degree(self) -> None:
        base, micro = quantize_micro(45.0)
        assert base == 45
        assert micro == 0

    def test_half_degree(self) -> None:
        # 45.5° = base=45, fractional=0.5, micro = int(0.5 * 1000) = 500
        base, micro = quantize_micro(45.5)
        assert base == 45
        assert micro == 500

    def test_wrap(self) -> None:
        # 360.3° mod 360 = 0.3°, base=0, micro = int(0.3 * 1000) = 300
        base, micro = quantize_micro(360.3)
        assert base == 0
        assert micro == 300

    def test_small_fraction(self) -> None:
        # With round(): round(0.001 * 1000) = round(0.9999...) = 1
        base, micro = quantize_micro(1.001)
        assert base == 1
        assert micro == 1

    def test_cardinality(self) -> None:
        from hve.angular import micro_angular_cardinality, micro_state_cardinality
        assert micro_angular_cardinality() == 360_000
        assert micro_state_cardinality() == 32_400_000

    def test_composition_factors(self) -> None:
        from hve.angular import MICRO_FACTOR, NANO_PER_MICRO, NANO_TOTAL_FACTOR
        assert MICRO_FACTOR == 1_000
        assert NANO_PER_MICRO == 1_080
        assert NANO_TOTAL_FACTOR == MICRO_FACTOR * NANO_PER_MICRO
        assert NANO_TOTAL_FACTOR == 1_080_000


# ─── quantize_nano ────────────────────────────────────────────────────────────

class TestQuantizeNano:
    """Sub-micro resolution quantization (m=1000, n=1080)."""

    def test_exact_degree(self) -> None:
        base, micro, nano = quantize_nano(90.0)
        assert base == 90
        assert micro == 0
        assert nano == 0

    def test_precise_value(self) -> None:
        # With round()-based flat-tick approach:
        # 10.35 * 1,080,000 = 11,178,000 (exact)
        # decompose: 11,178,000 / 1080 = 10,350; 10,350 / 1000 = 10 r 350
        base, micro, nano = quantize_nano(10.35)
        assert base == 10
        assert micro == 350
        assert nano == 0

    def test_fine_granularity(self) -> None:
        # 0.001 * 1,080,000 = 1080
        # decompose: 1080 / 1080 = 1 r 0; 1 / 1000 = 0 r 1
        base, micro, nano = quantize_nano(0.001)
        assert base == 0
        assert micro == 1
        assert nano == 0

    def test_sub_micro_fraction(self) -> None:
        # 0.0005 * 1,080,000 = 540
        # decompose: 540 / 1080 = 0 r 540; 0 / 1000 = 0 r 0
        base, micro, nano = quantize_nano(0.0005)
        assert base == 0
        assert micro == 0
        assert nano == 540

    def test_cardinality(self) -> None:
        from hve.angular import nano_angular_cardinality, nano_state_cardinality
        assert nano_angular_cardinality() == 388_800_000
        assert nano_state_cardinality() == 34_992_000_000


# ─── project_resolution ──────────────────────────────────────────────────────

class TestProjectResolution:
    """Project between base / micro / nano resolution levels."""

    def test_base_to_micro(self) -> None:
        assert project_resolution((90,), "base", "micro") == (90, 0)

    def test_base_to_nano(self) -> None:
        assert project_resolution((90,), "base", "nano") == (90, 0, 0)

    def test_micro_to_nano(self) -> None:
        assert project_resolution((90, 5), "micro", "nano") == (90, 5, 0)

    def test_nano_to_base(self) -> None:
        assert project_resolution((90, 5, 3), "nano", "base") == (90,)

    def test_nano_to_micro(self) -> None:
        assert project_resolution((90, 5, 3), "nano", "micro") == (90, 5)

    def test_same_level(self) -> None:
        assert project_resolution((42,), "base", "base") == (42,)

    def test_bad_level_raises(self) -> None:
        with pytest.raises(HVEError):
            project_resolution((1,), "base", "pico")

    def test_wrong_tuple_length_raises(self) -> None:
        with pytest.raises(HVEError):
            project_resolution((1, 2, 3), "base", "nano")


# ─── geodesic_distance ───────────────────────────────────────────────────────

class TestGeodesicDistance:
    """geodesic_distance must be an exact alias for circular_distance."""

    def test_matches_circular_distance(self) -> None:
        for a, b in [(0, 0), (359, 0), (0, 180), (90, 270), (1, 359)]:
            assert geodesic_distance(a, b) == circular_distance(a, b)
