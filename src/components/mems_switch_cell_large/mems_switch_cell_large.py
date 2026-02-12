"""MEMS switch cell assembly — 1.75x scaled variant.

Same design as mems_switch_cell but with macro dimensions scaled by 1.75x
(75% larger overall cell). Minor/process-constrained dimensions (etch hole
size, web widths, finger cross-section, structural linewidths, layer
overhangs) are preserved.

Scaling philosophy:
    SCALED (x1.75): proof mass dimensions, spring length/gap, finger length,
        number of finger pairs, holder heights, anchor widths, pad sizes,
        inter-comb spacing, edge insets, finger distance
    FIXED: hole_diameter, hole_gap, finger_width, finger_gap, spring_width,
        holder_linewidth, holder_gap_min, holder_top_over, holder_bottom_over,
        anchor_SOI_over, edge_fixed, pad_width (spring connector)
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
    """Import a module from a relative file path, avoiding name collisions."""
    path = os.path.normpath(os.path.join(_comp_dir, rel_path))
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_shuttle_beam = _import_from("shuttle_beam/shuttle_beam.py", "_lg_shuttle_beam")
_folded_spring = _import_from("folded_spring/folded_spring.py", "_lg_folded_spring")
_comb_drive = _import_from("comb_drive/comb_drive.py", "_lg_comb_drive")
_anchor = _import_from("anchor/anchor.py", "_lg_anchor")

make_proofmass = _shuttle_beam.make_proofmass
make_spring_pair = _folded_spring.make_spring_pair
make_comb_drive = _comb_drive.make_comb_drive
make_comb_drive_cut = _comb_drive.make_comb_drive_cut
make_mems_anchor = _anchor.make_mems_anchor

# ---------------------------------------------------------------------------
# Scale factor
# ---------------------------------------------------------------------------
S = 1.75  # 75% larger


@gf.cell
def make_switch_mems_large(
    # --- Proof mass (SCALED) ---
    proof_length: float = 7.0 * S,
    proof_height: float = 120.0 * S,
    # --- Etch holes (FIXED) ---
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    # --- Springs (length/gap SCALED, width FIXED) ---
    spring_length: float = 30.0 * S,
    spring_width: float = 0.5,
    spring_gap: float = 5.0 * S,
    pad_length: float = 8.0 * S,
    pad_width: float = 0.8,
    # --- Fingers (length SCALED, width/gap FIXED, count SCALED) ---
    finger_length: float = 5.0 * S,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 3.0 * S,
    num_pair: int = round(20 * S),
    # --- Comb holder (linewidth FIXED, heights SCALED) ---
    edge_fixed: float = 1.0,
    holder_distance: float = 0.0,
    holder_linewidth: float = 0.8,
    holder_width_move: float = 3.0 * S,
    holder_width_fixed: float = 20.0 * S,
    # --- Anchor internals (FIXED) ---
    holder_gap_min: float = 2.0,
    holder_top_over: float = 0.3,
    holder_bottom_over: float = 0.3,
    # --- Layout offsets (SCALED) ---
    spring_edge_upper: float = 1.0 * S,
    spring_edge_lower: float = 1.0 * S,
    comb_edge_lower: float = 5.0 * S,
    anchor_edge_upper: float = 1.0 * S,
    anchor_edge_lower: float = 1.0 * S,
    anchor_width_upper: float = 5.0 * S,
    anchor_width_lower: float = 5.0 * S,
    # --- Pads (SCALED) ---
    pad_length_upper: float = 30.0 * S,
    pad_width_upper: float = 30.0 * S,
    pad_length_lower: float = 30.0 * S,
    pad_width_lower: float = 30.0 * S,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Single-comb-pair MEMS switch cell, 1.75x scale.

    Identical topology to make_switch_mems() but with macro dimensions
    scaled by 1.75x. Process-constrained dimensions (etch holes, finger
    cross-section, structural linewidths, layer overhangs) are unchanged.
    """
    # Snap proof mass dimensions to hole grid
    p_r = hole_diameter + hole_gap
    proof_length = int((proof_length - hole_gap) / p_r) * p_r + hole_gap
    proof_height = int((proof_height - hole_gap) / p_r) * p_r + hole_gap

    # Auto-compute holder_distance
    if holder_distance == 0:
        L = num_pair * 2 * (finger_width + finger_gap) + finger_width + 2 * edge_fixed
        W = holder_width_move - holder_linewidth
        N = math.ceil(L / W)
        holder_distance = N * W - L

    switch = gf.Component()

    # Proof mass
    pm = make_proofmass(proof_length, proof_height, hole_diameter, hole_gap, layer)
    switch.add_ref(pm)

    # Upper spring (mirrored in y)
    spring = make_spring_pair(
        spring_length, spring_width, spring_gap, proof_length, pad_length, pad_width, layer
    )
    spring_upper = switch.add_ref(spring)
    spring_upper.dmirror_y()
    spring_upper.dmovey(proof_height / 2 - spring_width - spring_edge_upper)

    # Lower spring
    spring_lower = switch.add_ref(spring)
    spring_lower.dmovey(-proof_height / 2 + spring_width + spring_edge_lower)

    # Comb drives (right and left, mirrored)
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

    # Upper anchor
    anchor_upper = make_mems_anchor(
        proof_length, anchor_width_upper + holder_linewidth,
        holder_gap_min, holder_linewidth, holder_top_over, holder_bottom_over,
    )
    au = switch.add_ref(anchor_upper)
    au.dmovey(
        anchor_width_upper / 2 + proof_height / 2
        - spring_edge_upper + spring_gap - anchor_edge_upper
    )

    # Upper pad
    pad_upper = make_mems_anchor(
        pad_length_upper, pad_width_upper,
        holder_gap_min, holder_linewidth, holder_top_over, holder_bottom_over,
    )
    pu = switch.add_ref(pad_upper)
    pu.dmovey(
        pad_width_upper / 2 - holder_linewidth / 2
        + proof_height / 2 - spring_edge_upper + spring_gap
        - anchor_edge_upper + anchor_width_upper
    )

    # Lower anchor
    anchor_lower = make_mems_anchor(
        proof_length, anchor_width_lower + holder_linewidth,
        holder_gap_min, holder_linewidth, holder_top_over, holder_bottom_over,
    )
    al = switch.add_ref(anchor_lower)
    al.dmovey(
        -anchor_width_lower / 2 - proof_height / 2
        + spring_edge_lower - spring_gap + anchor_edge_lower
    )

    # Lower pad
    pad_lower = make_mems_anchor(
        pad_length_lower, pad_width_lower,
        holder_gap_min, holder_linewidth, holder_top_over, holder_bottom_over,
    )
    pl = switch.add_ref(pad_lower)
    pl.dmovey(
        -pad_width_lower / 2 + holder_linewidth / 2
        - proof_height / 2 + spring_edge_lower - spring_gap
        + anchor_edge_lower - anchor_width_lower
    )

    return switch


