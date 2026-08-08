from hve.core import encode_base, decode_base, HVEState


def test_bijection_lemmas():
    # Verify forward and inverse formulas for a subset of random states
    for theta in range(0, 360, 30):
        for s in (0, 1):
            for tau in range(5):
                for phi in range(9):
                    state = HVEState(theta, s, tau, phi)
                    idx = encode_base(state)
                    # Reconstruct via the inverse formula (decode_base)
                    rev = decode_base(idx)
                    assert rev == state

    # Verify the explicit inverse calculation matches decode_base for random indices
    for i in [0, 1, 45, 11140, 32399]:
        theta = i // (2 * 5 * 9)
        rem = i % (2 * 5 * 9)
        s = rem // (5 * 9)
        rem2 = rem % (5 * 9)
        tau = rem2 // 9
        phi = rem2 % 9
        state = HVEState(theta, s, tau, phi)
        assert encode_base(state) == i
        assert decode_base(i) == state

def test_group_axioms():
    from hve.core import group_add, group_inverse, group_identity
    # associativity for a few random triples
    a = HVEState(10, 1, 2, 3)
    b = HVEState(20, 0, 1, 4)
    c = HVEState(30, 1, 3, 5)
    assert group_add(group_add(a, b), c) == group_add(a, group_add(b, c))
    # identity
    e = group_identity()
    assert group_add(a, e) == a and group_add(e, a) == a
    # inverse
    inv = group_inverse(a)
    assert group_add(a, inv) == e

def test_parseval_identity():
    from hve.harmonic import dft, idft, parseval_check
    import numpy as np
    # random real signal in the group shape
    f = np.random.randn(360, 2, 5, 9) + 0j
    f_hat = dft(f)
    # Inverse returns original (within tolerance)
    f_back = idft(f_hat)
    assert np.allclose(f, f_back, atol=1e-12)
    # Parseval must hold
    assert parseval_check(f, f_hat)
