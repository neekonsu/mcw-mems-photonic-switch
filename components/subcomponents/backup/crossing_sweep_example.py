#!/usr/bin/env python3
"""
Example script showing how to use the parametric waveguide crossing PCell
for running parameter sweeps and optimization.
"""

from pathlib import Path
from waveguide_crossing_pcell import waveguide_crossing
import numpy as np

def sweep_center_width():
    """Sweep the center width parameter."""
    print("="*70)
    print("SWEEP EXAMPLE: CENTER WIDTH")
    print("="*70)

    output_dir = Path(__file__).parent.parent / "outputs" / "sweeps"
    output_dir.mkdir(exist_ok=True)

    center_widths = np.linspace(1.0, 5.0, 9)

    print(f"\nGenerating {len(center_widths)} crossing variants...")
    print(f"Center widths: {center_widths}")

    for cw in center_widths:
        # Adjust taper widths to match center width
        taper_widths = np.linspace(0.4, cw, 9).tolist()

        crossing = waveguide_crossing(
            input_width=0.4,
            num_taper_sections=8,
            taper_widths=taper_widths,
            center_width=cw,
            layer=(1, 0)
        )

        # Save GDS
        output_file = output_dir / f"crossing_cw_{cw:.2f}um.gds"
        crossing.write_gds(str(output_file))
        print(f"  ✓ {output_file.name}")

    print(f"\n✓ Generated {len(center_widths)} GDS files in {output_dir}")
    print("\n🔬 Next step: Import these GDS files into Lumerical FDTD for simulation")


def sweep_taper_lengths():
    """Sweep the taper section lengths."""
    print("\n" + "="*70)
    print("SWEEP EXAMPLE: TAPER LENGTHS")
    print("="*70)

    output_dir = Path(__file__).parent.parent / "outputs" / "sweeps"
    output_dir.mkdir(exist_ok=True)

    # Vary the taper length uniformly
    taper_length_values = np.linspace(1.0, 4.0, 7)

    print(f"\nGenerating {len(taper_length_values)} crossing variants...")
    print(f"Taper lengths (per section): {taper_length_values}")

    for tl in taper_length_values:
        # All sections have the same length
        taper_lengths = [tl] * 8

        crossing = waveguide_crossing(
            input_width=0.4,
            num_taper_sections=8,
            taper_lengths=taper_lengths,
            center_width=3.0,
            layer=(1, 0)
        )

        # Save GDS
        output_file = output_dir / f"crossing_tl_{tl:.2f}um.gds"
        crossing.write_gds(str(output_file))
        print(f"  ✓ {output_file.name}")

    print(f"\n✓ Generated {len(taper_length_values)} GDS files in {output_dir}")


def sweep_num_taper_sections():
    """Sweep the number of taper sections."""
    print("\n" + "="*70)
    print("SWEEP EXAMPLE: NUMBER OF TAPER SECTIONS")
    print("="*70)

    output_dir = Path(__file__).parent.parent / "outputs" / "sweeps"
    output_dir.mkdir(exist_ok=True)

    num_sections_values = [2, 4, 6, 8, 10, 12]

    print(f"\nGenerating {len(num_sections_values)} crossing variants...")
    print(f"Number of sections: {num_sections_values}")

    for n_sec in num_sections_values:
        # Keep total taper length constant at ~18µm
        taper_lengths = [18.0 / n_sec] * n_sec
        taper_widths = np.linspace(0.4, 3.0, n_sec + 1).tolist()

        crossing = waveguide_crossing(
            input_width=0.4,
            num_taper_sections=n_sec,
            taper_lengths=taper_lengths,
            taper_widths=taper_widths,
            center_width=3.0,
            layer=(1, 0)
        )

        # Save GDS
        output_file = output_dir / f"crossing_n{n_sec:02d}.gds"
        crossing.write_gds(str(output_file))
        print(f"  ✓ {output_file.name}")

    print(f"\n✓ Generated {len(num_sections_values)} GDS files in {output_dir}")


def custom_taper_profile():
    """Create a crossing with a custom non-linear taper profile."""
    print("\n" + "="*70)
    print("CUSTOM EXAMPLE: NON-LINEAR TAPER")
    print("="*70)

    output_dir = Path(__file__).parent.parent / "outputs" / "sweeps"
    output_dir.mkdir(exist_ok=True)

    # Exponential taper profile (faster expansion near center)
    n_sections = 8
    x = np.linspace(0, 1, n_sections + 1)
    taper_widths = 0.4 + (3.0 - 0.4) * (x ** 2)  # Quadratic taper
    taper_widths = taper_widths.tolist()

    print(f"\nCustom taper widths: {[f'{w:.2f}' for w in taper_widths]}")

    crossing = waveguide_crossing(
        input_width=0.4,
        num_taper_sections=n_sections,
        taper_widths=taper_widths,
        center_width=3.0,
        layer=(1, 0)
    )

    # Save GDS
    output_file = output_dir / "crossing_quadratic_taper.gds"
    crossing.write_gds(str(output_file))
    print(f"✓ Saved: {output_file.name}")


def main():
    """Run all sweep examples."""
    print("\n" + "🔬"*35)
    print("WAVEGUIDE CROSSING - PARAMETER SWEEP EXAMPLES")
    print("🔬"*35 + "\n")

    # Run different sweeps
    sweep_center_width()
    sweep_taper_lengths()
    sweep_num_taper_sections()
    custom_taper_profile()

    print("\n" + "="*70)
    print("ALL SWEEPS COMPLETE")
    print("="*70)

    print("\n📊 Summary:")
    output_dir = Path(__file__).parent.parent / "outputs" / "sweeps"
    gds_files = list(output_dir.glob("*.gds"))
    print(f"  Generated {len(gds_files)} GDS files total")
    print(f"  Location: {output_dir}")

    print("\n🔬 Recommended workflow:")
    print("  1. Import GDS files into Lumerical FDTD Solutions")
    print("  2. Set up simulation with:")
    print("     - TE/TM mode source at one input port")
    print("     - Monitors at all four output ports")
    print("     - Wavelength sweep (1520-1580 nm)")
    print("  3. Extract S-parameters:")
    print("     - S21: Through port (transmission)")
    print("     - S31: Cross port (crosstalk)")
    print("     - S41: Opposite port (back-reflection)")
    print("  4. Optimize parameters for:")
    print("     - Minimize insertion loss (maximize S21)")
    print("     - Minimize crosstalk (minimize S31)")
    print("     - Broadband operation across C-band")


if __name__ == "__main__":
    main()
