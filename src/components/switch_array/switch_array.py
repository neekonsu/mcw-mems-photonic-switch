"""8x8 MEMS switch array with routed interconnects.

Places 1.75x-scale single-comb switch cells in an 8x8 grid at 250 um pitch.
Routes POLY_MEMS interconnects to spring anchors (row buses) and comb drive
fixed anchors (column buses), with 10x10 um stiction-prevention anchors
every 100 um along each route.
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


_shuttle_beam = _import_from("shuttle_beam/shuttle_beam.py", "_arr_shuttle_beam")
_folded_spring = _import_from("folded_spring/folded_spring.py", "_arr_folded_spring")
_comb_drive = _import_from("comb_drive/comb_drive.py", "_arr_comb_drive")
_anchor_mod = _import_from("anchor/anchor.py", "_arr_anchor")

make_proofmass = _shuttle_beam.make_proofmass
make_spring_pair = _folded_spring.make_spring_pair
make_comb_drive = _comb_drive.make_comb_drive
make_mems_anchor = _anchor_mod.make_mems_anchor

# ---------------------------------------------------------------------------
# Scale factor (same as mems_switch_cell_large)
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
ANCHOR_HOLE_MAX = 2.0  # um, hole size inside stiction anchor
ANCHOR_LINEWIDTH = 0.8  # um, rib width inside stiction anchor
ANCHOR_OVER_TOP = 0.3  # um, POLY_TOP overhang
ANCHOR_OVER_BOT = 0.5  # um, SI_FULL overhang


# ---------------------------------------------------------------------------
# Padless switch cell (omits the large upper/lower pads so cell fits pitch)
# ---------------------------------------------------------------------------
@gf.cell
def make_switch_cell_padless(
    proof_length: float = 7.0 * S,
    proof_height: float = 120.0 * S,
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    spring_length: float = 30.0 * S,
    spring_width: float = 0.5,
    spring_gap: float = 5.0 * S,
    pad_length: float = 8.0 * S,
    pad_width: float = 0.8,
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
    spring_edge_upper: float = 1.0 * S,
    spring_edge_lower: float = 1.0 * S,
    comb_edge_lower: float = 5.0 * S,
    anchor_edge_upper: float = 1.0 * S,
    anchor_edge_lower: float = 1.0 * S,
    anchor_width_upper: float = 5.0 * S,
    anchor_width_lower: float = 5.0 * S,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """1.75x switch cell without large pads (fits 250 um pitch).

    Same as make_switch_mems_large but omits the large upper/lower pad
    anchors. The spring anchor strips remain as routing targets.
    Height ~239 um (vs 342 um with pads).
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

    # Springs
    spring = make_spring_pair(
        spring_length, spring_width, spring_gap, proof_length, pad_length, pad_width, layer
    )
    spring_upper = switch.add_ref(spring)
    spring_upper.dmirror_y()
    spring_upper.dmovey(proof_height / 2 - spring_width - spring_edge_upper)

    spring_lower = switch.add_ref(spring)
    spring_lower.dmovey(-proof_height / 2 + spring_width + spring_edge_lower)

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

    # Spring anchor strips (no large pads)
    anchor_upper = make_mems_anchor(
        proof_length, anchor_width_upper + holder_linewidth,
        holder_gap_min, holder_linewidth, holder_top_over, holder_bottom_over,
    )
    au = switch.add_ref(anchor_upper)
    au.dmovey(
        anchor_width_upper / 2 + proof_height / 2
        - spring_edge_upper + spring_gap - anchor_edge_upper
    )

    anchor_lower = make_mems_anchor(
        proof_length, anchor_width_lower + holder_linewidth,
        holder_gap_min, holder_linewidth, holder_top_over, holder_bottom_over,
    )
    al = switch.add_ref(anchor_lower)
    al.dmovey(
        -anchor_width_lower / 2 - proof_height / 2
        + spring_edge_lower - spring_gap + anchor_edge_lower
    )

    return switch


