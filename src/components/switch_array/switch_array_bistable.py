"""8x8 bistable MEMS switch array with routed interconnects.

Mirrors ``switch_array.py`` but uses the bistable switch cell variant
(CCS springs instead of folded springs).  Places 1.75x-scale single-comb
bistable switch cells in an 8x8 grid at 250 um pitch.  Routes POLY_MEMS
interconnects to the CCS spring anchors (row buses) and comb drive fixed
anchors (column buses), with stiction-prevention anchors along each route.
"""

import importlib.util
import math
import os
import sys

import gdsfactory as gf

_comp_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


def _import_from(rel_path, module_name):
    path = os.path.normpath(os.path.join(_comp_dir, rel_path))
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_shuttle_beam = _import_from("shuttle_beam/shuttle_beam.py", "_barr_shuttle_beam")
_bistable_spring = _import_from(
    "bistable_spring/bistable_spring_pair.py", "_barr_bistable_spring"
)
_comb_drive = _import_from("comb_drive/comb_drive.py", "_barr_comb_drive")
_anchor_mod = _import_from("anchor/anchor.py", "_barr_anchor")

make_proofmass = _shuttle_beam.make_proofmass
make_bistable_spring_pair = _bistable_spring.make_bistable_spring_pair
make_comb_drive = _comb_drive.make_comb_drive
make_mems_anchor = _anchor_mod.make_mems_anchor

# ---------------------------------------------------------------------------
# Scale factor (same as mems_switch_cell_large / switch_array)
# ---------------------------------------------------------------------------
S = 1.75

# ---------------------------------------------------------------------------
# Array parameters
# ---------------------------------------------------------------------------
NROWS = 8
NCOLS = 8
PITCH = 250.0  # um

# Interconnect parameters
TRACE_WIDTH = 2.0      # um, poly-Si trace width
ANCHOR_SIZE = 10.0     # um, stiction-prevention anchor side length
ANCHOR_PITCH = 100.0   # um, max distance between anchors along a route
ANCHOR_OVER_TOP = 0.3  # um, POLY_TOP overhang
ANCHOR_OVER_BOT = 0.5  # um, SI_FULL overhang


