# -*- coding: utf-8 -*-
"""
Geometry visualization script for MEMS photonic switches.

This script visualizes the 3D geometries defined in geometry.py, showing:
1. XY plane outlines (top view)
2. 3D extruded shapes

All dimensions are in microns.
Figures are automatically saved to ./figures/<timestamp_min>/<timestamp_sec>_<name>.png
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from typing import List
from datetime import datetime

from geometry import ExtrudedPolygon, get_example_geometries


# Colors for different geometry types
TYPE_COLORS = {
    'waveguide': '#4682B4',  # Steel Blue
    'switch': '#FF6B6B',     # Coral Red
    'comb': '#4ECDC4',       # Turquoise
    'spring': '#95A5A6',     # Gray
    'anchor': '#34495E',     # Dark Gray
    'generic': '#7F8C8D',    # Medium Gray
}


def get_timestamp_minute():
    """Get timestamp string for folder name (down to minute)."""
    return datetime.now().strftime("%Y%m%d_%H%M")


def get_timestamp_second():
    """Get timestamp string for file name (down to second)."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_output_directory(base_dir="figures"):
    """
    Create output directory structure.

    Args:
        base_dir: Base directory for figures

    Returns:
        Path to the timestamped subdirectory (down to minute)
    """
    # Get timestamp down to minute for folder name
    timestamp_min = get_timestamp_minute()
    output_dir = os.path.join(base_dir, timestamp_min)

    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    return output_dir