def _get_cell_connection_points():
    """Compute connection point offsets relative to cell center.

    Returns dict with keys:
        spring_upper_y:    y-center of upper spring anchor strip
        spring_lower_y:    y-center of lower spring anchor strip
        spring_anchor_top: y of upper anchor top edge
        spring_anchor_bot: y of lower anchor bottom edge
        comb_right_cx:     x-center of right comb fixed anchor
        comb_left_cx:      x-center of left comb fixed anchor
        comb_anchor_cy:    y-center of comb fixed anchors
        comb_anchor_top:   y of comb fixed anchor top edge
        comb_anchor_bot:   y of comb fixed anchor bottom edge
    """
    p_r = 5.0 + 0.8  # hole_diameter + hole_gap
    proof_height = int((120.0 * S - 0.8) / p_r) * p_r + 0.8  # ~209.6
    proof_length = int((7.0 * S - 0.8) / p_r) * p_r + 0.8    # ~6.6

    spring_edge = 1.0 * S
    spring_gap = 5.0 * S
    anchor_edge = 1.0 * S
    anchor_width = 5.0 * S
    holder_linewidth = 0.8
    comb_edge_lower = 5.0 * S

    # Spring anchor strip center y
    spring_upper_y = (
        anchor_width / 2 + proof_height / 2
        - spring_edge + spring_gap - anchor_edge
    )
    spring_lower_y = (
        -anchor_width / 2 - proof_height / 2
        + spring_edge - spring_gap + anchor_edge
    )

    anchor_half_h = (anchor_width + holder_linewidth) / 2
    spring_anchor_top = spring_upper_y + anchor_half_h + 0.3  # + over_top
    spring_anchor_bot = spring_lower_y - anchor_half_h - 0.3

    # Comb drive fixed anchor position
    # Comb origin: x = proof_length/2, y = -proof_height/2 + comb_edge_lower
    finger_width = 0.5
    finger_gap = 0.5
    finger_length = 5.0 * S
    finger_distance = 3.0 * S
    num_pair = round(20 * S)
    edge_fixed = 1.0
    holder_width_move = 3.0 * S
    holder_width_fixed = 20.0 * S

    # Holder distance (auto-computed)
    L_comb = num_pair * 2 * (finger_width + finger_gap) + finger_width + 2 * edge_fixed
    W_comb = holder_width_move - holder_linewidth
    N_comb = math.ceil(L_comb / W_comb)
    holder_distance = N_comb * W_comb - L_comb

    # Fixed anchor center within comb drive (comb origin at (0,0))
    l_hf = 2 * num_pair * (finger_width + finger_gap)
    comb_anchor_local_x = l_hf / 2 + holder_distance + edge_fixed + finger_width
    comb_anchor_local_y = holder_width_fixed / 2 + holder_width_move + finger_length + finger_distance

    # Global position of right comb's fixed anchor
    comb_origin_x = proof_length / 2
    comb_origin_y = -proof_height / 2 + comb_edge_lower
    comb_right_cx = comb_origin_x + comb_anchor_local_x
    comb_anchor_cy = comb_origin_y + comb_anchor_local_y
    comb_left_cx = -(comb_origin_x + comb_anchor_local_x)

    comb_anchor_top = comb_anchor_cy + holder_width_fixed / 2 + 0.3
    comb_anchor_bot = comb_anchor_cy - holder_width_fixed / 2 - 0.3

    # Comb anchor POLY_MEMS x-edges (for stub routing)
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


def _add_trace_with_anchors(
    parent: gf.Component,
    x0: float, y0: float,
    x1: float, y1: float,
    trace_width: float = TRACE_WIDTH,
    anchor_size: float = ANCHOR_SIZE,
    anchor_pitch: float = ANCHOR_PITCH,
    layer=LAYER.POLY_MEMS,
):
    """Add a straight POLY_MEMS trace with stiction-prevention anchors.

    Draws a rectangle from (x0,y0) to (x1,y1) on the structural layer,
    then places 3-layer MEMS anchors (POLY_TOP + POLY_MEMS + SI_FULL)
    at regular intervals along the trace to prevent stiction.

    The trace can be horizontal (y0==y1) or vertical (x0==x1).
    """
    is_horizontal = abs(y1 - y0) < 0.01
    is_vertical = abs(x1 - x0) < 0.01

    if is_horizontal:
        xlo, xhi = min(x0, x1), max(x0, x1)
        trace_length = xhi - xlo
        # Draw trace
        parent.add_polygon(
            [(xlo, y0 - trace_width / 2),
             (xhi, y0 - trace_width / 2),
             (xhi, y0 + trace_width / 2),
             (xlo, y0 + trace_width / 2)],
            layer=layer,
        )
        # Stiction anchors
        n_anchors = max(2, int(trace_length / anchor_pitch) + 1)
        if trace_length > 0:
            spacing = trace_length / (n_anchors - 1) if n_anchors > 1 else 0
        else:
            spacing = 0
        for i in range(n_anchors):
            ax = xlo + i * spacing
            _add_stiction_anchor(parent, ax, y0, anchor_size)

    elif is_vertical:
        ylo, yhi = min(y0, y1), max(y0, y1)
        trace_length = yhi - ylo
        # Draw trace
        parent.add_polygon(
            [(x0 - trace_width / 2, ylo),
             (x0 + trace_width / 2, ylo),
             (x0 + trace_width / 2, yhi),
             (x0 - trace_width / 2, yhi)],
            layer=layer,
        )
        # Stiction anchors
        n_anchors = max(2, int(trace_length / anchor_pitch) + 1)
        if trace_length > 0:
            spacing = trace_length / (n_anchors - 1) if n_anchors > 1 else 0
        else:
            spacing = 0
        for i in range(n_anchors):
            ay = ylo + i * spacing
            _add_stiction_anchor(parent, x0, ay, anchor_size)


