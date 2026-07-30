"""Tests for hve.harmonic — DFT on G = Z₃₆₀ × Z₂ × Z₅ × Z₉."""

import numpy as np
import pytest

from hve.harmonic import (
    character,
    character_matrix,
    dft,
    idft,
    dft_reference,
    convolve,
    correlate,
    power_spectrum,
    spectral_filter,
    parseval_check,
    orthogonality_check,
    harmonic_modes,
    laplacian_spectrum,
    GROUP_SHAPE,
    GROUP_ORDER,
)


class TestCharacter:
    def test_trivial_character(self):
        """χ₀(g) = 1 for all g."""
        k0 = (0, 0, 0, 0)
        for g in [(0, 0, 0, 0), (180, 1, 2, 4), (359, 1, 4, 8)]:
            assert abs(character(k0, g) - 1.0) < 1e-14

    def test_on_unit_circle(self):
        """All characters lie on S¹ ⊂ ℂ."""
        for k in [(1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1),
                  (100, 1, 3, 7)]:
            for g in [(90, 0, 2, 3), (180, 1, 4, 8)]:
                val = character(k, g)
                assert abs(abs(val) - 1.0) < 1e-14

    def test_known_value(self):
        """χ_(1,0,0,0)(180,0,0,0) = exp(2πi·180/360) = exp(πi) = -1."""
        val = character((1, 0, 0, 0), (180, 0, 0, 0))
        assert abs(val - (-1.0)) < 1e-14

    def test_character_half(self):
        """χ_(0,1,0,0)(0,1,0,0) = exp(2πi·1/2) = exp(πi) = -1."""
        val = character((0, 1, 0, 0), (0, 1, 0, 0))
        assert abs(val - (-1.0)) < 1e-14


class TestCharacterMatrix:
    def test_shape(self):
        assert character_matrix("theta").shape == (360, 360)
        assert character_matrix("s").shape == (2, 2)
        assert character_matrix("tau").shape == (5, 5)
        assert character_matrix("phi").shape == (9, 9)

    def test_unitary(self):
        """DFT matrices are unitary up to scaling."""
        for axis in ("s", "tau", "phi"):
            W = character_matrix(axis)
            N = W.shape[0]
            product = W @ W.conj().T / N
            assert np.allclose(product, np.eye(N), atol=1e-12)


class TestDFTRoundTrip:
    def test_idft_of_dft_is_identity(self):
        """idft(dft(f)) ≈ f for random signal."""
        rng = np.random.default_rng(42)
        f = rng.standard_normal(GROUP_SHAPE) + 1j * rng.standard_normal(GROUP_SHAPE)
        recovered = idft(dft(f))
        assert np.allclose(recovered, f, atol=1e-10)

    def test_dft_of_constant(self):
        """DFT of constant function: f̂(0) = |G|·c, f̂(k≠0) = 0."""
        c = 3.0 + 2.0j
        f = np.full(GROUP_SHAPE, c, dtype=np.complex128)
        f_hat = dft(f)
        assert abs(f_hat[0, 0, 0, 0] - GROUP_ORDER * c) < 1e-8
        # All other coefficients should be ~0
        f_hat_copy = f_hat.copy()
        f_hat_copy[0, 0, 0, 0] = 0
        assert np.max(np.abs(f_hat_copy)) < 1e-8

    def test_dft_of_delta(self):
        """DFT of δ at origin: f̂(k) = 1 for all k."""
        f = np.zeros(GROUP_SHAPE, dtype=np.complex128)
        f[0, 0, 0, 0] = 1.0
        f_hat = dft(f)
        assert np.allclose(f_hat, 1.0, atol=1e-10)


class TestDFTvsReference:
    def test_small_subgroup(self):
        """Compare separable DFT with reference on a small domain.

        We test on the full group but with a sparse signal
        (only a few nonzero entries) to make the reference tractable.
        """
        rng = np.random.default_rng(123)
        f = np.zeros(GROUP_SHAPE, dtype=np.complex128)
        # Set a few entries
        for _ in range(20):
            idx = (rng.integers(0, 360), rng.integers(0, 2),
                   rng.integers(0, 5), rng.integers(0, 9))
            f[idx] = rng.standard_normal() + 1j * rng.standard_normal()

        # We cannot run the full reference (too slow for all 32400 outputs),
        # so we check a few specific k values
        f_hat_sep = dft(f)
        for k in [(0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0),
                  (0, 0, 0, 1), (5, 1, 2, 3)]:
            # Direct computation for this specific k
            total = 0j
            for idx in np.ndindex(*GROUP_SHAPE):
                if f[idx] != 0:
                    total += f[idx] * character(k, idx).conjugate()
            assert abs(f_hat_sep[k] - total) < 1e-8, f"mismatch at k={k}"


