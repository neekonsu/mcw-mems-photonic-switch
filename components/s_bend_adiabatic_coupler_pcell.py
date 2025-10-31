#!/usr/bin/env python3
"""
Parametric S-bend with adiabatic coupler PCell.

This creates a waveguide structure with:
1. S-bend downward (smooth curve)
2. Adiabatic taper section (variable width)
3. S-bend upward (smooth curve)

The complete structure connects an input waveguide to an output that is
horizontally displaced with controlled width variation in the middle section.
"""

import gdsfactory as gf
import numpy as np
from typing import List, Tuple
from pathlib import Path
from scipy.interpolate import CubicSpline

@gf.cell
def s_bend_adiabatic_coupler(
    input_width: float = 0.4,
    s_bend_length_x: float = 10.0,
    s_bend_length_y: float = 5.0,
    n_pts_curve: int = 4,
    n_pts_s_bend: int = 20,
    n_adiabatic_segments: int = 10,
    length_adiabatic_segments: float = 20.0,
    adiabatic_widths: List[float] = None,
    layer: Tuple[int, int] = (1, 0)
) -> gf.Component:
    """
    Parametric S-bend with adiabatic coupler.

    Parameters
    ----------
    input_width : float
        Input waveguide width (µm)
    s_bend_length_x : float
        Horizontal displacement per S-bend section (µm)
    s_bend_length_y : float
        Vertical displacement per S-bend section (µm)
    n_pts_curve : int
        Number of curve points per S-bend section (excluding start/middle/end)
    n_pts_s_bend : int
        Number of point pairs to generate along each S-bend
    n_adiabatic_segments : int
        Number of vertical segments in adiabatic section
    length_adiabatic_segments : float
        Horizontal spacing between adiabatic segments (µm)
    adiabatic_widths : List[float]
        Width at each adiabatic segment. If None, uses constant input_width.
        Must have n_adiabatic_segments + 1 values (including start and end)
    layer : Tuple[int, int]
        GDS layer (layer, datatype)

    Returns
    -------
    Component
        GDSFactory component with S-bend and adiabatic coupler
    """
    c = gf.Component()

    # Set default adiabatic widths if not provided
    if adiabatic_widths is None:
        adiabatic_widths = [input_width] * (n_adiabatic_segments + 1)
    else:
        if len(adiabatic_widths) != n_adiabatic_segments + 1:
            raise ValueError(
                f"adiabatic_widths must have {n_adiabatic_segments + 1} values "
                f"(got {len(adiabatic_widths)})"
            )

    # =========================================================================
    # FIRST S-BEND (DOWNWARD)
    # =========================================================================

    # Define control points for first S-bend
    # Start at origin, go 2*length right and 2*length down
    x_start = 0.0
    y_start = 0.0
    x_mid1 = x_start + s_bend_length_x
    y_mid1 = y_start - s_bend_length_y
    x_end1 = x_mid1 + s_bend_length_x
    y_end1 = y_mid1 - s_bend_length_y

    # Generate smooth curve using cubic spline through control points
    # Add intermediate curve points between start-middle and middle-end
    curve1_x = []
    curve1_y = []

    # Start point
    curve1_x.append(x_start)
    curve1_y.append(y_start)

    # First section: start to middle (add n_pts_curve intermediate points)
    for i in range(1, n_pts_curve + 1):
        t = i / (n_pts_curve + 1)
        curve1_x.append(x_start + t * (x_mid1 - x_start))
        curve1_y.append(y_start + t * (y_mid1 - y_start))

    # Middle point
    curve1_x.append(x_mid1)
    curve1_y.append(y_mid1)

    # Second section: middle to end (add n_pts_curve intermediate points)
    for i in range(1, n_pts_curve + 1):
        t = i / (n_pts_curve + 1)
        curve1_x.append(x_mid1 + t * (x_end1 - x_mid1))
        curve1_y.append(y_mid1 + t * (y_end1 - y_mid1))

    # End point
    curve1_x.append(x_end1)
    curve1_y.append(y_end1)

    # Create smooth spline through control points
    curve1_x = np.array(curve1_x)
    curve1_y = np.array(curve1_y)

    # Use cubic spline for smooth curve
    spline1 = CubicSpline(curve1_x, curve1_y, bc_type='clamped')

    # Generate evenly spaced points along the S-bend
    x_samples1 = np.linspace(x_start, x_end1, n_pts_s_bend)
    y_samples1 = spline1(x_samples1)

    # Calculate derivatives (tangent vectors)
    dy_dx1 = spline1(x_samples1, 1)  # First derivative

    # Generate point pairs perpendicular to curve
    points_top1 = []
    points_bottom1 = []

    for i in range(n_pts_s_bend):
        x = x_samples1[i]
        y = y_samples1[i]
        dy_dx = dy_dx1[i]

        # Tangent vector (normalized)
        tangent = np.array([1.0, dy_dx])
        tangent = tangent / np.linalg.norm(tangent)

        # Normal vector (perpendicular, rotated 90 degrees)
        normal = np.array([-tangent[1], tangent[0]])

        # Points at +/- width/2 from centerline
        offset = input_width / 2
        pt_top = np.array([x, y]) + offset * normal
        pt_bottom = np.array([x, y]) - offset * normal

        points_top1.append(tuple(pt_top))
        points_bottom1.append(tuple(pt_bottom))

    # =========================================================================
    # ADIABATIC TAPER SECTION
    # =========================================================================

    # Start from the end of first S-bend
    x_adiabatic_start = x_end1
    y_adiabatic_start = y_end1

    points_top_adiabatic = []
    points_bottom_adiabatic = []

    for i in range(n_adiabatic_segments + 1):
        x = x_adiabatic_start + i * length_adiabatic_segments
        y = y_adiabatic_start
        width = adiabatic_widths[i]

        # Vertical point pairs (normal is along y-axis)
        pt_top = (x, y + width / 2)
        pt_bottom = (x, y - width / 2)

        points_top_adiabatic.append(pt_top)
        points_bottom_adiabatic.append(pt_bottom)

    # =========================================================================
    # SECOND S-BEND (UPWARD)
    # =========================================================================

    # Start from end of adiabatic section
    x_start2 = x_adiabatic_start + n_adiabatic_segments * length_adiabatic_segments
    y_start2 = y_adiabatic_start
    final_width = adiabatic_widths[-1]

    # End points: go 2*length right and 2*length UP
    x_mid2 = x_start2 + s_bend_length_x
    y_mid2 = y_start2 + s_bend_length_y  # UP (positive y)
    x_end2 = x_mid2 + s_bend_length_x
    y_end2 = y_mid2 + s_bend_length_y    # UP (positive y)

    # Generate smooth curve
    curve2_x = []
    curve2_y = []

    # Start point
    curve2_x.append(x_start2)
    curve2_y.append(y_start2)

    # First section: start to middle
    for i in range(1, n_pts_curve + 1):
        t = i / (n_pts_curve + 1)
        curve2_x.append(x_start2 + t * (x_mid2 - x_start2))
        curve2_y.append(y_start2 + t * (y_mid2 - y_start2))

    # Middle point
    curve2_x.append(x_mid2)
    curve2_y.append(y_mid2)

    # Second section: middle to end
    for i in range(1, n_pts_curve + 1):
        t = i / (n_pts_curve + 1)
        curve2_x.append(x_mid2 + t * (x_end2 - x_mid2))
        curve2_y.append(y_mid2 + t * (y_end2 - y_mid2))

    # End point
    curve2_x.append(x_end2)
    curve2_y.append(y_end2)

    # Create spline
    curve2_x = np.array(curve2_x)
    curve2_y = np.array(curve2_y)
    spline2 = CubicSpline(curve2_x, curve2_y, bc_type='clamped')

    # Generate evenly spaced points
    x_samples2 = np.linspace(x_start2, x_end2, n_pts_s_bend)
    y_samples2 = spline2(x_samples2)
    dy_dx2 = spline2(x_samples2, 1)

    # Generate point pairs
    points_top2 = []
    points_bottom2 = []

    for i in range(n_pts_s_bend):
        x = x_samples2[i]
        y = y_samples2[i]
        dy_dx = dy_dx2[i]

        # Tangent and normal vectors
        tangent = np.array([1.0, dy_dx])
        tangent = tangent / np.linalg.norm(tangent)
        normal = np.array([-tangent[1], tangent[0]])

        # Use final width from adiabatic section
        offset = final_width / 2
        pt_top = np.array([x, y]) + offset * normal
        pt_bottom = np.array([x, y]) - offset * normal

        points_top2.append(tuple(pt_top))
        points_bottom2.append(tuple(pt_bottom))

    # =========================================================================
    # CONSTRUCT COMPLETE POLYGON
    # =========================================================================

    # Combine all sections
    # Order: top of S-bend1, top of adiabatic, top of S-bend2,
    #        then reverse: bottom of S-bend2, bottom of adiabatic, bottom of S-bend1

    all_points = []

    # Top side (left to right)
    all_points.extend(points_top1)
    all_points.extend(points_top_adiabatic[1:])  # Skip first (duplicate)
    all_points.extend(points_top2[1:])           # Skip first (duplicate)

    # Bottom side (right to left)
    all_points.extend(reversed(points_bottom2))
    all_points.extend(reversed(points_bottom_adiabatic[:-1]))  # Skip last (duplicate)
    all_points.extend(reversed(points_bottom1[:-1]))           # Skip last (duplicate)

    # Add polygon to component
    c.add_polygon(all_points, layer=layer)

    # Add ports
    # Input port (left side)
    c.add_port(
        name="o1",
        center=(x_start, y_start),
        width=input_width,
        orientation=180,
        layer=layer
    )

    # Output port (right side)
    c.add_port(
        name="o2",
        center=(x_end2, y_end2),
        width=final_width,
        orientation=0,
        layer=layer
    )

    # Store parameters in component info
    c.info['input_width'] = input_width
    c.info['s_bend_length_x'] = s_bend_length_x
    c.info['s_bend_length_y'] = s_bend_length_y
    c.info['n_adiabatic_segments'] = n_adiabatic_segments
    c.info['total_length'] = x_end2 - x_start
    c.info['vertical_offset'] = 0.0  # Returns to same height

    return c


