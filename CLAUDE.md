# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a silicon photonic MEMS switch tapeout project targeting **Tower Semiconductor SiPho 0.18μm 200mm process** for October MPW tapeout.

The design replicates the 32×32 silicon photonic MEMS switch described in:
**Han et al., "32 × 32 silicon photonic MEMS switch with gap-adjustable directional couplers fabricated in commercial CMOS foundry" (Journal of Optical Microsystems, 2021)**

### Primary Components:
- **Directional Coupler Switch Cell**: Gap-adjustable directional couplers (20μm length, 450nm width, 220nm thickness)
- **MEMS Comb-Drive Actuator**: 88μm × 88μm footprint, 44 comb finger pairs for gap tuning (550nm → 135nm)
- **Waveguide Crossings**: For signal routing in switch matrix
- **Grating Couplers**: Fiber-chip interface (640nm pitch, 50% duty cycle)

## Design Workflow

**IMPORTANT**: This project follows a **layout-first** workflow using GDSFactory. This is the industry-standard approach for silicon photonics that prevents "design lock-in" and enables design automation.

The workflow has 5 stages:

### 1. Layout Design (GDSFactory - Python)
**Why first:** Parametric, version-controlled layout generation enables design automation and rapid iteration
- Define all waveguides, directional couplers, gratings, MEMS structures as parameterized Python components
- Generate complete GDS layout files with proper layer assignments
- **Output:** `.gds` files ready for verification and simulation

### 2. Layout Verification (KLayout)
**Why now:** Visual inspection and preliminary checks before time-consuming simulation
- View complete layout and verify dimensions
- Check layer assignments (waveguide layer, etch layers, metal layers, etc.)
- Perform basic geometric checks
- **Output:** Verified layout ready for simulation

### 3. Optical Simulation (Lumerical FDTD/MODE)
**Why here:** After layout verification, simulate optical performance of critical components
- **Import GDS sections** (directional couplers, crossings, gratings)
- Run FDTD simulations for coupling vs. gap, transmission spectra
- Use MODE solver for waveguide mode analysis
- Extract S-parameters for circuit-level simulation
- **Output:** Validated optical performance data

### 4. Mechanical Simulation (Optional - COMSOL/ANSYS)
Can run in parallel with optical simulation
- Verify MEMS actuator displacement vs. voltage
- Calculate spring stiffness and resonance frequency
- Ensure gap tuning range meets requirements (550nm → 135nm)

### 5. Foundry DRC/LVS (Synopsys OptoCompiler)
**Why last:** Final validation against Tower SiPho foundry rules before tapeout
- Import final GDS layout
- Run Tower SiPho PDK-specific DRC checks
- Verify layer mappings to foundry process layers
- Fix any rule violations (return to Step 1 if geometry changes needed)
- **Output:** Manufacturing-ready tape-out file

**Workflow Rationale:** Layout-first prevents early DRC compliance from restricting later optimization. Optical simulation may reveal needed geometry changes, so it comes before final DRC verification.

## Repository Structure

**NOTE**: The repository is transitioning from an old simulation-first workflow to the new GDSFactory-first workflow described above. Legacy code in component directories will be replaced with GDSFactory-based layout generation.

```
tower-tapeout/
├── .gitattributes              # Git LFS configuration for .fsp files
├── documentation/
│   └── tower-switch-approach.md  # Design parameters and workflow reference (Han et al. paper)
├── switch-cell/                # [LEGACY - will be replaced]
│   ├── geometry.py             # Old Python geometry definitions (ExtrudedPolygon)
│   ├── lumerical_sim.py        # Old Lumerical simulation approach
│   └── visualize_geometry.py   # Old matplotlib visualization
├── waveguide-crossing/         # [LEGACY - reference only]
│   ├── metadata.json           # Component metadata
│   ├── waveguide_crossing.fsp  # Legacy Lumerical simulation (git-lfs tracked)
│   └── waveguide_crossing.lsf  # Legacy GDS export script
└── [NEW] components/           # [TO BE CREATED]
    ├── directional_coupler.py  # GDSFactory component for gap-adjustable DC
    ├── comb_drive.py           # GDSFactory component for MEMS actuator
    ├── grating_coupler.py      # GDSFactory component for fiber coupling
    ├── waveguide_crossing.py   # GDSFactory component for waveguide crossing
    └── switch_cell.py          # Complete switch cell assembly
```

