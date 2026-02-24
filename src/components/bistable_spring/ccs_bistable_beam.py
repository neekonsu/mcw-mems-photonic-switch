"""Centrally-Clamped Stepped (CCS) Bistable Mechanical Beam.

Implements the CCS bistable beam geometry described in:

    Ma et al., "Nonvolatile Silicon Photonic MEMS Switch Based on
    Centrally-Clamped Stepped Bistable Mechanical Beams"
    (Zhejiang University, 2024)

The CCS beam achieves stronger bistability than conventional cosine-shaped
beams by incorporating rigid widened straight sections into flexible
cosine-shaped sections.  This produces a more symmetric switching-force
profile (switching-ON / switching-OFF force ratio = 0.87, vs 0.76 for a
pure cosine beam of the same span and offset).

Beam layout (as-fabricated, viewed from above):

    Anchor ── Flex (cosine) ── Taper ── Rigid (straight) ── Rod ── ...
    (fixed)   flex_width wide          rigid_width wide     (shuttle)
              3/10 of span             7/10 of span

The beam is symmetric about its center:
    Anchor ─ Flex ─ Rigid ─ Rod ─ Rigid ─ Flex ─ Anchor

Default parameters are scaled for the 500 nm POLY_MEMS structural layer
(Tower 0.18 um SiPho process).  For the original 220 nm SOI values from
the paper, pass flex_width=0.1, rigid_width=0.4, initial_offset=0.2,
taper_length=1.0, layer=LAYER.SI_FULL.

Bistability condition:  Q = initial_offset / thickness > 2.31
    Default: Q = 1.2 / 0.5 = 2.4  (satisfies bistability)
"""

