"""Island (comb-drive node) component for MEMS switch.

U-shaped frame that electrically connects all fixed comb drives.
Surrounds the shuttle on three sides with notches for comb-drive anchors.
"""

import gdsfactory as gf

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


def make_comb_drive_node(
    right_inner: float = 81.0,
    right_outer: float = 96.0,
    left_inner: float = -70.0,
    left_outer: float = -85.0,
    top_y: float = 125.0,
    bot_outer: float = -25.0,
    bot_inner: float = -5.0,
    notch_depth: float = 5.0,
    notch_lo: float = 65.0,
    notch_hi: float = 75.0,
    notch2_lo: float = 115.0,
    notch2_hi: float = 125.0,
    psg_inset: float = 3.0,
    psg_inset_ri: float = 2.0,
    struct_layer=LAYER.POLY_MEMS,
    sac_layer=LAYER.OXIDE_PSG,
    anchor_si_layer=LAYER.SI_FULL,
) -> gf.Component:
    """Comb-drive node: U-shaped frame electrically connecting all fixed comb drives.

    The frame surrounds the shuttle on three sides (left, bottom, right) with
    notches cut out where the comb-drive anchors sit.

    The polygon is traced clockwise starting from the top-right inner corner.

    Args:
        right_inner:    Inner x-coordinate on the right side (um).
        right_outer:    Outer x-coordinate on the right side (um).
        left_inner:     Inner x-coordinate on the left side (um).
        left_outer:     Outer x-coordinate on the left side (um).
        top_y:          Top y-coordinate of the frame (um).
        bot_outer:      Outer bottom y-coordinate (um).
        bot_inner:      Inner bottom y-coordinate (um).
        notch_depth:    How far each notch extends inward from the inner edge (um).
        notch_lo:       Lower y-bound of the lower notch pair (um).
        notch_hi:       Upper y-bound of the lower notch pair (um).
        notch2_lo:      Lower y-bound of the upper notch pair (um).
        notch2_hi:      Upper y-bound of the upper notch pair (um).
        psg_inset:      General PSG inset from edges (um).
        psg_inset_ri:   PSG inset at the right-inner edge (um).
        struct_layer:   Structural poly-Si layer.
        sac_layer:      Sacrificial PSG layer.
        anchor_si_layer: SOI anchor layer.
    """
    ri = right_inner
    ro = right_outer
    li = left_inner
    lo = left_outer
    nd = notch_depth

    # Clockwise from top-right inner corner
    dpoly_pts = [
        (ri, top_y), (ro, top_y), (ro, bot_outer), (lo, bot_outer),
        (lo, top_y), (li, top_y),
        # Left upper notch
        (li, notch2_lo), (li - nd, notch2_lo),
        (li - nd, notch_hi), (li, notch_hi),
        # Left lower notch
        (li, notch_lo), (li - nd, notch_lo),
        (li - nd, bot_inner), (ri + nd, bot_inner),
        # Right lower notch
        (ri + nd, notch_lo), (ri, notch_lo),
        (ri, notch_hi), (ri + nd, notch_hi),
        # Right upper notch
        (ri + nd, notch2_lo), (ri, notch2_lo),
    ]

    p = psg_inset
    p_ri = psg_inset_ri
    psg_pts = [
        (ri + p_ri, top_y - p), (ro - p, top_y - p),
        (ro - p, bot_outer + p), (lo + p, bot_outer + p),
        (lo + p, top_y - p), (li - p, top_y - p),
        (li - p, notch2_lo + p), (li - nd - p, notch2_lo + p),
        (li - nd - p, notch_hi - p), (li - p, notch_hi - p),
        (li - p, notch_lo + p), (li - nd - p, notch_lo + p),
        (li - nd - p, bot_inner - p), (ri + nd + p, bot_inner - p),
        (ri + nd + p, notch_lo + p), (ri + p_ri, notch_lo + p),
        (ri + p_ri, notch_hi - p), (ri + nd + p, notch_hi - p),
        (ri + nd + p, notch2_lo + p), (ri + p_ri, notch2_lo + p),
    ]

    cdn = gf.Component()
    cdn.add_polygon(dpoly_pts, layer=struct_layer)
    cdn.add_polygon(psg_pts, layer=sac_layer)
    cdn.add_polygon(dpoly_pts, layer=anchor_si_layer)
    return cdn


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()
    cdn = make_comb_drive_node()
    cdn.show()