# ---------------------------------------------------------------------------
# Padless bistable switch cell (omits large pads so cell fits pitch)
# ---------------------------------------------------------------------------
@gf.cell
def make_switch_cell_bistable_padless(
    proof_length: float = 7.0 * S,
    proof_height: float = 120.0 * S,
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    # Bistable spring parameters (scaled)
    spring_span: float = 40.0 * S,
    spring_flex_ratio: float = 0.3,
    spring_flex_width: float = 0.8,
    spring_rigid_width: float = 1.5,
    spring_initial_offset: float = 1.2,
    spring_taper_length: float = 2.0,
    spring_beam_spacing: float = 5.0 * S,
    spring_anchor_length: float = 8.0 * S,
    spring_anchor_width: float = 8.0 * S,
    spring_anchor_hole_max: float = 2.0,
    spring_anchor_linewidth: float = 0.8,
    spring_anchor_over_top: float = 0.4,
    spring_anchor_over_bottom: float = 0.5,
    # Comb drive parameters (scaled)
    finger_length: float = 5.0 * S,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 3.0 * S,
    num_pair: int = round(20 * S),
    edge_fixed: float = 1.0,
    holder_distance: float = 0.0,
    holder_linewidth: float = 0.8,
    holder_width_move: float = 3.0 * S,
    holder_width_fixed: float = 20.0 * S,
    holder_gap_min: float = 2.0,
    holder_top_over: float = 0.3,
    holder_bottom_over: float = 0.3,
    # Positioning (scaled)
    spring_edge_upper: float = 1.0 * S,
    spring_edge_lower: float = 1.0 * S,
    comb_edge_lower: float = 5.0 * S,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """1.75x bistable switch cell without large pads (fits 250 um pitch).

    Same as make_switch_mems_bistable but scaled 1.75x and without large
    pad anchors.  The CCS spring's built-in multi-layer anchors serve as
    routing targets for the array interconnects.
    """
    p_r = hole_diameter + hole_gap
    proof_length = int((proof_length - hole_gap) / p_r) * p_r + hole_gap
    proof_height = int((proof_height - hole_gap) / p_r) * p_r + hole_gap

    if holder_distance == 0:
        L = num_pair * 2 * (finger_width + finger_gap) + finger_width + 2 * edge_fixed
        W = holder_width_move - holder_linewidth
        N = math.ceil(L / W)
        holder_distance = N * W - L

    switch = gf.Component()

    # Proof mass
    pm = make_proofmass(proof_length, proof_height, hole_diameter, hole_gap, layer)
    switch.add_ref(pm)

    # Bistable spring pairs
    spring = make_bistable_spring_pair(
        span=spring_span,
        flex_ratio=spring_flex_ratio,
        flex_width=spring_flex_width,
        rigid_width=spring_rigid_width,
        initial_offset=spring_initial_offset,
        taper_length=spring_taper_length,
        beam_spacing=spring_beam_spacing,
        anchor_gap_length=proof_length,
        anchor_length=spring_anchor_length,
        anchor_width=spring_anchor_width,
        anchor_hole_max=spring_anchor_hole_max,
        anchor_linewidth=spring_anchor_linewidth,
        anchor_over_top=spring_anchor_over_top,
        anchor_over_bottom=spring_anchor_over_bottom,
        layer=layer,
    )

    spring_upper = switch.add_ref(spring)
    spring_upper.dmirror_y()
    spring_upper.dmovey(proof_height / 2 - spring_edge_upper)

    spring_lower = switch.add_ref(spring)
    spring_lower.dmovey(-proof_height / 2 + spring_edge_lower)

    # Comb drives
    comb = make_comb_drive(
        finger_length, finger_width, finger_gap, finger_distance, num_pair,
        edge_fixed, holder_distance, holder_linewidth, holder_width_move,
        holder_width_fixed, holder_gap_min, holder_top_over, holder_bottom_over, layer,
    )
    comb_right = switch.add_ref(comb)
    comb_right.dmovex(proof_length / 2)
    comb_right.dmovey(-proof_height / 2 + comb_edge_lower)

    comb_left = switch.add_ref(comb)
    comb_left.dmirror_x()
    comb_left.dmovex(-proof_length / 2)
    comb_left.dmovey(-proof_height / 2 + comb_edge_lower)

    return switch


def _get_bistable_cell_connection_points():
    """Compute connection point offsets for the bistable padless cell.

    Returns dict with keys:
        spring_upper_y:     y-center of upper CCS spring anchors
        spring_lower_y:     y-center of lower CCS spring anchors
        spring_anchor_top:  y of upper spring anchor top edge
        spring_anchor_bot:  y of lower spring anchor bottom edge
        comb_right_cx:      x-center of right comb fixed anchor
        comb_left_cx:       x-center of left comb fixed anchor
        comb_anchor_cy:     y-center of comb fixed anchors
        comb_anchor_top:    y of comb fixed anchor top edge
        comb_anchor_bot:    y of comb fixed anchor bottom edge
        comb_right_edge:    x of right comb anchor right edge
        comb_left_edge:     x of left comb anchor left edge
    """
    p_r = 5.0 + 0.8  # hole_diameter + hole_gap
    proof_height = int((120.0 * S - 0.8) / p_r) * p_r + 0.8
    proof_length = int((7.0 * S - 0.8) / p_r) * p_r + 0.8

    spring_edge = 1.0 * S
    spring_anchor_width = 8.0 * S
    spring_anchor_over_top = 0.4
    spring_anchor_over_bot = 0.5

    # CCS spring anchor centers (the bistable spring pair's center is at
    # the proof mass edge; the built-in anchors are at the outer ends)
    spring_upper_y = proof_height / 2 - spring_edge
    spring_lower_y = -proof_height / 2 + spring_edge

    spring_anchor_top = spring_upper_y + spring_anchor_width / 2 + spring_anchor_over_bot
    spring_anchor_bot = spring_lower_y - spring_anchor_width / 2 - spring_anchor_over_bot

    # Comb drive fixed anchor position (same as switch_array.py)
    holder_linewidth = 0.8
    comb_edge_lower = 5.0 * S
    finger_width = 0.5
    finger_gap = 0.5
    finger_length = 5.0 * S
    finger_distance = 3.0 * S
    num_pair = round(20 * S)
    edge_fixed = 1.0
    holder_width_move = 3.0 * S
    holder_width_fixed = 20.0 * S

    L_comb = num_pair * 2 * (finger_width + finger_gap) + finger_width + 2 * edge_fixed
    W_comb = holder_width_move - holder_linewidth
    N_comb = math.ceil(L_comb / W_comb)
    holder_distance = N_comb * W_comb - L_comb

    l_hf = 2 * num_pair * (finger_width + finger_gap)
    comb_anchor_local_x = l_hf / 2 + holder_distance + edge_fixed + finger_width
    comb_anchor_local_y = holder_width_fixed / 2 + holder_width_move + finger_length + finger_distance

    comb_origin_x = proof_length / 2
    comb_origin_y = -proof_height / 2 + comb_edge_lower
    comb_right_cx = comb_origin_x + comb_anchor_local_x
    comb_anchor_cy = comb_origin_y + comb_anchor_local_y
    comb_left_cx = -(comb_origin_x + comb_anchor_local_x)

    comb_anchor_top = comb_anchor_cy + holder_width_fixed / 2 + 0.3
    comb_anchor_bot = comb_anchor_cy - holder_width_fixed / 2 - 0.3

    comb_right_edge = comb_origin_x + comb_anchor_local_x + l_hf / 2
    comb_left_edge = -(comb_origin_x + comb_anchor_local_x + l_hf / 2)

    return {
        "spring_upper_y": spring_upper_y,
        "spring_lower_y": spring_lower_y,
        "spring_anchor_top": spring_anchor_top,
        "spring_anchor_bot": spring_anchor_bot,
        "comb_right_cx": comb_right_cx,
        "comb_left_cx": comb_left_cx,
        "comb_anchor_cy": comb_anchor_cy,
        "comb_anchor_top": comb_anchor_top,
        "comb_anchor_bot": comb_anchor_bot,
        "comb_right_edge": comb_right_edge,
        "comb_left_edge": comb_left_edge,
    }


def _add_stiction_anchor(parent, cx, cy, size=ANCHOR_SIZE):
    """Place a 3-layer stiction-prevention anchor at (cx, cy)."""
    hs = size / 2
    over_top = ANCHOR_OVER_TOP
    over_bot = ANCHOR_OVER_BOT

    parent.add_polygon(
        [(cx - hs - over_top, cy - hs - over_top),
         (cx + hs + over_top, cy - hs - over_top),
         (cx + hs + over_top, cy + hs + over_top),
         (cx - hs - over_top, cy + hs + over_top)],
        layer=LAYER.POLY_TOP,
    )
    parent.add_polygon(
        [(cx - hs, cy - hs),
         (cx + hs, cy - hs),
         (cx + hs, cy + hs),
         (cx - hs, cy + hs)],
        layer=LAYER.POLY_MEMS,
    )
    parent.add_polygon(
        [(cx - hs - over_bot, cy - hs - over_bot),
         (cx + hs + over_bot, cy - hs - over_bot),
         (cx + hs + over_bot, cy + hs + over_bot),
         (cx - hs - over_bot, cy + hs + over_bot)],
        layer=LAYER.SI_FULL,
    )


def _add_stub(
    parent: gf.Component,
    x0: float, y0: float,
    x1: float, y1: float,
    trace_width: float = TRACE_WIDTH,
    anchor_size: float = ANCHOR_SIZE,
    layer=LAYER.POLY_MEMS,
):
    """Draw a short trace stub with a stiction anchor at the endpoint (x1, y1)."""
    is_horizontal = abs(y1 - y0) < 0.01
    is_vertical = abs(x1 - x0) < 0.01

    if is_horizontal:
        xlo, xhi = min(x0, x1), max(x0, x1)
        parent.add_polygon(
            [(xlo, y0 - trace_width / 2),
             (xhi, y0 - trace_width / 2),
             (xhi, y0 + trace_width / 2),
             (xlo, y0 + trace_width / 2)],
            layer=layer,
        )
    elif is_vertical:
        ylo, yhi = min(y0, y1), max(y0, y1)
        parent.add_polygon(
            [(x0 - trace_width / 2, ylo),
             (x0 + trace_width / 2, ylo),
             (x0 + trace_width / 2, yhi),
             (x0 - trace_width / 2, yhi)],
            layer=layer,
        )

    _add_stiction_anchor(parent, x1, y1, anchor_size)


def make_switch_array_bistable(
    nrows: int = NROWS,
    ncols: int = NCOLS,
    pitch: float = PITCH,
    stub_length: float = 20.0,
) -> gf.Component:
    """Bistable MEMS switch array with per-cell stub interconnects.

    Places padless bistable switch cells at ``pitch`` spacing. Each cell
    gets 4 short stub traces extending away from cell center:

    - Upper CCS spring anchor: vertical stub going UP
    - Lower CCS spring anchor: vertical stub going DOWN
    - Right comb anchor: horizontal stub going RIGHT
    - Left comb anchor: horizontal stub going LEFT

    Each stub has a stiction-prevention anchor at its endpoint.  Stubs
    are disconnected between cells.

    Args:
        nrows: Number of rows.
        ncols: Number of columns.
        pitch: Center-to-center spacing (um).
        stub_length: Length of each routing stub (um).
    """
    array = gf.Component()

    cell = make_switch_cell_bistable_padless()

    cp = _get_bistable_cell_connection_points()

    for row in range(nrows):
        for col in range(ncols):
            cx = col * pitch
            cy = row * pitch

            ref = array.add_ref(cell)
            ref.dmovex(cx)
            ref.dmovey(cy)

            # Upper CCS spring anchor -> stub going UP
            _add_stub(
                array,
                cx, cy + cp["spring_anchor_top"],
                cx, cy + cp["spring_anchor_top"] + stub_length,
            )

            # Lower CCS spring anchor -> stub going DOWN
            _add_stub(
                array,
                cx, cy + cp["spring_anchor_bot"],
                cx, cy + cp["spring_anchor_bot"] - stub_length,
            )

            # Right comb anchor -> stub going RIGHT
            _add_stub(
                array,
                cx + cp["comb_right_edge"], cy + cp["comb_anchor_cy"],
                cx + cp["comb_right_edge"] + stub_length, cy + cp["comb_anchor_cy"],
            )

            # Left comb anchor -> stub going LEFT
            _add_stub(
                array,
                cx + cp["comb_left_edge"], cy + cp["comb_anchor_cy"],
                cx + cp["comb_left_edge"] - stub_length, cy + cp["comb_anchor_cy"],
            )

    return array


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK

    PDK.activate()

    arr = make_switch_array_bistable()
    bb = arr.dbbox()
    print(f"Bistable array size: {bb.width():.0f} x {bb.height():.0f} um")
    arr.write_gds("../../../layouts/switch_array_bistable_8x8.gds")
    arr.show()
