# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Silicon photonic MEMS switch tapeout targeting **Tower Semiconductor SiPho 0.18μm 200mm process**. The design replicates the 32×32 silicon photonic MEMS switch from Han et al. (J. Optical Microsystems, 2021) with gap-adjustable directional couplers.

## Environment Setup

```bash
# Local conda environment prefix at switch-env/ (Python 3.11, gitignored)
# Activate using the prefix path:
conda activate ./switch-env

# Or run commands directly via the prefix Python:
./switch-env/bin/python <script>

# Key dependencies: gdsfactory>=7.0.0, klayout>=0.28.0, numpy, scipy, matplotlib, shapely
# environment.yml defines the env spec (name: tower-tapeout)
```

## Common Commands

```bash
# Run the main assembly notebook (generates MEMS layout)
jupyter notebook src/mems_test_cell_components.ipynb

# Run individual component notebooks
jupyter notebook src/components/comb_drive/comb_drive.ipynb

# Preview PDK layer set
python src/libraries/mcw_custom_optical_mems_pdk.py

# View generated GDS layouts in KLayout
klayout layouts/mems.gds
# With custom layer properties:
klayout layouts/mems.gds -ly src/libraries/mcw_custom_optical_mems_layers.lyp
```

No build system, tests, or linter are configured. Development is notebook-driven.

## Repository Structure

```
src/
├── libraries/
│   ├── mcw_custom_optical_mems_pdk.py        # Custom PDK (layers, design rules, layer stack, cross-sections)
│   ├── mcw_custom_optical_mems_layers.lyp     # KLayout layer properties file
│   └── mcw_custom_optical_mems_pdk_2d5.lyd25  # KLayout 2.5D layer stack definition
├── mems_test_cell_components.ipynb            # Main assembly notebook (all components + positioning)
└── components/                                # Individual component notebooks
    ├── comb_drive/comb_drive.ipynb             # Fixed and moving comb drives
    ├── folded_spring/folded_spring.ipynb       # Folded-spring flexure
    ├── shuttle_beam/shuttle_beam.ipynb         # Shuttle body with etch holes
    ├── interconnect/interconnect.ipynb         # Beam + anchored pad
    ├── island/island.ipynb                     # U-shaped comb-drive node frame
    ├── etch_hole/etch_hole.ipynb               # Single etch hole primitive
    ├── bus_waveguide/                           # [empty template]
    ├── transfer_waveguide/                      # [empty template]
    ├── waveguide_crossing/                      # [empty template]
    ├── bistable_spring/                         # [empty template]
    └── bistable_folded_spring/                  # [empty template]
layouts/
├── mems.gds                                   # Generated MEMS layout (git-lfs tracked)
└── reference-layouts/                         # Reference GDS files from Han et al. and MCW lab
docs/
└── mcw-optical-mems-master-document.xlsx      # Master document (layers, fab process, design rules, targets)
```

## Architecture

### Design Workflow

This project follows a **layout-first** workflow: GDSFactory layout → KLayout verification → Lumerical optical simulation → foundry DRC. Layout comes first so optical simulation results can inform geometry changes before final DRC.

### Custom PDK (`src/libraries/mcw_custom_optical_mems_pdk.py`)

Central file defining the entire process technology. Import with:
```python
import sys
sys.path.insert(0, "../../libraries")
from mcw_custom_optical_mems_pdk import LAYER, LAYER_STACK, PDK, DESIGN_RULES
```

Key exports:
- **`LAYER`** (LayerMap): Structure layers (1-10)/0, mask layers (11-16)/0, dummy layers (21-23)/0
- **`DESIGN_RULES`**: Widths, gaps, enclosures, extensions, areas, MEMS structural, photonic, and geometry integrity rules (all in μm)
- **`LAYER_STACK`**: Physical cross-section with Z-reference at SOI surface (0 μm)
- **`PDK`**: GDSFactory Pdk object combining all definitions
- **`activate()`**: Activates PDK and returns `LAYER_ALIASES` dict for backward compatibility
- **Cross-sections**: `xs_strip` (SOI waveguide), `xs_rib` (shallow etch), `xs_poly_mems`, `xs_metal`

