#!/usr/bin/env python3
"""
S-bend with adiabatic coupler using gdsfactory's native bend_s.

This module provides:
1. Standalone adiabatic taper component (with ports)
2. Option A: Merged polygon version (single component)
3. Option C: Hierarchical version (sub-components with references)

Uses bend_s (Bezier S-bend) which provides exact size control (x, y displacement).
"""

import gdsfactory as gf
import numpy as np
from typing import List, Tuple
from pathlib import Path


@gf.cell
def adiabatic_taper(
    n_segments: int = 10,
    segment_length: float = 20.0,
    widths: List[float] = None,
    input_width: float = 0.4,
    output_width: float = 0.4,
    layer: Tuple[int, int] = (1, 0)
) -> gf.Component:
    """
    Adiabatic taper section with configurable width profile.

    Parameters
    ----------
    n_segments : int
        Number of taper segments
    segment_length : float
        Length of each segment (µm)
    widths : List[float]
        Width at each position (n_segments + 1 values)
        If None, uses linear taper from input_width to output_width
    input_width : float
        Input width (µm), used if widths is None
    output_width : float
        Output width (µm), used if widths is None
    layer : Tuple[int, int]
        GDS layer

    Returns
    -------
    Component
        Adiabatic taper with input port 'o1' and output port 'o2'
    """
    c = gf.Component()

    # Set default widths if not provided
    if widths is None:
        widths = np.linspace(input_width, output_width, n_segments + 1).tolist()
    else:
        if len(widths) != n_segments + 1:
            raise ValueError(f"widths must have {n_segments + 1} values")

    # Generate vertical point pairs for each segment
    points_top = []
    points_bottom = []

    for i in range(n_segments + 1):
        x = i * segment_length
        y = 0.0
        width = widths[i]

        # Vertical point pairs
        pt_top = (x, y + width / 2)
        pt_bottom = (x, y - width / 2)

        points_top.append(pt_top)
        points_bottom.append(pt_bottom)

    # Construct polygon (top edge, then bottom edge reversed)
    all_points = points_top + list(reversed(points_bottom))
    c.add_polygon(all_points, layer=layer)

    # Add ports at input and output
    total_length = n_segments * segment_length

    c.add_port(
        name="o1",
        center=(0, 0),
        width=widths[0],
        orientation=180,
        layer=layer
    )

    c.add_port(
        name="o2",
        center=(total_length, 0),
        width=widths[-1],
        orientation=0,
        layer=layer
    )

    # Store parameters
    c.info['n_segments'] = n_segments
    c.info['segment_length'] = segment_length
    c.info['total_length'] = total_length
    c.info['input_width'] = widths[0]
    c.info['output_width'] = widths[-1]

    return c


