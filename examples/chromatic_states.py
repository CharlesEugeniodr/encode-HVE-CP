"""HVE-χ Chromatic extension example."""

from hve import (
    HVEState,
    HVEColor,
    encode_chi,
    decode_chi,
    color_kappa,
    color_kappa_inverse,
    pack_chi40,
    unpack_chi40,
    CHI_CARDINALITY,
)

# === NoColor vs Black ===
print("=== NoColor ≠ Black ===")
no_color = HVEColor.no_color()
black = HVEColor.rgb(0, 0, 0)
white = HVEColor.rgb(255, 255, 255)

print(f"NoColor: κ = {color_kappa(no_color)}")      # 0
print(f"Black:   κ = {color_kappa(black)}")           # 1
print(f"White:   κ = {color_kappa(white)}")           # 16,777,216
print(f"NoColor == Black? {no_color == black}")       # False

# === HVE-χ Round-trip ===
print("\n=== HVE-χ Encode/Decode ===")
state = HVEState(45, 0, 2, 3)
color = HVEColor.rgb(128, 64, 32)

chi_index = encode_chi(state, color)
print(f"State: {state}, Color: RGB({color.r},{color.g},{color.b})")
print(f"χ-index: {chi_index}")

dec_state, dec_color = decode_chi(chi_index)
print(f"Decoded: {dec_state}, Color: RGB({dec_color.r},{dec_color.g},{dec_color.b})")
assert dec_state == state and dec_color == color

# === CHI40 Wire Format ===
print("\n=== CHI40 Wire Format ===")
packed = pack_chi40(state, color)
print(f"CHI40 bytes: {packed.hex()}")
print(f"CHI40 length: {len(packed)} bytes (40 bits)")

dec_state2, dec_color2 = unpack_chi40(packed)
assert dec_state2 == state and dec_color2 == color
print("Round-trip verified ✓")

# === Total Cardinality ===
print(f"\n|HVE-χ| = {CHI_CARDINALITY:,} unique states")
print(f"= 32,400 × 16,777,217 = {32400 * 16777217:,}")
