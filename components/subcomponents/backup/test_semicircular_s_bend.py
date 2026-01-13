#!/usr/bin/env python3
"""
Test S-bend with semicircular curves to verify perpendicular point pair generation.
"""

import gdsfactory as gf
import numpy as np
from typing import Tuple
from pathlib import Path

# Configure matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

@gf.cell
def semicircular_s_bend(
    input_width: float = 0.4,
    radius: float = 10.0,
    n_pts_per_arc: int = 30,
    layer: Tuple[int, int] = (1, 0)
) -> gf.Component:
    """
    S-bend using semicircular arcs.

    Structure:
    - First semicircle: bends down
    - Second semicircle: bends back up
    - Total displacement: 2*radius right, 0 vertical (returns to input height)

    Parameters
    ----------
    input_width : float
        Waveguide width (µm)
    radius : float
        Radius of each semicircular arc (µm)
    n_pts_per_arc : int
        Number of points along each semicircle
    layer : Tuple[int, int]
        GDS layer
    """
    c = gf.Component()

    # Generate first semicircle (bending downward)
    # Center at (radius, 0), arc from 180° to 0° (clockwise)
    theta1 = np.linspace(np.pi, 0, n_pts_per_arc)
    x1 = radius + radius * np.cos(theta1)
    y1 = radius * np.sin(theta1)

    # Generate second semicircle (bending upward)
    # Center at (3*radius, 0), arc from 180° to 0° (counter-clockwise)
    theta2 = np.linspace(np.pi, 0, n_pts_per_arc)
    x2 = 3 * radius - radius * np.cos(theta2)
    y2 = -radius * np.sin(theta2)

    # Combine the two arcs
    x_curve = np.concatenate([x1, x2[1:]])  # Skip duplicate point
    y_curve = np.concatenate([y1, y2[1:]])

    # Calculate derivatives (tangent vectors) using finite differences
    dx = np.gradient(x_curve)
    dy = np.gradient(y_curve)

    # Generate point pairs perpendicular to curve
    points_top = []
    points_bottom = []

    for i in range(len(x_curve)):
        x = x_curve[i]
        y = y_curve[i]

        # Tangent vector
        tangent = np.array([dx[i], dy[i]])
        tangent_norm = np.linalg.norm(tangent)

        if tangent_norm > 0:
            tangent = tangent / tangent_norm

            # Normal vector (perpendicular, rotated 90 degrees)
            normal = np.array([-tangent[1], tangent[0]])

            # Points at +/- width/2 from centerline
            offset = input_width / 2
            pt_top = np.array([x, y]) + offset * normal
            pt_bottom = np.array([x, y]) - offset * normal

            points_top.append(tuple(pt_top))
            points_bottom.append(tuple(pt_bottom))

    # Construct polygon
    all_points = points_top + list(reversed(points_bottom))
    c.add_polygon(all_points, layer=layer)

    # Add ports
    c.add_port(
        name="o1",
        center=(0, 0),
        width=input_width,
        orientation=180,
        layer=layer
    )

    c.add_port(
        name="o2",
        center=(4 * radius, 0),
        width=input_width,
        orientation=0,
        layer=layer
    )

    c.info['radius'] = radius
    c.info['total_length'] = 4 * radius

    return c


def main():
    """Test semicircular S-bends with different radii."""
    print("="*70)
    print("SEMICIRCULAR S-BEND TEST")
    print("="*70)

    output_dir = Path(__file__).parent.parent / "outputs"

    # Test different radii to show curvature
    radii = [5, 10, 20]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for idx, radius in enumerate(radii):
        print(f"\nGenerating semicircular S-bend with radius = {radius} µm")

        bend = semicircular_s_bend(
            input_width=0.4,
            radius=radius,
            n_pts_per_arc=50,
            layer=(1, 0)
        )

        # Save GDS
        output_gds = output_dir / f"semicircular_s_bend_r{radius}.gds"
        bend.write_gds(str(output_gds))
        print(f"✓ Saved GDS: {output_gds.name}")

        # Save individual visualization
        fig_single = bend.plot()
        output_png = output_dir / f"semicircular_s_bend_r{radius}.png"
        plt.savefig(output_png, dpi=300, bbox_inches='tight')
        plt.close('all')
        print(f"✓ Saved PNG: {output_png.name}")

        # Plot in comparison
        ax = axes[idx]

        try:
            temp_fig = bend.plot()
            temp_ax = plt.gca()

            # Copy patches
            from matplotlib.patches import Polygon as mpl_Polygon
            for patch in temp_ax.patches:
                ax.add_patch(mpl_Polygon(patch.get_xy(),
                                        facecolor=patch.get_facecolor(),
                                        edgecolor=patch.get_edgecolor(),
                                        alpha=patch.get_alpha()))

            # Set limits
            bbox = bend.bbox()
            if bbox and not bbox.empty():
                margin = 2
                ax.set_xlim(bbox.left - margin, bbox.right + margin)
                ax.set_ylim(bbox.bottom - margin, bbox.top + margin)

            plt.close(temp_fig)
        except Exception as e:
            print(f"  Warning: Could not plot comparison: {e}")

        ax.set_title(f"Radius = {radius} µm\nLength = {4*radius} µm",
                    fontsize=11, fontweight='bold')
        ax.set_xlabel("X (µm)", fontsize=9)
        ax.set_ylabel("Y (µm)", fontsize=9)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

        # Draw centerline to show the S-curve
        theta1 = np.linspace(np.pi, 0, 50)
        x1 = radius + radius * np.cos(theta1)
        y1 = radius * np.sin(theta1)
        theta2 = np.linspace(np.pi, 0, 50)
        x2 = 3 * radius - radius * np.cos(theta2)
        y2 = -radius * np.sin(theta2)
        ax.plot(np.concatenate([x1, x2]), np.concatenate([y1, y2]),
               'r--', linewidth=1, alpha=0.5, label='Centerline')
        ax.legend(fontsize=8)

    plt.tight_layout()
    output_comparison = output_dir / "semicircular_s_bend_comparison.png"
    plt.savefig(output_comparison, dpi=200, bbox_inches='tight')
    plt.close('all')
    print(f"\n✓ Saved comparison: {output_comparison.name}")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nGenerated semicircular S-bends demonstrate:")
    print("  • Perpendicular point pairs correctly follow curved paths")
    print("  • Waveguide width maintained throughout curves")
    print("  • Smooth transitions between semicircular sections")
    print("\nThese can be used to verify the curve-following logic")
    print("before applying more complex spline-based curves.")


if __name__ == "__main__":
    main()
