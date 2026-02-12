"""
optical_mems_pdk.py — Custom PDK for Optical MEMS Photonic Switch

Process:  Custom SOI-based MEMS + photonic process (6 masks)
Wafer:    220 nm SOI on 2 µm BOX
Layers:   10 structure layers, 6 mask layers, 3 dummy layers

Usage:
    from optical_mems_pdk import LAYER, LAYER_STACK, PDK
    PDK.activate()
"""

from functools import partial

import gdsfactory as gf
from gdsfactory.cross_section import CrossSection, cross_section, xsection
from gdsfactory.pdk import Pdk
from gdsfactory.technology import (
    LayerLevel,
    LayerMap,
    LayerStack,
    LayerView,
    LayerViews,
    LogicalLayer,
)
from gdsfactory.typings import Layer

nm = 1e-3  # 1 nm in µm (gdsfactory works in µm)

# =============================================================================
# Layer Map
# =============================================================================
# Follows the "Layer Names" tab of the process spreadsheet.
#
#   Structure layers  (1–10)/0  — physical materials present in the GDS
#   Mask layers       (11–16)/0 — drawn layers that define etch/deposition masks
#   Dummy layers      (21–23)/0 — auxiliary/visualization layers


class LAYER(LayerMap):
    """Layer map for the Optical MEMS photonic switch process.

    Structure layers represent physical materials in the fabricated device.
    Mask layers represent lithographic mask definitions.
    Dummy layers are auxiliary (visualization / bookkeeping).
    """

    # --- Structure layers ---
    SI_FULL: Layer = (1, 0)        # SOI silicon, full 220 nm thickness
    SI_PARTIAL: Layer = (2, 0)     # SOI silicon after 70 nm shallow etch (150 nm slab)
    OXIDE_SOI: Layer = (3, 0)      # Buried oxide (BOX) of the SOI wafer
    OXIDE_LTO: Layer = (4, 0)      # Low-temperature oxide (~1 µm, CMP planarized)
    OXIDE_PSG: Layer = (5, 0)      # Phosphosilicate glass (~2 µm, sacrificial)
    POLY_ANCHOR: Layer = (6, 0)    # Undoped poly-Si anchor (~200 nm, deposited on SOI)
    POLY_MEMS: Layer = (7, 0)      # Doped poly-Si structural MEMS (~500 nm, partially etched)
    POLY_TOP: Layer = (8, 0)       # Doped poly-Si full-thickness (~500 nm, anchors/static)
    METAL: Layer = (9, 0)          # Aluminium (~500 nm, lift-off)
    SI_SUBSTRATE: Layer = (10, 0)  # Silicon handle wafer (substrate)

    # --- Mask layers ---
    MASK_SI_FULL_ETCH: Layer = (11, 0)     # Mask #2: Si full etch
    MASK_SI_PARTIAL_ETCH: Layer = (12, 0)  # Mask #1: Si partial (shallow) etch
    MASK_ANCHOR_ETCH: Layer = (13, 0)      # Mask #4: Anchor etch through PSG/LTO
    MASK_PSG_ETCH: Layer = (14, 0)         # Mask #3: PSG etch (via hard mask)
    MASK_POLYSI_ETCH: Layer = (15, 0)      # Mask #5: poly-Si structural etch
    MASK_METAL_LIFTOFF: Layer = (16, 0)    # Mask #6: Metal lift-off

    # --- Dummy / auxiliary layers ---
    HARD_MASK: Layer = (21, 0)       # a-Si hard mask (visualization)
    RELEASE: Layer = (22, 0)         # Release region (where PSG is removed)
    METAL_LIFTOFF_AUX: Layer = (23, 0)  # Metal lift-off auxiliary

    # --- Utility layers (gdsfactory conventions) ---
    FLOORPLAN: Layer = (64, 0)
    TEXT: Layer = (66, 0)
    DEVREC: Layer = (68, 0)        # Device recognition
    PORT: Layer = (1, 10)
    PORTE: Layer = (1, 11)


# =============================================================================
# Design Rules
# =============================================================================
# Extracted from the "Layer Specifications" tab of the process spreadsheet.
# All values in µm.