@gf.cell
def s_bend_adiabatic_merged(
    input_width: float = 0.4,
    s_bend_size: Tuple[float, float] = (20.0, 10.0),
    n_adiabatic_segments: int = 10,
    length_adiabatic_segments: float = 20.0,
    adiabatic_widths: List[float] = None,
    nb_points: int = 99,
    layer: Tuple[int, int] = (1, 0)
) -> gf.Component:
    """
    Option A: S-bend with adiabatic coupler (merged polygons).

    All geometry is merged into a single polygon in one component.

    Parameters
    ----------
    input_width : float
        Input waveguide width (µm)
    s_bend_size : Tuple[float, float]
        S-bend size as (length, offset) in µm
        E.g., (20, 10) creates 20 µm horizontal, ±10 µm vertical
    n_adiabatic_segments : int
        Number of adiabatic segments
    length_adiabatic_segments : float
        Length of each segment (µm)
    adiabatic_widths : List[float]
        Width profile (n_segments + 1 values)
    nb_points : int
        Number of points for S-bend smoothness
    layer : Tuple[int, int]
        GDS layer

    Returns
    -------
    Component
        Single merged component with input/output ports
    """
    c = gf.Component()

    # Set default widths
    if adiabatic_widths is None:
        adiabatic_widths = [input_width] * (n_adiabatic_segments + 1)

    final_width = adiabatic_widths[-1]

    # =========================================================================
    # Create first S-bend (downward) with input_width
    # =========================================================================
    s_bend_1 = gf.components.bend_s(
        size=s_bend_size,
        npoints=nb_points,
        cross_section=gf.cross_section.strip(width=input_width, layer=layer)
    )

    # Get the bounding box to understand offset
    bbox1 = s_bend_1.bbox()
    s_bend_1_length_x = s_bend_size[0]
    s_bend_1_offset_y = s_bend_size[1]  # This is the vertical offset

    # Extract polygons from first S-bend
    polygons_dict = s_bend_1.get_polygons(by='tuple', layers=[layer])
    if layer in polygons_dict:
        for polygon in polygons_dict[layer]:
            # Convert polygon to list of tuples
            points = [(p.x, p.y) for p in polygon.each_point_hull()]
            c.add_polygon(points, layer=layer)

    # =========================================================================
    # Create adiabatic taper and position it
    # =========================================================================
    adiabatic = adiabatic_taper(
        n_segments=n_adiabatic_segments,
        segment_length=length_adiabatic_segments,
        widths=adiabatic_widths,
        layer=layer
    )

    # Position adiabatic section at end of first S-bend
    # The first S-bend ends at (s_bend_1_length_x, -s_bend_1_offset_y)
    x_offset_adia = s_bend_1_length_x
    y_offset_adia = -s_bend_1_offset_y

    # Extract and add adiabatic polygons with manual translation
    polygons_dict_adia = adiabatic.get_polygons(by='tuple', layers=[layer])
    if layer in polygons_dict_adia:
        for polygon in polygons_dict_adia[layer]:
            # Translate polygon points
            points = [(p.x + x_offset_adia, p.y + y_offset_adia) for p in polygon.each_point_hull()]
            c.add_polygon(points, layer=layer)

    # =========================================================================
    # Create second S-bend (upward) with final_width
    # =========================================================================
    s_bend_2 = gf.components.bend_s(
        size=s_bend_size,
        npoints=nb_points,
        cross_section=gf.cross_section.strip(width=final_width, layer=layer)
    )

    # Position second S-bend at end of adiabatic section
    # Start position: end of first S-bend + adiabatic length
    x_offset_s2 = s_bend_1_length_x + n_adiabatic_segments * length_adiabatic_segments
    y_offset_s2 = -s_bend_1_offset_y

    # Extract second S-bend polygons, mirror and translate manually
    polygons_dict_s2 = s_bend_2.get_polygons(by='tuple', layers=[layer])
    if layer in polygons_dict_s2:
        for polygon in polygons_dict_s2[layer]:
            # Mirror around x-axis (flip y coordinates) and translate
            points = [(p.x + x_offset_s2, -p.y + y_offset_s2) for p in polygon.each_point_hull()]
            c.add_polygon(points, layer=layer)

    # =========================================================================
    # Add ports at input and output
    # =========================================================================
    c.add_port(
        name="o1",
        center=(0, 0),
        width=input_width,
        orientation=180,
        layer=layer
    )

    # Output is at the end of second S-bend
    # Second S-bend ends at x_offset_s2 + s_bend_1_length_x, y_offset_s2 + s_bend_1_offset_y
    x_output = x_offset_s2 + s_bend_1_length_x
    y_output = y_offset_s2 + s_bend_1_offset_y  # Should return to 0

    c.add_port(
        name="o2",
        center=(x_output, y_output),
        width=final_width,
        orientation=0,
        layer=layer
    )

    # Store parameters
    c.info['total_length'] = x_output
    c.info['vertical_offset'] = y_output
    c.info['input_width'] = input_width
    c.info['output_width'] = final_width

    return c


