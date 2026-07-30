"""HVE CLI — Command-line interface for HVE-720 operations.

Usage:
    hve validate                                    # Exhaustive validation
    hve encode --theta 45 --s 0 --tau 2 --phi 3    # Encode to BASE index
    hve encode --theta 45 ... --color 128,64,32     # Encode to HVE-χ
    hve decode 4071                                  # Decode BASE index
    hve decode --chi 68301430233                     # Decode HVE-χ index
    hve angular-distance 359 0                       # Circular distance
    hve neighborhood 0 --radius 3                    # Angular neighborhood
    hve benchmark --iterations 100000                # Performance benchmark
    hve visualize --mode angular --output fig.png    # Visualization
"""

from __future__ import annotations

import json
import sys
import time

import click

from hve.core import (
    HVEState,
    HVEError,
    encode_base,
    decode_base,
    group_add,
    group_inverse,
    group_identity,
    BASE_CARDINALITY,
    RESERVED_WORDS,
)
from hve.chromatic import (
    HVEColor,
    encode_chi,
    decode_chi,
    CHI_CARDINALITY,
)
from hve.angular import circular_distance, neighborhood, shortest_path
from hve.canonical import validate_canonical_table


@click.group()
@click.version_option(package_name="hve-engine")
def main() -> None:
    """HVE-720 Harmonic Vector Encoding — computational engine."""


# ─── validate ─────────────────────────────────────────────────────────────────

@main.command()
def validate() -> None:
    """Exhaustive validation: 32,400 round-trips + 368 reserved word rejections."""
    click.echo("HVE-720 Exhaustive Validation")
    click.echo("=" * 50)

    valid, reserved, failures = validate_canonical_table()

    click.echo(f"  Valid states round-tripped:  {valid:>6,}")
    click.echo(f"  Reserved words rejected:     {reserved:>6,}")
    click.echo(f"  Failures:                    {failures:>6,}")
    click.echo("=" * 50)

    if failures == 0 and valid == BASE_CARDINALITY and reserved == RESERVED_WORDS:
        click.secho("VALIDATION PASSED [OK]", fg="green", bold=True)
    else:
        click.secho("VALIDATION FAILED [FAIL]", fg="red", bold=True)
        sys.exit(1)


# ─── encode ───────────────────────────────────────────────────────────────────

@main.command()
@click.option("--theta", required=True, type=int, help="Angular position [0, 359]")
@click.option("--s", required=True, type=int, help="Polarity index {0, 1}")
@click.option("--tau", required=True, type=int, help="Auxiliary coordinate [0, 4]")
@click.option("--phi", required=True, type=int, help="Auxiliary coordinate [0, 8]")
@click.option("--color", default=None, type=str, help="RGB color as 'R,G,B' (e.g. '128,64,32')")
def encode(theta: int, s: int, tau: int, phi: int, color: str | None) -> None:
    """Encode an HVE state to its unique index."""
    try:
        state = HVEState(theta, s, tau, phi)
        base_index = encode_base(state)

        result = {
            "state": {"theta": theta, "s": s, "tau": tau, "phi": phi},
            "base_index": base_index,
        }

        if color is not None:
            parts = [int(x.strip()) for x in color.split(",")]
            if len(parts) != 3:
                raise HVEError("color must be 'R,G,B'")
            hve_color = HVEColor.rgb(*parts)
            chi_index = encode_chi(state, hve_color)
            result["color"] = {"r": parts[0], "g": parts[1], "b": parts[2]}
            result["chi_index"] = chi_index

        click.echo(json.dumps(result, indent=2))
    except HVEError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)


# ─── decode ───────────────────────────────────────────────────────────────────

@main.command()
@click.argument("index", required=False, type=int, default=None)
@click.option("--chi", type=int, default=None, help="HVE-χ index to decode")
def decode(index: int | None, chi: int | None) -> None:
    """Decode an index back to its HVE state."""
    try:
        if chi is not None:
            state, color = decode_chi(chi)
            result = {
                "chi_index": chi,
                "state": {"theta": state.theta, "s": state.s,
                          "tau": state.tau, "phi": state.phi},
                "color": {"present": color.present, "r": color.r,
                          "g": color.g, "b": color.b},
            }
        elif index is not None:
            state = decode_base(index)
            result = {
                "base_index": index,
                "state": {"theta": state.theta, "s": state.s,
                          "tau": state.tau, "phi": state.phi},
            }
        else:
            raise HVEError("provide a BASE index or --chi <index>")

        click.echo(json.dumps(result, indent=2))
    except HVEError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)


# ─── angular-distance ────────────────────────────────────────────────────────