class DesignRules:
    """Design rules for the Optical MEMS process.

    Attributes are grouped by rule type.  All values are in µm.
    """

    # --- Minimum feature size (width) ---
    min_width_si_full: float = 0.25
    min_width_si_partial: float = 0.25
    min_width_anchor: float = 0.3
    min_width_psg: float = 0.3
    min_width_metal: float = 1.0

    # --- Minimum gap (space) on same layer ---
    min_gap_si_full: float = 0.25
    min_gap_si_partial: float = 0.25
    min_gap_anchor: float = 0.3
    min_gap_psg: float = 0.3
    min_gap_metal: float = 1.0

    # --- Enclosure rules  (A encloses B by at least X) ---
    enc_si_full_of_si_partial: float = 0.3    # Si full encloses Si partial
    enc_si_full_of_anchor: float = 0.5        # Si full encloses anchor
    enc_polysi_of_anchor: float = 0.4         # PolySi encloses anchor
    enc_polysi_of_psg: float = 0.5            # PolySi encloses PSG
    enc_polysi_of_metal: float = 0.5          # PolySi encloses metal

    # --- Overlap / extension rules (A extends outside B by at least X) ---
    ext_si_partial_outside_si_full: float = 0.2   # Si partial extends past Si full
    ext_metal_outside_anchor: float = 0.5          # Metal extends past anchor
    ext_metal_outside_polysi: float = 0.5          # Metal extends past PolySi
    ext_polysi_outside_metal: float = 0.5          # PolySi extends past metal

    # --- Inter-layer gap rules (minimum distance between features on different layers) ---
    gap_si_full_to_si_partial: float = 0.2
    gap_anchor_to_psg: float = 1.0
    gap_psg_to_anchor: float = 1.0
    gap_anchor_to_polysi: float = 0.5
    gap_polysi_to_anchor: float = 0.5
    gap_metal_to_polysi: float = 0.5
    gap_polysi_to_metal: float = 0.5


DESIGN_RULES = DesignRules()


# =============================================================================
# Layer Stack  (post-fabrication physical cross-section)
# =============================================================================
# Z-reference: top surface of SOI silicon = 0 µm.
#
# Physical stack (bottom → top):
#   Si substrate        — bulk handle wafer
#   BOX (buried oxide)  — 2 µm SiO2
#   SOI Si              — 220 nm (full) / 150 nm (after shallow etch)
#   LTO                 — ~1 µm (fills around Si features, CMP planarized)
#   PSG                 — ~2 µm (sacrificial, removed during release)
#   poly-Si anchor      — ~200 nm undoped (fills anchor etch holes, bonds to SOI)
#   poly-Si structural  — ~500 nm doped (MEMS + top)
#   Metal               — 500 nm Al (on top of structural poly)


# --- Process thicknesses ---
THICKNESS_SOI = 220 * nm           # 0.22 µm
THICKNESS_BOX = 2.0                # 2 µm
THICKNESS_SHALLOW_ETCH = 70 * nm   # 0.07 µm (partial etch depth)
THICKNESS_LTO = 1.0                # ~1 µm (after CMP)
THICKNESS_PSG = 2.0                # ~2 µm (sacrificial)
THICKNESS_POLY_ANCHOR = 200 * nm   # 0.2 µm (undoped, hard-mask a-Si → poly)
THICKNESS_POLY_MEMS = 500 * nm     # 0.5 µm (doped structural poly-Si)
THICKNESS_METAL = 500 * nm         # 0.5 µm (Al, lift-off)
THICKNESS_SUBSTRATE = 500.0        # ~500 µm handle wafer

# --- Z-positions (zmin = bottom of each layer) ---
ZMIN_SOI = 0.0
ZMIN_BOX = -THICKNESS_BOX                                        # -2.0
ZMIN_SUBSTRATE = ZMIN_BOX - THICKNESS_SUBSTRATE                   # -502.0
ZMIN_LTO = ZMIN_SOI + THICKNESS_SOI                               # 0.22
ZMIN_PSG = ZMIN_LTO + THICKNESS_LTO                               # 1.22
ZMIN_POLY_ANCHOR = ZMIN_SOI + THICKNESS_SOI                       # 0.22 (fills from SOI surface)
ZMIN_POLY_STRUCTURAL = ZMIN_PSG + THICKNESS_PSG                   # 3.22
ZMIN_METAL = ZMIN_POLY_STRUCTURAL + THICKNESS_POLY_MEMS           # 3.72