@gf.cell
def s_bend_adiabatic_hierarchical(
    input_width: float = 0.4,
    s_bend_size: Tuple[float, float] = (20.0, 10.0),
    n_adiabatic_segments: int = 10,
    length_adiabatic_segments: float = 20.0,
    adiabatic_widths: List[float] = None,
    nb_points: int = 99,
    layer: Tuple[int, int] = (1, 0)
) -> gf.Component:
    """
    Option C: S-bend with adiabatic coupler (hierarchical with sub-components).

    Uses references/instances for each section, connected via ports.

    Parameters
    ----------
    input_width : float
        Input waveguide width (µm)
    s_bend_size : Tuple[float, float]
        S-bend size as (length, offset) in µm
    n_adiabatic_segments : int
        Number of adiabatic segments
    length_adiabatic_segments : float
        Length of each segment (µm)
    adiabatic_widths : List[float]
        Width profile (n_segments + 1 values)
    nb_points : int
        Number of points for S-bend smoothness
    layer : Tuple[int, int]
        GDS layer

    Returns
    -------
    Component
        Hierarchical component with sub-component references
    """
    c = gf.Component()

    # Set default widths
    if adiabatic_widths is None:
        adiabatic_widths = [input_width] * (n_adiabatic_segments + 1)

    final_width = adiabatic_widths[-1]

    # =========================================================================
    # Create first S-bend (downward)
    # =========================================================================
    s_bend_1 = gf.components.bend_s(
        size=s_bend_size,
        npoints=nb_points,
        cross_section=gf.cross_section.strip(width=input_width, layer=layer)
    )

    s_bend_1_ref = c.add_ref(s_bend_1)

    # =========================================================================
    # Create and connect adiabatic taper
    # =========================================================================
    adiabatic = adiabatic_taper(
        n_segments=n_adiabatic_segments,
        segment_length=length_adiabatic_segments,
        widths=adiabatic_widths,
        layer=layer
    )

    adiabatic_ref = c.add_ref(adiabatic)

    # Connect adiabatic to first S-bend output
    # Note: gdsfactory S-bends have ports 'o1' (input) and 'o2' (output)
    adiabatic_ref.connect("o1", s_bend_1_ref.ports["o2"], allow_width_mismatch=True)

    # =========================================================================
    # Create second S-bend (upward, mirrored)
    # =========================================================================
    s_bend_2 = gf.components.bend_s(
        size=s_bend_size,
        npoints=nb_points,
        cross_section=gf.cross_section.strip(width=final_width, layer=layer)
    )

    # Add reference first, then connect with mirror flag
    s_bend_2_ref = c.add_ref(s_bend_2)

    # Connect second S-bend to adiabatic output with mirroring
    s_bend_2_ref.connect("o1", adiabatic_ref.ports["o2"], mirror=True, allow_width_mismatch=True)

    # =========================================================================
    # Add top-level ports
    # =========================================================================
    c.add_port("o1", port=s_bend_1_ref.ports["o1"])
    c.add_port("o2", port=s_bend_2_ref.ports["o2"])

    # Store parameters
    c.info['structure'] = 'hierarchical'
    c.info['input_width'] = input_width
    c.info['output_width'] = final_width

    return c


