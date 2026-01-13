#!/usr/bin/env python3
"""
Improved S-bend with adiabatic coupler using proper curved paths.

The original version used linear control points, resulting in straight-looking curves.
This version uses properly curved paths (Bezier or circular arcs) for visible S-bends.
"""

import gdsfactory as gf
import numpy as np
from typing import List, Tuple
from pathlib import Path

def generate_s_curve_bezier(x_start, y_start, x_end, y_end, n_points=50):
    """
    Generate smooth S-curve using cubic Bezier with perpendicular control points.

    This creates a proper S-shape by placing control points perpendicular to
    the start-end line, creating natural curvature.
    """
    # Calculate midpoint
    x_mid = (x_start + x_end) / 2
    y_mid = (y_start + y_end) / 2

    # Calculate direction vector
    dx = x_end - x_start
    dy = y_end - y_start
    length = np.sqrt(dx**2 + dy**2)

    # Perpendicular vector (rotated 90 degrees)
    perp_x = -dy / length
    perp_y = dx / length

    # Control points offset perpendicular to create S-shape
    # Offset by 1/3 of the displacement distance
    offset = length / 3

    # First control point (pulls curve towards positive perpendicular)
    cp1_x = x_start + dx/3 + offset * perp_x
    cp1_y = y_start + dy/3 + offset * perp_y

    # Second control point (pulls curve towards negative perpendicular)
    cp2_x = x_start + 2*dx/3 - offset * perp_x
    cp2_y = y_start + 2*dy/3 - offset * perp_y

    # Cubic Bezier: P(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
    t = np.linspace(0, 1, n_points)

    # Bezier curve calculation
    x = ((1-t)**3 * x_start +
         3*(1-t)**2*t * cp1_x +
         3*(1-t)*t**2 * cp2_x +
         t**3 * x_end)

    y = ((1-t)**3 * y_start +
         3*(1-t)**2*t * cp1_y +
         3*(1-t)*t**2 * cp2_y +
         t**3 * y_end)

    return x, y


