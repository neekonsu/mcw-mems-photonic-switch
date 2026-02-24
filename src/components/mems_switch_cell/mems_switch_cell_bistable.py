"""Bistable MEMS switch cell assemblies.

Drop-in replacements for the folded-spring switch cells in
``mems_switch_cell.py``, using CCS bistable spring pairs instead of
linear folded springs.  The bistable mechanism provides two stable
shuttle positions (nonvolatile switching) without continuous power.

Key differences from folded-spring variants:
  - ``make_spring_pair()`` replaced by ``make_bistable_spring_pair()``
  - External anchor strips above/below the proof mass are removed
    (the bistable spring pair has built-in multi-layer anchors)
  - Pad anchors are repositioned to attach to the CCS spring anchors

Provides three variants mirroring the original:
  - ``make_switch_mems_bistable()``      → ``make_switch_mems()``
  - ``make_switch_mems_multi_bistable()`` → ``make_switch_mems_multi()``
  - ``make_switch_mems_cut_bistable()``   → ``make_switch_mems_cut()``
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


_shuttle_beam = _import_from("shuttle_beam/shuttle_beam.py", "_bsw_shuttle_beam")
_bistable_spring = _import_from(
    "bistable_spring/bistable_spring_pair.py", "_bsw_bistable_spring"
)
_comb_drive = _import_from("comb_drive/comb_drive.py", "_bsw_comb_drive")
_anchor = _import_from("anchor/anchor.py", "_bsw_anchor")

make_proofmass = _shuttle_beam.make_proofmass
make_bistable_spring_pair = _bistable_spring.make_bistable_spring_pair
make_comb_drive = _comb_drive.make_comb_drive
make_comb_drive_cut = _comb_drive.make_comb_drive_cut
make_mems_anchor = _anchor.make_mems_anchor


@gf.cell
def make_switch_mems_bistable(
    proof_length: float = 7.0,
    proof_height: float = 120.0,
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    # Bistable spring parameters
    spring_span: float = 40.0,
    spring_flex_ratio: float = 0.3,
    spring_flex_width: float = 0.5,
    spring_rigid_width: float = 0.9375,
    spring_initial_offset: float = 1.2,
    spring_taper_length: float = 2.0,
    spring_beam_spacing: float = 5.0,
    spring_anchor_length: float = 8.0,
    spring_anchor_width: float = 8.0,
    spring_anchor_hole_max: float = 2.0,
    spring_anchor_linewidth: float = 0.8,
    spring_anchor_over_top: float = 0.4,
    spring_anchor_over_bottom: float = 0.5,
    # Comb drive parameters
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
    # Positioning
    spring_edge_upper: float = 1.0,
    spring_edge_lower: float = 1.0,
    comb_edge_lower: float = 5.0,
    # Pad parameters
    pad_length_upper: float = 30.0,
    pad_width_upper: float = 30.0,
    pad_length_lower: float = 30.0,
    pad_width_lower: float = 30.0,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Single-comb-pair MEMS switch cell with bistable CCS springs.

    Central proof mass with:
    - Upper and lower CCS bistable spring pairs (with built-in anchors)
    - Left and right comb drives (mirrored)
    - Upper and lower pad anchors (repositioned to CCS spring anchors)

    The CCS bistable springs replace the folded springs and include their
    own multi-layer anchors, eliminating the need for separate anchor strips.

    Args:
        proof_length:      Proof mass width (um). Auto-snapped to hole grid.
        proof_height:      Proof mass height (um). Auto-snapped to hole grid.
        hole_diameter:     Release hole size (um).
        hole_gap:          Gap between holes (um).
        spring_*:          CCS bistable spring pair parameters.
        finger_*:          Comb drive finger parameters.
        num_pair:          Number of finger pairs per comb.
        holder_*:          Comb drive holder/anchor parameters.
        spring_edge_*:     Spring inset from proof mass edges (um).
        comb_edge_lower:   Comb drive offset from bottom of proof mass (um).
        pad_*_upper/lower: Pad anchor dimensions (um).
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

    # Upper spring (mirror y so offset direction points inward)
    spring_upper = switch.add_ref(spring)
    spring_upper.dmirror_y()
    spring_upper.dmovey(proof_height / 2 - spring_edge_upper)

    # Lower spring
    spring_lower = switch.add_ref(spring)
    spring_lower.dmovey(-proof_height / 2 + spring_edge_lower)

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

    # Pad anchors above/below the CCS spring anchors
    # The CCS spring anchors are at x = ±(proof_length/2 + spring_span)
    # Pads sit above/below the spring anchors in y
    spring_anchor_y_upper = proof_height / 2 - spring_edge_upper
    spring_anchor_y_lower = -proof_height / 2 + spring_edge_lower

    pad_upper = make_mems_anchor(
        pad_length_upper, pad_width_upper,
        holder_gap_min, holder_linewidth, holder_top_over, holder_bottom_over,
    )
    pu = switch.add_ref(pad_upper)
    pu.dmovey(
        spring_anchor_y_upper + spring_anchor_width / 2
        + spring_anchor_over_top + pad_width_upper / 2
    )

    pad_lower = make_mems_anchor(
        pad_length_lower, pad_width_lower,
        holder_gap_min, holder_linewidth, holder_top_over, holder_bottom_over,
    )
    pl = switch.add_ref(pad_lower)
    pl.dmovey(
        spring_anchor_y_lower - spring_anchor_width / 2
        - spring_anchor_over_top - pad_width_lower / 2
    )

    return switch


@gf.cell
def make_switch_mems_multi_bistable(
    proof_length: float = 7.0,
    proof_height: float = 110.0,
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    # Bistable spring parameters
    spring_span: float = 40.0,
    spring_flex_ratio: float = 0.3,
    spring_flex_width: float = 0.5,
    spring_rigid_width: float = 0.9375,
    spring_initial_offset: float = 1.2,
    spring_taper_length: float = 2.0,
    spring_beam_spacing: float = 5.0,
    spring_anchor_length: float = 8.0,
    spring_anchor_width: float = 8.0,
    spring_anchor_hole_max: float = 2.0,
    spring_anchor_linewidth: float = 0.8,
    spring_anchor_over_top: float = 0.4,
    spring_anchor_over_bottom: float = 0.5,
    # Comb drive parameters
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
    # Positioning
    spring_edge_upper: float = 1.0,
    spring_edge_lower: float = 1.0,
    comb_edge_lower_array: list | None = None,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Multi-comb-group MEMS switch cell with bistable CCS springs.

    Same structure as make_switch_mems_bistable but with multiple comb drive
    groups stacked along the proof mass height. The CCS bistable spring
    pairs include their own multi-layer anchors.

    Arrays default to ``num_combs`` copies of typical values if None.

    Args:
        num_combs:               Number of comb drive groups per side.
        num_pair_array:          Finger pairs per comb group.
        (other comb args same as make_switch_mems_multi)
        spring_*:                CCS bistable spring parameters.
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

    return switch


@gf.cell
def make_switch_mems_cut_bistable(
    proof_length: float = 7.0,
    proof_height: float = 110.0,
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    # Bistable spring parameters
    spring_span: float = 40.0,
    spring_flex_ratio: float = 0.3,
    spring_flex_width: float = 0.5,
    spring_rigid_width: float = 0.9375,
    spring_initial_offset: float = 1.2,
    spring_taper_length: float = 2.0,
    spring_beam_spacing: float = 5.0,
    spring_anchor_length: float = 8.0,
    spring_anchor_width: float = 8.0,
    spring_anchor_hole_max: float = 2.0,
    spring_anchor_linewidth: float = 0.8,
    spring_anchor_over_top: float = 0.4,
    spring_anchor_over_bottom: float = 0.5,
    # Comb drive parameters
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
    # Positioning
    spring_edge_upper: float = 1.0,
    spring_edge_lower: float = 1.0,
    comb_edge_lower_array: list | None = None,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Multi-comb MEMS switch with optional corner-cut anchors and bistable springs.

    Each comb group has a ``shape_code``: 0 for normal rectangular anchor,
    1 for corner-cut anchor. CCS bistable spring pairs replace folded springs.

    Args:
        shape_code_array:          0=normal, 1=corner-cut per comb group.
        holder_fixed_leftcut_array: Horizontal cut extent per group (um).
        holder_fixed_topcut_array:  Vertical cut extent per group (um).
        spring_*:                  CCS bistable spring parameters.
        (other args same as make_switch_mems_cut)
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

    return switch


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK

    PDK.activate()

    # Test: single-comb bistable
    sw1 = make_switch_mems_bistable()
    bb = sw1.dbbox()
    print(f"Single-comb bistable: {bb.width():.0f} x {bb.height():.0f} um")

    # Test: 3-comb multi bistable
    sw2 = make_switch_mems_multi_bistable(
        num_combs=3,
        num_pair_array=[25, 25, 25],
        comb_edge_lower_array=[4, 34, 64],
    )
    bb = sw2.dbbox()
    print(f"Multi-comb bistable:  {bb.width():.0f} x {bb.height():.0f} um")

    # Test: 3-comb cut bistable
    sw3 = make_switch_mems_cut_bistable(
        num_combs=3,
        num_pair_array=[25, 25, 25],
        comb_edge_lower_array=[4, 34, 64],
    )
    bb = sw3.dbbox()
    print(f"Cut-comb bistable:    {bb.width():.0f} x {bb.height():.0f} um")

    sw2.show()