class TestParseval:
    def test_parseval_random(self):
        rng = np.random.default_rng(99)
        f = rng.standard_normal(GROUP_SHAPE) + 1j * rng.standard_normal(GROUP_SHAPE)
        f_hat = dft(f)
        assert parseval_check(f, f_hat, tol=1e-8)

    def test_parseval_zero(self):
        f = np.zeros(GROUP_SHAPE, dtype=np.complex128)
        f_hat = dft(f)
        assert parseval_check(f, f_hat)


class TestOrthogonality:
    def test_same_k(self):
        assert orthogonality_check((0, 0, 0, 0), (0, 0, 0, 0))
        assert orthogonality_check((5, 1, 2, 3), (5, 1, 2, 3))

    def test_different_k(self):
        assert orthogonality_check((0, 0, 0, 0), (1, 0, 0, 0))
        assert orthogonality_check((0, 0, 0, 0), (0, 1, 0, 0))
        assert orthogonality_check((5, 1, 2, 3), (6, 0, 1, 4))


class TestConvolution:
    def test_convolution_with_delta(self):
        """Convolution with δ at origin is identity."""
        rng = np.random.default_rng(77)
        f = rng.standard_normal(GROUP_SHAPE) + 1j * rng.standard_normal(GROUP_SHAPE)
        delta = np.zeros(GROUP_SHAPE, dtype=np.complex128)
        delta[0, 0, 0, 0] = 1.0
        result = convolve(f, delta)
        assert np.allclose(result, f, atol=1e-8)

    def test_convolution_is_commutative(self):
        rng = np.random.default_rng(88)
        f = rng.standard_normal(GROUP_SHAPE) + 1j * rng.standard_normal(GROUP_SHAPE)
        g = rng.standard_normal(GROUP_SHAPE) + 1j * rng.standard_normal(GROUP_SHAPE)
        assert np.allclose(convolve(f, g), convolve(g, f), atol=1e-8)


class TestPowerSpectrum:
    def test_non_negative(self):
        rng = np.random.default_rng(55)
        f = rng.standard_normal(GROUP_SHAPE)
        ps = power_spectrum(f)
        assert np.all(ps >= -1e-15)

    def test_delta_power(self):
        """Power spectrum of delta has uniform magnitude."""
        f = np.zeros(GROUP_SHAPE, dtype=np.complex128)
        f[0, 0, 0, 0] = 1.0
        ps = power_spectrum(f)
        assert np.allclose(ps, 1.0, atol=1e-10)


class TestSpectralFilter:
    def test_all_pass(self):
        """Mask of ones = identity."""
        rng = np.random.default_rng(33)
        f = rng.standard_normal(GROUP_SHAPE) + 1j * rng.standard_normal(GROUP_SHAPE)
        mask = np.ones(GROUP_SHAPE, dtype=np.complex128)
        result = spectral_filter(f, mask)
        assert np.allclose(result, f, atol=1e-8)

    def test_all_stop(self):
        """Mask of zeros kills signal."""
        rng = np.random.default_rng(44)
        f = rng.standard_normal(GROUP_SHAPE) + 1j * rng.standard_normal(GROUP_SHAPE)
        mask = np.zeros(GROUP_SHAPE, dtype=np.complex128)
        result = spectral_filter(f, mask)
        assert np.allclose(result, 0.0, atol=1e-10)


class TestHarmonicModes:
    def test_count(self):
        modes = harmonic_modes(5)
        assert len(modes) == 5

    def test_first_is_constant(self):
        """First mode (lowest frequency) is the constant χ₀."""
        modes = harmonic_modes(1)
        assert np.allclose(modes[0], 1.0, atol=1e-14)

    def test_zero_modes(self):
        assert harmonic_modes(0) == []


class TestLaplacianSpectrum:
    def test_shape(self):
        L = laplacian_spectrum()
        assert L.shape == GROUP_SHAPE

    def test_zero_at_origin(self):
        """Eigenvalue at k=0 is 0 (constant mode)."""
        L = laplacian_spectrum()
        assert abs(L[0, 0, 0, 0]) < 1e-14

    def test_non_negative(self):
        L = laplacian_spectrum()
        assert np.all(L >= -1e-14)