def get_layer_stack(
    thickness_soi: float = THICKNESS_SOI,
    thickness_box: float = THICKNESS_BOX,
    thickness_shallow_etch: float = THICKNESS_SHALLOW_ETCH,
    thickness_lto: float = THICKNESS_LTO,
    thickness_psg: float = THICKNESS_PSG,
    thickness_poly_anchor: float = THICKNESS_POLY_ANCHOR,
    thickness_poly_mems: float = THICKNESS_POLY_MEMS,
    thickness_metal: float = THICKNESS_METAL,
    thickness_substrate: float = THICKNESS_SUBSTRATE,
) -> LayerStack:
    """Return the LayerStack for the Optical MEMS process.

    All thicknesses are in µm.  Z-reference is the top of the SOI layer.
    """
    zmin_box = -thickness_box
    zmin_substrate = zmin_box - thickness_substrate
    zmin_lto = thickness_soi
    zmin_psg = zmin_lto + thickness_lto
    zmin_poly_anchor = thickness_soi
    zmin_poly_structural = zmin_psg + thickness_psg
    zmin_metal = zmin_poly_structural + thickness_poly_mems

    return LayerStack(
        layers=dict(
            # ---- Substrate & BOX ----
            substrate=LayerLevel(
                layer=LogicalLayer(layer=LAYER.SI_SUBSTRATE),
                thickness=thickness_substrate,
                zmin=zmin_substrate,
                material="si",
                mesh_order=99,
                info={"description": "Si handle wafer"},
            ),
            box=LayerLevel(
                layer=LogicalLayer(layer=LAYER.OXIDE_SOI),
                thickness=thickness_box,
                zmin=zmin_box,
                material="sio2",
                mesh_order=98,
                info={"description": "Buried oxide (BOX)"},
            ),
            # ---- SOI silicon ----
            si_full=LayerLevel(
                layer=LogicalLayer(layer=LAYER.SI_FULL),
                thickness=thickness_soi,
                zmin=0.0,
                material="si",
                mesh_order=1,
                info={"description": "SOI Si full thickness (220 nm)"},
            ),
            si_shallow_etch=LayerLevel(
                layer=LogicalLayer(layer=LAYER.MASK_SI_PARTIAL_ETCH),
                thickness=thickness_shallow_etch,
                zmin=0.0,
                material="si",
                mesh_order=1,
                layer_type="etch",
                into=["si_full"],
                info={"description": "70 nm shallow etch into SOI Si"},
            ),
            si_partial=LayerLevel(
                layer=LogicalLayer(layer=LAYER.SI_PARTIAL),
                thickness=thickness_soi - thickness_shallow_etch,
                zmin=0.0,
                material="si",
                mesh_order=2,
                info={"description": "SOI Si after shallow etch (150 nm slab)"},
            ),
            # ---- Oxides ----
            oxide_lto=LayerLevel(
                layer=LogicalLayer(layer=LAYER.OXIDE_LTO),
                thickness=thickness_lto,
                zmin=zmin_lto,
                material="sio2",
                mesh_order=10,
                info={"description": "LTO fill oxide (~1 µm, CMP)"},
            ),
            oxide_psg=LayerLevel(
                layer=LogicalLayer(layer=LAYER.OXIDE_PSG),
                thickness=thickness_psg,
                zmin=zmin_psg,
                material="sio2",
                mesh_order=11,
                info={"description": "PSG sacrificial oxide (~2 µm)"},
            ),
            # ---- Poly-silicon ----
            poly_anchor=LayerLevel(
                layer=LogicalLayer(layer=LAYER.POLY_ANCHOR),
                thickness=thickness_poly_anchor,
                zmin=zmin_poly_anchor,
                material="si",
                mesh_order=3,
                info={
                    "description": (
                        "Undoped poly-Si anchor (~200 nm). "
                        "Fills anchor etch holes from SOI surface upward."
                    ),
                    "doping": "undoped",
                },
            ),
            poly_mems=LayerLevel(
                layer=LogicalLayer(layer=LAYER.POLY_MEMS),
                thickness=thickness_poly_mems,
                zmin=zmin_poly_structural,
                material="si",
                mesh_order=2,
                info={
                    "description": (
                        "Doped poly-Si structural MEMS (~500 nm). "
                        "Partially etched for moving structures and comb fingers."
                    ),
                    "doping": "n-type (PSG dopant source)",
                },
            ),
            poly_top=LayerLevel(
                layer=LogicalLayer(layer=LAYER.POLY_TOP),
                thickness=thickness_poly_mems,
                zmin=zmin_poly_structural,
                material="si",
                mesh_order=2,
                info={
                    "description": (
                        "Doped poly-Si full thickness (~500 nm). "
                        "Same deposition as POLY_MEMS but unetched — "
                        "used for anchors and non-moving structures."
                    ),
                    "doping": "n-type (PSG dopant source)",
                },
            ),
            # ---- Metal ----
            metal=LayerLevel(
                layer=LogicalLayer(layer=LAYER.METAL),
                thickness=thickness_metal,
                zmin=zmin_metal,
                material="al",
                mesh_order=1,
                info={"description": "Aluminium (~500 nm, lift-off)"},
            ),
        )
    )