@main.command("angular-distance")
@click.argument("theta1", type=int)
@click.argument("theta2", type=int)
def angular_distance_cmd(theta1: int, theta2: int) -> None:
    """Compute the circular distance between two angles on C₃₆₀."""
    dist = circular_distance(theta1, theta2)
    path = shortest_path(theta1, theta2)
    result = {
        "theta1": theta1,
        "theta2": theta2,
        "distance": dist,
        "normalized": dist / 180.0,
        "direction": path.direction,
        "clockwise_steps": path.clockwise,
        "counterclockwise_steps": path.counterclockwise,
    }
    click.echo(json.dumps(result, indent=2))


# ─── neighborhood ────────────────────────────────────────────────────────────

@main.command()
@click.argument("theta", type=int)
@click.option("--radius", "-r", default=1, type=int, help="Neighborhood radius")
def neighborhood_cmd(theta: int, radius: int) -> None:
    """Show the r-neighborhood of angle θ on C₃₆₀."""
    nbrs = sorted(neighborhood(theta, radius))
    click.echo(json.dumps({"theta": theta, "radius": radius, "neighborhood": nbrs}))


# ─── benchmark ────────────────────────────────────────────────────────────────

@main.command()
@click.option("--iterations", "-n", default=100_000, type=int, help="Number of iterations")
def benchmark(iterations: int) -> None:
    """Run host implementation diagnostic benchmark on BASE encode/decode."""
    import platform

    click.echo("HVE-720 Host Implementation Diagnostic Benchmark")
    click.echo("=" * 50)
    click.echo(f"  Python:     {platform.python_version()}")
    click.echo(f"  OS:         {platform.platform()}")
    click.echo(f"  CPU:        {platform.processor()}")
    click.echo(f"  Machine:    {platform.machine()}")
    click.echo(f"  Iterations: {iterations:,}")
    click.echo("-" * 50)

    # Warm-up (10% of iterations, at least 100)
    warmup = max(100, iterations // 10)
    for i in range(warmup):
        state = HVEState(i % 360, (i >> 9) % 2, (i >> 10) % 5, (i >> 13) % 9)
        _ = encode_base(state)
        _ = decode_base(i % BASE_CARDINALITY)

    # BASE encode
    t0 = time.perf_counter()
    checksum = 0
    for i in range(iterations):
        state = HVEState(i % 360, (i >> 9) % 2, (i >> 10) % 5, (i >> 13) % 9)
        idx = encode_base(state)
        checksum ^= idx
    elapsed_encode = time.perf_counter() - t0

    # BASE decode
    t0 = time.perf_counter()
    for i in range(iterations):
        idx = i % BASE_CARDINALITY
        state = decode_base(idx)
        checksum ^= state.theta
    elapsed_decode = time.perf_counter() - t0

    # BASE round-trip
    t0 = time.perf_counter()
    for i in range(iterations):
        state = HVEState(i % 360, (i >> 9) % 2, (i >> 10) % 5, (i >> 13) % 9)
        idx = encode_base(state)
        _ = decode_base(idx)
    elapsed_roundtrip = time.perf_counter() - t0

    def report(name: str, elapsed: float) -> None:
        ops_per_sec = iterations / elapsed if elapsed > 0 else float("inf")
        ns_per_op = elapsed * 1e9 / iterations if iterations > 0 else 0
        click.echo(f"  {name:<20s}  {ns_per_op:>8.1f} ns/op  {ops_per_sec:>10,.0f} ops/s")

    report("BASE encode", elapsed_encode)
    report("BASE decode", elapsed_decode)
    report("BASE round-trip", elapsed_roundtrip)
    click.echo(f"  Checksum: 0x{checksum:08X}")
    click.echo("-" * 50)
    click.echo("  NOTE: These are host implementation diagnostics,")
    click.echo("  not intrinsic HVE performance claims.")
    click.echo("=" * 50)


# ─── visualize ────────────────────────────────────────────────────────────────

@main.command()
@click.option("--mode", type=click.Choice(["angular", "state-space", "harmonic", "chromatic"]),
              default="angular", help="Visualization mode")
@click.option("--output", "-o", default=None, type=str, help="Output file path (default: display)")
def visualize(mode: str, output: str | None) -> None:
    """Generate HVE visualizations."""
    try:
        from hve.visualize import (
            plot_angular_wheel,
            plot_state_space,
            plot_harmonic_spectrum,
            plot_chromatic_extension,
        )
    except ImportError:
        click.secho("Visualization requires matplotlib: pip install hve-engine[viz]", fg="red")
        sys.exit(1)

    dispatch = {
        "angular": plot_angular_wheel,
        "state-space": plot_state_space,
        "harmonic": plot_harmonic_spectrum,
        "chromatic": plot_chromatic_extension,
    }

    fig = dispatch[mode]()

    if output:
        fig.savefig(output, dpi=150, bbox_inches="tight")
        click.echo(f"Saved to {output}")
    else:
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == "__main__":
    main()
