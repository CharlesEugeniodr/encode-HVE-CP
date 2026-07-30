"""HVE-720 Harmonic Vector Encoding — computational engine.

The HVE state space is the finite Abelian group:

    G = Z_360 × Z_2 × Z_5 × Z_9

with cardinality |G| = 32,400 states, bijectively mapped to 15-bit indices.

The chromatic extension HVE-χ adds a pointed color space (NoColor ∪ RGB),
yielding 543,581,830,800 unique states in 39 bits.

AI Mapping Layer defines an extensible inference interface.
No trained model is included in the core release.
"""

__version__ = "1.0.0"
__author__ = "Charles de Paula Eugênio"

from hve.core import (
    HVEState,
    HVEError,
    encode_base,
    decode_base,
    group_add,
    group_inverse,
    group_identity,
    validate_state,
    validate_index,
    BASE_CARDINALITY,
    THETA_CARDINALITY,
    S_CARDINALITY,
    TAU_CARDINALITY,
    PHI_CARDINALITY,
    RESERVED_WORDS,
)

from hve.chromatic import (
    HVEColor,
    encode_chi,
    decode_chi,
    color_kappa,
    color_kappa_inverse,
    CHI_CARDINALITY,
    CHI_MAX_INDEX,
    COLOR_RGB_CARDINALITY,
    COLOR_POINTED_CARDINALITY,
)

from hve.protocol import (
    pack_base15,
    unpack_base15,
    pack_chi40,
    unpack_chi40,
    pack_chi39,
    unpack_chi39,
    make_frame,
    parse_frame,
)

from hve.ai_mapping import (
    MappingResult,
    AbstractMapper,
    MapperRegistry,
    DeterministicMapper,
    RuleBasedMapper,
)

from hve.canonical import (
    generate_canonical_table,
    get_state,
    get_index,
    validate_canonical_table,
    canonical_table_summary,
)

__all__ = [
    # Core
    "HVEState",
    "HVEError",
    "encode_base",
    "decode_base",
    "group_add",
    "group_inverse",
    "group_identity",
    "validate_state",
    "validate_index",
    "BASE_CARDINALITY",
    "THETA_CARDINALITY",
    "S_CARDINALITY",
    "TAU_CARDINALITY",
    "PHI_CARDINALITY",
    "RESERVED_WORDS",
    # Chromatic
    "HVEColor",
    "encode_chi",
    "decode_chi",
    "color_kappa",
    "color_kappa_inverse",
    "CHI_CARDINALITY",
    "CHI_MAX_INDEX",
    "COLOR_RGB_CARDINALITY",
    "COLOR_POINTED_CARDINALITY",
    # Protocol
    "pack_base15",
    "unpack_base15",
    "pack_chi40",
    "unpack_chi40",
    "pack_chi39",
    "unpack_chi39",
    "make_frame",
    "parse_frame",
    # AI Mapping
    "MappingResult",
    "AbstractMapper",
    "MapperRegistry",
    "DeterministicMapper",
    "RuleBasedMapper",
    # Canonical
    "generate_canonical_table",
    "get_state",
    "get_index",
    "validate_canonical_table",
    "canonical_table_summary",
]