def _add_stiction_anchor(parent, cx, cy, size=ANCHOR_SIZE):
    """Place a 3-layer stiction-prevention anchor at (cx, cy).

    Layers: POLY_TOP cap + POLY_MEMS solid square + SI_FULL base.
    Simple solid squares (no internal grid) since anchors are small.
    """
    hs = size / 2
    over_top = ANCHOR_OVER_TOP
    over_bot = ANCHOR_OVER_BOT

    # POLY_TOP (slightly larger)
    parent.add_polygon(
        [(cx - hs - over_top, cy - hs - over_top),
         (cx + hs + over_top, cy - hs - over_top),
         (cx + hs + over_top, cy + hs + over_top),
         (cx - hs - over_top, cy + hs + over_top)],
        layer=LAYER.POLY_TOP,
    )
    # POLY_MEMS
    parent.add_polygon(
        [(cx - hs, cy - hs),
         (cx + hs, cy - hs),
         (cx + hs, cy + hs),
         (cx - hs, cy + hs)],
        layer=LAYER.POLY_MEMS,
    )
    # SI_FULL (slightly larger)
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
    """Draw a short trace stub with a stiction anchor at the endpoint (x1, y1).

    The stub is a straight horizontal or vertical POLY_MEMS trace.
    A single 3-layer stiction anchor is placed at the far end.
    """
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


def make_switch_array(
    nrows: int = NROWS,
    ncols: int = NCOLS,
    pitch: float = PITCH,
    stub_length: float = 20.0,
) -> gf.Component:
    """MEMS switch array with per-cell stub interconnects.

    Places padless switch cells at ``pitch`` spacing. Each cell gets 4 short
    stub traces extending away from cell center:

    - Upper spring anchor: vertical stub going UP
    - Lower spring anchor: vertical stub going DOWN
    - Right comb anchor: horizontal stub going RIGHT
    - Left comb anchor: horizontal stub going LEFT

    Each stub has a stiction-prevention anchor at its endpoint. Stubs are
    disconnected between cells — no shared buses.

    Args:
        nrows: Number of rows.
        ncols: Number of columns.
        pitch: Center-to-center spacing (um).
        stub_length: Length of each routing stub (um).
    """
    array = gf.Component()

    # Build the padless cell once
    cell = make_switch_cell_padless()

    # Connection point offsets (relative to cell center)
    cp = _get_cell_connection_points()

    for row in range(nrows):
        for col in range(ncols):
            cx = col * pitch
            cy = row * pitch

            # Place cell
            ref = array.add_ref(cell)
            ref.dmovex(cx)
            ref.dmovey(cy)

            # Upper spring anchor → stub going UP
            _add_stub(
                array,
                cx, cy + cp["spring_anchor_top"],
                cx, cy + cp["spring_anchor_top"] + stub_length,
            )

            # Lower spring anchor → stub going DOWN
            _add_stub(
                array,
                cx, cy + cp["spring_anchor_bot"],
                cx, cy + cp["spring_anchor_bot"] - stub_length,
            )

            # Right comb anchor → stub going RIGHT
            _add_stub(
                array,
                cx + cp["comb_right_edge"], cy + cp["comb_anchor_cy"],
                cx + cp["comb_right_edge"] + stub_length, cy + cp["comb_anchor_cy"],
            )

            # Left comb anchor → stub going LEFT
            _add_stub(
                array,
                cx + cp["comb_left_edge"], cy + cp["comb_anchor_cy"],
                cx + cp["comb_left_edge"] - stub_length, cy + cp["comb_anchor_cy"],
            )

    return array


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()

    arr = make_switch_array()
    bb = arr.dbbox()
    print(f"Array size: {bb.width():.0f} x {bb.height():.0f} um")
    arr.write_gds("../../../layouts/switch_array_8x8.gds")
    arr.show()