### Future Repository Structure (GDSFactory-based)
```
tower-tapeout/
├── components/                 # GDSFactory component library
├── layouts/                    # Generated GDS files
│   ├── directional_coupler.gds
│   ├── comb_drive.gds
│   └── full_chip.gds
├── simulations/                # Lumerical simulation files (import GDS)
│   ├── dc_sweep/               # Directional coupler gap sweep simulations
│   └── grating/                # Grating coupler simulations
├── drc/                        # DRC reports and scripts
└── documentation/              # Design reference documents
```

## Common Commands

### Workflow Commands (GDSFactory-based)

#### 1. Generate GDS Layouts (GDSFactory)
```bash
# Generate individual component GDS files
python components/directional_coupler.py   # Outputs: layouts/directional_coupler.gds
python components/comb_drive.py            # Outputs: layouts/comb_drive.gds
python components/switch_cell.py           # Outputs: layouts/switch_cell.gds

# Generate full chip layout
python components/full_chip.py             # Outputs: layouts/full_chip.gds
```

#### 2. View Layouts (KLayout)
```bash
# Open individual components
klayout layouts/directional_coupler.gds
klayout layouts/comb_drive.gds

# Open full chip layout
klayout layouts/full_chip.gds
```

#### 3. Run Optical Simulations (Lumerical)
```bash
# Lumerical simulations import GDS sections for optical analysis
# These are interactive - open in Lumerical FDTD Solutions GUI

# Example workflow:
# 1. Open Lumerical FDTD Solutions
# 2. Import GDS: File > Import > GDS
# 3. Select simulation region and run sweep
# 4. Export S-parameters or transmission data
```

#### 4. Run DRC (Synopsys OptoCompiler)
```bash
# Run Tower SiPho DRC checks (requires Tower PDK)
# Typically done via OptoCompiler GUI or batch scripts

# Example batch command (when PDK is available):
# optocompiler -drc -pdk tower_sipho_018 -input layouts/full_chip.gds
```

### Legacy Commands (Old Workflow)
These commands reference the old simulation-first approach and will be deprecated:

```bash
# Old: Visualize switch-cell geometry (matplotlib-based)
cd switch-cell
python visualize_geometry.py

# Old: Run Lumerical simulation from Python geometry
cd switch-cell
python lumerical_sim.py
```

## Architecture

### GDSFactory Design Pattern
The new workflow uses **GDSFactory** for parametric layout generation:

#### Component Design Philosophy
Each photonic component is defined as a **parameterized Python function** that returns a GDSFactory `Component` object:

```python
import gdsfactory as gf

@gf.cell
def directional_coupler(
    length: float = 20.0,      # Coupling length (μm)
    width: float = 0.45,       # Waveguide width (μm)
    gap: float = 0.55,         # Waveguide gap (μm)
    layer: tuple = (1, 0)      # GDS layer
) -> gf.Component:
    """Gap-adjustable directional coupler for MEMS switch."""
    c = gf.Component()
    # Define waveguide geometry, ports, etc.
    return c
```

#### Key Architecture Principles
1. **Parameterization**: All dimensions are function parameters (enables optimization sweeps)
2. **Layer Management**: GDS layers map to Tower SiPho process layers
3. **Port Definitions**: Components have optical ports for automatic routing
4. **Hierarchical Assembly**: Complex devices built from simpler components
5. **Version Control**: Python code is easily tracked in git (unlike binary GDS)

#### Component Hierarchy
```
switch_cell (top-level assembly)
├── directional_coupler × 2
├── comb_drive (MEMS actuator)
│   ├── comb_fingers × 44
│   └── springs × 4
└── waveguide_sections (routing)
```

### Design Specifications
Based on Han et al., J. Optical Microsystems (2021):

#### SOI Platform
- **Device layer (Si)**: 220 nm thickness
- **BOX layer (SiO2)**: 3 μm thickness
- **Handle wafer (Si)**: 725 μm (standard for 200mm)

#### Directional Coupler Switch Cell
- **Coupling length**: 20 μm
- **Waveguide width**: 450 nm
- **Waveguide thickness**: 220 nm (device layer)
- **Initial gap (OFF state)**: 550 nm → weak coupling, light stays in same waveguide
- **Optimal gap (ON state)**: 135 nm → strong coupling, light crosses waveguides
- **Gap tuning range**: 0 nm to 550 nm

