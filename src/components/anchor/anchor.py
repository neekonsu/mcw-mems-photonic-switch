"""Anchor components for MEMS switch structures.

Provides fixed anchor frames (with internal grid ribs), multi-layer
MEMS anchors (POLY_TOP + POLY_MEMS frame + SI_FULL), and metal pads.

Adapted from Sirui's reference design (draw_fixedanchor_*, draw_mems_anchor*,
draw_mems_pad).
"""

import math

import gdsfactory as gf

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


# ---------------------------------------------------------------------------
# Anchor frame variants (single-layer POLY_MEMS frame with internal grid ribs)
# ---------------------------------------------------------------------------

@gf.cell
def make_anchor_frame(
    length: float = 30.0,
    height: float = 110.0,
    hole_diameter_max: float = 10.0,
    linewidth: float = 5.0,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Rectangular frame with internal grid ribs and release holes.

    The frame is a rectangle with an outer border of width ``linewidth``.
    Internal vertical and horizontal ribs divide the interior into a grid
    of holes whose size is adjusted to fit evenly (ceiling rounding).

    Centered at origin.

    Args:
        length:            Total width of the frame (um).
        height:            Total height of the frame (um).
        hole_diameter_max: Maximum desired hole size (um).
        linewidth:         Rib / border width (um).
        layer:             GDS layer.
    """
    p_r = hole_diameter_max + linewidth
    n_hole_l = math.ceil((length - linewidth) / p_r)
    n_hole_h = math.ceil((height - linewidth) / p_r)

    d_r_l = int(100 * (length - linewidth) / n_hole_l) / 100 - linewidth
    d_r_h = int(100 * (height - linewidth) / n_hole_h) / 100 - linewidth

    # Outer rectangle
    proof = gf.Component()
    proof_temp = gf.components.rectangle(size=(length, height), layer=layer)
    proof_ref = proof.add_ref(proof_temp)
    proof_ref.dmovex(-length / 2)
    proof_ref.dmovey(-height / 2)

    # Inner rectangle (to subtract for outer frame)
    proof_inner = gf.Component()
    proof_inner_temp = gf.components.rectangle(
        size=(length - 2 * linewidth, height - 2 * linewidth), layer=layer
    )
    proof_inner_ref = proof_inner.add_ref(proof_inner_temp)
    proof_inner_ref.dmovex(-length / 2 + linewidth)
    proof_inner_ref.dmovey(-height / 2 + linewidth)

    proof_outerframe = gf.boolean(proof, proof_inner, operation="not", layer=layer)

    # Internal rib grid
    framework = gf.Component()
    frame_l_temp = gf.components.rectangle(size=(length, linewidth), layer=layer)
    frame_h_temp = gf.components.rectangle(size=(linewidth, height), layer=layer)
    p_r_l = d_r_l + linewidth
    p_r_h = d_r_h + linewidth

    frame_refs = {}
    for ii in range(n_hole_l - 1):
        frame_refs[ii] = framework.add_ref(frame_h_temp)
        frame_refs[ii].dmovex(
            -linewidth / 2 - p_r_l * (n_hole_l - 2) / 2 + ii * p_r_l
        )
        frame_refs[ii].dmovey(-height / 2)

    for jj in range(n_hole_h - 1):
        frame_refs[n_hole_l + jj] = framework.add_ref(frame_l_temp)
        frame_refs[n_hole_l + jj].dmovex(-length / 2)
        frame_refs[n_hole_l + jj].dmovey(
            -linewidth / 2 - p_r_h * (n_hole_h - 2) / 2 + jj * p_r_h
        )

    result = gf.Component()
    combined = gf.boolean(proof_outerframe, framework, operation="or", layer=layer)
    result.add_ref(combined)
    return result


@gf.cell
def make_anchor_frame_large(
    length: float = 30.0,
    height: float = 110.0,
    hole_diameter_max: float = 10.0,
    linewidth: float = 5.0,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Anchor frame variant with floor-rounded hole sizes.

    Same as make_anchor_frame but uses floor rounding (int) instead of
    ceiling rounding for determining the number of holes. This produces
    larger holes.

    Centered at origin.
    """
    p_r = hole_diameter_max + linewidth
    n_hole_l = int((length - linewidth) / p_r)
    n_hole_h = int((height - linewidth) / p_r)

    d_r_l = int(100 * (length - linewidth) / n_hole_l) / 100 - linewidth
    d_r_h = int(100 * (height - linewidth) / n_hole_h) / 100 - linewidth

    proof = gf.Component()
    proof_temp = gf.components.rectangle(size=(length, height), layer=layer)
    proof_ref = proof.add_ref(proof_temp)
    proof_ref.dmovex(-length / 2)
    proof_ref.dmovey(-height / 2)

    proof_inner = gf.Component()
    proof_inner_temp = gf.components.rectangle(
        size=(length - 2 * linewidth, height - 2 * linewidth), layer=layer
    )
    proof_inner_ref = proof_inner.add_ref(proof_inner_temp)
    proof_inner_ref.dmovex(-length / 2 + linewidth)
    proof_inner_ref.dmovey(-height / 2 + linewidth)

    proof_outerframe = gf.boolean(proof, proof_inner, operation="not", layer=layer)

    framework = gf.Component()
    frame_l_temp = gf.components.rectangle(size=(length, linewidth), layer=layer)
    frame_h_temp = gf.components.rectangle(size=(linewidth, height), layer=layer)
    p_r_l = d_r_l + linewidth
    p_r_h = d_r_h + linewidth

    frame_refs = {}
    for ii in range(n_hole_l - 1):
        frame_refs[ii] = framework.add_ref(frame_h_temp)
        frame_refs[ii].dmovex(
            -linewidth / 2 - p_r_l * (n_hole_l - 2) / 2 + ii * p_r_l
        )
        frame_refs[ii].dmovey(-height / 2)

    for jj in range(n_hole_h - 1):
        frame_refs[n_hole_l + jj] = framework.add_ref(frame_l_temp)
        frame_refs[n_hole_l + jj].dmovex(-length / 2)
        frame_refs[n_hole_l + jj].dmovey(
            -linewidth / 2 - p_r_h * (n_hole_h - 2) / 2 + jj * p_r_h
        )

    result = gf.Component()
    combined = gf.boolean(proof_outerframe, framework, operation="or", layer=layer)
    result.add_ref(combined)
    return result


@gf.cell
def make_anchor_frame_cut(
    length: float = 50.0,
    height: float = 110.0,
    left_cut: float = 30.0,
    top_cut: float = 70.0,
    hole_diameter_max: float = 10.0,
    linewidth: float = 5.0,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Anchor frame with a triangular corner chamfer (top-left).

    The top-left corner is cut along a line from (0, height-top_cut) to
    (left_cut, height). Internal grid ribs are added then the triangle
    is subtracted.

    Centered at origin.

    Args:
        length:            Total width (um).
        height:            Total height (um).
        left_cut:          Horizontal extent of the corner cut (um).
        top_cut:           Vertical extent of the corner cut (um).
        hole_diameter_max: Maximum desired hole size (um).
        linewidth:         Rib / border width (um).
        layer:             GDS layer.
    """
    p_r = hole_diameter_max + linewidth
    n_hole_l = math.ceil((length - linewidth) / p_r)
    n_hole_h = math.ceil((height - linewidth) / p_r)

    d_r_l = int(100 * (length - linewidth) / n_hole_l) / 100 - linewidth
    d_r_h = int(100 * (height - linewidth) / n_hole_h) / 100 - linewidth

    # Outer pentagon (cut corner)
    proof = gf.Component()
    vtx = [
        (0, 0), (length, 0), (length, height),
        (left_cut, height), (0, height - top_cut),
    ]
    proof_temp = gf.Component()
    proof_temp.add_polygon(vtx, layer=layer)
    proof_ref = proof.add_ref(proof_temp)
    proof_ref.dmovex(-length / 2)
    proof_ref.dmovey(-height / 2)

    # Inner pentagon
    m = top_cut / left_cut
    s = math.sqrt(1 + m**2)
    vtx_in = [
        (linewidth, linewidth),
        (length - linewidth, linewidth),
        (length - linewidth, height - linewidth),
        ((top_cut - linewidth + linewidth * s) / m, height - linewidth),
        (linewidth, height - top_cut + m * linewidth - linewidth * s),
    ]
    proof_inner = gf.Component()
    proof_inner_temp = gf.Component()
    proof_inner_temp.add_polygon(vtx_in, layer=layer)
    proof_inner_ref = proof_inner.add_ref(proof_inner_temp)
    proof_inner_ref.dmovex(-length / 2)
    proof_inner_ref.dmovey(-height / 2)

    proof_outerframe = gf.boolean(proof, proof_inner, operation="not", layer=layer)

    # Internal rib grid
    framework = gf.Component()
    frame_l_temp = gf.components.rectangle(size=(length, linewidth), layer=layer)
    frame_h_temp = gf.components.rectangle(size=(linewidth, height), layer=layer)
    p_r_l = d_r_l + linewidth
    p_r_h = d_r_h + linewidth

    frame_refs = {}
    for ii in range(n_hole_l - 1):
        frame_refs[ii] = framework.add_ref(frame_h_temp)
        frame_refs[ii].dmovex(
            -linewidth / 2 - p_r_l * (n_hole_l - 2) / 2 + ii * p_r_l
        )
        frame_refs[ii].dmovey(-height / 2)

    for jj in range(n_hole_h - 1):
        frame_refs[n_hole_l + jj] = framework.add_ref(frame_l_temp)
        frame_refs[n_hole_l + jj].dmovex(-length / 2)
        frame_refs[n_hole_l + jj].dmovey(
            -linewidth / 2 - p_r_h * (n_hole_h - 2) / 2 + jj * p_r_h
        )

    # Combine frame + ribs
    proof_with_ribs = gf.boolean(proof_outerframe, framework, operation="or", layer=layer)

    # Cut the triangle
    triangle_cut = gf.Component()
    triangle_cut.add_polygon(
        [(-length / 2, height / 2),
         (-length / 2 + left_cut, height / 2),
         (-length / 2, height / 2 - top_cut)],
        layer,
    )
    proof_final = gf.boolean(proof_with_ribs, triangle_cut, operation="not", layer=layer)

    result = gf.Component()
    result.add_ref(proof_final)
    return result


# ---------------------------------------------------------------------------
# Multi-layer MEMS anchors
# ---------------------------------------------------------------------------

@gf.cell
def make_mems_anchor(
    length: float = 30.0,
    height: float = 20.0,
    hole_diameter_max: float = 2.0,
    linewidth: float = 0.8,
    over_top: float = 0.3,
    over_bottom: float = 0.3,
) -> gf.Component:
    """3-layer MEMS anchor: POLY_TOP cap + POLY_MEMS frame + SI_FULL base.

    Centered at origin. The POLY_TOP and SI_FULL rectangles extend beyond
    the POLY_MEMS frame by ``over_top`` and ``over_bottom`` respectively.

    Args:
        length:            Frame width (um).
        height:            Frame height (um).
        hole_diameter_max: Max hole size for the frame grid (um).
        linewidth:         Rib width (um).
        over_top:          POLY_TOP overhang beyond frame (um).
        over_bottom:       SI_FULL overhang beyond frame (um).
    """
    mems_anchor = gf.Component()

    # POLY_TOP cap
    anchor_top_temp = gf.components.rectangle(
        size=(length + 2 * over_top, height + 2 * over_top), layer=LAYER.POLY_TOP
    )
    anchor_top = mems_anchor.add_ref(anchor_top_temp)
    anchor_top.dmovex(-length / 2 - over_top)
    anchor_top.dmovey(-height / 2 - over_top)

    # POLY_MEMS frame
    anchor_frame_temp = make_anchor_frame(
        length, height, hole_diameter_max, linewidth, layer=LAYER.POLY_MEMS
    )
    mems_anchor.add_ref(anchor_frame_temp)

    # SI_FULL base
    anchor_bottom_temp = gf.components.rectangle(
        size=(length + 2 * over_bottom, height + 2 * over_bottom), layer=LAYER.SI_FULL
    )
    anchor_bottom = mems_anchor.add_ref(anchor_bottom_temp)
    anchor_bottom.dmovex(-length / 2 - over_bottom)
    anchor_bottom.dmovey(-height / 2 - over_bottom)

    return mems_anchor


@gf.cell
def make_mems_anchor_cut(
    length: float = 50.0,
    height: float = 20.0,
    left_cut: float = 20.0,
    top_cut: float = 10.0,
    hole_diameter_max: float = 2.0,
    linewidth: float = 0.8,
    over_top: float = 0.3,
    over_bottom: float = 0.3,
) -> gf.Component:
    """3-layer MEMS anchor with triangular corner chamfer.

    Same as make_mems_anchor but with a cut in the top-left corner on all layers.

    Args:
        length:            Frame width (um).
        height:            Frame height (um).
        left_cut:          Horizontal extent of corner cut (um).
        top_cut:           Vertical extent of corner cut (um).
        hole_diameter_max: Max hole size for the frame grid (um).
        linewidth:         Rib width (um).
        over_top:          POLY_TOP overhang beyond frame (um).
        over_bottom:       SI_FULL overhang beyond frame (um).
    """
    mems_anchor = gf.Component()

    # POLY_TOP cap (pentagon)
    anchor_top_temp = gf.Component()
    anchor_top_temp.add_polygon(
        [
            (0, 0),
            (length + 2 * over_top, 0),
            (length + 2 * over_top, height + 2 * over_top),
            (left_cut, height + 2 * over_top),
            (0, height + 2 * over_top - top_cut),
        ],
        layer=LAYER.POLY_TOP,
    )
    anchor_top = mems_anchor.add_ref(anchor_top_temp)
    anchor_top.dmovex(-length / 2 - over_top)
    anchor_top.dmovey(-height / 2 - over_top)

    # POLY_MEMS frame (with cut)
    anchor_frame_temp = make_anchor_frame_cut(
        length, height, left_cut, top_cut, hole_diameter_max, linewidth,
        layer=LAYER.POLY_MEMS,
    )
    mems_anchor.add_ref(anchor_frame_temp)

    # SI_FULL base (pentagon)
    anchor_bottom_temp = gf.Component()
    anchor_bottom_temp.add_polygon(
        [
            (0, 0),
            (length + 2 * over_bottom, 0),
            (length + 2 * over_bottom, height + 2 * over_bottom),
            (left_cut, height + 2 * over_bottom),
            (0, height + 2 * over_bottom - top_cut),
        ],
        layer=LAYER.SI_FULL,
    )
    anchor_bottom = mems_anchor.add_ref(anchor_bottom_temp)
    anchor_bottom.dmovex(-length / 2 - over_bottom)
    anchor_bottom.dmovey(-height / 2 - over_bottom)

    return mems_anchor


@gf.cell
def make_mems_pad(
    length: float = 30.0,
    height: float = 30.0,
    hole_diameter_max: float = 2.0,
    linewidth: float = 0.8,
    over_top: float = 0.3,
    over_bottom: float = 0.3,
    over_metal: float = 1.0,
) -> gf.Component:
    """4-layer MEMS pad: METAL + POLY_TOP + POLY_MEMS frame + SI_FULL.

    Same as make_mems_anchor with an additional METAL rectangle on top,
    inset by ``over_metal`` from the POLY_TOP edges.

    Args:
        length:            Frame width (um).
        height:            Frame height (um).
        hole_diameter_max: Max hole size for the frame grid (um).
        linewidth:         Rib width (um).
        over_top:          POLY_TOP overhang beyond frame (um).
        over_bottom:       SI_FULL overhang beyond frame (um).
        over_metal:        Metal inset from POLY_TOP edges (um).
    """
    mems_pad = gf.Component()

    # POLY_TOP cap
    pad_top_temp = gf.components.rectangle(
        size=(length + 2 * over_top, height + 2 * over_top), layer=LAYER.POLY_TOP
    )
    pad_top = mems_pad.add_ref(pad_top_temp)
    pad_top.dmovex(-length / 2 - over_top)
    pad_top.dmovey(-height / 2 - over_top)

    # POLY_MEMS frame
    pad_frame_temp = make_anchor_frame(
        length, height, hole_diameter_max, linewidth, layer=LAYER.POLY_MEMS
    )
    mems_pad.add_ref(pad_frame_temp)

    # SI_FULL base
    pad_bottom_temp = gf.components.rectangle(
        size=(length + 2 * over_bottom, height + 2 * over_bottom), layer=LAYER.SI_FULL
    )
    pad_bottom = mems_pad.add_ref(pad_bottom_temp)
    pad_bottom.dmovex(-length / 2 - over_bottom)
    pad_bottom.dmovey(-height / 2 - over_bottom)

    # METAL
    pad_metal_temp = gf.components.rectangle(
        size=(
            length + 2 * over_top - 2 * over_metal,
            height + 2 * over_top - 2 * over_metal,
        ),
        layer=LAYER.METAL,
    )
    pad_metal = mems_pad.add_ref(pad_metal_temp)
    pad_metal.dmovex(-length / 2 - over_top + over_metal)
    pad_metal.dmovey(-height / 2 - over_top + over_metal)

    return mems_pad


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()
    anchor = make_mems_anchor()
    anchor.show()