LAYER_STACK = get_layer_stack()


# =============================================================================
# Layer Views  (colors/styles for KLayout and matplotlib rendering)
# =============================================================================


class OpticalMEMSLayerViews(LayerViews):
    """Display settings for the Optical MEMS layers."""

    # --- Structure layers ---
    SI_FULL: LayerView = LayerView(
        layer=(1, 0), color="#4444cc", hatch_pattern="dotted", width=1
    )
    SI_PARTIAL: LayerView = LayerView(
        layer=(2, 0), color="#8888ff", hatch_pattern="coarsely dotted",
        transparent=True, width=1,
    )
    OXIDE_SOI: LayerView = LayerView(
        layer=(3, 0), color="#f3ff80", hatch_pattern="dotted",
        visible=False, width=1,
    )
    OXIDE_LTO: LayerView = LayerView(
        layer=(4, 0), color="#E9DD8A", hatch_pattern="coarsely dotted",
        visible=False, width=1,
    )
    OXIDE_PSG: LayerView = LayerView(
        layer=(5, 0), color="#439093", hatch_pattern="coarsely dotted",
        transparent=True, width=1,
    )
    POLY_ANCHOR: LayerView = LayerView(
        layer=(6, 0), color="#F09B93", hatch_pattern="left-hatched", width=1,
    )
    POLY_MEMS: LayerView = LayerView(
        layer=(7, 0), color="#EBD6D7", hatch_pattern="dotted", width=1,
    )
    POLY_TOP: LayerView = LayerView(
        layer=(8, 0), color="#F9EBD9", hatch_pattern="solid", width=1,
    )
    METAL: LayerView = LayerView(
        layer=(9, 0), color="#01ff6b", hatch_pattern="coarsely dotted", width=1,
    )
    SI_SUBSTRATE: LayerView = LayerView(
        layer=(10, 0), color="#999999", hatch_pattern="solid",
        visible=False, width=1,
    )

    # --- Mask layers ---
    MASK_SI_FULL_ETCH: LayerView = LayerView(
        layer=(11, 0), color="#0000cc", hatch_pattern="left-hatched",
        transparent=True, width=1,
    )
    MASK_SI_PARTIAL_ETCH: LayerView = LayerView(
        layer=(12, 0), color="#6666ff", hatch_pattern="left-hatched",
        transparent=True, width=1,
    )
    MASK_ANCHOR_ETCH: LayerView = LayerView(
        layer=(13, 0), color="#ff8800", hatch_pattern="cross-hatched",
        transparent=True, width=1,
    )
    MASK_PSG_ETCH: LayerView = LayerView(
        layer=(14, 0), color="#ffaa00", hatch_pattern="cross-hatched",
        transparent=True, width=1,
    )
    MASK_POLYSI_ETCH: LayerView = LayerView(
        layer=(15, 0), color="#ff4444", hatch_pattern="cross-hatched",
        transparent=True, width=1,
    )
    MASK_METAL_LIFTOFF: LayerView = LayerView(
        layer=(16, 0), color="#44ff44", hatch_pattern="cross-hatched",
        transparent=True, width=1,
    )

    # --- Dummy layers ---
    HARD_MASK: LayerView = LayerView(
        layer=(21, 0), color="#808080", hatch_pattern="coarsely dotted",
        visible=False, width=1,
    )
    RELEASE: LayerView = LayerView(
        layer=(22, 0), color="#ff66ff", hatch_pattern="hollow",
        transparent=True, width=1,
    )
    METAL_LIFTOFF_AUX: LayerView = LayerView(
        layer=(23, 0), color="#66ff66", hatch_pattern="hollow",
        visible=False, width=1,
    )

    # --- Utility layers ---
    FLOORPLAN: LayerView = LayerView(
        layer=(64, 0), color="pink", hatch_pattern="hollow",
    )
    TEXT: LayerView = LayerView(
        layer=(66, 0), color="gray", hatch_pattern="hollow", width=1,
    )
    DEVREC: LayerView = LayerView(
        layer=(68, 0), color="#004080", hatch_pattern="hollow",
        visible=False, transparent=True, width=1,
    )


