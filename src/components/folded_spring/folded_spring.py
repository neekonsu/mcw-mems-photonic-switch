"""Folded-spring flexure for MEMS switch.

Provides a 4-beam folded spring pair that connects the proof mass to
the anchor. Purely structural (POLY_MEMS layer only, no anchor pads).

Adapted from Sirui's reference design (draw_spring_pair).
"""

import gdsfactory as gf

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


@gf.cell
def make_spring_pair(
    spring_length: float = 30.0,
    spring_width: float = 0.5,
    spring_gap: float = 5.0,
    anchor_gap_length: float = 7.0,
    pad_length: float = 8.0,
    pad_width: float = 0.8,
    layer=LAYER.POLY_MEMS,
) -> gf.Component:
    """4-beam folded spring pair.

    Two pairs of parallel beams connected at their outer ends by
    connector pads. The inner ends attach to the proof mass (via
    the anchor_gap_length opening). The spring center is at y=0
    at the midpoint between the two beam pairs.

    Geometry (viewed from above, symmetric about x=0):
        - Left pair: two beams extending leftward from x=-anchor_gap_length/2
        - Right pair: two beams extending rightward from x=+anchor_gap_length/2
        - Left connector: vertical pad at the left beam ends
        - Right connector: vertical pad at the right beam ends

    The spring deflects along x (actuation direction).

    Args:
        spring_length:    Length of each beam (um).
        spring_width:     Width of each beam (um).
        spring_gap:       Vertical gap between the two beams in a pair (um).
        anchor_gap_length: Horizontal gap at center for proof mass attachment (um).
        pad_length:       Height of the connector pads at beam ends (um).
        pad_width:        Width of the connector pads (um).
        layer:            GDS layer.
    """
    l_s = spring_length
    w_s = spring_width
    g_s = spring_gap
    l_sa = anchor_gap_length
    l_c = pad_length
    w_c = pad_width

    spring_pair = gf.Component()

    spring_temp = gf.components.rectangle(size=(l_s, w_s), layer=layer)

    # Upper-left beam (extends left from -l_sa/2)
    spring_upper_left = spring_pair.add_ref(spring_temp)
    spring_upper_left.drotate(180)
    spring_upper_left.dmovex(-l_sa / 2)

    # Lower-left beam
    spring_lower_left = spring_pair.add_ref(spring_temp)
    spring_lower_left.drotate(180)
    spring_lower_left.dmovex(-l_sa / 2)
    spring_lower_left.dmovey(-g_s - w_s)

    # Upper-right beam
    spring_upper_right = spring_pair.add_ref(spring_temp)
    spring_upper_right.dmovex(l_sa / 2)
    spring_upper_right.dmovey(-w_s)

    # Lower-right beam
    spring_lower_right = spring_pair.add_ref(spring_temp)
    spring_lower_right.dmovex(l_sa / 2)
    spring_lower_right.dmovey(-w_s - g_s - w_s)

    # Connector pads at beam ends
    spring_connect_temp = gf.components.rectangle(size=(w_c, l_c), layer=layer)

    # Left connector
    spring_connect_left = spring_pair.add_ref(spring_connect_temp)
    spring_connect_left.drotate(180)
    spring_connect_left.dmovex(-l_sa / 2 - l_s)
    spring_connect_left.dmovey(-w_s - g_s / 2 + l_c / 2)

    # Right connector
    spring_connect_right = spring_pair.add_ref(spring_connect_temp)
    spring_connect_right.dmovex(l_sa / 2 + l_s)
    spring_connect_right.dmovey(-w_s - g_s / 2 - l_c / 2)

    return spring_pair


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()
    sp = make_spring_pair()
    sp.show()
