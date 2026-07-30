"""Angular distance and geometry example on C₃₆₀."""

from hve.angular import (
    circular_distance,
    normalized_distance,
    shortest_path,
    neighborhood,
    circular_mean,
    sector_group,
    geodesic_distance,
)

# === Circular Distance ===
# On the cycle C₃₆₀, the distance wraps around:
print("=== Circular Distance ===")
print(f"δ(359, 0)  = {circular_distance(359, 0)}")    # 1, not 359
print(f"δ(0, 180)  = {circular_distance(0, 180)}")    # 180 (antipodal)
print(f"δ(90, 270) = {circular_distance(90, 270)}")    # 180

# === Normalized Distance ===
print(f"\nδ̄(359, 0)  = {normalized_distance(359, 0):.4f}")  # ~0.0056
print(f"δ̄(0, 180)  = {normalized_distance(0, 180):.4f}")    # 1.0

# === Shortest Path ===
print("\n=== Shortest Path ===")
path = shortest_path(350, 10)
print(f"350 → 10: distance={path.distance}, direction={path.direction}")
print(f"  clockwise={path.clockwise}, counterclockwise={path.counterclockwise}")

path = shortest_path(0, 180)
print(f"0 → 180: distance={path.distance}, direction={path.direction}")

# === Neighborhood ===
print("\n=== Neighborhood ===")
N1 = neighborhood(0, 1)
print(f"N₁(0) = {sorted(N1)}")  # {359, 0, 1}

N3 = neighborhood(358, 3)
print(f"N₃(358) = {sorted(N3)}")  # {355, 356, 357, 358, 359, 0, 1}

# === Circular Mean ===
print("\n=== Circular Mean ===")
mean = circular_mean([350, 10])
print(f"mean(350°, 10°) = {mean:.1f}°")  # ~0° (between them)

# === Sector Grouping ===
print("\n=== Sector Grouping ===")
angles = [0, 45, 90, 135, 180, 225, 270, 315]
sectors = sector_group(angles, 4)
for s, members in sorted(sectors.items()):
    print(f"  Sector {s}: {members}")

# === Geodesic ===
print(f"\nGeodesic distance on C₃₆₀:")
print(f"d(359, 0) = {geodesic_distance(359, 0)}")
