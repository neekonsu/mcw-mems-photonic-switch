# Tower SiPho MEMS Switch Design Approach

## Reference Design Overview

This document aggregates key design parameters and workflow information for replicating the 32×32 silicon photonic MEMS switch described in Han et al., "32 × 32 silicon photonic MEMS switch with gap-adjustable directional couplers fabricated in commercial CMOS foundry" (Journal of Optical Microsystems, 2021).

Target fabrication: Tower Semiconductor SiPho 0.18μm 200mm process, October MPW tapeout.

---

## Design Geometry Parameters

### Explicitly Stated Dimensions

**Directional Couplers:**
- Length: 20 μm
- Waveguide width: 450 nm
- Waveguide thickness: 220 nm
- Initial gap: 550 nm
- Optimal (actuated) gap: 135 nm
- Gap tuning range: ~0 nm to 550 nm

**Comb-Drive Actuator:**
- Footprint: 88 μm × 88 μm
- Number of comb finger pairs: 44
- Comb finger width: 300 nm
- Comb finger spacing (gap): 400 nm
- Comb finger thickness: 220 nm (same as device layer)
- Spring width: 300 nm
- Spring length: 30 μm
- Number of springs: 4 (folded configuration)

**Overall Layout:**
- Switch matrix area: 5.9 mm × 5.9 mm
- Waveguide pitch: 166 μm
- Grating coupler + routing area: 0.7 mm × 8.4 mm

**Grating Couplers:**
- Pitch: 640 nm
- Duty cycle: 50%
- Etch depth: 70 nm
- Bandwidth: 30 nm

**Substrate:**
- SOI device layer: 220 nm
- BOX layer: 3 μm

### Missing or Unclear Details

The following parameters need to be inferred from context, images, or conventional design practices:

1. **Directional coupler taper geometry** - No mention of whether waveguides have tapers at coupling region entry/exit
2. **Exact spring geometry** - Folded spring detailed shape/routing not specified
3. **Actuator anchor point locations** - Exact positioning relative to couplers unclear
4. **Waveguide routing between components** - Bend radii, routing strategy not detailed
5. **Metal pad dimensions** - Size and placement specifications not given
6. **Grating coupler footprint** - Lateral dimensions not stated
7. **Waveguide crossing design details** - Only referenced (Refs 21, 22) but not described
8. **Gap-to-voltage calibration curve specifics** - Mentioned 9.45V average but full actuation curve not detailed
9. **Comb finger overlap length** - Critical for force calculation, not explicitly stated
10. **Exact mechanical coupling between actuator and both directional couplers** - Movement transfer mechanism not fully detailed

---

## Wafer Specifications

### Si Substrate Thickness

**Standard SOI wafer structure for 200mm silicon photonics:**
- Device layer (Si): 220 nm (stated)
- BOX (SiO2): 3 μm (stated)
- **Handle wafer (Si substrate): 725 μm** (standard for 200mm wafers)

---

## Tool Workflow

### Conventional Workflow for Silicon Photonic MEMS Design

**1. Layout Design: GDSFactory (Python)**
- **Why first:** Parametric, version-controlled layout generation; enables design automation and rapid iteration
- **What you do:** Define all waveguides, couplers, gratings, MEMS structures as parameterized components; generate GDS file
- **Output:** `.gds` file with all layers properly defined

**2. Layout Verification: KLayout**
- **Why now:** Visual inspection and preliminary layer checking before simulation
- **What you do:** View layout, check layer assignments, verify dimensions, perform basic geometric checks
- **Why this order:** Catch obvious errors before time-consuming simulation

**3. Optical Simulation: Lumerical (FDTD/MODE)**
- **Why here:** After layout is verified, simulate optical performance of critical components
- **What you do:** 
  - Import GDS sections (directional couplers, crossings, gratings)
  - Run FDTD for coupling vs. gap, transmission spectra
  - Use MODE for waveguide mode analysis
  - Extract S-parameters for circuit simulation
- **Why this order:** Layout must be finalized for geometry; optical performance informs if redesign needed before DRC

**4. Mechanical Simulation: (Typically COMSOL/ANSYS, but can extract from layout)**
- **What you do:** Verify actuator displacement, spring stiffness, resonance frequency
- **Note:** Often done in parallel with optical simulation

