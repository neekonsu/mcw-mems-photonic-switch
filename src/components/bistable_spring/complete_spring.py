"""Complete bistable spring mechanism for MEMS switch.

Assembles the full doubly-clamped bistable mechanism: 4 CCS half-beams
connected by a central shuttle, with multi-layer anchors at both ends.

Geometry (top view):
    Left Anchor --- upper half-beam L --+            +-- upper half-beam R --- Right Anchor
                                        |  shuttle   |
    Left Anchor --- lower half-beam L --+            +-- lower half-beam R --- Right Anchor

Both beam pairs curve in +y (same buckling mode).  The shuttle connects
their midpoints, providing axial coupling for snap-through bistability.

This is the layout component corresponding to the full-spring FEM
verification (notebooks 4a/4b/5a/5b).
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
    "bistable_spring/ccs_bistable_beam.py", "_cs_ccs_beam"
)
_anchor_mod = _import_from("anchor/anchor.py", "_cs_anchor")
_shuttle_mod = _import_from("shuttle_beam/shuttle_beam.py", "_cs_shuttle")

make_ccs_half_beam = _ccs_beam.make_ccs_half_beam
make_mems_anchor = _anchor_mod.make_mems_anchor
make_proofmass = _shuttle_mod.make_proofmass


@gf.cell
def make_complete_spring(
    anchor_distance: float = 80.0,
    beam_spacing: float = 10.0,
    shuttle_length: float = 7.0,
    shuttle_height: float = 12.0,
    shuttle_hole_diameter: float = 5.0,
    shuttle_hole_gap: float = 0.8,
    flex_ratio: float = 0.3,
    flex_width: float = 0.5,
    rigid_width: float = 0.9375,
    initial_offset: float = 1.2,
    taper_length: float = 2.0,
    thickness: float = 0.5,
    anchor_length: float = 8.0,
    anchor_width: float = 8.0,
    anchor_hole_max: float = 2.0,
    anchor_linewidth: float = 0.8,
    anchor_over_top: float = 0.4,
    anchor_over_bottom: float = 0.5,
    n_points: int = 400,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Complete bistable spring: 4 half-beams + shuttle + 2 anchors.

    The mechanism spans from left anchor (x=0) to right anchor
    (x=anchor_distance), with the shuttle centered at
    x=anchor_distance/2.  All beams curve in +y.

    Coordinate system:
      - x-axis: along beam span (left anchor at x=0, right at x=anchor_distance)
      - y-axis: perpendicular (actuation direction, beams curve in +y)
      - Origin at left anchor center

    Args:
        anchor_distance:      Inner-edge to inner-edge of anchors (um).
        beam_spacing:         Center-to-center distance between upper/lower beams (um).
        shuttle_length:       Shuttle x-extent along beam axis (um).
        shuttle_height:       Shuttle y-extent perpendicular to beams (um).
        shuttle_hole_diameter: Square hole side in shuttle (um).
        shuttle_hole_gap:     Gap between holes in shuttle (um).
        flex_ratio:           Fraction of half_span for each flex section.
        flex_width:           Width of flex section (um).
        rigid_width:          Width of rigid section (um).
        initial_offset:       CCS y-offset at shuttle end (um).
        taper_length:         Flex-to-rigid width taper (um).
        thickness:            Structural layer thickness (um).
        anchor_length:        Anchor extent along beam direction (um).
        anchor_width:         Anchor extent perpendicular to beam (um).
        anchor_hole_max:      Max hole size in anchor frame (um).
        anchor_linewidth:     Rib width in anchor frame (um).
        anchor_over_top:      POLY_TOP overhang (um).
        anchor_over_bottom:   SI_FULL overhang (um).
        n_points:             Polygon resolution per half-beam.
        layer:                Structural GDS layer.
    """
    c = gf.Component()

    half_span = (anchor_distance - shuttle_length) / 2.0
    half_sp = beam_spacing / 2.0
    half_n = max(n_points // 2, 100)

    # Build one CCS half-beam (anchor at x=0, shuttle end at x=half_span)
    half_beam = make_ccs_half_beam(
        half_span=half_span,
        flex_ratio=flex_ratio,
        flex_width=flex_width,
        rigid_width=rigid_width,
        initial_offset=initial_offset,
        taper_length=taper_length,
        thickness=thickness,
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

    # Build shuttle (proof mass with release holes)
    shuttle = make_proofmass(
        length=shuttle_length,
        height=shuttle_height,
        hole_diameter=shuttle_hole_diameter,
        hole_gap=shuttle_hole_gap,
        layer=layer,
    )

    # --- Place 4 half-beams ---
    # Half-beam profile: anchor at (0, 0) -> shuttle at (half_span, initial_offset)
    #
    # Left side:  anchor at x=0, shuttle end at x=half_span
    # Right side: anchor at x=anchor_distance, shuttle end at x=anchor_distance-half_span
    #
    # Upper beams at y = +half_sp, lower beams at y = -half_sp

    for sign_x, sign_y in [(-1, +1), (-1, -1), (+1, +1), (+1, -1)]:
        ref = c.add_ref(half_beam)

        if sign_x < 0:
            # Left side: no mirror, just place at x=0
            pass
        else:
            # Right side: mirror x so anchor is at right, shuttle points left
            ref.dmirror_x()
            ref.dmovex(anchor_distance)

        # Shift in y for upper (+half_sp) or lower (-half_sp) beam
        ref.dmovey(sign_y * half_sp)

    # --- Place shuttle at center ---
    # Shuttle center at x = anchor_distance/2
    # y-center at initial_offset (where beam shuttle ends meet)
    shuttle_ref = c.add_ref(shuttle)
    shuttle_ref.dmovex(anchor_distance / 2.0)
    shuttle_ref.dmovey(initial_offset)

    # --- Place 2 multi-layer anchors ---
    # Left anchor centered at x=0
    anchor_left = c.add_ref(anchor)
    # anchor is centered at origin, so just leave it

    # Right anchor centered at x=anchor_distance
    anchor_right = c.add_ref(anchor)
    anchor_right.dmovex(anchor_distance)

    return c


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK

    PDK.activate()

    sp = make_complete_spring()
    bb = sp.dbbox()
    print(f"Complete spring size: {bb.width():.1f} x {bb.height():.1f} um")
    print(f"  anchor_distance=80, half_span={(80-7)/2:.1f} um")
    sp.show()