#### MEMS Comb-Drive Actuator
- **Footprint**: 88 μm × 88 μm
- **Comb finger pairs**: 44
- **Finger width**: 300 nm
- **Finger spacing**: 400 nm
- **Finger thickness**: 220 nm (device layer)
- **Spring width**: 300 nm
- **Spring length**: 30 μm per spring
- **Number of springs**: 4 (folded configuration)

#### Grating Couplers (Fiber Interface)
- **Pitch**: 640 nm
- **Duty cycle**: 50%
- **Etch depth**: 70 nm
- **Bandwidth**: 30 nm

#### Overall Layout
- **Switch matrix area**: 5.9 mm × 5.9 mm (32×32 array)
- **Waveguide pitch**: 166 μm
- **Grating coupler + routing area**: 0.7 mm × 8.4 mm

## Development Notes

### Current Status (Workflow Transition)
- **Workflow Migration**: 🚧 Transitioning from simulation-first to GDSFactory-first approach
- **Legacy Code**: Switch-cell and waveguide-crossing directories contain old workflow code (will be replaced)
- **New GDSFactory Components**: 📋 To be implemented (see Repository Structure above)
- **Tower SiPho PDK**: 📋 To be obtained for DRC verification
- **Documentation**: ✅ Design specifications compiled in `documentation/tower-switch-approach.md`

### Development Workflow (GDSFactory-based)

#### 1. Creating New Components
```python
# Template for new GDSFactory component
import gdsfactory as gf

@gf.cell
def my_component(param1: float = 1.0, layer: tuple = (1, 0)) -> gf.Component:
    """Component description."""
    c = gf.Component("my_component")

    # Add geometry using GDSFactory primitives
    # rect = gf.components.rectangle(size=(10, 5), layer=layer)
    # c.add_ref(rect)

    # Define optical ports for routing
    # c.add_port(name="o1", center=[0, 0], width=0.5, orientation=0, layer=layer)

    return c

# Generate GDS file
if __name__ == "__main__":
    c = my_component()
    c.write_gds("layouts/my_component.gds")
    c.show()  # Open in KLayout viewer
```

#### 2. Parameter Sweeps and Optimization
```python
# Generate design variants for gap sweep
for gap in [0.05, 0.10, 0.15, 0.20, 0.30, 0.55]:  # μm
    c = directional_coupler(gap=gap)
    c.write_gds(f"layouts/dc_gap_{int(gap*1000)}nm.gds")
```

#### 3. Design Verification Checklist
- [ ] **Visual Check**: Open GDS in KLayout, verify dimensions
- [ ] **Layer Check**: Confirm all layers map to Tower SiPho process
- [ ] **Port Check**: Verify optical port locations and orientations
- [ ] **Overlap Check**: Use KLayout DRC mode for basic overlap detection
- [ ] **Dimension Check**: Measure critical dimensions (gaps, widths) in KLayout

### Best Practices

#### GDSFactory Design
- **Use parameterized components**: All dimensions should be function parameters
- **Define clear ports**: Optical ports enable automatic routing between components
- **Use layer constants**: Define layer tuples as named constants (e.g., `LAYER_WG = (1, 0)`)
- **Version control**: Commit Python code frequently; GDS files are generated artifacts
- **Test components individually**: Generate and verify each component before assembly

#### Lumerical Simulation
- **Import GDS sections**: Use "Import GDS" in Lumerical, not Python API geometry
- **Set material properties**: Silicon (Palik), SiO2 (Palik) for accurate refractive indices
- **Use symmetry**: Enable symmetry boundaries to reduce simulation time
- **Mesh refinement**: Use override mesh for critical regions (waveguide cores, gaps)

#### Tower SiPho Foundry Process
- **Layer mapping**: Map GDSFactory layers to Tower process layers (requires PDK documentation)
- **Design rules**: Follow minimum width, spacing, and density rules from foundry
- **DRC early and often**: Run preliminary DRC checks before final tape-out
- **Keep backups**: Save working GDS versions before major changes

### Git Configuration
- **Git LFS**: Large binary files (`.fsp`, `.gds` archives) tracked with git-lfs
- Ensure git-lfs is installed: `git lfs install`
- Current tracked extensions: `*.fsp` (Lumerical simulation files)
- Consider adding: `*.gds` if files become very large (typically keep small GDS in git)

### Reference Documents
- **`documentation/tower-switch-approach.md`**: Complete design parameters from Han et al. paper
- **Han et al. paper**: "32 × 32 silicon photonic MEMS switch..." (J. Optical Microsystems, 2021)
- **Tower SiPho PDK**: Obtain from foundry for layer mapping and DRC rules