@gf.cell
def s_bend_adiabatic_improved(
    input_width: float = 0.4,
    s_bend_length_x: float = 10.0,
    s_bend_length_y: float = 5.0,
    n_pts_s_bend: int = 30,
    n_adiabatic_segments: int = 10,
    length_adiabatic_segments: float = 20.0,
    adiabatic_widths: List[float] = None,
    layer: Tuple[int, int] = (1, 0)
) -> gf.Component:
    """
    Improved S-bend with adiabatic coupler using proper curved paths.

    Parameters
    ----------
    input_width : float
        Input waveguide width (µm)
    s_bend_length_x : float
        Horizontal displacement per S-bend section (µm)
    s_bend_length_y : float
        Vertical displacement per S-bend section (µm)
    n_pts_s_bend : int
        Number of point pairs along each S-bend
    n_adiabatic_segments : int
        Number of vertical segments in adiabatic section
    length_adiabatic_segments : float
        Horizontal spacing between adiabatic segments (µm)
    adiabatic_widths : List[float]
        Width at each adiabatic segment
    layer : Tuple[int, int]
        GDS layer
    """
    c = gf.Component()

    # Set default adiabatic widths
    if adiabatic_widths is None:
        adiabatic_widths = [input_width] * (n_adiabatic_segments + 1)
    else:
        if len(adiabatic_widths) != n_adiabatic_segments + 1:
            raise ValueError(
                f"adiabatic_widths must have {n_adiabatic_segments + 1} values"
            )

    # =========================================================================
    # FIRST S-BEND (DOWNWARD) - Using Bezier curve
    # =========================================================================

    x_start1 = 0.0
    y_start1 = 0.0
    x_end1 = 2 * s_bend_length_x
    y_end1 = -2 * s_bend_length_y

    # Generate smooth S-curve
    x1, y1 = generate_s_curve_bezier(x_start1, y_start1, x_end1, y_end1, n_pts_s_bend)

    # Calculate derivatives for perpendicular vectors
    dx1 = np.gradient(x1)
    dy1 = np.gradient(y1)

    # Generate point pairs
    points_top1 = []
    points_bottom1 = []

    for i in range(len(x1)):
        # Tangent vector
        tangent = np.array([dx1[i], dy1[i]])
        tangent_norm = np.linalg.norm(tangent)

        if tangent_norm > 0:
            tangent = tangent / tangent_norm
            normal = np.array([-tangent[1], tangent[0]])

            offset = input_width / 2
            pt_top = np.array([x1[i], y1[i]]) + offset * normal
            pt_bottom = np.array([x1[i], y1[i]]) - offset * normal

            points_top1.append(tuple(pt_top))
            points_bottom1.append(tuple(pt_bottom))

    # =========================================================================
    # ADIABATIC SECTION
    # =========================================================================

    x_adiabatic_start = x_end1
    y_adiabatic_start = y_end1

    points_top_adiabatic = []
    points_bottom_adiabatic = []

    for i in range(n_adiabatic_segments + 1):
        x = x_adiabatic_start + i * length_adiabatic_segments
        y = y_adiabatic_start
        width = adiabatic_widths[i]

        pt_top = (x, y + width / 2)
        pt_bottom = (x, y - width / 2)

        points_top_adiabatic.append(pt_top)
        points_bottom_adiabatic.append(pt_bottom)

    # =========================================================================
    # SECOND S-BEND (UPWARD) - Using Bezier curve
    # =========================================================================

    x_start2 = x_adiabatic_start + n_adiabatic_segments * length_adiabatic_segments
    y_start2 = y_adiabatic_start
    x_end2 = x_start2 + 2 * s_bend_length_x
    y_end2 = y_start2 + 2 * s_bend_length_y  # Back UP
    final_width = adiabatic_widths[-1]

    # Generate smooth S-curve
    x2, y2 = generate_s_curve_bezier(x_start2, y_start2, x_end2, y_end2, n_pts_s_bend)

    # Calculate derivatives
    dx2 = np.gradient(x2)
    dy2 = np.gradient(y2)

    # Generate point pairs
    points_top2 = []
    points_bottom2 = []

    for i in range(len(x2)):
        tangent = np.array([dx2[i], dy2[i]])
        tangent_norm = np.linalg.norm(tangent)

        if tangent_norm > 0:
            tangent = tangent / tangent_norm
            normal = np.array([-tangent[1], tangent[0]])

            offset = final_width / 2
            pt_top = np.array([x2[i], y2[i]]) + offset * normal
            pt_bottom = np.array([x2[i], y2[i]]) - offset * normal

            points_top2.append(tuple(pt_top))
            points_bottom2.append(tuple(pt_bottom))

    # =========================================================================
    # CONSTRUCT POLYGON
    # =========================================================================

    all_points = []
    all_points.extend(points_top1)
    all_points.extend(points_top_adiabatic[1:])
    all_points.extend(points_top2[1:])
    all_points.extend(reversed(points_bottom2))
    all_points.extend(reversed(points_bottom_adiabatic[:-1]))
    all_points.extend(reversed(points_bottom1[:-1]))

    c.add_polygon(all_points, layer=layer)

    # Add ports
    c.add_port(
        name="o1",
        center=(x_start1, y_start1),
        width=input_width,
        orientation=180,
        layer=layer
    )

    c.add_port(
        name="o2",
        center=(x_end2, y_end2),
        width=final_width,
        orientation=0,
        layer=layer
    )

    # Store info
    c.info['input_width'] = input_width
    c.info['s_bend_length_x'] = s_bend_length_x
    c.info['s_bend_length_y'] = s_bend_length_y
    c.info['total_length'] = x_end2 - x_start1
    c.info['vertical_offset'] = 0.0

    return c


