"""HVE Visualization — matplotlib renderings of the HVE state space.

Requires the 'viz' optional dependency: pip install hve-engine[viz]
"""

from __future__ import annotations

import numpy as np

from hve.core import (
    THETA_CARDINALITY,
    S_CARDINALITY,
    TAU_CARDINALITY,
    PHI_CARDINALITY,
    BASE_CARDINALITY,
)


def _import_plt():
    """Lazily import matplotlib."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        return plt
    except ImportError:
        raise ImportError(
            "Visualization requires matplotlib. Install with: pip install hve-engine[viz]"
        )


def plot_angular_wheel():
    """Plot the Z₃₆₀ angular wheel with tau and phi overlay.

    Returns a matplotlib Figure.
    """
    plt = _import_plt()
    fig, ax = plt.subplots(1, 1, figsize=(10, 10), subplot_kw={"projection": "polar"})

    thetas_rad = np.linspace(0, 2 * np.pi, THETA_CARDINALITY, endpoint=False)

    # Outer ring: all 360 positions
    ax.scatter(thetas_rad, np.ones(THETA_CARDINALITY) * 1.0,
               c=thetas_rad, cmap="hsv", s=15, alpha=0.8, zorder=3)

    # Tau markers (every 72°)
    for tau in range(TAU_CARDINALITY):
        angle = 2 * np.pi * tau / TAU_CARDINALITY
        ax.plot([angle, angle], [0, 1.15], color="#555555", lw=1.5, alpha=0.5)
        ax.annotate(f"τ={tau}", xy=(angle, 1.2), fontsize=9,
                    ha="center", va="center", color="#333333")

    # Phi markers (every 40°)
    for phi in range(PHI_CARDINALITY):
        angle = 2 * np.pi * phi / PHI_CARDINALITY
        ax.plot([angle, angle], [0, 0.85], color="#AA5500", lw=1, alpha=0.4, ls="--")

    # Cardinal directions
    for deg, label in [(0, "0°"), (90, "90°"), (180, "180°"), (270, "270°")]:
        ax.annotate(label, xy=(np.radians(deg), 1.35), fontsize=12,
                    ha="center", va="center", fontweight="bold")

    ax.set_rticks([])
    ax.set_title(
        f"HVE-720 Angular Wheel — Z₃₆₀\n"
        f"|G| = {BASE_CARDINALITY:,} states",
        pad=20, fontsize=14, fontweight="bold"
    )
    ax.set_ylim(0, 1.45)
    fig.tight_layout()
    return fig


def plot_state_space():
    """Plot the decomposition of the HVE state space G = Z₃₆₀ × Z₂ × Z₅ × Z₉.

    Returns a matplotlib Figure.
    """
    plt = _import_plt()
    fig, axes = plt.subplots(1, 4, figsize=(18, 4))

    components = [
        ("Z₃₆₀ (θ)", THETA_CARDINALITY, "hsv"),
        ("Z₂ (s)", S_CARDINALITY, "coolwarm"),
        ("Z₅ (τ)", TAU_CARDINALITY, "viridis"),
        ("Z₉ (φ)", PHI_CARDINALITY, "plasma"),
    ]

    for ax, (name, card, cmap) in zip(axes, components):
        values = np.arange(card)
        angles = 2 * np.pi * values / card
        x = np.cos(angles)
        y = np.sin(angles)
        colors = plt.cm.get_cmap(cmap)(values / max(card - 1, 1))
        ax.scatter(x, y, c=colors, s=200 / max(card / 10, 1), zorder=3, edgecolors="black", linewidths=0.5)
        for i, (xi, yi) in enumerate(zip(x, y)):
            if card <= 20:
                ax.annotate(str(i), (xi, yi), fontsize=8, ha="center", va="center")
        ax.set_title(f"{name}\n|{name.split()[0]}| = {card}", fontsize=11, fontweight="bold")
        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-1.4, 1.4)
        ax.set_aspect("equal")
        ax.axis("off")

    fig.suptitle(
        f"HVE-720 State Space Decomposition\n"
        f"G = Z₃₆₀ × Z₂ × Z₅ × Z₉  ⟹  |G| = {BASE_CARDINALITY:,}",
        fontsize=14, fontweight="bold", y=1.05
    )
    fig.tight_layout()
    return fig


def plot_harmonic_spectrum():
    """Plot the Laplacian spectrum of the HVE group.

    Returns a matplotlib Figure.
    """
    plt = _import_plt()
    from hve.harmonic import laplacian_spectrum

    L = laplacian_spectrum()
    eigenvalues = L.flatten()
    eigenvalues.sort()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram
    ax1.hist(eigenvalues, bins=100, color="#4A90D9", edgecolor="black", alpha=0.8)
    ax1.set_xlabel("Eigenvalue λ", fontsize=12)
    ax1.set_ylabel("Count", fontsize=12)
    ax1.set_title("Laplacian Eigenvalue Distribution", fontsize=13, fontweight="bold")
    ax1.axvline(0, color="red", lw=2, alpha=0.6, label="λ₀ = 0")
    ax1.legend()

    # Cumulative
    ax2.plot(range(len(eigenvalues)), eigenvalues, color="#D94A4A", lw=1.5)
    ax2.set_xlabel("Mode index", fontsize=12)
    ax2.set_ylabel("λ", fontsize=12)
    ax2.set_title("Sorted Eigenvalues", fontsize=13, fontweight="bold")
    ax2.set_xlim(0, min(1000, len(eigenvalues)))

    fig.suptitle(
        "HVE-720 Harmonic Spectrum\nGraph Laplacian on G = Z₃₆₀ × Z₂ × Z₅ × Z₉",
        fontsize=14, fontweight="bold", y=1.02
    )
    fig.tight_layout()
    return fig


def plot_chromatic_extension():
    """Plot the HVE-χ chromatic extension structure.

    Returns a matplotlib Figure.
    """
    plt = _import_plt()
    from hve.chromatic import COLOR_RGB_CARDINALITY, COLOR_POINTED_CARDINALITY, CHI_CARDINALITY

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    # Draw the pointed color space
    categories = ["NoColor\n(κ=0)", "Black\n(κ=1)", "RGB Space\n(κ ∈ [1, 2²⁴])"]
    sizes = [1, 1, COLOR_RGB_CARDINALITY]
    colors = ["#CCCCCC", "#222222", "#4A90D9"]

    # Use log scale for bar heights
    log_sizes = [np.log10(max(s, 1)) + 1 for s in sizes]

    bars = ax.bar(categories, log_sizes, color=colors, edgecolor="black",
                  width=0.5, alpha=0.9)

    # Annotate with actual sizes
    for bar, size in zip(bars, sizes):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{size:,}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_ylabel("log₁₀(cardinality) + 1", fontsize=12)
    ax.set_title(
        f"HVE-χ Pointed Chromatic Space\n"
        f"|C*| = {COLOR_POINTED_CARDINALITY:,}  →  |HVE-χ| = {CHI_CARDINALITY:,}",
        fontsize=13, fontweight="bold"
    )

    # Add annotation about total
    ax.text(0.95, 0.95,
            f"|G| × |C*| = {BASE_CARDINALITY:,} × {COLOR_POINTED_CARDINALITY:,}\n"
            f"= {CHI_CARDINALITY:,} states\n"
            f"({39} bits compact / {40} bits aligned)",
            transform=ax.transAxes, fontsize=10, ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", edgecolor="orange"))

    fig.tight_layout()
    return fig
