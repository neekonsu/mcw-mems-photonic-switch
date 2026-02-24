"""Bistable spring pair for MEMS switch — drop-in replacement for folded spring.

Provides a 4-half-beam CCS bistable spring pair that connects the proof mass
to multi-layer anchors.  Intended as a direct replacement for
``make_spring_pair()`` from ``folded_spring.py``.

Geometry (top view, symmetric about x=0):
    Left Anchor ─ upper half-beam ─╮         ╭─ upper half-beam ─ Right Anchor
                                   ├─ gap ──┤
    Left Anchor ─ lower half-beam ─╯         ╰─ lower half-beam ─ Right Anchor
                              anchor_gap_length
                             (shuttle sits here)

Each half-beam is a CCS profile (cosine flex + straight rigid) with the
anchor at the outer end (y=0) and rising to y=initial_offset at the
shuttle edge.  The bistable mechanism acts in Y (perpendicular to the
beam axis).

Anchors are 3-layer stacks (POLY_TOP + POLY_MEMS frame + SI_FULL) built
using ``make_mems_anchor()`` from the anchor module.
"""

import importlib.util
import os
import sys

import gdsfactory as gf

_comp_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


def _import_from(rel_path, module_name):
    """Import a module from a relative file path, avoiding name collisions."""
    path = os.path.normpath(os.path.join(_comp_dir, rel_path))
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ccs_beam = _import_from(
    "bistable_spring/ccs_bistable_beam.py", "_bsp_ccs_beam"
)
_anchor_mod = _import_from("anchor/anchor.py", "_bsp_anchor")

make_ccs_half_beam = _ccs_beam.make_ccs_half_beam
make_mems_anchor = _anchor_mod.make_mems_anchor


@gf.cell
def make_bistable_spring_pair(
    span: float = 40.0,
    flex_ratio: float = 0.3,
    flex_width: float = 0.5,
    rigid_width: float = 0.9375,
    initial_offset: float = 1.2,
    taper_length: float = 2.0,
    beam_spacing: float = 5.0,
    anchor_gap_length: float = 7.0,
    anchor_length: float = 8.0,
    anchor_width: float = 8.0,
    anchor_hole_max: float = 2.0,
    anchor_linewidth: float = 0.8,
    anchor_over_top: float = 0.4,
    anchor_over_bottom: float = 0.5,
    n_points: int = 400,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """4-half-beam CCS bistable spring pair — drop-in replacement for folded spring.

    Two pairs of CCS half-beams connect left/right multi-layer anchors to
    the central shuttle gap.  Each half-beam runs from an anchor (y=0) to
    the shuttle edge (y=initial_offset), providing bistability in Y.

    The center gap (anchor_gap_length) matches the proof mass width, just
    like the folded spring's anchor_gap_length parameter.

    Coordinate system matches folded spring:
      - x-axis: along beam span
      - y-axis: perpendicular (actuation direction)
      - Center of component at midpoint between upper/lower beam pairs

    Args:
        span:              Total beam span per side, anchor to shuttle edge (um).
        flex_ratio:        Fraction of span for flexible cosine section.
        flex_width:        Width of flex section (um).  Default 0.5.
        rigid_width:       Width of rigid section (um).
        initial_offset:    CCS y-offset at shuttle end (um).  Bistability
                           requires initial_offset / thickness > 2.31;
                           default 1.2 / 0.5 = 2.4.
        taper_length:      Width transition zone (um).
        beam_spacing:      Gap between upper and lower beams in a pair (um).
        anchor_gap_length: Horizontal center gap for shuttle attachment (um).
        anchor_length:     Anchor extent along beam direction (um).
        anchor_width:      Anchor extent perpendicular to beam (um).
        anchor_hole_max:   Max hole size in anchor frame grid (um).
        anchor_linewidth:  Rib width in anchor frame (um).
        anchor_over_top:   POLY_TOP overhang beyond anchor frame (um).  >= 0.4 (E.03).
        anchor_over_bottom: SI_FULL overhang beyond anchor frame (um).  >= 0.5 (E.02).
        n_points:          Polygon resolution per half-beam.
        layer:             Structural GDS layer.
    """
    c = gf.Component()

    half_gap = anchor_gap_length / 2.0
    half_sp = beam_spacing / 2.0
    half_n = max(n_points // 2, 100)

    # Build one CCS half-beam (anchor at x=0, shuttle end at x=span)
    half_beam = make_ccs_half_beam(
        half_span=span,
        flex_ratio=flex_ratio,
        flex_width=flex_width,
        rigid_width=rigid_width,
        initial_offset=initial_offset,
        taper_length=taper_length,
        n_points=half_n,
        layer=layer,
    )

    # Build multi-layer anchor
    anchor = make_mems_anchor(
        length=anchor_length,
        height=anchor_width,
        hole_diameter_max=anchor_hole_max,
        linewidth=anchor_linewidth,
        over_top=anchor_over_top,
        over_bottom=anchor_over_bottom,
    )

    # Place 4 half-beams: left-upper, left-lower, right-upper, right-lower
    #
    # Half-beam profile: anchor at (0, 0) → shuttle at (span, initial_offset)
    # The shuttle end (with y-offset) must be near the center gap so that
    # bistability acts on the proof mass.
    #
    # Left side:  anchor at x = -(half_gap + span), shuttle at x = -half_gap
    #             No mirror needed — just shift x by -(half_gap + span)
    # Right side: anchor at x = +(half_gap + span), shuttle at x = +half_gap
    #             Mirror in x, then shift x by +(half_gap + span)

    for sign_x, sign_y in [(-1, +1), (-1, -1), (+1, +1), (+1, -1)]:
        ref = c.add_ref(half_beam)

        if sign_x < 0:
            # Left side: shift so anchor is at far left, shuttle near center
            ref.dmovex(-(half_gap + span))
        else:
            # Right side: mirror x so beam points left, then shift right
            ref.dmirror_x()
            ref.dmovex(half_gap + span)

        # Shift in y for upper (+half_sp) or lower (-half_sp) beam
        ref.dmovey(sign_y * half_sp)

    # Place 2 multi-layer anchors (left and right)
    # Left anchor at x = -(half_gap + span)
    anchor_left = c.add_ref(anchor)
    anchor_left.dmovex(-(half_gap + span))

    # Right anchor at x = +(half_gap + span)
    anchor_right = c.add_ref(anchor)
    anchor_right.dmovex(half_gap + span)

    return c


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK

    PDK.activate()

    sp = make_bistable_spring_pair()
    bb = sp.dbbox()
    print(f"Bistable spring pair size: {bb.width():.1f} x {bb.height():.1f} um")
    sp.show()