import numpy as np
import gdsfactory as gf

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_ccs_centerline(span, flex_ratio, initial_offset, n_points=400):
    """Compute the CCS beam centerline y(x).

    Profile consists of four sections (left-to-right):
      1. Left flexible  – cosine rise from y=0 to y=A
      2. Left rigid     – straight line from y=A to y=h  (beam center)
      3. Right rigid    – straight line from y=h  to y=A (symmetric)
      4. Right flexible – cosine descent from y=A to y=0

    C1 continuity (matching position AND slope) is enforced at every
    section boundary.

    The cosine sections use:
        y(x) = A * [1 - cos(pi * x / (2 * L_flex))]
    where A is chosen so that dy/dx at x=L_flex matches the rigid slope.

    Derivation of amplitude A from the C1 condition:
        At x = L_flex:
            y       = A
            dy/dx   = A * pi / (2 * L_flex)
        Rigid slope = (h - A) / L_rigid
        Setting equal and solving:
            A = h / (1 + pi * L_rigid / (2 * L_flex))

    Args:
        span:           Total beam span, anchor-to-anchor (um).
        flex_ratio:     Fraction of total span occupied by flexible sections.
        initial_offset: Maximum y-offset at beam center, h (um).
        n_points:       Total number of sample points.

    Returns:
        (x, y) as numpy arrays.
    """
    half = span / 2.0
    L_flex = flex_ratio * half          # flexible section length per side
    L_rigid = half - L_flex             # rigid section length per side

    # Cosine amplitude from C1 continuity
    A = initial_offset / (1.0 + np.pi * L_rigid / (2.0 * L_flex))
    slope = A * np.pi / (2.0 * L_flex)

    n_sec = max(n_points // 4, 30)

    # --- Section 1: left flexible (cosine rise from 0 to A) ---
    x1 = np.linspace(0, L_flex, n_sec, endpoint=False)
    y1 = A * (1.0 - np.cos(np.pi * x1 / (2.0 * L_flex)))

    # --- Section 2: left rigid (straight from A to h) ---
    x2 = np.linspace(L_flex, half, n_sec, endpoint=False)
    y2 = A + slope * (x2 - L_flex)

    # --- Section 3: right rigid (straight from h down to A) ---
    x3 = np.linspace(half, span - L_flex, n_sec, endpoint=False)
    y3 = initial_offset - slope * (x3 - half)

    # --- Section 4: right flexible (cosine descent from A to 0) ---
    x4 = np.linspace(span - L_flex, span, n_sec, endpoint=True)
    y4 = A * (1.0 - np.cos(np.pi * (span - x4) / (2.0 * L_flex)))

    return np.concatenate([x1, x2, x3, x4]), np.concatenate([y1, y2, y3, y4])


def _compute_ccs_half_centerline(half_span, flex_ratio, initial_offset, n_points=200):
    """Compute a CCS half-beam centerline y(x) from anchor to shuttle end.

    Profile consists of two sections (left-to-right):
      1. Flexible  – cosine rise from y=0 to y=A
      2. Rigid     – straight line from y=A to y=initial_offset

    The beam starts at x=0 (anchor end, y=0) and ends at x=half_span
    (shuttle end, y=initial_offset).

    Args:
        half_span:      Half-beam span, anchor to shuttle edge (um).
        flex_ratio:     Fraction of half_span for the flexible section.
        initial_offset: y-offset at shuttle end (um).
        n_points:       Total number of sample points.

    Returns:
        (x, y) as numpy arrays.
    """
    L_flex = flex_ratio * half_span
    L_rigid = half_span - L_flex

    # Cosine amplitude from C1 continuity (same derivation as full beam)
    A = initial_offset / (1.0 + np.pi * L_rigid / (2.0 * L_flex))
    slope = A * np.pi / (2.0 * L_flex)

    n_sec = max(n_points // 2, 30)

    # --- Section 1: flexible (cosine rise from 0 to A) ---
    x1 = np.linspace(0, L_flex, n_sec, endpoint=False)
    y1 = A * (1.0 - np.cos(np.pi * x1 / (2.0 * L_flex)))

    # --- Section 2: rigid (straight from A to initial_offset) ---
    x2 = np.linspace(L_flex, half_span, n_sec, endpoint=True)
    y2 = A + slope * (x2 - L_flex)

    return np.concatenate([x1, x2]), np.concatenate([y1, y2])


def _compute_half_width_profile(x, half_span, flex_ratio, flex_width,
                                rigid_width, taper_length):
    """Compute beam width for a half-beam with one taper transition.

    The beam is thin (flex_width) in the flexible section and wide
    (rigid_width) in the rigid section, with a single cosine taper
    at the junction.

    Args:
        x:            Array of x-coordinates.
        half_span:    Half-beam span (um).
        flex_ratio:   Fraction of half_span for flex section.
        flex_width:   Width in flexible section (um).
        rigid_width:  Width in rigid section (um).
        taper_length: Taper transition length (um).

    Returns:
        Array of widths, same shape as x.
    """
    L_flex = flex_ratio * half_span
    w = np.full_like(x, rigid_width)

    # Taper zone boundaries (centered on flex-rigid junction)
    t_start = L_flex - taper_length / 2.0
    t_end = L_flex + taper_length / 2.0

    # Flexible region
    mask = x <= t_start
    w[mask] = flex_width

    # Taper (flex -> rigid)
    mask = (x > t_start) & (x < t_end)
    if np.any(mask):
        t = (x[mask] - t_start) / taper_length
        w[mask] = flex_width + (rigid_width - flex_width) * 0.5 * (
            1.0 - np.cos(np.pi * t)
        )

    return w


def _compute_width_profile(x, span, flex_ratio, flex_width, rigid_width,
                           taper_length):
    """Compute beam width at each x with cosine-interpolated tapers.

    The beam is thin (flex_width) in the flexible sections and wide
    (rigid_width) in the rigid sections.  Cosine interpolation ensures
    smooth C1-continuous width transitions at the boundaries, matching
    the paper's "taper transitions" that avoid strain concentration.

    Args:
        x:            Array of x-coordinates.
        span:         Total beam span (um).
        flex_ratio:   Fraction of span for flexible sections.
        flex_width:   Width in flexible sections (um).
        rigid_width:  Width in rigid sections (um).
        taper_length: Taper transition length (um).

    Returns:
        Array of widths, same shape as x.
    """
    L_flex = flex_ratio * span / 2.0
    w = np.full_like(x, rigid_width)

    # Taper zone boundaries (centered on flex-rigid junction)
    lt_start = L_flex - taper_length / 2.0
    lt_end = L_flex + taper_length / 2.0
    rt_start = span - L_flex - taper_length / 2.0
    rt_end = span - L_flex + taper_length / 2.0

    # Left flexible region
    mask = x <= lt_start
    w[mask] = flex_width

    # Left taper (flex -> rigid)
    mask = (x > lt_start) & (x < lt_end)
    if np.any(mask):
        t = (x[mask] - lt_start) / taper_length
        w[mask] = flex_width + (rigid_width - flex_width) * 0.5 * (
            1.0 - np.cos(np.pi * t)
        )

    # Right taper (rigid -> flex)
    mask = (x > rt_start) & (x < rt_end)
    if np.any(mask):
        t = (x[mask] - rt_start) / taper_length
        w[mask] = rigid_width + (flex_width - rigid_width) * 0.5 * (
            1.0 - np.cos(np.pi * t)
        )

    # Right flexible region
    mask = x >= rt_end
    w[mask] = flex_width

    return w


# ---------------------------------------------------------------------------
# Public component functions
# ---------------------------------------------------------------------------

@gf.cell
def make_ccs_half_beam(
    half_span: float = 20.0,
    flex_ratio: float = 0.3,
    flex_width: float = 0.8,
    rigid_width: float = 1.5,
    initial_offset: float = 1.2,
    taper_length: float = 2.0,
    thickness: float = 0.5,
    n_points: int = 200,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Single CCS half-beam (anchor end to shuttle end).

    The half-beam spans from (0, 0) at the anchor to (half_span, initial_offset)
    at the shuttle connection.  It contains one flex section (cosine) and one
    rigid section (straight), with a cosine-interpolated taper between them.

    This is the building block for the split-center bistable spring pair,
    where four half-beams connect two outer anchors to a central shuttle gap.

    Bistability condition:  Q = initial_offset / thickness > 2.31
        Default: Q = 1.2 / 0.5 = 2.4  (satisfies bistability)

    Args:
        half_span:      Beam span, anchor to shuttle edge (um).  Default 20.
        flex_ratio:     Fraction of half_span for flexible section.  Default 0.3.
        flex_width:     Width of flexible cosine section (um).  Default 0.8.
        rigid_width:    Width of rigid straight section (um).  Default 1.5.
        initial_offset: y-offset at shuttle end (um).  Default 1.2.
        taper_length:   Flex-to-rigid width taper length (um).  Default 2.0.
        thickness:      Structural layer thickness (um).  Default 0.5 (POLY_MEMS).
                        Used for documentation; adjust initial_offset to maintain
                        Q = initial_offset / thickness > 2.31 for bistability.
        n_points:       Polygon discretization resolution.  Default 200.
        layer:          GDS layer tuple.  Default POLY_MEMS (7,0).
    """
    c = gf.Component()

    x_c, y_c = _compute_ccs_half_centerline(
        half_span, flex_ratio, initial_offset, n_points
    )
    w = _compute_half_width_profile(
        x_c, half_span, flex_ratio, flex_width, rigid_width, taper_length
    )

    # Build closed polygon: upper edge (left-to-right), lower edge (reversed)
    upper = np.column_stack([x_c, y_c + w / 2.0])
    lower = np.column_stack([x_c[::-1], (y_c - w / 2.0)[::-1]])
    points = np.vstack([upper, lower])

    c.add_polygon(points, layer=layer)
    return c


@gf.cell
def make_ccs_beam(
    span: float = 40.0,
    flex_ratio: float = 0.3,
    flex_width: float = 0.8,
    rigid_width: float = 1.5,
    initial_offset: float = 1.2,
    taper_length: float = 2.0,
    thickness: float = 0.5,
    n_points: int = 400,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Single CCS bistable beam (as-fabricated mask shape).

    The beam spans from (0, 0) at the left anchor to (span, 0) at the
    right anchor.  The centerline bulges in the +y direction, reaching
    maximum offset at x = span/2.

    Beam structure (left to right):
        Anchor -> cosine flex (flex_width wide)
               -> taper
               -> straight rigid (rigid_width wide)
               -> [center: max offset = initial_offset]
               -> straight rigid -> taper -> cosine flex -> Anchor

    Bistability condition:  Q = initial_offset / thickness > 2.31
        Default: Q = 1.2 / 0.5 = 2.4  (satisfies bistability)

    Args:
        span:           Beam span, anchor to anchor (um).  Default 40.
        flex_ratio:     Fraction of span for flexible sections.  Default 0.3.
        flex_width:     Width of flexible cosine beams (um).  Default 0.8.
        rigid_width:    Width of rigid straight beams (um).  Default 1.5.
        initial_offset: Max y-offset at beam center (um).  Default 1.2.
        taper_length:   Flex-to-rigid width taper length (um).  Default 2.0.
        thickness:      Structural layer thickness (um).  Default 0.5 (POLY_MEMS).
                        Used for documentation; adjust initial_offset to maintain
                        Q = initial_offset / thickness > 2.31 for bistability.
        n_points:       Polygon discretization resolution.  Default 400.
        layer:          GDS layer tuple.  Default POLY_MEMS (7,0).
    """
    c = gf.Component()

    # Compute centerline and width profiles
    x_c, y_c = _compute_ccs_centerline(
        span, flex_ratio, initial_offset, n_points
    )
    w = _compute_width_profile(
        x_c, span, flex_ratio, flex_width, rigid_width, taper_length
    )

    # Build closed polygon: upper edge (left-to-right), lower edge (reversed)
    upper = np.column_stack([x_c, y_c + w / 2.0])
    lower = np.column_stack([x_c[::-1], (y_c - w / 2.0)[::-1]])
    points = np.vstack([upper, lower])

    c.add_polygon(points, layer=layer)
    return c


@gf.cell
def make_ccs_beam_set(
    span: float = 40.0,
    flex_ratio: float = 0.3,
    flex_width: float = 0.8,
    rigid_width: float = 1.5,
    initial_offset: float = 1.2,
    taper_length: float = 2.0,
    thickness: float = 0.5,
    beam_spacing: float = 6.0,
    rod_width: float = 1.5,
    anchor_width: float = 6.0,
    anchor_length: float = 6.0,
    n_points: int = 400,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Parallel pair of CCS bistable beams with anchors and central rod.

    Two CCS beams are arranged symmetrically about y=0, both curving in
    the +y direction (same buckling mode).  Their centers are connected
    by a rigid vertical rod that attaches to the shuttle beam.  Anchor
    pads are placed at both ends of each beam.

    This is one complete "set" of CCS beams as described in the paper.
    The full switch uses two sets (one on each side of the shuttle),
    driven by a bidirectional electrostatic comb actuator.

    Coordinate system:
      x: along beam span; x=0 at left anchors, x=span at right anchors
      y: perpendicular to beams; y=0 midway between the beam pair
      Beams curve in +y; first stable state displaces shuttle in +y

    Bistability condition:  Q = initial_offset / thickness > 2.31
        Default: Q = 1.2 / 0.5 = 2.4  (satisfies bistability)

    Args:
        span:           Beam span, anchor to anchor (um).  Default 40.
        flex_ratio:     Fraction of span for flexible sections.  Default 0.3.
        flex_width:     Flexible beam width (um).  Default 0.8.
        rigid_width:    Rigid beam width (um).  Default 1.5.
        initial_offset: Max y-offset at beam center (um).  Default 1.2.
        taper_length:   Width taper length (um).  Default 2.0.
        thickness:      Structural layer thickness (um).  Default 0.5 (POLY_MEMS).
        beam_spacing:   Center-to-center distance between beams (um).  Default 6.
        rod_width:      Width of the connecting rod (um).  Default 1.5.
        anchor_width:   Anchor pad width (um).  Default 6.
        anchor_length:  Anchor pad length (um).  Default 6.
        n_points:       Polygon resolution.  Default 400.
        layer:          GDS layer tuple.  Default POLY_MEMS (7,0).
    """
    c = gf.Component()
    half_sp = beam_spacing / 2.0

    beam = make_ccs_beam(
        span=span,
        flex_ratio=flex_ratio,
        flex_width=flex_width,
        rigid_width=rigid_width,
        initial_offset=initial_offset,
        taper_length=taper_length,
        thickness=thickness,
        n_points=n_points,
        layer=layer,
    )

    # --- Two parallel beams, both curving in +y ---
    # Upper beam (centered at y = +half_sp)
    ref_up = c.add_ref(beam)
    ref_up.dmove((0, half_sp))

    # Lower beam (centered at y = -half_sp, same orientation)
    ref_lo = c.add_ref(beam)
    ref_lo.dmove((0, -half_sp))

    # --- Central rod connecting both beam centers ---
    # Upper beam center point: (span/2, half_sp + initial_offset)
    # Lower beam center point: (span/2, -half_sp + initial_offset)
    rod_bottom = -half_sp + initial_offset
    rod_top = half_sp + initial_offset
    rod_height = rod_top - rod_bottom

    rod = gf.components.rectangle(size=(rod_width, rod_height), layer=layer)
    rod_ref = c.add_ref(rod)
    rod_ref.dmove((span / 2.0 - rod_width / 2.0, rod_bottom))

    # --- Anchor pads (4 total, one per beam endpoint) ---
    anchor = gf.components.rectangle(
        size=(anchor_length, anchor_width), layer=layer
    )
    for y_off in [half_sp, -half_sp]:
        # Left anchor (extends left of x=0)
        ref_la = c.add_ref(anchor)
        ref_la.dmove((-anchor_length, y_off - anchor_width / 2.0))
        # Right anchor (extends right of x=span)
        ref_ra = c.add_ref(anchor)
        ref_ra.dmove((span, y_off - anchor_width / 2.0))

    return c


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK

    PDK.activate()

    # Generate individual components for inspection
    half = make_ccs_half_beam()
    half.show()

    beam = make_ccs_beam()
    beam.show()

    beam_set = make_ccs_beam_set()
    beam_set.show()
