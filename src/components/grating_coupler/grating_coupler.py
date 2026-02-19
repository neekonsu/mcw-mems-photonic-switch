"""Grating coupler component.

Uniform-period grating coupler on SOI with partial-etch teeth,
connected to a 440 nm strip waveguide via a linear taper.
"""

import numpy as np
import gdsfactory as gf

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../libraries"))
from mcw_custom_optical_mems_pdk import LAYER


def make_grating_coupler(
    n_periods: int = 20,
    period: float = 0.63,
    duty_cycle: float = 0.5,
    grating_width: float = 12.0,
    taper_length: float = 15.0,
    wg_width: float = 0.44,
    wg_length: float = 5.0,
    full_etch_layer=LAYER.SI_FULL,
    partial_etch_layer=LAYER.SI_PARTIAL,
) -> gf.Component:
    """Uniform grating coupler with partial-etch teeth and taper to waveguide.

    The grating region is a slab of SI_FULL with SI_PARTIAL teeth etched
    into it. A linear taper connects the grating to a 440 nm strip waveguide.

    Geometry (left to right):
        waveguide (440 nm) -> taper -> grating teeth

    Args:
        n_periods:          Number of grating periods.
        period:             Grating period (um).
        duty_cycle:         Fraction of period that is etched (tooth).
        grating_width:      Width of the grating region (um).
        taper_length:       Length of the linear taper (um).
        wg_width:           Waveguide width (um).
        wg_length:          Length of output waveguide (um).
        full_etch_layer:    SOI full-thickness layer.
        partial_etch_layer: SOI partial-etch (slab) layer.
    """
    c = gf.Component()
    tooth_width = period * duty_cycle
    grating_length = n_periods * period

    # --- Waveguide (strip, SI_FULL) ---
    wg_y0 = -wg_width / 2
    wg_y1 = wg_width / 2
    c.add_polygon(
        [(0, wg_y0), (wg_length, wg_y0),
         (wg_length, wg_y1), (0, wg_y1)],
        layer=full_etch_layer,
    )

    # --- Linear taper (SI_FULL) ---
    taper_x0 = wg_length
    taper_x1 = wg_length + taper_length
    c.add_polygon(
        [(taper_x0, wg_y0), (taper_x1, -grating_width / 2),
         (taper_x1, grating_width / 2), (taper_x0, wg_y1)],
        layer=full_etch_layer,
    )

    # --- Grating slab (SI_FULL base under all teeth) ---
    grating_x0 = taper_x1
    grating_x1 = taper_x1 + grating_length
    c.add_polygon(
        [(grating_x0, -grating_width / 2), (grating_x1, -grating_width / 2),
         (grating_x1, grating_width / 2), (grating_x0, grating_width / 2)],
        layer=full_etch_layer,
    )

    # --- Grating teeth (SI_PARTIAL, shallow-etched) ---
    for i in range(n_periods):
        tx0 = grating_x0 + i * period
        tx1 = tx0 + tooth_width
        c.add_polygon(
            [(tx0, -grating_width / 2), (tx1, -grating_width / 2),
             (tx1, grating_width / 2), (tx0, grating_width / 2)],
            layer=partial_etch_layer,
        )

    return c


if __name__ == "__main__":
    from mcw_custom_optical_mems_pdk import PDK
    PDK.activate()
    c = make_grating_coupler()
    c.show()
