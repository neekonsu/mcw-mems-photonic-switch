"""Focusing grating coupler component.

Curved/focusing grating coupler on SOI with partial-etch teeth.  Each
grating line is an elliptical arc that satisfies the Bragg condition at
every point while focusing diffracted light directly into a 440 nm strip
waveguide — no separate taper is needed.

Design approach
---------------
A conventional grating coupler uses straight, parallel teeth and requires a
long (10–15 µm) linear taper to funnel the ~10 µm mode-field diameter of a
single-mode fiber down to a ~440 nm waveguide.  A *focusing* (curved) grating
eliminates the taper by shaping each tooth so that it simultaneously
(a) satisfies the Bragg diffraction condition and (b) acts as a curved lens
that focuses the diffracted light to a common focal point at the waveguide
facet.

Phase condition
---------------
For a point at polar coordinates (r, α) relative to the focal point (α = 0
along the waveguide axis), the optical path difference between the diffracted
ray and a reference plane wave arriving at fiber tilt angle θ is:

    Δφ = (2π / λ) · [ n_eff · r  −  n_clad · sin(θ) · r · cos(α) ]

Constructive interference for the m-th grating arc requires Δφ = 2πm:

    n_eff · r  −  n_clad · sin(θ) · r · cos(α)  =  m · λ

Solving for r:

    r_m(α) = m · λ / ( n_eff − n_clad · sin(θ) · cos(α) )

This is the equation of an ellipse in polar form.  At α = 0 (on-axis) the
local period equals λ / (n_eff − n_clad · sin θ) ≈ 0.63 µm, matching
standard straight-grating designs.  Off-axis the period increases smoothly,
which is what provides the focusing.

Each etched tooth spans a fraction *duty_cycle* of a period, i.e. from
grating order m to m + duty_cycle.  The unetched silicon between teeth spans
the remaining fraction.

Default parameters
------------------
- λ  = 1.55 µm          (C-band telecom)
- n_eff = 2.63           (partially etched 220 nm SOI slab TE₀ mode)
- n_clad = 1.0           (air cladding; use 1.44 for oxide-clad)
- θ  = 10°               (near-vertical fiber tilt from surface normal)
- duty_cycle = 0.5       (equal etch / unetched widths)
- focal_distance = 25 µm (distance from waveguide facet to first tooth)
- half_angle = 22°       (grating fan opens ±22°, capturing ~10 µm fiber MFD)
- 20 periods             (sufficient for >90 % power extraction)

Layer usage
-----------
- SI_FULL  (1, 0):  Full-thickness 220 nm SOI — used for the slab base
  under the entire grating sector and for the output strip waveguide.
- SI_PARTIAL (2, 0): 150 nm slab after 70 nm shallow etch — used for the
  curved grating teeth.  The partial etch creates the periodic refractive-
  index modulation that diffracts light upward toward the fiber.

Geometry (from left to right in the layout)
-------------------------------------------
    ◄── wg_length ──►◄── focal_distance ──►◄── n_periods × Λ(α) ──►
    ┌────────────────┐
    │  440 nm strip  │ ← SI_FULL waveguide
    │   waveguide    │
    └────────────────┘
                     ╲                               ╱
                      ╲   SI_FULL slab sector        ╱
                       ╲  with SI_PARTIAL curved    ╱
                        ╲ teeth (elliptical arcs)  ╱
                         ╲                        ╱
                          ╲──────────────────────╱
                           focal point (origin)

References
----------
- F. Van Laere et al., "Compact Focusing Grating Couplers for Silicon-on-
  Insulator Integrated Circuits," IEEE Photon. Technol. Lett., 2007.
- D. Taillaert et al., "Grating Couplers for Coupling between Optical Fibers
  and Nanophotonic Waveguides," Jpn. J. Appl. Phys., 2006.
"""

import numpy as np
import gdsfactory as gf

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


def _grating_radius(m, wavelength, n_eff, nc_sin_theta, alpha):
    """Radius of the m-th grating contour at angle *alpha* (radians).

    Implements  r_m(α) = m · λ / (n_eff − n_clad · sin θ · cos α).
    *m* can be non-integer to locate points within a period (e.g.
    m + duty_cycle for the outer edge of a tooth).
    """
    return m * wavelength / (n_eff - nc_sin_theta * np.cos(alpha))


