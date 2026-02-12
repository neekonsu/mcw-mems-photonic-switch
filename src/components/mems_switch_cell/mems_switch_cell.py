"""MEMS switch cell assembly.

Combines all MEMS components (proof mass, springs, comb drives, anchors)
into complete switch cell variants.

Adapted from Sirui's reference design (draw_switch_MEMS, draw_switch_MEMS3,
draw_switch_MEMS3_cut).
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


_shuttle_beam = _import_from("shuttle_beam/shuttle_beam.py", "_asm_shuttle_beam")
_folded_spring = _import_from("folded_spring/folded_spring.py", "_asm_folded_spring")
_comb_drive = _import_from("comb_drive/comb_drive.py", "_asm_comb_drive")
_anchor = _import_from("anchor/anchor.py", "_asm_anchor")

make_proofmass = _shuttle_beam.make_proofmass
make_spring_pair = _folded_spring.make_spring_pair
make_comb_drive = _comb_drive.make_comb_drive
make_comb_drive_cut = _comb_drive.make_comb_drive_cut
make_mems_anchor = _anchor.make_mems_anchor


@gf.cell
def make_switch_mems(
    proof_length: float = 7.0,
    proof_height: float = 120.0,
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    spring_length: float = 30.0,
    spring_width: float = 0.5,
    spring_gap: float = 5.0,
    pad_length: float = 8.0,
    pad_width: float = 0.8,
    finger_length: float = 5.0,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 3.0,
    num_pair: int = 20,
    edge_fixed: float = 1.0,
    holder_distance: float = 0.0,
    holder_linewidth: float = 0.8,
    holder_width_move: float = 3.0,
    holder_width_fixed: float = 20.0,
    holder_gap_min: float = 2.0,
    holder_top_over: float = 0.3,
    holder_bottom_over: float = 0.3,
    spring_edge_upper: float = 1.0,
    spring_edge_lower: float = 1.0,
    comb_edge_lower: float = 5.0,
    anchor_edge_upper: float = 1.0,
    anchor_edge_lower: float = 1.0,
    anchor_width_upper: float = 5.0,
    anchor_width_lower: float = 5.0,
    pad_length_upper: float = 30.0,
    pad_width_upper: float = 30.0,
    pad_length_lower: float = 30.0,
    pad_width_lower: float = 30.0,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Single-comb-pair MEMS switch cell.

    Central proof mass with:
    - Upper and lower folded spring pairs
    - Left and right comb drives (mirrored)
    - Upper and lower anchors with pads

    Args:
        proof_length:      Proof mass width (um). Auto-snapped to hole grid.
        proof_height:      Proof mass height (um). Auto-snapped to hole grid.
        hole_diameter:     Release hole size (um).
        hole_gap:          Gap between holes (um).
        spring_*:          Folded spring parameters.
        finger_*:          Comb drive finger parameters.
        num_pair:          Number of finger pairs per comb.
        holder_*:          Comb drive holder/anchor parameters.
        spring_edge_*:     Spring inset from proof mass edges (um).
        comb_edge_lower:   Comb drive offset from bottom of proof mass (um).
        anchor_edge_*:     Anchor offset from spring connection (um).
        anchor_width_*:    Anchor strip height (um).
        pad_*_upper/lower: Anchor pad dimensions (um).
    """
    # Snap proof mass dimensions to hole grid
    p_r = hole_diameter + hole_gap
    proof_length = int((proof_length - hole_gap) / p_r) * p_r + hole_gap
    proof_height = int((proof_height - hole_gap) / p_r) * p_r + hole_gap

    # Auto-compute holder_distance if zero
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
def make_switch_mems_multi(
    proof_length: float = 7.0,
    proof_height: float = 110.0,
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    spring_length: float = 45.0,
    spring_width: float = 0.5,
    spring_gap: float = 5.0,
    pad_length: float = 8.0,
    pad_width: float = 0.8,
    num_combs: int = 3,
    finger_length: float = 4.0,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 2.0,
    num_pair_array: list | None = None,
    edge_fixed_array: list | None = None,
    holder_distance_array: list | None = None,
    holder_linewidth: float = 0.8,
    holder_width_move_array: list | None = None,
    holder_width_fixed_array: list | None = None,
    holder_gap_min: float = 2.0,
    holder_top_over_array: list | None = None,
    holder_bottom_over_array: list | None = None,
    spring_edge_upper: float = 1.0,
    spring_edge_lower: float = 1.0,
    comb_edge_lower_array: list | None = None,
    anchor_edge_upper: float = 1.0,
    anchor_edge_lower: float = 1.0,
    anchor_width_upper: float = 5.0,
    anchor_width_lower: float = 5.0,
    anchor_SOI_over: float = 4.0,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Multi-comb-group MEMS switch cell.

    Same structure as make_switch_mems but with multiple comb drive groups
    stacked along the proof mass height. Each group can have different
    parameters (num_pair, holder sizes, etc.).

    Arrays default to ``num_combs`` copies of typical values if None.

    Args:
        num_combs:               Number of comb drive groups per side.
        num_pair_array:          Finger pairs per comb group.
        edge_fixed_array:        Edge spacing per group.
        holder_distance_array:   Holder distance per group (auto-computed if [0,...]).
        holder_width_move_array: Movable holder height per group.
        holder_width_fixed_array: Fixed anchor height per group.
        holder_top_over_array:   POLY_TOP overhang per group.
        holder_bottom_over_array: SI_FULL overhang per group.
        comb_edge_lower_array:   Y-offset from proof mass bottom per group.
        anchor_SOI_over:         SI_FULL overhang for spring anchors.
    """
    # Defaults
    if num_pair_array is None:
        num_pair_array = [25] * num_combs
    if edge_fixed_array is None:
        edge_fixed_array = [1.0] * num_combs
    if holder_width_move_array is None:
        holder_width_move_array = [3.0] * num_combs
    if holder_width_fixed_array is None:
        holder_width_fixed_array = [15.0] * num_combs
    if holder_top_over_array is None:
        holder_top_over_array = [0.3] * num_combs
    if holder_bottom_over_array is None:
        holder_bottom_over_array = [0.5] * num_combs
    if comb_edge_lower_array is None:
        comb_edge_lower_array = [4 + 30 * i for i in range(num_combs)]

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
def make_switch_mems_cut(
    proof_length: float = 7.0,
    proof_height: float = 110.0,
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    spring_length: float = 45.0,
    spring_width: float = 0.5,
    spring_gap: float = 5.0,
    pad_length: float = 8.0,
    pad_width: float = 0.8,
    num_combs: int = 3,
    finger_length: float = 4.0,
    finger_width: float = 0.5,
    finger_gap: float = 0.5,
    finger_distance: float = 2.0,
    num_pair_array: list | None = None,
    edge_fixed_array: list | None = None,
    holder_distance_array: list | None = None,
    holder_linewidth: float = 0.8,
    holder_width_move_array: list | None = None,
    holder_width_fixed_array: list | None = None,
    holder_fixed_leftcut_array: list | None = None,
    holder_fixed_topcut_array: list | None = None,
    shape_code_array: list | None = None,
    holder_gap_min: float = 2.0,
    holder_top_over_array: list | None = None,
    holder_bottom_over_array: list | None = None,
    spring_edge_upper: float = 1.0,
    spring_edge_lower: float = 1.0,
    comb_edge_lower_array: list | None = None,
    anchor_edge_upper: float = 1.0,
    anchor_edge_lower: float = 1.0,
    anchor_width_upper: float = 5.0,
    anchor_width_lower: float = 5.0,
    anchor_SOI_over: float = 4.0,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Multi-comb MEMS switch with optional corner-cut anchors.

    Each comb group has a ``shape_code``: 0 for normal rectangular anchor,
    1 for corner-cut anchor.

    Args:
        shape_code_array:          0=normal, 1=corner-cut per comb group.
        holder_fixed_leftcut_array: Horizontal cut extent per group (um).
        holder_fixed_topcut_array:  Vertical cut extent per group (um).
        (other args same as make_switch_mems_multi)
    """
    # Defaults
    if num_pair_array is None:
        num_pair_array = [25] * num_combs
    if edge_fixed_array is None:
        edge_fixed_array = [1.0] * num_combs
    if holder_width_move_array is None:
        holder_width_move_array = [3.0] * num_combs
    if holder_width_fixed_array is None:
        holder_width_fixed_array = [15.0] * num_combs
    if holder_top_over_array is None:
        holder_top_over_array = [0.3] * num_combs
    if holder_bottom_over_array is None:
        holder_bottom_over_array = [0.5] * num_combs
    if comb_edge_lower_array is None:
        comb_edge_lower_array = [4 + 30 * i for i in range(num_combs)]
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

    # Test: 3-comb variant from reference cell 68
    sw = make_switch_mems_multi(
        num_combs=3,
        num_pair_array=[25, 25, 25],
        comb_edge_lower_array=[4, 34, 64],
    )
    sw.show()