LAYER_VIEWS = OpticalMEMSLayerViews()


# =============================================================================
# Cross-Sections
# =============================================================================
# Define common cross-sections used in the layout:
#   - strip waveguide (SOI full-thickness)
#   - rib waveguide (SOI with shallow etch)
#   - poly-Si MEMS routing (structural doped poly)
#   - metal routing


@xsection
def xs_strip(
    width: float = 0.5,
    layer: Layer = LAYER.SI_FULL,
    radius: float = 10.0,
    radius_min: float = 5.0,
    **kwargs,
) -> CrossSection:
    """Strip waveguide cross-section (full 220 nm SOI etch)."""
    return cross_section(
        width=width, layer=layer,
        radius=radius, radius_min=radius_min,
        **kwargs,
    )


@xsection
def xs_rib(
    width: float = 0.5,
    layer: Layer = LAYER.SI_FULL,
    radius: float = 10.0,
    radius_min: float = 5.0,
    slab_layer: Layer = LAYER.SI_PARTIAL,
    slab_width: float = 5.0,
    **kwargs,
) -> CrossSection:
    """Rib waveguide cross-section (70 nm shallow etch, 150 nm slab)."""
    sections = (
        gf.Section(layer=slab_layer, width=slab_width, offset=0),
    )
    return cross_section(
        width=width, layer=layer,
        radius=radius, radius_min=radius_min,
        sections=sections,
        **kwargs,
    )


@xsection
def xs_poly_mems(
    width: float = 1.5,
    layer: Layer = LAYER.POLY_MEMS,
    radius: float = 50.0,
    radius_min: float = 25.0,
    **kwargs,
) -> CrossSection:
    """Poly-Si MEMS interconnect cross-section (doped, structural)."""
    return cross_section(
        width=width, layer=layer,
        radius=radius, radius_min=radius_min,
        **kwargs,
    )


@xsection
def xs_metal(
    width: float = 5.0,
    layer: Layer = LAYER.METAL,
    radius: float = 50.0,
    radius_min: float = 25.0,
    **kwargs,
) -> CrossSection:
    """Metal routing cross-section (Al, lift-off)."""
    return cross_section(
        width=width, layer=layer,
        radius=radius, radius_min=radius_min,
        **kwargs,
    )


cross_sections = dict(
    xs_strip=xs_strip,
    xs_rib=xs_rib,
    xs_poly_mems=xs_poly_mems,
    xs_metal=xs_metal,
)


# =============================================================================
# Process Constants
# =============================================================================


class OpticalMEMSConstants(gf.Constants):
    """Process and design constants for the Optical MEMS PDK."""

    # --- Material properties ---
    youngs_modulus_poly_si: float = 160.0       # GPa (doped poly-Si)
    permittivity_free_space: float = 8.854e-12  # F/m

    # --- Process thicknesses (µm) ---
    thickness_soi: float = THICKNESS_SOI
    thickness_box: float = THICKNESS_BOX
    thickness_shallow_etch: float = THICKNESS_SHALLOW_ETCH
    thickness_lto: float = THICKNESS_LTO
    thickness_psg: float = THICKNESS_PSG
    thickness_poly_anchor: float = THICKNESS_POLY_ANCHOR
    thickness_poly_mems: float = THICKNESS_POLY_MEMS
    thickness_metal: float = THICKNESS_METAL

    # --- Design targets ---
    target_footprint: float = 250.0  # µm (basic), 200 µm (higher)
    target_voltage_basic: float = 20.0  # V
    target_voltage_higher: float = 10.0  # V
    target_frequency_basic: float = 100e3  # Hz
    target_frequency_higher: float = 200e3  # Hz


# =============================================================================
# Fabrication Process Steps
# =============================================================================
# This section documents the 16-step fabrication process as dataclasses.
# Can be used by simulation plugins (e.g., gplugins process simulation).

