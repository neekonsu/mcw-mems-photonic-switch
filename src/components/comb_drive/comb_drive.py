"""Comb drive components for MEMS electrostatic actuator.

Provides interdigitated finger pairs and complete comb drive assemblies
(movable holder + fingers + fixed anchor).

Adapted from Sirui's reference design (draw_finger_pair, draw_comb_drive,
draw_comb_drive_cut).
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


_shuttle_beam = _import_from("shuttle_beam/shuttle_beam.py", "_comb_shuttle_beam")
_anchor = _import_from("anchor/anchor.py", "_comb_anchor")

make_proofmass_side = _shuttle_beam.make_proofmass_side
make_mems_anchor = _anchor.make_mems_anchor
make_mems_anchor_cut = _anchor.make_mems_anchor_cut


@gf.cell
def make_finger_pair(
    finger_length: float = 5.0,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 2.0,
    num_pair: int = 25,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Interdigitated finger pair array.

    Creates ``num_pair`` pairs of interleaved fingers plus one extra finger.
    Moving fingers are at y=0, fixed fingers are offset by ``finger_distance``.

    Both moving and fixed fingers use the same layer (POLY_MEMS) since they
    are on the same structural poly-Si, just differentiated by whether they
    are anchored or released.

    Origin at bottom-left of the first moving finger.

    Args:
        finger_length:   Length of each finger (um).
        finger_width:    Width of each finger (um).
        finger_gap:      Gap between adjacent fingers (um).
        finger_distance: Vertical overlap/offset between moving and fixed fingers (um).
        num_pair:        Number of finger pairs.
        layer:           GDS layer.
    """
    l_f = finger_length
    w_f = finger_width
    g_f = finger_gap
    d_f = finger_distance

    finger_pair = gf.Component()

    for ii in range(num_pair):
        # Moving finger
        left_finger_temp = gf.components.rectangle(size=(w_f, l_f), layer=layer)
        left_finger = finger_pair.add_ref(left_finger_temp)
        left_finger.dmovex(ii * 2 * (w_f + g_f))

        # Fixed finger (offset by finger_distance)
        right_finger_temp = gf.components.rectangle(size=(w_f, l_f), layer=layer)
        right_finger = finger_pair.add_ref(right_finger_temp)
        right_finger.dmovex(ii * 2 * (w_f + g_f) + w_f + g_f)
        right_finger.dmovey(d_f)

    # Extra moving finger at the end
    extra_temp = gf.components.rectangle(size=(w_f, l_f), layer=layer)
    extra = finger_pair.add_ref(extra_temp)
    extra.dmovex(num_pair * 2 * (w_f + g_f))

    return finger_pair