def make_grating_coupler(
    n_periods: int = 20,
    wavelength: float = 1.55,
    n_eff: float = 2.63,
    n_clad: float = 1.0,
    fiber_angle: float = 10.0,
    duty_cycle: float = 0.5,
    focal_distance: float = 25.0,
    half_angle: float = 22.0,
    wg_width: float = 0.44,
    wg_length: float = 5.0,
    n_arc_points: int = 128,
    full_etch_layer=LAYER.SI_FULL,
    partial_etch_layer=LAYER.SI_PARTIAL,
) -> gf.Component:
    """Focusing grating coupler with curved partial-etch teeth.

    The focal point is at the junction between the waveguide and the
    grating.  Elliptical arcs fan out from the focal point; no linear
    taper is required because the curvature provides mode matching.

    Args:
        n_periods:          Number of grating periods.
        wavelength:         Free-space wavelength (um).
        n_eff:              Effective index of the partially etched slab.
        n_clad:             Cladding refractive index.
        fiber_angle:        Fiber tilt from surface normal (degrees).
        duty_cycle:         Fraction of each period that is etched.
        focal_distance:     Distance from focal point to first tooth (um).
        half_angle:         Half-opening angle of the grating fan (degrees).
        wg_width:           Output waveguide width (um).
        wg_length:          Length of the output waveguide (um).
        n_arc_points:       Number of points per arc for polygon discretization.
        full_etch_layer:    SOI full-thickness layer.
        partial_etch_layer: SOI partial-etch (slab) layer.
    """
    c = gf.Component()

    theta_rad = np.radians(fiber_angle)
    nc_sin_theta = n_clad * np.sin(theta_rad)
    half_angle_rad = np.radians(half_angle)

    # Compute the starting grating order m_start so that the first tooth
    # sits at approximately *focal_distance* from the focal point.  At
    # α = 0 (on-axis), r_m(0) = m · λ / (n_eff − n_clad · sin θ), so
    # m_start = ceil( focal_distance · (n_eff − n_clad · sin θ) / λ ).
    m_start = int(np.ceil(
        focal_distance * (n_eff - nc_sin_theta) / wavelength
    ))

    # Sample the angular span at n_arc_points to discretize arcs into
    # polygon vertices.  More points → smoother curves but larger GDS.
    alphas = np.linspace(-half_angle_rad, half_angle_rad, n_arc_points)

    # -----------------------------------------------------------------
    # SI_FULL slab — a pie-shaped sector from the focal point out to the
    # outermost grating arc.  This is the full-thickness 220 nm SOI that
    # forms the base beneath all teeth and the unetched gaps.
    # -----------------------------------------------------------------
    m_last = m_start + n_periods
    outer_radii = _grating_radius(m_last, wavelength, n_eff, nc_sin_theta, alphas)

    slab_points = [(0.0, 0.0)]  # start at focal point
    for a, r in zip(alphas, outer_radii):
        slab_points.append((r * np.cos(a), r * np.sin(a)))
    slab_points.append((0.0, 0.0))  # close back to focal point
    c.add_polygon(slab_points, layer=full_etch_layer)

    # -----------------------------------------------------------------
    # Output waveguide — a 440 nm strip (SI_FULL) extending in the −x
    # direction from the focal point.  Light focused by the curved teeth
    # couples directly into this waveguide.
    # -----------------------------------------------------------------
    c.add_polygon(
        [(-wg_length, -wg_width / 2), (0, -wg_width / 2),
         (0, wg_width / 2), (-wg_length, wg_width / 2)],
        layer=full_etch_layer,
    )

    # -----------------------------------------------------------------
    # Curved grating teeth (SI_PARTIAL) — each tooth is a ring-sector
    # polygon bounded by two elliptical arcs:
    #   inner arc at order  m_start + i             (start of etched region)
    #   outer arc at order  m_start + i + duty_cycle (end of etched region)
    # The polygon is built by sweeping the inner arc from −half_angle to
    # +half_angle, then sweeping the outer arc back from +half_angle to
    # −half_angle to form a closed contour.
    # -----------------------------------------------------------------
    for i in range(n_periods):
        m_inner = m_start + i
        m_outer = m_start + i + duty_cycle

        inner_r = _grating_radius(m_inner, wavelength, n_eff, nc_sin_theta, alphas)
        outer_r = _grating_radius(m_outer, wavelength, n_eff, nc_sin_theta, alphas)

        tooth_pts = []
        # Inner arc (forward sweep, −half_angle → +half_angle)
        for a, r in zip(alphas, inner_r):
            tooth_pts.append((r * np.cos(a), r * np.sin(a)))
        # Outer arc (reverse sweep, +half_angle → −half_angle, closes polygon)
        for a, r in zip(alphas[::-1], outer_r[::-1]):
            tooth_pts.append((r * np.cos(a), r * np.sin(a)))

        c.add_polygon(tooth_pts, layer=partial_etch_layer)

    return c


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()
    c = make_grating_coupler()
    c.show()