@gf.cell
def make_switch_mems_multi_large(
    # --- Proof mass (SCALED) ---
    proof_length: float = 7.0 * S,
    proof_height: float = 110.0 * S,
    # --- Etch holes (FIXED) ---
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    # --- Springs (length/gap SCALED, width FIXED) ---
    spring_length: float = 45.0 * S,
    spring_width: float = 0.5,
    spring_gap: float = 5.0 * S,
    pad_length: float = 8.0 * S,
    pad_width: float = 0.8,
    # --- Comb groups ---
    num_combs: int = 3,
    # --- Fingers (length SCALED, width/gap FIXED) ---
    finger_length: float = 4.0 * S,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 2.0 * S,
    num_pair_array: list | None = None,
    edge_fixed_array: list | None = None,
    holder_distance_array: list | None = None,
    # --- Comb holder (linewidth FIXED, heights SCALED) ---
    holder_linewidth: float = 0.8,
    holder_width_move_array: list | None = None,
    holder_width_fixed_array: list | None = None,
    # --- Anchor internals (FIXED) ---
    holder_gap_min: float = 2.0,
    holder_top_over_array: list | None = None,
    holder_bottom_over_array: list | None = None,
    # --- Layout offsets (SCALED) ---
    spring_edge_upper: float = 1.0 * S,
    spring_edge_lower: float = 1.0 * S,
    comb_edge_lower_array: list | None = None,
    anchor_edge_upper: float = 1.0 * S,
    anchor_edge_lower: float = 1.0 * S,
    anchor_width_upper: float = 5.0 * S,
    anchor_width_lower: float = 5.0 * S,
    # --- Anchor layer overhangs (FIXED) ---
    anchor_SOI_over: float = 4.0,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Multi-comb-group MEMS switch cell, 1.75x scale.

    Identical topology to make_switch_mems_multi() but with macro dimensions
    scaled by 1.75x. Process-constrained dimensions are unchanged.
    """
    # Defaults (num_pair SCALED, overhangs FIXED)
    if num_pair_array is None:
        num_pair_array = [round(25 * S)] * num_combs
    if edge_fixed_array is None:
        edge_fixed_array = [1.0] * num_combs
    if holder_width_move_array is None:
        holder_width_move_array = [3.0 * S] * num_combs
    if holder_width_fixed_array is None:
        holder_width_fixed_array = [15.0 * S] * num_combs
    if holder_top_over_array is None:
        holder_top_over_array = [0.3] * num_combs
    if holder_bottom_over_array is None:
        holder_bottom_over_array = [0.5] * num_combs
    if comb_edge_lower_array is None:
        comb_edge_lower_array = [4 * S + 30 * S * i for i in range(num_combs)]

    # Auto-compute holder distances
    if holder_distance_array is None:
        holder_distance_array = [0.0] * num_combs
    for ii in range(num_combs):
        if holder_distance_array[ii] == 0:
            L = (num_pair_array[ii] * 2 * (finger_width + finger_gap)
                 + finger_width + 2 * edge_fixed_array[ii])
            W = holder_width_move_array[ii] - holder_linewidth
            N = math.ceil(L / W)
            holder_distance_array[ii] = N * W - L

    # Snap proof mass dimensions
    p_r = hole_diameter + hole_gap
    proof_length = int((proof_length - hole_gap) / p_r) * p_r + hole_gap
    proof_height = int((proof_height - hole_gap) / p_r) * p_r + hole_gap

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

    # Comb drive groups
    for ii in range(num_combs):
        comb = make_comb_drive(
            finger_length, finger_width, finger_gap, finger_distance,
            num_pair_array[ii], edge_fixed_array[ii], holder_distance_array[ii],
            holder_linewidth, holder_width_move_array[ii], holder_width_fixed_array[ii],
            holder_gap_min, holder_top_over_array[ii], holder_bottom_over_array[ii], layer,
        )
        comb_right = switch.add_ref(comb)
        comb_right.dmovex(proof_length / 2)
        comb_right.dmovey(-proof_height / 2 + comb_edge_lower_array[ii])

        comb_left = switch.add_ref(comb)
        comb_left.dmirror_x()
        comb_left.dmovex(-proof_length / 2)
        comb_left.dmovey(-proof_height / 2 + comb_edge_lower_array[ii])

    # Upper anchor
    anchor_upper = make_mems_anchor(
        proof_length, anchor_width_upper + holder_linewidth,
        holder_gap_min, holder_linewidth, holder_top_over_array[0], anchor_SOI_over,
    )
    au = switch.add_ref(anchor_upper)
    au.dmovey(
        anchor_width_upper / 2 + proof_height / 2
        - spring_edge_upper + spring_gap - anchor_edge_upper
    )

    # Lower anchor
    anchor_lower = make_mems_anchor(
        proof_length, anchor_width_lower + holder_linewidth,
        holder_gap_min, holder_linewidth, holder_top_over_array[0], anchor_SOI_over,
    )
    al = switch.add_ref(anchor_lower)
    al.dmovey(
        -anchor_width_lower / 2 - proof_height / 2
        + spring_edge_lower - spring_gap + anchor_edge_lower
    )

    return switch


@gf.cell
def make_switch_mems_cut_large(
    # --- Proof mass (SCALED) ---
    proof_length: float = 7.0 * S,
    proof_height: float = 110.0 * S,
    # --- Etch holes (FIXED) ---
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    # --- Springs (length/gap SCALED, width FIXED) ---
    spring_length: float = 45.0 * S,
    spring_width: float = 0.5,
    spring_gap: float = 5.0 * S,
    pad_length: float = 8.0 * S,
    pad_width: float = 0.8,
    # --- Comb groups ---
    num_combs: int = 3,
    # --- Fingers (length SCALED, width/gap FIXED) ---
    finger_length: float = 4.0 * S,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 2.0 * S,
    num_pair_array: list | None = None,
    edge_fixed_array: list | None = None,
    holder_distance_array: list | None = None,
    # --- Comb holder (linewidth FIXED, heights SCALED) ---
    holder_linewidth: float = 0.8,
    holder_width_move_array: list | None = None,
    holder_width_fixed_array: list | None = None,
    holder_fixed_leftcut_array: list | None = None,
    holder_fixed_topcut_array: list | None = None,
    shape_code_array: list | None = None,
    # --- Anchor internals (FIXED) ---
    holder_gap_min: float = 2.0,
    holder_top_over_array: list | None = None,
    holder_bottom_over_array: list | None = None,
    # --- Layout offsets (SCALED) ---
    spring_edge_upper: float = 1.0 * S,
    spring_edge_lower: float = 1.0 * S,
    comb_edge_lower_array: list | None = None,
    anchor_edge_upper: float = 1.0 * S,
    anchor_edge_lower: float = 1.0 * S,
    anchor_width_upper: float = 5.0 * S,
    anchor_width_lower: float = 5.0 * S,
    # --- Anchor layer overhangs (FIXED) ---
    anchor_SOI_over: float = 4.0,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Multi-comb MEMS switch with optional corner-cut anchors, 1.75x scale.

    Identical topology to make_switch_mems_cut() but with macro dimensions
    scaled by 1.75x.
    """
    # Defaults
    if num_pair_array is None:
        num_pair_array = [round(25 * S)] * num_combs
    if edge_fixed_array is None:
        edge_fixed_array = [1.0] * num_combs
    if holder_width_move_array is None:
        holder_width_move_array = [3.0 * S] * num_combs
    if holder_width_fixed_array is None:
        holder_width_fixed_array = [15.0 * S] * num_combs
    if holder_top_over_array is None:
        holder_top_over_array = [0.3] * num_combs
    if holder_bottom_over_array is None:
        holder_bottom_over_array = [0.5] * num_combs
    if comb_edge_lower_array is None:
        comb_edge_lower_array = [4 * S + 30 * S * i for i in range(num_combs)]
    if shape_code_array is None:
        shape_code_array = [0] * num_combs
    if holder_fixed_leftcut_array is None:
        holder_fixed_leftcut_array = [0.0] * num_combs
    if holder_fixed_topcut_array is None:
        holder_fixed_topcut_array = [0.0] * num_combs

    # Auto-compute holder distances
    if holder_distance_array is None:
        holder_distance_array = [0.0] * num_combs
    for ii in range(num_combs):
        if holder_distance_array[ii] == 0:
            L = (num_pair_array[ii] * 2 * (finger_width + finger_gap)
                 + finger_width + 2 * edge_fixed_array[ii])
            W = holder_width_move_array[ii] - holder_linewidth
            N = math.ceil(L / W)
            holder_distance_array[ii] = N * W - L

    # Snap proof mass dimensions
    p_r = hole_diameter + hole_gap
    proof_length = int((proof_length - hole_gap) / p_r) * p_r + hole_gap
    proof_height = int((proof_height - hole_gap) / p_r) * p_r + hole_gap

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

    # Comb drive groups
    for ii in range(num_combs):
        shape_code = shape_code_array[ii]

        if shape_code == 0:
            comb = make_comb_drive(
                finger_length, finger_width, finger_gap, finger_distance,
                num_pair_array[ii], edge_fixed_array[ii], holder_distance_array[ii],
                holder_linewidth, holder_width_move_array[ii], holder_width_fixed_array[ii],
                holder_gap_min, holder_top_over_array[ii], holder_bottom_over_array[ii], layer,
            )
        else:
            comb = make_comb_drive_cut(
                finger_length, finger_width, finger_gap, finger_distance,
                num_pair_array[ii], edge_fixed_array[ii], holder_distance_array[ii],
                holder_linewidth, holder_width_move_array[ii], holder_width_fixed_array[ii],
                holder_fixed_leftcut_array[ii], holder_fixed_topcut_array[ii],
                holder_gap_min, holder_top_over_array[ii], holder_bottom_over_array[ii], layer,
            )

        comb_right = switch.add_ref(comb)
        comb_right.dmovex(proof_length / 2)
        comb_right.dmovey(-proof_height / 2 + comb_edge_lower_array[ii])

        comb_left = switch.add_ref(comb)
        comb_left.dmirror_x()
        comb_left.dmovex(-proof_length / 2)
        comb_left.dmovey(-proof_height / 2 + comb_edge_lower_array[ii])

    # Upper anchor
    anchor_upper = make_mems_anchor(
        proof_length, anchor_width_upper + holder_linewidth,
        holder_gap_min, holder_linewidth, holder_top_over_array[0], anchor_SOI_over,
    )
    au = switch.add_ref(anchor_upper)
    au.dmovey(
        anchor_width_upper / 2 + proof_height / 2
        - spring_edge_upper + spring_gap - anchor_edge_upper
    )

    # Lower anchor
    anchor_lower = make_mems_anchor(
        proof_length, anchor_width_lower + holder_linewidth,
        holder_gap_min, holder_linewidth, holder_top_over_array[0], anchor_SOI_over,
    )
    al = switch.add_ref(anchor_lower)
    al.dmovey(
        -anchor_width_lower / 2 - proof_height / 2
        + spring_edge_lower - spring_gap + anchor_edge_lower
    )

    return switch


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()

    sw = make_switch_mems_multi_large()
    bb = sw.dbbox()
    print(f"1.75x multi-comb cell: {bb}")
    print(f"  width:  {bb.width():.1f} um")
    print(f"  height: {bb.height():.1f} um")
    sw.show()
