"""
gds3xtrude technology file for the Optical MEMS PDK.

Defines the physical layer stack (z-positions and materials) for 3D extrusion
of GDS layouts.  Used by gds3xtrude's render_scad / render_scad_to_file.

Only structure layers are extruded — mask and dummy layers are omitted since
they have no physical thickness in the final device.

Z-reference: top of SOI silicon = 0 µm.
"""

from gds3xtrude.gds3xtrude import AbstractLayer
from gds3xtrude.types import Material

# ---- Materials (name + RGBA-style color for OpenSCAD rendering) ----
si      = Material("si",    color=(0.55, 0.55, 0.70))   # silicon (blue-gray)
sio2    = Material("sio2",  color=(0.85, 0.85, 0.60))   # oxide (pale yellow)
polysi  = Material("polysi", color=(0.90, 0.70, 0.70))  # poly-Si (salmon)
al      = Material("al",    color=(0.75, 0.75, 0.78))   # aluminium (silver)

# ---- Process thicknesses (µm) ----
T_SUBSTRATE     = 5.0       # truncated for visualization (real: ~500 µm)
T_BOX           = 2.0
T_SOI           = 0.22
T_LTO           = 1.0
T_PSG           = 2.0
T_POLY_ANCHOR   = 0.2
T_POLY_MEMS     = 0.5
T_METAL         = 0.5

# ---- Z-positions (zmin of each layer, µm) ----
Z_SUBSTRATE     = -T_BOX - T_SUBSTRATE          # -7.0
Z_BOX           = -T_BOX                        # -2.0
Z_SOI           = 0.0
Z_LTO           = T_SOI                         #  0.22
Z_PSG           = Z_LTO + T_LTO                 #  1.22
Z_POLY_ANCHOR   = T_SOI                         #  0.22
Z_POLY_MEMS     = Z_PSG + T_PSG                 #  3.22
Z_METAL         = Z_POLY_MEMS + T_POLY_MEMS     #  3.72

# ---- Layer stack for gds3xtrude ----
# Each entry: ([AbstractLayer(gds_layer, gds_datatype, material)], z_start, z_end)
# Only structure layers (1-10) are included; mask/dummy layers are not extruded.

layerstack = [
    # Substrate (truncated)
    ([AbstractLayer(10, 0, si)],       Z_SUBSTRATE,          Z_SUBSTRATE + T_SUBSTRATE),
    # Buried oxide (BOX)
    ([AbstractLayer(3, 0, sio2)],      Z_BOX,                Z_BOX + T_BOX),
    # SOI silicon — full thickness
    ([AbstractLayer(1, 0, si)],        Z_SOI,                Z_SOI + T_SOI),
    # SOI silicon — partial etch (150 nm slab)
    ([AbstractLayer(2, 0, si)],        Z_SOI,                Z_SOI + T_SOI - 0.07),
    # LTO fill oxide
    ([AbstractLayer(4, 0, sio2)],      Z_LTO,                Z_LTO + T_LTO),
    # PSG sacrificial oxide
    ([AbstractLayer(5, 0, sio2)],      Z_PSG,                Z_PSG + T_PSG),
    # Poly-Si anchor
    ([AbstractLayer(6, 0, polysi)],    Z_POLY_ANCHOR,        Z_POLY_ANCHOR + T_POLY_ANCHOR),
    # Poly-Si structural MEMS (moving)
    ([AbstractLayer(7, 0, polysi)],    Z_POLY_MEMS,          Z_POLY_MEMS + T_POLY_MEMS),
    # Poly-Si top (static, same z as MEMS)
    ([AbstractLayer(8, 0, polysi)],    Z_POLY_MEMS,          Z_POLY_MEMS + T_POLY_MEMS),
    # Metal (aluminium)
    ([AbstractLayer(9, 0, al)],        Z_METAL,              Z_METAL + T_METAL),
]