def main():
    """Generate and visualize the S-bend with adiabatic coupler."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    print("="*70)
    print("S-BEND WITH ADIABATIC COUPLER - PCELL GENERATOR")
    print("="*70)

    output_dir = Path(__file__).parent.parent / "outputs"

    # Example 1: Constant width
    print("\nExample 1: Constant width (0.4 µm)")
    coupler1 = s_bend_adiabatic_coupler(
        input_width=0.4,
        s_bend_length_x=10.0,
        s_bend_length_y=5.0,
        n_pts_s_bend=30,
        n_adiabatic_segments=10,
        length_adiabatic_segments=20.0,
        adiabatic_widths=None,  # Constant width
        layer=(1, 0)
    )

    print(f"✓ Created: {coupler1.name}")
    print(f"  Total length: {coupler1.info['total_length']:.2f} µm")

    output_gds = output_dir / "s_bend_coupler_constant.gds"
    coupler1.write_gds(str(output_gds))
    print(f"✓ Saved GDS: {output_gds}")

    fig = coupler1.plot()
    output_png = output_dir / "s_bend_coupler_constant.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close('all')
    print(f"✓ Saved visualization: {output_png}")

    # Example 2: Tapered width (expand and contract)
    print("\nExample 2: Adiabatic taper (0.4 → 1.2 → 0.4 µm)")

    # Create smooth taper profile
    n_seg = 10
    widths = []
    for i in range(n_seg + 1):
        t = i / n_seg
        # Gaussian-like profile
        width = 0.4 + 0.8 * np.exp(-((t - 0.5) ** 2) / (2 * 0.1 ** 2))
        widths.append(width)

    coupler2 = s_bend_adiabatic_coupler(
        input_width=0.4,
        s_bend_length_x=10.0,
        s_bend_length_y=5.0,
        n_pts_s_bend=30,
        n_adiabatic_segments=10,
        length_adiabatic_segments=20.0,
        adiabatic_widths=widths,
        layer=(1, 0)
    )

    print(f"✓ Created: {coupler2.name}")
    print(f"  Width profile: {[f'{w:.2f}' for w in widths]}")

    output_gds = output_dir / "s_bend_coupler_tapered.gds"
    coupler2.write_gds(str(output_gds))
    print(f"✓ Saved GDS: {output_gds}")

    fig = coupler2.plot()
    output_png = output_dir / "s_bend_coupler_tapered.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close('all')
    print(f"✓ Saved visualization: {output_png}")

    # Example 3: Linear taper
    print("\nExample 3: Linear taper (0.4 → 0.8 → 0.4 µm)")

    n_seg = 10
    widths_linear = np.concatenate([
        np.linspace(0.4, 0.8, 6),
        np.linspace(0.8, 0.4, 6)[1:]
    ]).tolist()

    coupler3 = s_bend_adiabatic_coupler(
        input_width=0.4,
        n_adiabatic_segments=10,
        adiabatic_widths=widths_linear,
        layer=(1, 0)
    )

    output_gds = output_dir / "s_bend_coupler_linear.gds"
    coupler3.write_gds(str(output_gds))
    print(f"✓ Saved GDS: {output_gds}")

    fig = coupler3.plot()
    output_png = output_dir / "s_bend_coupler_linear.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close('all')
    print(f"✓ Saved visualization: {output_png}")

    # Create comparison plot - generate separate plots and combine
    print("\nCreating comparison plot...")

    # Create figure with subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for idx, (coupler, title) in enumerate([
        (coupler1, "Constant Width"),
        (coupler2, "Gaussian Taper"),
        (coupler3, "Linear Taper")
    ]):
        ax = axes[idx]

        # Create temporary plot and extract data
        try:
            temp_fig = coupler.plot()
            temp_ax = plt.gca()

            # Copy all patches from temp plot
            for patch in temp_ax.patches:
                from matplotlib.patches import Polygon as mpl_Polygon
                ax.add_patch(mpl_Polygon(patch.get_xy(),
                                        facecolor=patch.get_facecolor(),
                                        edgecolor=patch.get_edgecolor(),
                                        alpha=patch.get_alpha()))

            # Set limits from bbox
            bbox = coupler.bbox()
            if bbox and not bbox.empty():
                margin = 5
                ax.set_xlim(bbox.left - margin, bbox.right + margin)
                ax.set_ylim(bbox.bottom - margin, bbox.top + margin)

            plt.close(temp_fig)
        except Exception as e:
            # Fallback if plotting fails
            ax.text(0.5, 0.5, f"{title}\n(visualization error)",
                   ha='center', va='center', transform=ax.transAxes)

        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel("X (µm)", fontsize=10)
        ax.set_ylabel("Y (µm)", fontsize=10)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_comparison = output_dir / "s_bend_coupler_comparison.png"
    plt.savefig(output_comparison, dpi=200, bbox_inches='tight')
    plt.close('all')
    print(f"✓ Saved comparison: {output_comparison}")

    print("\n" + "="*70)
    print("COMPLETE")
    print("="*70)
    print(f"\nGenerated files in {output_dir}:")
    print(f"  • s_bend_coupler_constant.gds - Constant width design")
    print(f"  • s_bend_coupler_tapered.gds - Gaussian taper design")
    print(f"  • s_bend_coupler_linear.gds - Linear taper design")
    print(f"  • s_bend_coupler_comparison.png - Side-by-side comparison")
    print("\n🔬 Next steps:")
    print("  1. Review the generated designs")
    print("  2. Run parameter sweeps on taper profiles")
    print("  3. Import into Lumerical MODE for mode analysis")
    print("  4. Optimize for adiabatic coupling efficiency")


if __name__ == "__main__":
    main()
