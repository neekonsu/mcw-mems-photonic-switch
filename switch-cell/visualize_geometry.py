"""
Geometry visualization script for the gap-adjustable directional coupler.

This script visualizes the device geometry defined in geometry.py using matplotlib.
Saves figures to ./figures/ with timestamps to track design evolution.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os
from datetime import datetime

from geometry import get_geometry


# Material colors for visualization
MATERIAL_COLORS = {
    'Si': '#4682B4',      # Steel Blue
    'SiO2': '#87CEEB',    # Sky Blue
    'Air': '#F0F0F0',     # Light gray
}

MATERIAL_ALPHA = {
    'Si': 0.9,
    'SiO2': 0.3,
    'Air': 0.1,
}

# Type-specific colors for MEMS structures
TYPE_COLORS = {
    'waveguide': '#4682B4',  # Steel Blue
    'comb': '#FF6B6B',       # Coral Red (for comb fingers)
    'spring': '#4ECDC4',     # Turquoise (for springs)
    'anchor': '#95A5A6',     # Gray (for anchors)
    'shuttle': '#F39C12',    # Orange (for moving shuttle)
}

TYPE_ALPHA = {
    'waveguide': 0.9,
    'comb': 0.8,
    'spring': 0.7,
    'anchor': 0.9,
    'shuttle': 0.85,
}


def create_box_vertices(x, y, z, x_span, y_span, z_span):
    """
    Create vertices for a 3D box.

    Args:
        x, y, z: center position
        x_span, y_span, z_span: dimensions

    Returns:
        Array of 8 vertices defining the box corners
    """
    x_min, x_max = x - x_span/2, x + x_span/2
    y_min, y_max = y - y_span/2, y + y_span/2
    z_min, z_max = z - z_span/2, z + z_span/2

    vertices = np.array([
        [x_min, y_min, z_min],
        [x_max, y_min, z_min],
        [x_max, y_max, z_min],
        [x_min, y_max, z_min],
        [x_min, y_min, z_max],
        [x_max, y_min, z_max],
        [x_max, y_max, z_max],
        [x_min, y_max, z_max],
    ])

    return vertices


def get_box_faces(vertices):
    """Get the 6 faces of a box from its vertices."""
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
        [vertices[0], vertices[3], vertices[7], vertices[4]],  # left
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # right
    ]
    return faces


def plot_xy_view(geom, ax):
    """
    Plot top view (XY plane) of the device including waveguides and MEMS.

    Args:
        geom: DirectionalCouplerGeometry instance
        ax: matplotlib axis
    """
    structures = geom.get_waveguide_structures()

    # Plot all silicon structures (waveguides and MEMS)
    for struct in structures:
        if struct['material'] == 'Si' and struct['type'] != 'substrate':
            x = struct['x'] * 1e6  # Convert to μm
            y = struct['y'] * 1e6
            x_span = struct['x_span'] * 1e6
            y_span = struct['y_span'] * 1e6

            # Use type-specific colors if available
            struct_type = struct.get('type', 'waveguide')
            color = TYPE_COLORS.get(struct_type, MATERIAL_COLORS['Si'])
            alpha = TYPE_ALPHA.get(struct_type, MATERIAL_ALPHA['Si'])

            rect = Rectangle(
                (x - x_span/2, y - y_span/2),
                x_span, y_span,
                facecolor=color,
                edgecolor='black',
                linewidth=0.3,
                alpha=alpha
            )
            ax.add_patch(rect)

    # Add gap annotation
    gap_nm = geom.current_gap * 1e9
    ax.annotate(
        f'Gap: {gap_nm:.0f} nm\n({geom.gap_state.upper()})',
        xy=(0, 0), xytext=(geom.waveguide.coupling_length * 1e6 / 2 + 5, 0),
        fontsize=10, ha='left', va='center',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )

    ax.set_xlabel('X (μm)', fontsize=12)
    ax.set_ylabel('Y (μm)', fontsize=12)
    ax.set_title('Top View (XY plane)', fontsize=14, fontweight='bold')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5, linestyle='--', alpha=0.3)
    ax.axvline(x=0, color='k', linewidth=0.5, linestyle='--', alpha=0.3)

    # Set reasonable axis limits (already in μm from coordinate conversion)
    ax.autoscale()


def plot_xz_view(geom, ax):
    """
    Plot side view (XZ plane) of the device.

    Args:
        geom: DirectionalCouplerGeometry instance
        ax: matplotlib axis
    """
    structures = geom.get_waveguide_structures()

    for struct in structures:
        # Skip large substrate/cladding for clarity, or make them very transparent
        if struct['name'] in ['Si_substrate', 'cladding']:
            continue

        x = struct['x'] * 1e6  # Convert to μm
        z = struct['z'] * 1e6
        x_span = struct['x_span'] * 1e6
        z_span = struct['z_span'] * 1e6

        rect = Rectangle(
            (x - x_span/2, z - z_span/2),
            x_span, z_span,
            facecolor=MATERIAL_COLORS[struct['material']],
            edgecolor='black',
            linewidth=0.5,
            alpha=MATERIAL_ALPHA[struct['material']]
        )
        ax.add_patch(rect)

    # Add layer labels
    ax.text(-geom.waveguide.coupling_length * 1e6 / 2 - 5,
            -geom.soi.box_thickness * 1e6 / 2,
            'BOX (SiO₂)', fontsize=9, ha='right', va='center')
    ax.text(-geom.waveguide.coupling_length * 1e6 / 2 - 5,
            geom.soi.device_layer_thickness * 1e6 / 2,
            'Si', fontsize=9, ha='right', va='center')

    ax.set_xlabel('X (μm)', fontsize=12)
    ax.set_ylabel('Z (μm)', fontsize=12)
    ax.set_title('Side View (XZ plane)', fontsize=14, fontweight='bold')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5, linestyle='--', alpha=0.3)

    # Set reasonable axis limits
    ax.autoscale()


def plot_yz_view(geom, ax):
    """
    Plot cross-sectional view (YZ plane) through coupling region.

    Args:
        geom: DirectionalCouplerGeometry instance
        ax: matplotlib axis
    """
    structures = geom.get_waveguide_structures()

    # Plot BOX layer (convert to μm)
    box_struct = [s for s in structures if s['name'] == 'BOX'][0]
    rect = Rectangle(
        (-box_struct['y_span']/2 * 1e6, -box_struct['z_span'] * 1e6),
        box_struct['y_span'] * 1e6, box_struct['z_span'] * 1e6,
        facecolor=MATERIAL_COLORS['SiO2'],
        edgecolor='black',
        linewidth=0.5,
        alpha=MATERIAL_ALPHA['SiO2']
    )
    ax.add_patch(rect)

    # Plot waveguides in coupling region (convert to μm)
    y_off = geom.y_offset * 1e6
    wg_w = geom.waveguide.width * 1e6
    wg_h = geom.waveguide.height * 1e6

    # Waveguide 1 (top)
    rect1 = Rectangle(
        (y_off - wg_w/2, 0),
        wg_w, wg_h,
        facecolor=MATERIAL_COLORS['Si'],
        edgecolor='black',
        linewidth=1,
        alpha=MATERIAL_ALPHA['Si'],
        label='Waveguide'
    )
    ax.add_patch(rect1)

    # Waveguide 2 (bottom)
    rect2 = Rectangle(
        (-y_off - wg_w/2, 0),
        wg_w, wg_h,
        facecolor=MATERIAL_COLORS['Si'],
        edgecolor='black',
        linewidth=1,
        alpha=MATERIAL_ALPHA['Si']
    )
    ax.add_patch(rect2)

    # Gap annotation
    gap_nm = geom.current_gap * 1e9
    ax.annotate('', xy=(-y_off + wg_w/2, wg_h/2), xytext=(y_off - wg_w/2, wg_h/2),
                arrowprops=dict(arrowstyle='<->', color='red', lw=2))
    ax.text(0, wg_h/2 + 0.05, f'{gap_nm:.0f} nm',
            fontsize=10, ha='center', va='bottom', color='red', fontweight='bold')

    ax.set_xlabel('Y (μm)', fontsize=12)
    ax.set_ylabel('Z (μm)', fontsize=12)
    ax.set_title('Cross Section (YZ plane)', fontsize=14, fontweight='bold')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5, linestyle='--', alpha=0.3)
    ax.axvline(x=0, color='k', linewidth=0.5, linestyle='--', alpha=0.3)

    # Set reasonable axis limits
    ax.autoscale()


def plot_3d_view(geom, ax):
    """
    Plot 3D isometric view of the device.

    Args:
        geom: DirectionalCouplerGeometry instance
        ax: matplotlib 3D axis
    """
    structures = geom.get_waveguide_structures()

    for struct in structures:
        # Skip substrate and cladding for clarity
        if struct['name'] in ['Si_substrate', 'cladding']:
            continue

        # Create box
        vertices = create_box_vertices(
            struct['x'], struct['y'], struct['z'],
            struct['x_span'], struct['y_span'], struct['z_span']
        )
        faces = get_box_faces(vertices)

        # Create 3D polygon collection
        poly = Poly3DCollection(
            faces,
            facecolors=MATERIAL_COLORS[struct['material']],
            edgecolors='black',
            linewidths=0.3,
            alpha=MATERIAL_ALPHA[struct['material']]
        )
        ax.add_collection3d(poly)

    # Set labels and limits
    (x_bounds, y_bounds, z_bounds) = geom.get_device_bounds()

    ax.set_xlabel('X (μm)', fontsize=10)
    ax.set_ylabel('Y (μm)', fontsize=10)
    ax.set_zlabel('Z (μm)', fontsize=10)
    ax.set_title('3D View', fontsize=14, fontweight='bold')

    # Scale to micrometers
    ax.set_xlim(np.array(x_bounds) * 1e6)
    ax.set_ylim(np.array(y_bounds) * 1e6)
    ax.set_zlim([-geom.soi.box_thickness * 1e6,
                 (geom.soi.device_layer_thickness + 0.5e-6) * 1e6])

    # Set viewing angle
    ax.view_init(elev=20, azim=45)


def visualize_geometry(gap_state='off', save=True, timestamp=None):
    """
    Create a comprehensive visualization of the device geometry.

    Args:
        gap_state: 'off', 'on', or 'contact'
        save: Whether to save the figure
        timestamp: Optional timestamp string to use for folder/filename

    Returns:
        matplotlib figure
    """
    # Get geometry
    geom = get_geometry(gap_state=gap_state)

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))

    # Title
    fig.suptitle(
        f'Gap-Adjustable Directional Coupler Geometry\n'
        f'State: {gap_state.upper()} | Gap: {geom.current_gap*1e9:.0f} nm',
        fontsize=16, fontweight='bold'
    )

    # Create subplots
    ax1 = plt.subplot(2, 2, 1)  # XY view
    ax2 = plt.subplot(2, 2, 2)  # XZ view
    ax3 = plt.subplot(2, 2, 3)  # YZ view
    ax4 = plt.subplot(2, 2, 4, projection='3d')  # 3D view

    # Plot each view
    plot_xy_view(geom, ax1)
    plot_xz_view(geom, ax2)
    plot_yz_view(geom, ax3)
    plot_3d_view(geom, ax4)

    plt.tight_layout()

    # Save figure
    if save:
        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create timestamped subdirectory inside figures
        figures_base = os.path.join(os.path.dirname(__file__), 'figures')
        figures_dir = os.path.join(figures_base, timestamp)
        os.makedirs(figures_dir, exist_ok=True)

        # Generate filename with timestamp
        filename = f'{timestamp}_geometry_{gap_state}.png'
        filepath = os.path.join(figures_dir, filename)

        # Save with high DPI
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {filepath}")

    return fig


def compare_gap_states(timestamp=None):
    """
    Create a comparison visualization of OFF and ON states.

    Args:
        timestamp: Optional timestamp string to use for folder/filename
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Gap State Comparison: OFF vs ON', fontsize=16, fontweight='bold')

    # OFF state
    geom_off = get_geometry(gap_state='off')
    plot_xy_view(geom_off, axes[0, 0])
    axes[0, 0].set_title(f'OFF State - Top View\nGap: {geom_off.current_gap*1e9:.0f} nm',
                         fontweight='bold')

    plot_yz_view(geom_off, axes[0, 1])
    axes[0, 1].set_title(f'OFF State - Cross Section\nGap: {geom_off.current_gap*1e9:.0f} nm',
                         fontweight='bold')

    # ON state
    geom_on = get_geometry(gap_state='on')
    plot_xy_view(geom_on, axes[1, 0])
    axes[1, 0].set_title(f'ON State - Top View\nGap: {geom_on.current_gap*1e9:.0f} nm',
                         fontweight='bold')

    plot_yz_view(geom_on, axes[1, 1])
    axes[1, 1].set_title(f'ON State - Cross Section\nGap: {geom_on.current_gap*1e9:.0f} nm',
                         fontweight='bold')

    plt.tight_layout()

    # Save comparison with timestamp
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Create timestamped subdirectory inside figures
    figures_base = os.path.join(os.path.dirname(__file__), 'figures')
    figures_dir = os.path.join(figures_base, timestamp)
    os.makedirs(figures_dir, exist_ok=True)

    filepath = os.path.join(figures_dir, f'{timestamp}_comparison.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"Comparison figure saved to: {filepath}")

    return fig


if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("Directional Coupler Geometry Visualization")
    print("=" * 70)

    # Generate single timestamp for all figures in this run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Visualize OFF state
    print("\nGenerating OFF state visualization...")
    fig_off = visualize_geometry(gap_state='off', save=True, timestamp=timestamp)

    # Visualize ON state
    print("\nGenerating ON state visualization...")
    fig_on = visualize_geometry(gap_state='on', save=True, timestamp=timestamp)

    # Create comparison
    print("\nGenerating comparison visualization...")
    fig_compare = compare_gap_states(timestamp=timestamp)

    # Show all plots only if not running in non-interactive mode
    if '--no-show' not in sys.argv:
        plt.show()
    else:
        plt.close('all')

    print("\nVisualization complete!")
