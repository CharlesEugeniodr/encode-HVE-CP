"""Basic HVE-720 usage example."""

from hve import (
    HVEState,
    encode_base,
    decode_base,
    group_add,
    group_inverse,
    group_identity,
)

# === Encode and Decode ===
state = HVEState(theta=45, s=0, tau=2, phi=3)
index = encode_base(state)
print(f"State {state} -> index {index}")

recovered = decode_base(index)
print(f"Index {index} -> {recovered}")
assert recovered == state

# === Group Operations ===
a = HVEState(100, 1, 3, 7)
b = HVEState(200, 0, 2, 5)

# Sum
c = group_add(a, b)
print(f"\n{a} (+) {b} = {c}")

# Inverse
inv_a = group_inverse(a)
print(f"(-){a} = {inv_a}")

# Identity check
e = group_identity()
result = group_add(a, inv_a)
print(f"{a} (+) (-){a} = {result} = identity? {result == e}")

# === Boundary States ===
first = decode_base(0)
last = decode_base(32399)
print(f"\nFirst state: {first} -> index 0")
print(f"Last state:  {last} -> index 32399")