### Layer Aliases (Backward Compatibility)

The main notebook currently uses placeholder layer tuples that don't match the PDK. The `LAYER_ALIASES` dict maps old names to correct PDK layers:

| Notebook name | Alias        | PDK layer           | GDS (layer, datatype) |
|---------------|-------------|---------------------|-----------------------|
| `DPOLY`       | POLY_MEMS    | Doped structural poly-Si | (7, 0) |
| `PSG`         | OXIDE_PSG    | Sacrificial oxide   | (5, 0) |
| `UDPOLY`      | POLY_ANCHOR  | Undoped anchor poly | (6, 0) |
| `UDOXIDE`     | OXIDE_LTO    | LTO fill oxide      | (4, 0) |
| `METAL`       | METAL        | Aluminium           | (9, 0) |
| `SOI`         | SI_FULL      | SOI silicon         | (1, 0) |

**Important**: The main assembly notebook (`mems_test_cell_components.ipynb`) still uses the old placeholder layers and needs to be updated to import from the custom PDK.

### Component Architecture

All components are GDSFactory `Component` objects built with `gf.Component()`, `add_polygon()`, `add_ref()`, and `gf.boolean()`. The main notebook (`mems_test_cell_components.ipynb`) defines all component functions inline and assembles them with explicit `move()`/`mirror_x()`/`mirror_y()` positioning.

Component hierarchy:
```
mems (top-level assembly)
├── shuttle (body with etch-hole array)
├── spring × 4 (folded-spring flexures, mirrored pairs)
├── fixed_comb_drive × 4 (stator, anchored, mirrored pairs)
├── moving_comb_drive × 4 (rotor, freed during release)
├── interconnect × 4 (electrical connections with anchored pads)
└── comb_drive_node (U-shaped frame connecting fixed combs)
```

Components use multi-layer construction: structural poly-Si (POLY_MEMS) for geometry, OXIDE_PSG for release windows, POLY_ANCHOR/SI_FULL for anchor pads. Moving parts omit anchor layers.

### Key Design Parameters

- **SOI**: 220 nm Si on 2 μm BOX
- **Poly-Si structural**: 500 nm doped, on top of 2 μm PSG sacrificial gap
- **6-mask process**: Si partial etch, Si full etch, PSG etch, anchor etch, poly-Si etch, metal lift-off
- **17 fabrication steps** documented in `PROCESS_STEPS` list in PDK file (step 9 split into 9.1 hard mask removal + 9.2 a-Si deposition)
- **Target displacement**: 550 nm (comb-drive gap tuning for directional coupler switching)

### Design Targets (from master spreadsheet)

| Parameter | Basic | Higher |
|-----------|-------|--------|
| Frequency | 100 kHz | 200 kHz |
| Voltage | 20 V | 10 V |
| ER (OFF state) | 20 dB | 30 dB |
| ER (thru port) | 15 dB | 20 dB |
| Insertion loss | 0.5 dB | 0.2 dB |
| Footprint | 250 μm | 200 μm |

### Design Rules Summary

The `DESIGN_RULES` object contains ~50 rules organized by category. Rule IDs reference the "Layer Specifications" tab of `docs/mcw-optical-mems-master-document.xlsx`:

- **W.01–W.08**: Minimum widths (Si, anchor, PSG, metal, poly-Si, hard mask, release)
- **S.01–S.07**: Minimum gaps/spaces
- **E.01–E.07**: Enclosure rules (A encloses B)
- **X.01–X.04**: Extension/overlap rules
- **G.01–G.07**: Inter-layer gap rules
- **A.01–A.04**: Minimum area rules
- **M.01–M.08**: MEMS structural rules (max span, release holes, anchor aspect ratio, comb AR, spring width, isolation gap)
- **P.01–P.05**: Photonic rules (bend radii, waveguide-to-MEMS/metal clearance, coupler tolerance)
- **I.01–I.03**: Geometry integrity (min angle, notch width, grid snap)

### Git LFS

`.gds` and `.fsp` files are tracked by git-lfs (see `.gitattributes`).