**5. Foundry DRC/LVS: Synopsys OptoCompiler/OptoDesigner**
- **Why last:** Final validation against foundry rules before tapeout
- **What you do:** 
  - Import final GDS
  - Run Tower SiPho PDK-specific DRC checks
  - Verify layer mappings to foundry process
  - Generate final tape-out file
- **Why this order:** Only run expensive DRC on fully designed and simulated layout; DRC fixes are layout-only (return to step 1 if needed)

**Key Workflow Note:** This order prevents "design lock-in" where early DRC compliance restricts later optimization. Lumerical simulations may reveal needed geometry changes that would require DRC re-verification anyway, so optical validation comes first.

---

## Workflow Summary

1. Begin GDSFactory layout code for basic components
2. Infer missing parameters from paper figures and conventional design practices
3. Set up Lumerical simulation templates for directional couplers
4. Obtain Tower SiPho PDK for layer mapping and DRC rules

---

## Development Environment Setup

This section documents the installation and setup process for the GDSFactory-based design workflow.

### Prerequisites

- **Miniforge/Mambaforge**: Package and environment management
  - Provides `conda` and `mamba` commands
  - Download from: https://github.com/conda-forge/miniforge

### Installation Steps

#### 1. Create Conda Environment

Navigate to the project directory and create the environment from the provided configuration file:

```bash
cd /Users/neekon/git/mcw/tower-tapeout
mamba env create -f environment.yml
```

The `environment.yml` file includes:
- **Python 3.11**: Base interpreter
- **GDSFactory ≥7.0.0**: Parametric layout generation
- **KLayout ≥0.28.0**: GDS viewer and editor
- **NumPy, SciPy, Matplotlib**: Scientific computing and visualization
- **Pandas, Shapely**: Data handling and geometry operations

#### 2. Activate Environment

```bash
conda activate tower-tapeout
```

**Note**: Always activate this environment before running any design scripts.

#### 3. Verify Installation

Run the provided test script to verify all packages are correctly installed:

```bash
python test_setup.py
```

Expected output:
```
==================================================
GDSFactory Setup Verification
==================================================
Testing package imports...
✓ GDSFactory 9.19.0 (or later)
✓ NumPy 2.3.3 (or later)
✓ Matplotlib 3.10.7 (or later)

Testing basic component creation...
✓ Created component 'test_rect'
✓ Created built-in rectangle component

==================================================
✓ All tests passed! Setup is complete.
==================================================
```

### Repository Structure

The setup process creates the following directory structure:

```
tower-tapeout/
├── environment.yml          # Conda environment specification
├── .gitignore              # Python/conda artifacts excluded from git
├── test_setup.py           # Installation verification script
├── components/             # GDSFactory component definitions (Python)
├── layouts/                # Generated GDS layout files
├── simulations/            # Lumerical simulation files
├── drc/                    # DRC reports and scripts
└── documentation/          # Design documentation
    └── tower-switch-approach.md
```

### Common Commands

#### Environment Management

```bash
# Activate environment
conda activate tower-tapeout

# Deactivate environment
conda deactivate

# Update environment from yml file
mamba env update -f environment.yml

# List installed packages
conda list

# Remove environment (if needed)
conda env remove -n tower-tapeout
```

#### Running Design Scripts

All Python scripts should be run with the `tower-tapeout` environment activated:

```bash
# Activate environment first
conda activate tower-tapeout

# Generate a component layout
python components/directional_coupler.py

# Run verification tests
python test_setup.py
```

#### Viewing GDS Files

```bash
# Open GDS file in KLayout (if installed via conda)
klayout layouts/directional_coupler.gds

# Or use system KLayout installation
# macOS:
open -a KLayout layouts/directional_coupler.gds
```

### Troubleshooting

**Issue**: `mamba: command not found`
- **Solution**: Ensure Miniforge is installed and shell is restarted. Try using `conda` instead of `mamba`.

**Issue**: `ModuleNotFoundError: No module named 'gdsfactory'`
- **Solution**: Ensure the `tower-tapeout` environment is activated: `conda activate tower-tapeout`

**Issue**: KLayout not opening GDS files
- **Solution**: Install KLayout separately from https://www.klayout.de if conda installation has issues

### Next Steps

After successful installation:

1. Review the component design examples in `CLAUDE.md`
2. Start implementing the directional coupler component
3. Use KLayout to visualize generated layouts
4. Reference Han et al. paper for design parameters