PROCESS_STEPS = [
    {"step": 0,   "name": "Start with SOI",
     "description": "SOI wafer: 220 nm Si / 2 µm BOX / Si substrate"},
    {"step": 1,   "name": "Si partial etch",
     "description": "70 nm shallow etch (Mask #1)", "mask": "MASK_SI_PARTIAL_ETCH"},
    {"step": 2,   "name": "Si full etch",
     "description": "Full 220 nm Si etch (Mask #2)", "mask": "MASK_SI_FULL_ETCH"},
    {"step": 3,   "name": "LTO deposition + CMP",
     "description": "~1 µm LTO deposition, planarized by CMP"},
    {"step": 4,   "name": "PSG deposition",
     "description": "~2 µm PSG sacrificial layer"},
    {"step": 5,   "name": "a-Si hard mask deposition",
     "description": "~200 nm a-Si deposited as hard mask"},
    {"step": 6,   "name": "a-Si hard mask litho + etch",
     "description": "Pattern hard mask (Mask #3)", "mask": "MASK_PSG_ETCH"},
    {"step": 7.1, "name": "PR coating",
     "description": "Photoresist coating for anchor etch"},
    {"step": 7.2, "name": "PR litho",
     "description": "Anchor etch lithography (Mask #4)", "mask": "MASK_ANCHOR_ETCH"},
    {"step": 7.3, "name": "Anchor etch",
     "description": "Etch through PSG/LTO to SOI (anchor holes)"},
    {"step": 7.4, "name": "PR removal",
     "description": "Strip photoresist"},
    {"step": 8,   "name": "PSG etch",
     "description": "Etch PSG using hard mask to define sacrificial gap"},
    {"step": 9,   "name": "Hard mask removal + a-Si deposition",
     "description": "Optional hard mask removal, then ~500 nm a-Si deposition"},
    {"step": 10,  "name": "PSG deposition",
     "description": "Second PSG deposition (dopant source)"},
    {"step": 11,  "name": "Annealing",
     "description": "Doping drive-in and a-Si → poly-Si crystallization"},
    {"step": 12,  "name": "Top PSG removal",
     "description": "Remove top PSG after doping"},
    {"step": 13,  "name": "poly-Si litho + etch",
     "description": "Define MEMS structures (Mask #5)", "mask": "MASK_POLYSI_ETCH"},
    {"step": 14,  "name": "Metal lift-off",
     "description": "500 nm Al deposition + lift-off (Mask #6)",
     "mask": "MASK_METAL_LIFTOFF"},
    {"step": 15,  "name": "Release",
     "description": "HF release of sacrificial PSG to free MEMS structures"},
]


# =============================================================================
# PDK Assembly
# =============================================================================
# Combine all definitions into a single Pdk object.

# Backward-compatible layer aliases used in the existing notebook.
# These let existing code keep working while transitioning to the new PDK.
LAYER_ALIASES = {
    "DPOLY": LAYER.POLY_MEMS,
    "PSG": LAYER.OXIDE_PSG,
    "UDPOLY": LAYER.POLY_ANCHOR,
    "UDOXIDE": LAYER.OXIDE_LTO,
    "METAL": LAYER.METAL,
    "SOI": LAYER.SI_FULL,
}


PDK = Pdk(
    name="optical_mems",
    version="0.1.0",
    layers=LAYER,
    layer_stack=LAYER_STACK,
    layer_views=LAYER_VIEWS,
    cross_sections=cross_sections,
    cells={},            # Populated as MEMS cells are added
    constants=OpticalMEMSConstants(),
    connectivity=[],     # No multi-metal routing in this process
)


def activate():
    """Activate the Optical MEMS PDK and return convenience layer aliases."""
    PDK.activate()

    # Return aliases for backward compatibility with existing notebook code
    return LAYER_ALIASES


# =============================================================================
# Convenience: allow running this file directly to preview the layer set
# =============================================================================

if __name__ == "__main__":
    PDK.activate()
    c = LAYER_VIEWS.preview_layerset()
    c.show()
    print("Optical MEMS PDK activated successfully.")
    print(f"  Layers:          {len(dict(LAYER))} defined")
    print(f"  Layer stack:     {len(LAYER_STACK.layers)} physical levels")
    print(f"  Cross-sections:  {len(cross_sections)}")
    print(f"  Process steps:   {len(PROCESS_STEPS)}")
    print(f"\nDesign rules summary:")
    for attr in sorted(vars(DESIGN_RULES)):
        if not attr.startswith("_"):
            print(f"  {attr}: {getattr(DESIGN_RULES, attr)} µm")