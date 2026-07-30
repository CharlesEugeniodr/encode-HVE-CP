# HVE-720 Engine

**Harmonic Vector Encoding** — A deterministic bijective encoding architecture over the finite Abelian group G = Z₃₆₀ × Z₂ × Z₅ × Z₉.

[![Tests](https://github.com/CharlesEugeniodr/hve-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/CharlesEugeniodr/hve-engine/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)

## Overview

HVE-720 maps 32,400 unique states to 15-bit indices through a mixed-radix bijection:

```
E(θ, s, τ, φ) = (((θ · 2 + s) · 5 + τ) · 9 + φ)
```

The chromatic extension HVE-χ adds a pointed color space (NoColor ∪ RGB), yielding **543,581,830,800** unique states in 39 bits.

### Architecture

| Module | Description |
|--------|-------------|
| **Core** | BASE bijection, finite group operations on G |
| **Angular** | Circular geometry on C₃₆₀ — distance, geodesic, neighborhood |
| **Harmonic** | Fourier analysis on G — characters, DFT, convolution |
| **Chromatic** | HVE-χ pointed color extension |
| **Protocol** | HVE1 framing, BASE15/CHI40/CHI39 profiles, CRC-32 |
| **AI Mapping** | Extensible inference interface (no trained models in core) |

## Quick Start

```bash
git clone https://github.com/CharlesEugeniodr/hve-engine.git
cd hve-engine
pip install .
```

### Validate

```bash
hve validate
```

```
HVE-720 Exhaustive Validation
==================================================
  Valid states round-tripped:  32,400
  Reserved words rejected:       368
  Failures:                        0
==================================================
VALIDATION PASSED ✓
```

### Encode / Decode

```bash
hve encode --theta 45 --s 0 --tau 2 --phi 3
# {"state": {"theta": 45, "s": 0, "tau": 2, "phi": 3}, "base_index": 4071}

hve encode --theta 45 --s 0 --tau 2 --phi 3 --color 128,64,32
# {"state": {...}, "base_index": 4071, "color": {"r": 128, "g": 64, "b": 32}, "chi_index": 68301430233}

hve decode 32399
# {"base_index": 32399, "state": {"theta": 359, "s": 1, "tau": 4, "phi": 8}}
```

### Angular Distance

```bash
hve angular-distance 359 0
# {"theta1": 359, "theta2": 0, "distance": 1, "normalized": 0.0056, "direction": "cw"}
```

### Visualize

```bash
pip install ".[viz]"
hve visualize --mode angular --output angular_wheel.png
hve visualize --mode state-space --output state_decomposition.png
hve visualize --mode harmonic --output harmonic_spectrum.png
```

### Benchmark

```bash
hve benchmark --iterations 100000
```

## Python API

```python
from hve import (
    HVEState, encode_base, decode_base,
    group_add, group_inverse, group_identity,
    HVEColor, encode_chi, decode_chi,
)

# Encode
state = HVEState(theta=45, s=0, tau=2, phi=3)
index = encode_base(state)  # 4071

# Decode
state = decode_base(4071)  # HVEState(45, 0, 2, 3)

# Group operations
a = HVEState(100, 1, 3, 7)
b = HVEState(200, 0, 2, 5)
c = group_add(a, b)

# Chromatic
color = HVEColor.rgb(128, 64, 32)
chi_idx = encode_chi(state, color)

# Angular
from hve.angular import circular_distance, neighborhood
circular_distance(359, 0)  # 1
neighborhood(0, 2)         # {358, 359, 0, 1, 2}

# Harmonic
from hve.harmonic import dft, idft, parseval_check
import numpy as np
f = np.random.randn(360, 2, 5, 9) + 0j
f_hat = dft(f)
assert parseval_check(f, f_hat)
```

## Mathematical Foundation

The HVE-720 state space is the finite Abelian group:

**G = Z₃₆₀ × Z₂ × Z₅ × Z₉**

| Component | Symbol | Cardinality | Interpretation |
|-----------|--------|-------------|----------------|
| Angular | θ ∈ Z₃₆₀ | 360 | Position on cycle C₃₆₀ |
| Polarity | s ∈ Z₂ | 2 | σ = (-1)ˢ |
| Auxiliary | τ ∈ Z₅ | 5 | State coordinate |
| Auxiliary | φ ∈ Z₉ | 9 | State coordinate |

**|G| = 360 × 2 × 5 × 9 = 32,400** states → 15-bit addressing (368 reserved words).

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT — See [LICENSE](LICENSE).

## Author

Charles de Paula Eugênio

## Citation

See [CITATION.cff](CITATION.cff).
