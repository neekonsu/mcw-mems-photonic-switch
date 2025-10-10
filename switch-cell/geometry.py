# -*- coding: utf-8 -*-
"""
Geometry definitions for MEMS photonic switches.

This module defines 3D geometries as 2D polygons extruded in the Z direction,
matching the lithographic fabrication process for silicon photonics.

All dimensions are stored in microns (um) for consistency with simulation tools.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ExtrudedPolygon:
    """
    Represents a 3D structure as a 2D polygon extruded in the Z direction.

    This matches the lithographic fabrication process where features are defined
    in the XY plane and etched to specific depths.

    Attributes:
        vertices: Nx2 numpy array of (x, y) coordinates in microns
        z_min: Minimum Z coordinate in microns
        z_max: Maximum Z coordinate in microns
        name: Identifier for this geometry element
        material: Material type (e.g., 'Si', 'SiO2', 'Air')
        geometry_type: Type of structure (e.g., 'waveguide', 'comb', 'spring')
    """
    vertices: np.ndarray  # Shape: (N, 2) - XY coordinates in microns
    z_min: float  # microns
    z_max: float  # microns
    name: str = "unnamed"
    material: str = "Si"
    geometry_type: str = "generic"

    def __post_init__(self):
        """Validate and convert vertices to numpy array."""
        self.vertices = np.asarray(self.vertices, dtype=np.float64)
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 2:
            raise ValueError(f"vertices must be Nx2 array, got shape {self.vertices.shape}")

    @property
    def thickness(self) -> float:
        """Return the thickness (z_max - z_min) in microns."""
        return self.z_max - self.z_min

    @property
    def z_center(self) -> float:
        """Return the center Z coordinate in microns."""
        return (self.z_min + self.z_max) / 2

    def get_xy_bounds(self):
        """
        Get the bounding box in the XY plane.

        Returns:
            tuple: (x_min, x_max, y_min, y_max) in microns
        """
        x_min, y_min = self.vertices.min(axis=0)
        x_max, y_max = self.vertices.max(axis=0)
        return x_min, x_max, y_min, y_max

    def translate(self, dx: float, dy: float, dz: float = 0):
        """
        Translate the geometry by (dx, dy, dz) in microns.

        Args:
            dx: Translation in X direction (microns)
            dy: Translation in Y direction (microns)
            dz: Translation in Z direction (microns)
        """
        self.vertices = self.vertices + np.array([dx, dy])
        self.z_min += dz
        self.z_max += dz


@dataclass
class Waveguide(ExtrudedPolygon):
    """
    Waveguide structure represented as an extruded polygon.

    Inherits from ExtrudedPolygon with geometry_type set to 'waveguide'.
    """
    geometry_type: str = field(default='waveguide', init=False)


@dataclass
class Switch(ExtrudedPolygon):
    """
    Switch structure represented as an extruded polygon.

    Inherits from ExtrudedPolygon with geometry_type set to 'switch'.
    """
    geometry_type: str = field(default='switch', init=False)


def create_rectangle(x_center: float, y_center: float, width: float, height: float,
                     z_min: float, z_max: float, **kwargs) -> ExtrudedPolygon:
    """
    Create a rectangular ExtrudedPolygon centered at (x_center, y_center).

    Args:
        x_center: X coordinate of rectangle center (microns)
        y_center: Y coordinate of rectangle center (microns)
        width: Width in X direction (microns)
        height: Height in Y direction (microns)
        z_min: Minimum Z coordinate (microns)
        z_max: Maximum Z coordinate (microns)
        **kwargs: Additional arguments passed to ExtrudedPolygon

    Returns:
        ExtrudedPolygon with rectangular cross-section
    """
    half_w = width / 2
    half_h = height / 2
    vertices = np.array([
        [x_center - half_w, y_center - half_h],  # Bottom-left
        [x_center + half_w, y_center - half_h],  # Bottom-right
        [x_center + half_w, y_center + half_h],  # Top-right
        [x_center - half_w, y_center + half_h],  # Top-left
    ])
    return ExtrudedPolygon(vertices=vertices, z_min=z_min, z_max=z_max, **kwargs)


def create_waveguide_rectangle(x_center: float, y_center: float, width: float, height: float,
                                z_min: float, z_max: float, **kwargs) -> Waveguide:
    """
    Create a rectangular Waveguide centered at (x_center, y_center).

    Args:
        x_center: X coordinate of waveguide center (microns)
        y_center: Y coordinate of waveguide center (microns)
        width: Width in X direction (microns)
        height: Height in Y direction (microns)
        z_min: Minimum Z coordinate (microns)
        z_max: Maximum Z coordinate (microns)
        **kwargs: Additional arguments passed to Waveguide

    Returns:
        Waveguide with rectangular cross-section
    """
    half_w = width / 2
    half_h = height / 2
    vertices = np.array([
        [x_center - half_w, y_center - half_h],
        [x_center + half_w, y_center - half_h],
        [x_center + half_w, y_center + half_h],
        [x_center - half_w, y_center + half_h],
    ])
    return Waveguide(vertices=vertices, z_min=z_min, z_max=z_max, **kwargs)


# Example geometries for testing
def get_example_geometries() -> List[ExtrudedPolygon]:
    """
    Create example geometries for testing visualization.

    Returns:
        List of ExtrudedPolygon objects representing a simple photonic switch
    """
    geometries = []

    # Silicon device layer (220nm thick, standard SOI)
    si_z_min = 0.0
    si_z_max = 0.22

    # Create two parallel waveguides (450nm wide, 20um long)
    wg_width = 0.45  # microns
    wg_length = 20.0  # microns
    gap = 0.55  # microns (OFF state)

    # Waveguide 1 (top)
    wg1_y = gap / 2 + wg_width / 2
    wg1 = create_waveguide_rectangle(
        x_center=0, y_center=wg1_y,
        width=wg_length, height=wg_width,
        z_min=si_z_min, z_max=si_z_max,
        name="waveguide_1", material="Si"
    )
    geometries.append(wg1)

    # Waveguide 2 (bottom)
    wg2_y = -(gap / 2 + wg_width / 2)
    wg2 = create_waveguide_rectangle(
        x_center=0, y_center=wg2_y,
        width=wg_length, height=wg_width,
        z_min=si_z_min, z_max=si_z_max,
        name="waveguide_2", material="Si"
    )
    geometries.append(wg2)

    # Create a simple switch element (placeholder for MEMS actuator)
    # This is a simplified representation - actual MEMS structure will be more complex
    switch = Switch(
        vertices=np.array([
            [-5, -2], [5, -2], [5, 2], [-5, 2]
        ]),
        z_min=si_z_min, z_max=si_z_max,
        name="switch_element", material="Si"
    )
    geometries.append(switch)

    return geometries


if __name__ == "__main__":
    # Test the geometry creation
    print("Creating example geometries...")
    geometries = get_example_geometries()

    print(f"\nCreated {len(geometries)} geometry objects:")
    for geom in geometries:
        print(f"\n{geom.name}:")
        print(f"  Type: {geom.geometry_type}")
        print(f"  Material: {geom.material}")
        print(f"  Vertices: {geom.vertices.shape[0]} points")
        print(f"  Z range: {geom.z_min:.3f} to {geom.z_max:.3f} um")
        print(f"  Thickness: {geom.thickness:.3f} um")
        x_min, x_max, y_min, y_max = geom.get_xy_bounds()
        print(f"  XY bounds: X=[{x_min:.3f}, {x_max:.3f}], Y=[{y_min:.3f}, {y_max:.3f}] um")
