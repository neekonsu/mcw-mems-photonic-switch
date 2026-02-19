"""Trace-to-pad component.

A POLY_MEMS trace terminated with a METAL bond pad.
"""

import gdsfactory as gf

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


def make_trace_to_pad(
    trace_width: float = 2.0,
    trace_length: float = 20.0,
    pad_width: float = 10.0,
    pad_height: float = 10.0,
    metal_inset: float = 1.0,
    struct_layer=LAYER.POLY_MEMS,
    metal_layer=LAYER.METAL,
) -> gf.Component:
    """Poly trace terminated with a metal pad.

    The trace runs from x=0 to x=trace_length. A pad is appended at the
    far end, centred vertically on the trace. The pad has a POLY_MEMS
    base with a METAL layer inset from the edges.

    Args:
        trace_width:  Width of the poly trace (um).
        trace_length: Length of the poly trace (um).
        pad_width:    Width (x) of the bond pad (um).
        pad_height:   Height (y) of the bond pad (um).
        metal_inset:  Inset of metal from pad edges (um).
        struct_layer: Structural poly-Si layer.
        metal_layer:  Metal layer.
    """
    c = gf.Component()

    # Poly trace
    c.add_polygon(
        [(0, 0), (trace_length, 0),
         (trace_length, trace_width), (0, trace_width)],
        layer=struct_layer,
    )

    # Pad base (POLY_MEMS), centred on trace
    trace_mid_y = trace_width / 2
    px0 = trace_length
    px1 = trace_length + pad_width
    py0 = trace_mid_y - pad_height / 2
    py1 = trace_mid_y + pad_height / 2
    pad_rect = [(px0, py0), (px1, py0), (px1, py1), (px0, py1)]
    c.add_polygon(pad_rect, layer=struct_layer)

    # Metal on top of pad (inset)
    c.add_polygon(
        [(px0 + metal_inset, py0 + metal_inset),
         (px1 - metal_inset, py0 + metal_inset),
         (px1 - metal_inset, py1 - metal_inset),
         (px0 + metal_inset, py1 - metal_inset)],
        layer=metal_layer,
    )

    return c


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()
    c = make_trace_to_pad()
    c.show()
