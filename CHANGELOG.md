# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-07-19

### Added
- **Core Engine**: HVE-720 BASE bijection over G = Z₃₆₀ × Z₂ × Z₅ × Z₉
  - Mixed-radix encoding/decoding (32,400 valid states, 368 reserved)
  - Finite group operations (add, inverse, identity)
  - Complete state and index validation
- **Angular State Engine**: Discrete circular geometry on C₃₆₀
  - Circular distance, normalized distance, geodesic distance
  - Shortest path with direction detection (CW/CCW/antipodal)
  - Neighborhood, rotation, circular intervals, arc membership
  - Circular mean/center, sector grouping
  - Multi-resolution quantization (BASE/MICRO/NANO)
- **Harmonic Engine**: Fourier analysis on the finite group G
  - Character evaluation χ_k(g) with pre-computed roots of unity
  - Separable multidimensional DFT and inverse DFT
  - Reference O(N²) DFT implementation for validation
  - Convolution and cross-correlation via DFT
  - Power spectrum, spectral filtering
  - Parseval's theorem verification
  - Character orthogonality check
  - Harmonic modes (sorted by frequency)
  - Laplacian spectrum of the group graph
- **Chromatic Engine**: HVE-χ pointed color extension
  - Pointed color space C* = {NoColor} ∪ RGB (|C*| = 16,777,217)
  - Kappa bijection and inverse
  - Monolithic χ encoding (543,581,830,800 states in 39 bits)
- **Protocol**: HVE1 deterministic framing
  - BASE15 MSB-first stream packing
  - CHI40 aligned 40-bit profile
  - CHI39 compact 39-bit profile
  - CRC-32/ISO-HDLC integrity checking
- **AI Mapping Layer**: Extensible inference interface
  - AbstractMapper contract
  - DeterministicMapper (Unicode/index → HVE state)
  - RuleBasedMapper (string classification demo)
  - MapperRegistry (plugin system)
  - No trained models included (by design)
- **CLI**: Command-line interface via `hve` command
  - `hve validate` — exhaustive validation
  - `hve encode` — state to index
  - `hve decode` — index to state
  - `hve angular-distance` — circular distance
  - `hve neighborhood` — angular neighborhood
  - `hve benchmark` — performance measurement
  - `hve visualize` — matplotlib visualizations
- **Canonical States**: Complete table of 32,400 states with validation
- **Test Suite**: Comprehensive pytest suite
  - Exhaustive 32,400-state round-trip verification
  - 368 reserved word rejection
  - 10,000 randomized group associativity checks
  - 100,000 deterministic HVE-χ round-trips
  - DFT round-trip and Parseval verification
- **Documentation**: README, architecture, mathematical foundations
- **Examples**: Basic usage, angular distance, chromatic states

### Origin
Core algorithms imported and reorganized from the validated `encode-HVE-CP`
reference implementation (Parts I, II-A, II-B). The original repository is
retained as a historical development archive.
