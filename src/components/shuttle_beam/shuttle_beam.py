"""Shuttle beam (proof mass) components for MEMS switch.

Provides the central moving proof mass with 2D release hole arrays.

Adapted from Sirui's reference design (draw_proofmass, draw_proofmass_side).
"""

import gdsfactory as gf

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


@gf.cell
def make_proofmass(
    length: float = 20.0,
    height: float = 100.0,
    hole_diameter: float = 5.0,
    hole_gap: float = 0.8,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Proof mass with 2D release hole array, centered at origin.

    A rectangular body with a regular grid of square holes subtracted
    via boolean operation. Hole count is floor-rounded to fit within
    the dimensions.

    Args:
        length:        Width of the proof mass (um).
        height:        Height of the proof mass (um).
        hole_diameter: Side length of each square hole (um).
        hole_gap:      Gap between adjacent holes (um).
        layer:         GDS layer.
    """
    d_r = hole_diameter
    p_r = hole_diameter + hole_gap
    proof_full = gf.Component()

    # Rectangle
    proof = gf.Component()
    proof_temp = gf.components.rectangle(size=(length, height), layer=layer)
    proof_ref = proof.add_ref(proof_temp)
    proof_ref.dmovex(-length / 2)
    proof_ref.dmovey(-height / 2)

    # Hole array
    hole_array = gf.Component()
    hole_temp = gf.components.rectangle(size=(d_r, d_r), layer=layer)
    n_hole_l = int(length / p_r)
    n_hole_h = int(height / p_r)

    hole_refs = {}
    for ii in range(n_hole_l):
        for jj in range(n_hole_h):
            hole_refs[ii * n_hole_l + jj] = hole_array.add_ref(hole_temp)
            hole_refs[ii * n_hole_l + jj].dmovex(
                -d_r / 2 - p_r * (n_hole_l - 1) / 2 + ii * p_r
            )
            hole_refs[ii * n_hole_l + jj].dmovey(
                -d_r / 2 - p_r * (n_hole_h - 1) / 2 + jj * p_r
            )

    # Boolean subtraction
    proof_with_holes = gf.boolean(proof, hole_array, operation="not", layer=layer)
    proof_full.add_ref(proof_with_holes)
    return proof_full


@gf.cell
def make_proofmass_side(
    length: float = 20.0,
    height: float = 3.0,
    hole_diameter: float = 2.0,
    hole_gap: float = 0.8,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """Side-aligned proof mass for comb drive holders.

    Same as make_proofmass but with the left edge at x=0 (not centered
    horizontally). The y-axis is centered. Extra holes extend beyond the
    rectangle boundary and are clipped by the boolean operation.

    Args:
        length:        Width of the proof mass (um).
        height:        Height of the proof mass (um).
        hole_diameter: Side length of each square hole (um).
        hole_gap:      Gap between adjacent holes (um).
        layer:         GDS layer.
    """
    d_r = hole_diameter
    p_r = hole_diameter + hole_gap
    proof_full = gf.Component()

    # Rectangle (left edge at x=0, centered in y)
    proof = gf.Component()
    proof_temp = gf.components.rectangle(size=(length, height), layer=layer)
    proof_ref = proof.add_ref(proof_temp)
    proof_ref.dmovey(-height / 2)

    # Hole array (extended +2 columns to ensure coverage)
    hole_array = gf.Component()
    hole_temp = gf.components.rectangle(size=(d_r, d_r), layer=layer)
    n_hole_l = int(length / p_r) + 2
    n_hole_h = int(height / p_r)

    hole_refs = {}
    for ii in range(n_hole_l):
        for jj in range(n_hole_h):
            hole_refs[ii * n_hole_l + jj] = hole_array.add_ref(hole_temp)
            hole_refs[ii * n_hole_l + jj].dmovex(ii * p_r)
            hole_refs[ii * n_hole_l + jj].dmovey(
                -d_r / 2 - p_r * (n_hole_h - 1) / 2 + jj * p_r
            )

    # Boolean subtraction
    proof_with_holes = gf.boolean(proof, hole_array, operation="not", layer=layer)
    proof_full.add_ref(proof_with_holes)
    return proof_full


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()
    pm = make_proofmass(20, 100, 5, 0.8)
    pm.show()