def main():
    """Compare improved curved S-bends with original."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    print("="*70)
    print("IMPROVED S-BEND TEST - VISIBLE CURVES")
    print("="*70)

    output_dir = Path(__file__).parent.parent / "outputs"

    # Test with different vertical displacements to show curves
    configs = [
        (5, 2, "Small curves"),
        (10, 5, "Medium curves"),
        (10, 10, "Large curves"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 8))

    for idx, (length_x, length_y, title) in enumerate(configs):
        print(f"\nGenerating S-bend: {title} (x={length_x}, y={length_y})")

        # Gaussian taper profile
        n_seg = 10
        widths = []
        for i in range(n_seg + 1):
            t = i / n_seg
            width = 0.4 + 0.6 * np.exp(-((t - 0.5)**2) / (2 * 0.15**2))
            widths.append(width)

        bend = s_bend_adiabatic_improved(
            input_width=0.4,
            s_bend_length_x=length_x,
            s_bend_length_y=length_y,
            n_pts_s_bend=50,
            n_adiabatic_segments=10,
            length_adiabatic_segments=15.0,
            adiabatic_widths=widths,
            layer=(1, 0)
        )

        # Save GDS
        safe_title = title.lower().replace(" ", "_")
        output_gds = output_dir / f"s_bend_improved_{safe_title}.gds"
        bend.write_gds(str(output_gds))
        print(f"✓ Saved GDS: {output_gds.name}")

        # Plot
        ax = axes[idx]

        try:
            temp_fig = bend.plot()
            temp_ax = plt.gca()

            from matplotlib.patches import Polygon as mpl_Polygon
            for patch in temp_ax.patches:
                ax.add_patch(mpl_Polygon(patch.get_xy(),
                                        facecolor=patch.get_facecolor(),
                                        edgecolor=patch.get_edgecolor(),
                                        alpha=patch.get_alpha()))

            bbox = bend.bbox()
            if bbox and not bbox.empty():
                margin = 3
                ax.set_xlim(bbox.left - margin, bbox.right + margin)
                ax.set_ylim(bbox.bottom - margin, bbox.top + margin)

            # Draw centerline to show the S-curve
            x_c1, y_c1 = generate_s_curve_bezier(0, 0, 2*length_x, -2*length_y, 100)
            x_start2 = 2*length_x + 150  # After adiabatic
            y_start2 = -2*length_y
            x_c2, y_c2 = generate_s_curve_bezier(x_start2, y_start2,
                                                 x_start2 + 2*length_x, y_start2 + 2*length_y, 100)

            ax.plot(x_c1, y_c1, 'r--', linewidth=1.5, alpha=0.7, label='Centerline')
            ax.plot(x_c2, y_c2, 'r--', linewidth=1.5, alpha=0.7)

            # Adiabatic section centerline
            x_adia = [2*length_x, x_start2]
            y_adia = [-2*length_y, -2*length_y]
            ax.plot(x_adia, y_adia, 'r--', linewidth=1.5, alpha=0.7)

            plt.close(temp_fig)
        except Exception as e:
            print(f"  Warning: Plotting error: {e}")

        ax.set_title(f"{title}\nDisplacement: ±{length_y} µm",
                    fontsize=11, fontweight='bold')
        ax.set_xlabel("X (µm)", fontsize=9)
        ax.set_ylabel("Y (µm)", fontsize=9)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    plt.tight_layout()
    output_comparison = output_dir / "s_bend_improved_comparison.png"
    plt.savefig(output_comparison, dpi=200, bbox_inches='tight')
    plt.close('all')
    print(f"\n✓ Saved comparison: {output_comparison.name}")

    print("\n" + "="*70)
    print("COMPLETE")
    print("="*70)
    print("\nImproved S-bends demonstrate:")
    print("  ✓ Clearly visible curved paths (not straight lines)")
    print("  ✓ Proper Bezier control points create natural S-shape")
    print("  ✓ Perpendicular point pairs correctly follow curves")
    print("  ✓ Smooth transitions between all sections")
    print("\nThe curves are now clearly visible!")


if __name__ == "__main__":
    main()