def main():
    """Test both implementation options."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    print("="*70)
    print("S-BEND + ADIABATIC COUPLER - GDSFACTORY NATIVE")
    print("="*70)

    output_dir = Path(__file__).parent.parent / "outputs"

    # Test widths (Gaussian taper)
    n_seg = 10
    widths_gaussian = []
    for i in range(n_seg + 1):
        t = i / n_seg
        width = 0.4 + 0.6 * np.exp(-((t - 0.5)**2) / (2 * 0.15**2))
        widths_gaussian.append(width)

    print(f"\nWidth profile: {[f'{w:.2f}' for w in widths_gaussian]}")

    # =========================================================================
    # Test standalone adiabatic taper first
    # =========================================================================
    print("\n" + "-"*70)
    print("1. STANDALONE ADIABATIC TAPER")
    print("-"*70)

    adiabatic_test = adiabatic_taper(
        n_segments=10,
        segment_length=20.0,
        widths=widths_gaussian,
        layer=(1, 0)
    )

    print(f"✓ Created: {adiabatic_test.name}")
    print(f"  Length: {adiabatic_test.info['total_length']:.1f} µm")
    print(f"  Input width: {adiabatic_test.info['input_width']:.2f} µm")
    print(f"  Output width: {adiabatic_test.info['output_width']:.2f} µm")
    print(f"  Ports: {[p.name for p in adiabatic_test.ports]}")

    output_gds = output_dir / "adiabatic_taper_standalone.gds"
    adiabatic_test.write_gds(str(output_gds))
    print(f"✓ Saved: {output_gds.name}")

    # =========================================================================
    # Test Option A: Merged polygons
    # =========================================================================
    print("\n" + "-"*70)
    print("2. OPTION A: MERGED POLYGONS")
    print("-"*70)

    merged = s_bend_adiabatic_merged(
        input_width=0.4,
        s_bend_size=(20.0, 10.0),
        n_adiabatic_segments=10,
        length_adiabatic_segments=20.0,
        adiabatic_widths=widths_gaussian,
        nb_points=99,
        layer=(1, 0)
    )

    print(f"✓ Created: {merged.name}")
    print(f"  Total length: {merged.info['total_length']:.1f} µm")
    print(f"  Vertical offset: {merged.info['vertical_offset']:.1f} µm")
    print(f"  Ports: {[p.name for p in merged.ports]}")

    output_gds = output_dir / "s_bend_adiabatic_merged.gds"
    merged.write_gds(str(output_gds))
    print(f"✓ Saved: {output_gds.name}")

    fig = merged.plot()
    output_png = output_dir / "s_bend_adiabatic_merged.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close('all')
    print(f"✓ Saved visualization: {output_png.name}")

    # =========================================================================
    # Test Option C: Hierarchical
    # =========================================================================
    print("\n" + "-"*70)
    print("3. OPTION C: HIERARCHICAL")
    print("-"*70)

    hierarchical = s_bend_adiabatic_hierarchical(
        input_width=0.4,
        s_bend_size=(20.0, 10.0),
        n_adiabatic_segments=10,
        length_adiabatic_segments=20.0,
        adiabatic_widths=widths_gaussian,
        nb_points=99,
        layer=(1, 0)
    )

    print(f"✓ Created: {hierarchical.name}")
    print(f"  Structure: {hierarchical.info['structure']}")
    print(f"  Ports: {[p.name for p in hierarchical.ports]}")

    output_gds = output_dir / "s_bend_adiabatic_hierarchical.gds"
    hierarchical.write_gds(str(output_gds))
    print(f"✓ Saved: {output_gds.name}")

    fig = hierarchical.plot()
    output_png = output_dir / "s_bend_adiabatic_hierarchical.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close('all')
    print(f"✓ Saved visualization: {output_png.name}")

    # =========================================================================
    # Create comparison
    # =========================================================================
    print("\n" + "-"*70)
    print("4. COMPARISON")
    print("-"*70)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    for idx, (comp, title) in enumerate([
        (merged, "Option A: Merged Polygons"),
        (hierarchical, "Option C: Hierarchical")
    ]):
        ax = axes[idx]

        try:
            temp_fig = comp.plot()
            temp_ax = plt.gca()

            from matplotlib.patches import Polygon as mpl_Polygon
            for patch in temp_ax.patches:
                ax.add_patch(mpl_Polygon(patch.get_xy(),
                                        facecolor=patch.get_facecolor(),
                                        edgecolor=patch.get_edgecolor(),
                                        alpha=patch.get_alpha()))

            bbox = comp.bbox()
            if bbox and not bbox.empty():
                margin = 5
                ax.set_xlim(bbox.left - margin, bbox.right + margin)
                ax.set_ylim(bbox.bottom - margin, bbox.top + margin)

            plt.close(temp_fig)
        except Exception as e:
            print(f"  Warning: Plotting error: {e}")

        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel("X (µm)", fontsize=10)
        ax.set_ylabel("Y (µm)", fontsize=10)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_comparison = output_dir / "s_bend_adiabatic_comparison_native.png"
    plt.savefig(output_comparison, dpi=200, bbox_inches='tight')
    plt.close('all')
    print(f"✓ Saved comparison: {output_comparison.name}")

    print("\n" + "="*70)
    print("COMPLETE")
    print("="*70)
    print("\nGenerated components:")
    print("  1. Standalone adiabatic taper (with ports)")
    print("  2. Option A: Merged polygons (single flat component)")
    print("  3. Option C: Hierarchical (sub-components via references)")
    print("\nBoth options use gdsfactory's native bend_euler_s for S-bends!")
    print("\nKey differences:")
    print("  • Option A: Faster rendering, single polygon, no hierarchy")
    print("  • Option C: Reusable sub-components, better for design reuse")


if __name__ == "__main__":
    main()
