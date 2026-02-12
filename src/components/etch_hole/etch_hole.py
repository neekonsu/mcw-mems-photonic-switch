"""Etch hole primitive for MEMS release structures.

Single square etch hole used as a sub-component in shuttle beams,
moving comb drives, and other released MEMS structures.
"""

import gdsfactory as gf

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


def make_etch_hole(size: float = 5.0, layer=LAYER.POLY_MEMS) -> gf.Component:
    """Single square etch hole, centered at origin.

    Args:
        size:  Side length of the square hole (um).
        layer: GDS layer for the hole polygon.

    Returns:
        gf.Component with one square polygon centered at (0, 0).
    """
    c = gf.Component()
    c.add_polygon(
        [(-size / 2, -size / 2),
         (size / 2, -size / 2),
         (size / 2, size / 2),
         (-size / 2, size / 2)],
        layer=layer,
    )
    return c


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()
    hole = make_etch_hole()
    hole.show()
