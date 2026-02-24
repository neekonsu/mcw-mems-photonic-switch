"""Shared utilities for bistable beam verification.

Wraps geometry functions from ccs_bistable_beam.py and provides material
properties in consistent µm / µN / MPa units.
"""

import sys
import os
import numpy as np

# Import geometry functions from the existing CCS beam module
_beam_dir = os.path.join(os.path.dirname(__file__), "../components/bistable_spring")
sys.path.insert(0, _beam_dir)
from ccs_bistable_beam import (
    _compute_ccs_centerline,
    _compute_width_profile,
)

# ---------------------------------------------------------------------------
# Material properties — poly-Si in µm / µN / MPa unit system
# ---------------------------------------------------------------------------
POLY_SI = {
    "E": 160e3,       # Young's modulus [MPa]  (160 GPa)
    "nu": 0.22,       # Poisson's ratio
    "rho": 2330e-18,  # Density [µg/µm³]  (2330 kg/m³)
    "t": 0.5,         # Structural thickness [µm]
}

# ---------------------------------------------------------------------------
# Default beam parameters (make_ccs_beam defaults)
# ---------------------------------------------------------------------------
DEFAULT_BEAM_PARAMS = dict(
    span=40.0,
    flex_ratio=0.3,
    flex_width=0.5,
    rigid_width=0.9375,
    initial_offset=1.2,
    taper_length=2.0,
)


def get_beam_centerline(span=40.0, flex_ratio=0.3, initial_offset=1.2,
                        n_points=400):
    """Return (x, y) centerline arrays for a full CCS beam."""
    return _compute_ccs_centerline(span, flex_ratio, initial_offset, n_points)


def get_beam_width_profile(x, span=40.0, flex_ratio=0.3, flex_width=0.5,
                           rigid_width=0.9375, taper_length=2.0):
    """Return width array at each x position."""
    return _compute_width_profile(x, span, flex_ratio, flex_width,
                                  rigid_width, taper_length)


def get_beam_polygon(span=40.0, flex_ratio=0.3, flex_width=0.5,
                     rigid_width=0.9375, initial_offset=1.2,
                     taper_length=2.0, n_points=400):
    """Return Nx2 closed polygon of CCS beam outline (upper + lower edges).

    The polygon is closed (first point == last point) and suitable for
    meshing with triangle or gmsh.
    """
    x_c, y_c = _compute_ccs_centerline(span, flex_ratio, initial_offset,
                                        n_points)
    w = _compute_width_profile(x_c, span, flex_ratio, flex_width,
                               rigid_width, taper_length)

    upper = np.column_stack([x_c, y_c + w / 2.0])
    lower = np.column_stack([x_c[::-1], (y_c - w / 2.0)[::-1]])
    polygon = np.vstack([upper, lower])

    # Close the polygon
    if not np.allclose(polygon[0], polygon[-1]):
        polygon = np.vstack([polygon, polygon[0]])

    return polygon


def get_moment_of_inertia_profile(x, span=40.0, flex_ratio=0.3,
                                   flex_width=0.5, rigid_width=0.9375,
                                   taper_length=2.0, thickness=0.5):
    """Return I(x) = w(x) * t^3 / 12 for the CCS beam (variable width).

    For the analytical model with out-of-plane bending, I(x) depends on
    the local beam width w(x) and the constant thickness t.
    """
    w = _compute_width_profile(x, span, flex_ratio, flex_width,
                               rigid_width, taper_length)
    return w * thickness**3 / 12.0
