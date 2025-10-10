# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a photonic/optical chip tapeout project with three primary components:
- **comb-drive**: MEMS comb-drive actuator component (in development)
- **switch-cell**: Gap-adjustable directional coupler switch cell
- **waveguide-crossing**: Waveguide crossing component with GDS export

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
├── .gitattributes          # Git LFS configuration for .fsp files
├── comb-drive/
│   └── lumerical_sim.py    # Lumerical FDTD simulation setup (in development)
├── switch-cell/
│   ├── geometry.py         # Device geometry definition using ExtrudedPolygon classes
│   ├── lumerical_sim.py    # Lumerical FDTD simulation setup (in development)
│   ├── visualize_geometry.py  # Matplotlib visualization script
│   └── figures/            # Timestamped geometry visualizations
│       └── YYYYMMDD_HHMM/  # Each run creates folder (timestamp to minute)
│           ├── YYYYMMDD_HHMMSS_combined.png
│           ├── YYYYMMDD_HHMMSS_<name>_xy.png
│           └── YYYYMMDD_HHMMSS_<name>_3d.png
└── waveguide-crossing/
    ├── metadata.json       # Component metadata and reference
    ├── waveguide_crossing.fsp  # Lumerical FDTD simulation (tracked with git-lfs)
    ├── waveguide_crossing.lsf  # GDS export script
    ├── waveguide_crossing.gds  # Exported GDS file
    ├── GDS_auto_export.lsf     # GDS auto-export helper
    └── GDSexport_core.lsfx     # GDS export core library
```

## Common Commands

### Visualizing Geometry
```bash
# Visualize switch-cell geometry
cd switch-cell
python visualize_geometry.py

# Figures are automatically saved to figures/YYYYMMDD_HHMM/ with timestamps
# - Combined view: YYYYMMDD_HHMMSS_combined.png
# - Individual views: YYYYMMDD_HHMMSS_<name>_xy.png and _3d.png
```

### Running Lumerical Simulations
```bash
# Run simulation for comb-drive (currently in development)
cd comb-drive
python lumerical_sim.py

# Run simulation for switch-cell (currently in development)
cd switch-cell
python lumerical_sim.py

# Waveguide crossing simulation (already completed)
# - Simulation file: waveguide-crossing/waveguide_crossing.fsp
# - GDS export: Run waveguide_crossing.lsf in Lumerical
```

### Exporting to GDS
```bash
# Waveguide crossing GDS export (from Lumerical)
cd waveguide-crossing
# Run in Lumerical: waveguide_crossing.lsf
# Output: waveguide_crossing.gds
```

## Architecture

### Geometry Definition Pattern
The switch-cell component uses a modular architecture for geometry definition:

1. **`geometry.py`**: Defines 3D geometries as extruded 2D polygons
   - `ExtrudedPolygon` base class: Represents 3D structures extruded in Z
   - `Waveguide` and `Switch` subclasses: Specialized geometry types
   - Helper functions: `create_rectangle()`, `create_waveguide_rectangle()`
   - `get_example_geometries()`: Creates test geometries for visualization
   - All dimensions stored in microns for consistency

2. **`lumerical_sim.py`**: FDTD simulation using lumapi (in development)
   - Imports geometry from `geometry.py`
   - Will create simulation using ExtrudedPolygon geometry objects
   - Will generate `.fsp` files for Lumerical

3. **`visualize_geometry.py`**: Matplotlib visualization
   - Imports geometry classes from `geometry.py`
   - Generates XY plane outlines and 3D extruded views
   - Saves figures to `figures/YYYYMMDD_HHMM/` subdirectories
   - Each run creates a minute-stamped folder with second-stamped files
   - Supports both combined and individual geometry views
   - Uses equal aspect ratio scaling to preserve true dimensions

### Switch-Cell Specifications
Based on Han et al., J. Optical Microsystems (2021):
- **Platform**: 220nm SOI (3μm BOX)
- **Waveguides**: 450nm wide, 20μm coupling length
- **Gap States**:
  - OFF: 550nm gap (weak coupling → light stays in same waveguide)
  - ON: 50nm gap (strong coupling → light crosses to opposite waveguide)
- **Actuation**: MEMS comb-drive (defined separately)

### Waveguide-Crossing Component
Standard waveguide crossing for routing photonic signals:
- **Source**: Based on Ansys Lumerical guide (see metadata.json)
- **Status**: Completed - simulation and GDS export done
- **Files**:
  - `.fsp` file contains complete FDTD simulation (tracked with git-lfs)
  - `.lsf` scripts handle automated GDS export
  - `.gds` file ready for integration into final layout
- **Platform**: 220nm SOI with handle and BOX layers defined
- **Materials**: Silicon (Palik) waveguides, SiO2 (Palik) BOX layer

## Development Notes

### Current Status
- **waveguide-crossing**: ✅ Complete (simulation and GDS export done)
- **switch-cell**: 🚧 Geometry definition complete, simulation in development
- **comb-drive**: 🚧 Simulation setup in development

### Best Practices
- Geometry changes for switch-cell should be made in `geometry.py` only
- Run `visualize_geometry.py` after geometry changes to verify design
- Timestamped figures in `figures/` provide design history and version tracking
- Python scripts use Lumerical's Python API (lumapi)
- GDS export happens after simulation validation
- Final DRC is performed with Synopsys Optocompiler before tapeout

### Git Configuration
- **Git LFS**: Large `.fsp` files are tracked with git-lfs (see `.gitattributes`)
- This prevents bloating the repository with large binary simulation files
- Ensure git-lfs is installed before cloning: `git lfs install`

### File Organization
- Each component has its own directory with self-contained scripts
- Lumerical simulation files (`.fsp`) are component-specific
- GDS files are exported per component, then integrated for final tapeout
- Visualization figures use hierarchical timestamps (minute-level folders, second-level files)
