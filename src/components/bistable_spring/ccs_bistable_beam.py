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
    (fixed)   0.1 um wide              0.4 um wide         (shuttle)
              3/10 of span             7/10 of span

The beam is symmetric about its center:
    Anchor ─ Flex ─ Rigid ─ Rod ─ Rigid ─ Flex ─ Anchor

Key dimensions from the paper (fabricated on 220 nm SOI, 2 um BOX):
  - Total span (anchor-to-anchor, excl. rod): 40 um
  - Flexible cosine beam width:  0.1 um
  - Rigid straight beam width:   0.4 um
  - Flex : rigid length ratio:   3 : 7
  - Initial max y-offset:        0.2 um
  - Post-release displacement between stable states: ~1.2 um
  - SOI residual compressive pre-strain: ~4.1e-4
  - Switching energy per set: 64 fJ (to 2nd) / 58 fJ (to 1st)
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
def make_ccs_beam(
    span: float = 40.0,
    flex_ratio: float = 0.3,
    flex_width: float = 0.1,
    rigid_width: float = 0.4,
    initial_offset: float = 0.2,
    taper_length: float = 1.0,
    n_points: int = 400,
    layer=LAYER.SI_FULL,
) -> gf.Component:
    """Single CCS bistable beam (as-fabricated mask shape).

    The beam spans from (0, 0) at the left anchor to (span, 0) at the
    right anchor.  The centerline bulges in the +y direction, reaching
    maximum offset at x = span/2.

    Beam structure (left to right):
        Anchor -> cosine flex (0.1 um wide, 12 um long)
               -> taper
               -> straight rigid (0.4 um wide, 28 um long)
               -> [center: max offset = 0.2 um]
               -> straight rigid -> taper -> cosine flex -> Anchor

    After HF vapor release the residual compressive stress in the SOI
    layer (~4.1e-4 pre-strain) causes the beam to buckle to its first
    stable state with ~0.6 um additional offset.  A second stable state
    exists at ~-0.6 um from the as-fabricated position (total travel
    ~1.2 um between states).

    Args:
        span:           Beam span, anchor to anchor (um).  Default 40.
        flex_ratio:     Fraction of span for flexible sections.  Default 0.3.
        flex_width:     Width of flexible cosine beams (um).  Default 0.1.
        rigid_width:    Width of rigid straight beams (um).  Default 0.4.
        initial_offset: Max y-offset at beam center (um).  Default 0.2.
        taper_length:   Flex-to-rigid width taper length (um).  Default 1.0.
        n_points:       Polygon discretization resolution.  Default 400.
        layer:          GDS layer tuple.  Default SI_FULL (1,0).
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
    flex_width: float = 0.1,
    rigid_width: float = 0.4,
    initial_offset: float = 0.2,
    taper_length: float = 1.0,
    beam_spacing: float = 6.0,
    rod_width: float = 0.4,
    anchor_width: float = 2.0,
    anchor_length: float = 3.0,
    n_points: int = 400,
    layer=LAYER.SI_FULL,
) -> gf.Component:
    """Parallel pair of CCS bistable beams with anchors and central rod.

    Two CCS beams are arranged symmetrically about y=0, both curving in
    the +y direction (same buckling mode).  Their centers are connected
    by a rigid vertical rod that attaches to the shuttle beam.  Anchor
    pads are placed at both ends of each beam.

    This is one complete "set" of CCS beams as described in the paper.
    The full switch uses two sets (one on each side of the shuttle),
    driven by a bidirectional electrostatic comb actuator.

    In the first stable state (ON state, post-release), both beams
    buckle further in +y, pushing the shuttle upward toward the fixed
    waveguide of the horizontal adiabatic coupler (HAC).  Applying
    voltage to the lower comb pulls the shuttle in -y, snapping the
    beams into their second stable state (OFF state).

    Coordinate system:
      x: along beam span; x=0 at left anchors, x=span at right anchors
      y: perpendicular to beams; y=0 midway between the beam pair
      Beams curve in +y; first stable state displaces shuttle in +y

    Args:
        span:           Beam span, anchor to anchor (um).  Default 40.
        flex_ratio:     Fraction of span for flexible sections.  Default 0.3.
        flex_width:     Flexible beam width (um).  Default 0.1.
        rigid_width:    Rigid beam width (um).  Default 0.4.
        initial_offset: Max y-offset at beam center (um).  Default 0.2.
        taper_length:   Width taper length (um).  Default 1.0.
        beam_spacing:   Center-to-center distance between beams (um).
                        Default 6.
        rod_width:      Width of the connecting rod (um).  Default 0.4.
        anchor_width:   Anchor pad width (um).  Default 2.
        anchor_length:  Anchor pad length (um).  Default 3.
        n_points:       Polygon resolution.  Default 400.
        layer:          GDS layer tuple.  Default SI_FULL (1,0).
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
    # Anchors remain bonded to the BOX layer after HF release because
    # they are wide enough (>= 2 um) to resist undercut.
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

    # Generate the full beam set and display
    beam_set = make_ccs_beam_set()
    beam_set.show()