def plot_xy_outline(geom: ExtrudedPolygon, ax=None, show_vertices=True):
    """
    Plot the XY plane outline of a geometry.

    Args:
        geom: ExtrudedPolygon to visualize
        ax: Matplotlib axis (creates new figure if None)
        show_vertices: Whether to mark vertices with dots

    Returns:
        Matplotlib axis
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))

    # Get color for this geometry type
    color = TYPE_COLORS.get(geom.geometry_type, TYPE_COLORS['generic'])

    # Close the polygon by appending the first vertex
    vertices_closed = np.vstack([geom.vertices, geom.vertices[0]])

    # Plot the outline
    ax.plot(vertices_closed[:, 0], vertices_closed[:, 1],
            color=color, linewidth=2, label=geom.name)

    # Fill the polygon with transparency
    ax.fill(vertices_closed[:, 0], vertices_closed[:, 1],
            color=color, alpha=0.3)

    # Optionally show vertices
    if show_vertices:
        ax.plot(geom.vertices[:, 0], geom.vertices[:, 1],
                'o', color=color, markersize=6, markeredgecolor='black', markeredgewidth=1)

    # Configure axis
    ax.set_xlabel('X (μm)', fontsize=12)
    ax.set_ylabel('Y (μm)', fontsize=12)
    ax.set_title(f'{geom.name} - XY Plane Outline\n'
                 f'Type: {geom.geometry_type}, Material: {geom.material}',
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    ax.legend()

    return ax


def plot_3d_extrusion(geom: ExtrudedPolygon, ax=None):
    """
    Plot the 3D extruded geometry.

    Args:
        geom: ExtrudedPolygon to visualize
        ax: Matplotlib 3D axis (creates new figure if None)

    Returns:
        Matplotlib 3D axis
    """
    if ax is None:
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')

    # Get color for this geometry type
    color = TYPE_COLORS.get(geom.geometry_type, TYPE_COLORS['generic'])

    # Create vertices for the 3D extrusion
    n_vertices = len(geom.vertices)

    # Bottom face (at z_min)
    bottom_vertices = np.column_stack([geom.vertices, np.full(n_vertices, geom.z_min)])

    # Top face (at z_max)
    top_vertices = np.column_stack([geom.vertices, np.full(n_vertices, geom.z_max)])

    # Create faces for the 3D shape
    faces = []

    # Bottom face
    faces.append(bottom_vertices)

    # Top face
    faces.append(top_vertices)

    # Side faces (connect bottom and top)
    for i in range(n_vertices):
        next_i = (i + 1) % n_vertices
        # Create a quad face connecting bottom and top edges
        face = np.array([
            bottom_vertices[i],
            bottom_vertices[next_i],
            top_vertices[next_i],
            top_vertices[i]
        ])
        faces.append(face)

    # Create 3D polygon collection
    poly_collection = Poly3DCollection(faces, alpha=0.7, facecolor=color, edgecolor='black', linewidth=0.5)
    ax.add_collection3d(poly_collection)

    # Set axis limits with EQUAL SCALING to preserve true aspect ratios
    x_min, x_max, y_min, y_max = geom.get_xy_bounds()

    # Calculate ranges
    x_range = x_max - x_min
    y_range = y_max - y_min
    z_range = geom.z_max - geom.z_min

    # Find maximum range to use for all axes
    max_range = max(x_range, y_range, z_range)

    # Calculate centers
    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2
    z_center = (geom.z_min + geom.z_max) / 2

    # Add padding (10% of max range)
    padding = max_range * 0.1
    half_range = (max_range + 2 * padding) / 2

    # Set equal limits for all axes
    ax.set_xlim(x_center - half_range, x_center + half_range)
    ax.set_ylim(y_center - half_range, y_center + half_range)
    ax.set_zlim(z_center - half_range, z_center + half_range)

    # Set equal aspect ratio for 3D box
    ax.set_box_aspect([1, 1, 1])

    # Labels
    ax.set_xlabel('X (μm)', fontsize=12)
    ax.set_ylabel('Y (μm)', fontsize=12)
    ax.set_zlabel('Z (μm)', fontsize=12)
    ax.set_title(f'{geom.name} - 3D View\n'
                 f'Type: {geom.geometry_type}, Thickness: {geom.thickness:.3f} μm',
                 fontsize=14, fontweight='bold')

    # Set viewing angle for better perspective
    ax.view_init(elev=25, azim=45)

    return ax


def visualize_all_geometries(geometries: List[ExtrudedPolygon], combined_views=True,
                             output_dir=None, save=True):
    """
    Visualize all geometries, either as separate plots or combined views.

    Args:
        geometries: List of ExtrudedPolygon objects
        combined_views: If True, show all geometries in combined XY and 3D plots.
                       If False, create separate plots for each geometry.
        output_dir: Directory to save figures. If None and save=True, creates ./figures/<timestamp>/
        save: Whether to save figures to disk

    Returns:
        List of saved file paths (if save=True), otherwise empty list
    """
    saved_files = []

    # Setup output directory if saving
    if save:
        if output_dir is None:
            output_dir = ensure_output_directory("figures")
        else:
            os.makedirs(output_dir, exist_ok=True)

    if combined_views:
        # Create combined XY view and combined 3D view
        fig = plt.figure(figsize=(16, 7))

        # XY plane (all geometries)
        ax_xy = fig.add_subplot(121)
        for geom in geometries:
            plot_xy_outline(geom, ax=ax_xy, show_vertices=False)
        ax_xy.set_title('All Geometries - XY Plane', fontsize=14, fontweight='bold')
        ax_xy.legend()

        # 3D view (all geometries)
        ax_3d = fig.add_subplot(122, projection='3d')

        # Determine global bounds for consistent scaling
        all_x = []
        all_y = []
        all_z = []

        for geom in geometries:
            color = TYPE_COLORS.get(geom.geometry_type, TYPE_COLORS['generic'])
            n_vertices = len(geom.vertices)

            bottom_vertices = np.column_stack([geom.vertices, np.full(n_vertices, geom.z_min)])
            top_vertices = np.column_stack([geom.vertices, np.full(n_vertices, geom.z_max)])

            faces = []
            faces.append(bottom_vertices)
            faces.append(top_vertices)

            for i in range(n_vertices):
                next_i = (i + 1) % n_vertices
                face = np.array([
                    bottom_vertices[i],
                    bottom_vertices[next_i],
                    top_vertices[next_i],
                    top_vertices[i]
                ])
                faces.append(face)

            poly_collection = Poly3DCollection(faces, alpha=0.7, facecolor=color,
                                               edgecolor='black', linewidth=0.5, label=geom.name)
            ax_3d.add_collection3d(poly_collection)

            # Collect bounds
            x_min, x_max, y_min, y_max = geom.get_xy_bounds()
            all_x.extend([x_min, x_max])
            all_y.extend([y_min, y_max])
            all_z.extend([geom.z_min, geom.z_max])

        # Set limits with EQUAL SCALING to preserve true aspect ratios
        x_range = max(all_x) - min(all_x)
        y_range = max(all_y) - min(all_y)
        z_range = max(all_z) - min(all_z)

        # Find maximum range to use for all axes
        max_range = max(x_range, y_range, z_range)

        # Calculate centers
        x_center = (min(all_x) + max(all_x)) / 2
        y_center = (min(all_y) + max(all_y)) / 2
        z_center = (min(all_z) + max(all_z)) / 2

        # Add padding (10% of max range)
        padding = max_range * 0.1
        half_range = (max_range + 2 * padding) / 2

        # Set equal limits for all axes
        ax_3d.set_xlim(x_center - half_range, x_center + half_range)
        ax_3d.set_ylim(y_center - half_range, y_center + half_range)
        ax_3d.set_zlim(z_center - half_range, z_center + half_range)

        # Set equal aspect ratio for 3D box
        ax_3d.set_box_aspect([1, 1, 1])

        ax_3d.set_xlabel('X (μm)', fontsize=12)
        ax_3d.set_ylabel('Y (μm)', fontsize=12)
        ax_3d.set_zlabel('Z (μm)', fontsize=12)
        ax_3d.set_title('All Geometries - 3D View', fontsize=14, fontweight='bold')
        ax_3d.view_init(elev=25, azim=45)

        plt.tight_layout()

        # Save combined figure
        if save:
            timestamp_sec = get_timestamp_second()
            filename = f"{timestamp_sec}_combined.png"
            filepath = os.path.join(output_dir, filename)
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            saved_files.append(filepath)
            print(f"  Saved: {filepath}")

    else:
        # Create separate plots for each geometry
        for geom in geometries:
            # XY outline
            fig_xy, ax_xy = plt.subplots(figsize=(10, 8))
            plot_xy_outline(geom, ax=ax_xy, show_vertices=True)
            plt.tight_layout()

            if save:
                timestamp_sec = get_timestamp_second()
                filename = f"{timestamp_sec}_{geom.name}_xy.png"
                filepath = os.path.join(output_dir, filename)
                fig_xy.savefig(filepath, dpi=300, bbox_inches='tight')
                saved_files.append(filepath)
                print(f"  Saved: {filepath}")

            # 3D view
            fig_3d = plt.figure(figsize=(12, 10))
            ax_3d = fig_3d.add_subplot(111, projection='3d')
            plot_3d_extrusion(geom, ax=ax_3d)
            plt.tight_layout()

            if save:
                timestamp_sec = get_timestamp_second()
                filename = f"{timestamp_sec}_{geom.name}_3d.png"
                filepath = os.path.join(output_dir, filename)
                fig_3d.savefig(filepath, dpi=300, bbox_inches='tight')
                saved_files.append(filepath)
                print(f"  Saved: {filepath}")

    return saved_files


if __name__ == "__main__":
    print("=" * 70)
    print("MEMS Photonic Switch - Geometry Visualization")
    print("=" * 70)

    # Load example geometries
    print("\nLoading example geometries...")
    geometries = get_example_geometries()
    print(f"Loaded {len(geometries)} geometries:")
    for geom in geometries:
        print(f"  - {geom.name} ({geom.geometry_type})")

    # Create output directory
    output_dir = ensure_output_directory("figures")
    print(f"\nOutput directory: {output_dir}")

    # Visualize all geometries in combined view and save
    print("\nGenerating and saving combined visualization...")
    saved_files = visualize_all_geometries(geometries, combined_views=True,
                                           output_dir=output_dir, save=True)

    print(f"\nVisualization complete!")
    print(f"Saved {len(saved_files)} figure(s) to: {output_dir}")

    # Optionally display the plots (comment out if running headless)
    # plt.show()
