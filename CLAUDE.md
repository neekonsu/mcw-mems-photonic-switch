# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a photonic/optical chip tapeout project with two primary components:
- **comb-drive**: Comb drive component
- **switch-cell**: Switch cell component

## Design Workflow

The project follows a four-stage workflow:

1. **Geometry Definition (Python + Lumerical FDTD)**
   - Define 3D device geometries using Python
   - Each component has a Python script for Lumerical simulation setup

2. **Optical Simulation (Lumerical)**
   - Run FDTD simulations to validate device performance
   - Optimize geometries based on simulation results

3. **Layout Generation (GDS Factory + KLayout)**
   - Export validated designs to GDS format
   - Use GDS Factory for layout creation
   - Visualize and edit in KLayout

4. **Design Rule Checking (Synopsys Optocompiler)**
   - Run DRC checks on final layouts
   - Ensure manufacturing compliance

## Repository Structure

```
tower-tapeout/
├── comb-drive/
│   └── lumerical_sim.py    # Lumerical FDTD simulation setup
└── switch-cell/
    ├── geometry.py         # Device geometry definition (shared)
    ├── lumerical_sim.py    # Lumerical FDTD simulation setup
    ├── visualize_geometry.py  # Matplotlib visualization script
    └── figures/            # Timestamped geometry visualizations
        └── YYYYMMDD_HHMMSS/  # Each run gets its own folder
            ├── YYYYMMDD_HHMMSS_geometry_off.png
            ├── YYYYMMDD_HHMMSS_geometry_on.png
            └── YYYYMMDD_HHMMSS_comparison.png
```

## Common Commands

### Visualizing Geometry
```bash
# Visualize switch-cell geometry (both OFF and ON states)
cd switch-cell
python visualize_geometry.py

# Figures are automatically saved to figures/ with timestamps
```

### Running Lumerical Simulations
```bash
# Run simulation for comb-drive
cd comb-drive
python lumerical_sim.py

# Run simulation for switch-cell (OFF state - 550nm gap)
cd switch-cell
python lumerical_sim.py

# To simulate ON state (50nm gap), edit lumerical_sim.py:
# Change: gap_state = 'on'
```

## Architecture

### Geometry Definition Pattern
The switch-cell component uses a modular architecture for geometry definition:

1. **`geometry.py`**: Defines device geometry using dataclasses
   - `DirectionalCouplerGeometry` class encapsulates all geometric parameters
   - Provides methods: `get_parameters_dict()`, `get_waveguide_structures()`
   - Single source of truth for device dimensions

2. **`lumerical_sim.py`**: FDTD simulation using lumapi
   - Imports geometry from `geometry.py`
   - Creates simulation using `DirectionalCouplerGeometry` instance
   - Generates `.fsp` files in `results/`

3. **`visualize_geometry.py`**: Matplotlib visualization
   - Imports geometry from `geometry.py`
   - Generates multi-view plots (XY, XZ, YZ, 3D)
   - Saves figures to `figures/<timestamp>/` subdirectories
   - Each run creates a timestamped folder containing all related figures

### Switch-Cell Specifications
Based on Han et al., J. Optical Microsystems (2021):
- **Platform**: 220nm SOI (3μm BOX)
- **Waveguides**: 450nm wide, 20μm coupling length
- **Gap States**:
  - OFF: 550nm gap (weak coupling → light stays in same waveguide)
  - ON: 50nm gap (strong coupling → light crosses to opposite waveguide)
- **Actuation**: MEMS comb-drive (defined separately)

## Development Notes

- Geometry changes should be made in `geometry.py` only
- Run `visualize_geometry.py` after geometry changes to verify design
- Timestamped figures in `figures/` provide design history
- Python scripts use Lumerical's Python API (lumapi)
- GDS export happens after simulation validation
- Final DRC is performed with Synopsys Optocompiler before tapeout
