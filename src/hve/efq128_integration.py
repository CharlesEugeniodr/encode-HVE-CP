# efq128_integration.py – thin wrapper exposing the 128‑bit EFQ codec

"""Public API for packing and unpacking HVE‑128 (EFQ128) vectors.

The reference implementation lives in the C extension (`hve.c` / `hve.h`).
For Python users we expose two convenience functions that forward to the
underlying C bindings if they are available, otherwise raise a clear
`NotImplementedError`.

The CLI commands ``hve pack128`` and ``hve unpack128`` are registered in
``setup.cfg`` via entry points.
"""

from __future__ import annotations

import importlib

# Attempt to import the compiled extension module.  It is built as
# ``hve._c_ext`` by the package's ``setup.cfg``.
try:
    _c_ext = importlib.import_module("hve._c_ext")
except Exception:  # pragma: no cover – the pure‑Python fallback.
    _c_ext = None


def pack_hve128(data: bytes) -> bytes:
    """Pack a 16‑byte payload representing an HVE‑128 state.

    Parameters
    ----------
    data:
        A ``bytes`` object of length exactly 16 containing the raw fields
        according to the EFQ128 specification.
    Returns
    -------
    bytes
        The same 16‑byte payload – the function exists for symmetry with
        ``unpack_hve128`` and to provide a stable import path.
    """
    if _c_ext and hasattr(_c_ext, "pack_hve128"):
        return _c_ext.pack_hve128(data)
    raise NotImplementedError(
        "EFQ128 C extension not available – build the package with the "
        "C sources to use pack_hve128/unpack_hve128."
    )


def unpack_hve128(blob: bytes) -> bytes:
    """Unpack a 16‑byte EFQ128 payload into its constituent fields.

    The low‑level C implementation returns the raw 16‑byte buffer; this
    wrapper simply forwards the call or raises ``NotImplementedError`` when
    the extension is missing.
    """
    if _c_ext and hasattr(_c_ext, "unpack_hve128"):
        return _c_ext.unpack_hve128(blob)
    raise NotImplementedError(
        "EFQ128 C extension not available – build the package with the "
        "C sources to use pack_hve128/unpack_hve128."
    )
