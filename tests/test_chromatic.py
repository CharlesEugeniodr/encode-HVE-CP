"""Tests for hve.chromatic — HVE-χ pointed color extension."""

import pytest

from hve.core import HVEState, HVEError, encode_base, decode_base
from hve.chromatic import (
    HVEColor,
    validate_color,
    color_kappa,
    color_kappa_inverse,
    encode_chi,
    decode_chi,
    COLOR_RGB_CARDINALITY,
    COLOR_POINTED_CARDINALITY,
    CHI_CARDINALITY,
    CHI_MAX_INDEX,
)


class TestConstants:
    def test_color_cardinalities(self):
        assert COLOR_RGB_CARDINALITY == 2**24
        assert COLOR_POINTED_CARDINALITY == 2**24 + 1
        assert CHI_CARDINALITY == 32400 * COLOR_POINTED_CARDINALITY
        assert CHI_MAX_INDEX == CHI_CARDINALITY - 1


class TestHVEColor:
    def test_no_color(self):
        c = HVEColor.no_color()
        assert not c.present
        assert c.r == c.g == c.b == 0

    def test_rgb_black(self):
        c = HVEColor.rgb(0, 0, 0)
        assert c.present
        assert c.r == c.g == c.b == 0

    def test_no_color_is_not_black(self):
        assert HVEColor.no_color() != HVEColor.rgb(0, 0, 0)

    def test_rgb_white(self):
        c = HVEColor.rgb(255, 255, 255)
        assert c.present and c.r == c.g == c.b == 255

    def test_invalid_no_color_with_rgb(self):
        with pytest.raises(HVEError, match="NoColor"):
            validate_color(HVEColor(False, 1, 0, 0))

    def test_invalid_channel_range(self):
        with pytest.raises(HVEError):
            HVEColor.rgb(256, 0, 0)
        with pytest.raises(HVEError):
            HVEColor.rgb(0, -1, 0)


class TestKappaMapping:
    def test_no_color_kappa(self):
        assert color_kappa(HVEColor.no_color()) == 0

    def test_black_kappa(self):
        assert color_kappa(HVEColor.rgb(0, 0, 0)) == 1

    def test_white_kappa(self):
        assert color_kappa(HVEColor.rgb(255, 255, 255)) == COLOR_RGB_CARDINALITY

    def test_roundtrip_boundary_colors(self):
        colors = [
            HVEColor.no_color(),
            HVEColor.rgb(0, 0, 0),
            HVEColor.rgb(255, 255, 255),
            HVEColor.rgb(1, 2, 3),
            HVEColor.rgb(255, 0, 128),
        ]
        for color in colors:
            k = color_kappa(color)
            recovered = color_kappa_inverse(k)
            assert recovered == color

    def test_kappa_inverse_out_of_range(self):
        with pytest.raises(HVEError):
            color_kappa_inverse(COLOR_POINTED_CARDINALITY)


class TestChiBijection:
    def test_boundary_states_and_colors(self):
        states = [
            HVEState(0, 0, 0, 0),
            HVEState(359, 1, 4, 8),
            HVEState(123, 1, 2, 7),
        ]
        colors = [
            HVEColor.no_color(),
            HVEColor.rgb(0, 0, 0),
            HVEColor.rgb(255, 255, 255),
            HVEColor.rgb(10, 20, 30),
        ]
        for state in states:
            for color in colors:
                index = encode_chi(state, color)
                assert 0 <= index <= CHI_MAX_INDEX
                dec_state, dec_color = decode_chi(index)
                assert dec_state == state
                assert dec_color == color

    def test_chi_random_roundtrip(self):
        """100,000 deterministic random round-trips."""
        rng = 0xC0FFEE42
        for _ in range(100_000):
            rng ^= (rng << 13) & 0xFFFFFFFF
            rng ^= (rng >> 17)
            rng ^= (rng << 5) & 0xFFFFFFFF
            rng &= 0xFFFFFFFF
            state = HVEState(rng % 360, (rng >> 10) % 2,
                             (rng >> 11) % 5, (rng >> 14) % 9)
            rng ^= (rng << 13) & 0xFFFFFFFF
            rng ^= (rng >> 17)
            rng ^= (rng << 5) & 0xFFFFFFFF
            rng &= 0xFFFFFFFF
            color = HVEColor.rgb(rng & 0xFF, (rng >> 8) & 0xFF, (rng >> 16) & 0xFF)
            index = encode_chi(state, color)
            dec_state, dec_color = decode_chi(index)
            assert dec_state == state
            assert dec_color == color

    def test_chi_max_index_boundary(self):
        with pytest.raises(HVEError):
            decode_chi(CHI_MAX_INDEX + 1)

    def test_chi_first_index(self):
        state, color = decode_chi(0)
        assert state == HVEState(0, 0, 0, 0)
        assert color == HVEColor.no_color()

    def test_chi_last_index(self):
        state, color = decode_chi(CHI_MAX_INDEX)
        assert state == HVEState(359, 1, 4, 8)
        assert color == HVEColor.rgb(255, 255, 255)