@gf.cell
def make_comb_drive(
    finger_length: float = 5.0,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 2.0,
    num_pair: int = 25,
    edge_fixed: float = 1.0,
    holder_distance: float = 0.0,
    holder_linewidth: float = 0.8,
    holder_width_move: float = 3.0,
    holder_width_fixed: float = 15.0,
    holder_gap_min: float = 2.0,
    holder_top_over: float = 0.3,
    holder_bottom_over: float = 0.5,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Complete comb drive: movable holder + fingers + fixed anchor.

    The movable holder is a side-aligned proof mass strip at the bottom.
    Fingers extend upward from the holder. The fixed anchor (3-layer
    MEMS anchor) sits above the fingers.

    Origin at bottom-left of the movable holder.

    Args:
        finger_length:    Finger length (um).
        finger_width:     Finger width (um).
        finger_gap:       Gap between fingers (um).
        finger_distance:  Vertical offset between moving/fixed fingers (um).
        num_pair:         Number of finger pairs.
        edge_fixed:       Extra space at finger array edges (um).
        holder_distance:  Horizontal distance from holder start to finger array (um).
        holder_linewidth: Rib width of the movable holder (um).
        holder_width_move: Height of the movable holder strip (um).
        holder_width_fixed: Height of the fixed anchor (um).
        holder_gap_min:   Hole size parameter for anchors (um).
        holder_top_over:  POLY_TOP overhang of fixed anchor (um).
        holder_bottom_over: SI_FULL overhang of fixed anchor (um).
        layer:            GDS layer for structural poly.
    """
    w_f = finger_width
    g_f = finger_gap
    w_hm = holder_width_move
    w_h = holder_linewidth

    comb_drive = gf.Component()

    # Movable holder (side-aligned proof mass strip)
    hole_diameter = w_hm - 2 * w_h
    holder_length = num_pair * 2 * (w_f + g_f) + w_f + 2 * edge_fixed + holder_distance
    holder_move_temp = make_proofmass_side(
        holder_length, w_hm, hole_diameter, w_h, layer
    )
    holder_move = comb_drive.add_ref(holder_move_temp)
    holder_move.dmovey(w_hm / 2)

    # Fingers
    fingers_temp = make_finger_pair(
        finger_length, finger_width, finger_gap, finger_distance, num_pair, layer
    )
    fingers = comb_drive.add_ref(fingers_temp)
    fingers.dmovex(holder_distance + edge_fixed)
    fingers.dmovey(w_hm)

    # Fixed anchor (3-layer)
    l_hf = 2 * num_pair * (w_f + g_f)
    holder_fixed_temp = make_mems_anchor(
        l_hf, holder_width_fixed, holder_gap_min, holder_linewidth,
        holder_top_over, holder_bottom_over,
    )
    holder_fixed = comb_drive.add_ref(holder_fixed_temp)
    holder_fixed.dmovex(l_hf / 2 + holder_distance + edge_fixed + w_f)
    holder_fixed.dmovey(holder_width_fixed / 2 + w_hm + finger_length + finger_distance)

    return comb_drive


@gf.cell
def make_comb_drive_cut(
    finger_length: float = 5.0,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 2.0,
    num_pair: int = 25,
    edge_fixed: float = 1.0,
    holder_distance: float = 0.0,
    holder_linewidth: float = 0.8,
    holder_width_move: float = 3.0,
    holder_width_fixed: float = 15.0,
    holder_fixed_leftcut: float = 20.0,
    holder_fixed_topcut: float = 10.0,
    holder_gap_min: float = 2.0,
    holder_top_over: float = 0.3,
    holder_bottom_over: float = 0.5,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Comb drive with corner-cut fixed anchor.

    Same as make_comb_drive but the fixed anchor has a triangular corner
    chamfer and is x-mirrored.

    Args:
        (same as make_comb_drive, plus:)
        holder_fixed_leftcut: Horizontal extent of anchor corner cut (um).
        holder_fixed_topcut:  Vertical extent of anchor corner cut (um).
    """
    w_f = finger_width
    g_f = finger_gap
    w_hm = holder_width_move
    w_h = holder_linewidth

    comb_drive = gf.Component()

    # Movable holder
    hole_diameter = w_hm - 2 * w_h
    holder_length = num_pair * 2 * (w_f + g_f) + w_f + 2 * edge_fixed + holder_distance
    holder_move_temp = make_proofmass_side(
        holder_length, w_hm, hole_diameter, w_h, layer
    )
    holder_move = comb_drive.add_ref(holder_move_temp)
    holder_move.dmovey(w_hm / 2)

    # Fingers
    fingers_temp = make_finger_pair(
        finger_length, finger_width, finger_gap, finger_distance, num_pair, layer
    )
    fingers = comb_drive.add_ref(fingers_temp)
    fingers.dmovex(holder_distance + edge_fixed)
    fingers.dmovey(w_hm)

    # Fixed anchor (3-layer, with corner cut, x-mirrored)
    l_hf = 2 * num_pair * (w_f + g_f)
    holder_fixed_temp = make_mems_anchor_cut(
        l_hf, holder_width_fixed, holder_fixed_leftcut, holder_fixed_topcut,
        holder_gap_min, holder_linewidth, holder_top_over, holder_bottom_over,
    )
    holder_fixed = comb_drive.add_ref(holder_fixed_temp)
    holder_fixed.dmirror_x()
    holder_fixed.dmovex(l_hf / 2 + holder_distance + edge_fixed + w_f)
    holder_fixed.dmovey(holder_width_fixed / 2 + w_hm + finger_length + finger_distance)

    return comb_drive


if __name__ == "__main__":
    import math
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()

    # Test parameters from reference
    finger_length = 5; finger_width = 0.3; finger_gap = 0.3
    finger_distance = 1; num_pair = 30
    edge_fixed = 1; holder_linewidth = 0.5
    holder_width_move = 3; holder_width_fixed = 5
    holder_gap_min = 1; holder_top_over = 0.3; holder_bottom_over = 0.3

    L = num_pair * 2 * (finger_width + finger_gap) + finger_width + 2 * edge_fixed
    W = holder_width_move - holder_linewidth
    N = math.ceil(L / W)
    holder_distance = N * W - L

    cd = make_comb_drive(
        finger_length, finger_width, finger_gap, finger_distance, num_pair,
        edge_fixed, holder_distance, holder_linewidth, holder_width_move,
        holder_width_fixed, holder_gap_min, holder_top_over, holder_bottom_over,
    )
    cd.show()
