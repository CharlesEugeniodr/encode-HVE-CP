"""Golden Vector Conformance Tests.

Loads deterministic golden test vectors from golden_vectors.json
and validates that the Python engine produces identical results.

This ensures cross-implementation conformance (Python ↔ C11 ↔ future ports).
"""

from __future__ import annotations

import json
import pathlib

import pytest

from hve.core import HVEState, encode_base, decode_base
from hve.chromatic import (
    HVEColor,
    encode_chi,
    decode_chi,
    color_kappa,
)


VECTORS_PATH = pathlib.Path(__file__).parent / "golden_vectors.json"


@pytest.fixture(scope="module")
def golden() -> dict:
    """Load golden test vectors from JSON."""
    with open(VECTORS_PATH, encoding="utf-8") as f:
        return json.load(f)


# ─── BASE Vectors ────────────────────────────────────────────────────────────


class TestBaseGoldenVectors:
    """Verify base encode/decode matches golden vectors."""

    def test_all_base_vectors(self, golden: dict) -> None:
        for vec in golden["base_vectors"]:
            s = vec["state"]
            state = HVEState(s["theta"], s["s"], s["tau"], s["phi"])
            idx = vec["index"]

            # encode must produce the golden index
            assert encode_base(state) == idx, (
                f"encode({state}) expected {idx}, got {encode_base(state)}"
            )

            # decode must recover the golden state
            decoded = decode_base(idx)
            assert decoded == state, (
                f"decode({idx}) expected {state}, got {decoded}"
            )


# ─── CHI Vectors ─────────────────────────────────────────────────────────────


class TestChiGoldenVectors:
    """Verify chromatic encode/decode matches golden vectors."""

    def test_all_chi_vectors(self, golden: dict) -> None:
        for vec in golden["chi_vectors"]:
            s = vec["state"]
            state = HVEState(s["theta"], s["s"], s["tau"], s["phi"])

            c = vec["color"]
            if c["present"]:
                color = HVEColor.rgb(c["r"], c["g"], c["b"])
            else:
                color = HVEColor.no_color()

            expected_kappa = vec["kappa"]
            expected_chi_index = vec["chi_index"]

            # color_kappa must match
            kappa = color_kappa(color)
            assert kappa == expected_kappa, (
                f"color_kappa({color}) expected {expected_kappa}, got {kappa}"
            )

            # chi encode must match
            chi_idx = encode_chi(state, color)
            assert chi_idx == expected_chi_index, (
                f"encode_chi({state}, {color}) expected {expected_chi_index}, "
                f"got {chi_idx}"
            )

            # chi decode must round-trip
            decoded_state, decoded_color = decode_chi(chi_idx)
            assert decoded_state == state, (
                f"decode_chi({chi_idx})[0] expected {state}, "
                f"got {decoded_state}"
            )
            assert color_kappa(decoded_color) == expected_kappa, (
                f"decode_chi({chi_idx})[1] kappa expected "
                f"{expected_kappa}, got {color_kappa(decoded_color)}"
            )
