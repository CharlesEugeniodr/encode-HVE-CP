# HVE Engine repository instructions

These instructions govern every code, protocol, documentation, benchmark, and
evidence change in this repository. The canonical architectural data are in
`docs/article_data_v2_5.json`; the human-readable article-to-code map is in
`docs/article_architecture_v2_5.md`.

## 1. Source-of-truth order

When two files appear to conflict, use this order:

1. executable conformance tests and published golden vectors;
2. `SPECIFICATION.md` and `docs/hve25_implementation_contract.md`;
3. `docs/article_data_v2_5.json`;
4. public API documentation and examples;
5. benchmark reports and manuscript prose.

Do not silently reconcile contradictions. Stop, identify the conflicting
contract, and update code, tests, specification, evidence, and the article data
manifest together.

## 2. Architectural dependency direction

Preserve this order:

```text
finite core
-> refined geometry
-> structural graphs and operators
-> declared perceptual conductance
-> external typed conversion
-> control and representation envelopes
-> benchmarks and evidence
```

Boundary adapters such as Unicode, raw bytes, legacy layouts, EPI1, EFQ-128,
and application experiments must not redefine the finite core.

## 3. Immutable HVE 2.5 contracts

- The complete core is `Z_360 x Z_2 x Z_5 x Z_9`, with 32,400 states.
- `canonical-doc-v1` is geometry-major:
  `phi*3600 + tau*720 + s*360 + theta`.
- `engine-v1-legacy` remains explicit and is never guessed from bytes.
- EFQ is classical, deterministic, quantized, and bit-encoded; do not call it
  quantum computation.
- The refined geometry and pointed raw-color product keep the existing
  mixed-radix bijection. CR80 is exactly 10 network-order bytes and has a
  minimum dense width of 80 bits.
- CR88 is an 11-byte physical envelope: bytes 0..9 are unchanged CR80 and byte
  10 is `color_space[7:6] | color_state[5:4] | reserved[3:0]`.
- CR88 is not a new dense rank. Its valid transport domain has a minimum dense
  width of 82 bits, while the envelope is 88 physical bits.
- HVE2 profile `0x05` requires zero frame flags, exactly `11*N` payload bytes,
  and CRC-32/ISO-HDLC over the payload only.
- A decoder validates header and length, then CRC, then CR80 and metadata
  semantics. Reserved bits and inconsistent truth-table combinations fail
  closed.
- Structural RGB adjacency remains bounded L1 adjacency inside one declared
  profile fiber. No channel wraps. NoColor is isolated. Uncalibrated RGB is not
  navigable.
- `hve-chi-oklab/v1` changes edge weights, not adjacency. Use native Oklab
  scale and default `sigma = 0.02/sqrt(2)`.
- Oklab is not a CIE standard. A declared RGB profile is not physical-device
  calibration.
- Typed color conversion is external to the graph. Test target gamut in linear
  RGB before target transfer encoding and RGB8 quantization.
- Conversion outcomes remain exactly `EXACT`, `QUANTIZED`, `OUT_OF_GAMUT`,
  `CLIPPED`, and `MAPPED`; policies remain `REJECT`, `CLIP`, and
  `MAP_OKLCH_MINDE`.
- `MAPPED` requires the declared nonlinear local-MINDE procedure. Do not model
  gamut mapping as a single 3x3 matrix.

## 4. Code and data placement

- Python reference implementation: `src/hve/`.
- Portable C11 parity implementation: `c/`.
- Normative vectors: `tests/golden_vectors*.json`.
- Canonical datasets: `datasets/canonical/`.
- Reproducible benchmark drivers: `benchmarks/`.
- Preserved measurements and quality outputs: `evidence/`.
- Normative and explanatory documents: `SPECIFICATION.md` and `docs/`.

Do not commit virtual environments, caches, compiler outputs, coverage runtime
files, or locally generated binaries. Do not place release ZIPs in the source
tree. Manuscript binaries belong in release assets; their identities are
recorded by hash in `docs/article_data_v2_5.json`.

## 5. Required change discipline

For a protocol, rank, graph, colorimetric, or conversion change:

1. state whether it preserves or versions the current contract;
2. update Python and C11 together when the behavior is shared;
3. add positive, boundary, and rejection tests;
4. publish or update cross-language golden vectors;
5. run the complete quality chain;
6. regenerate evidence and `SHA256SUMS.txt` only after the tree is final;
7. update the specification, article map, article data manifest, changelog, and
   implementation status in the same commit.

Never weaken a test or widen a benchmark tolerance after observing a failure
without a separately documented scientific justification.

## 6. Minimum verification

```bash
python -m pytest -q
python -m ruff check .
python -m mypy src tests examples benchmarks
cmake -S c -B build/c
cmake --build build/c
ctest --test-dir build/c --output-on-failure
python benchmarks/run_hve25_conformance.py --vectors 100000
```

For a documentation-only change, run at least
`python benchmarks/validate_article_contract.py` and
the manifest check. For any wire or color operation, run the whole chain.

## 7. Scientific claim boundaries

Do not claim that HVE is cryptographic, a differentiable manifold, a validated
semantic embedding, an absolute perceptual metric, a measured device
calibration, or a hard-real-time implementation. Benchmark percentiles are
host measurements, not WCET, energy, interrupt, or embedded-target guarantees.
