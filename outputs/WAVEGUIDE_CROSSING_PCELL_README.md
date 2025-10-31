# Parametric Waveguide Crossing PCell

## Overview

Successfully converted Shape 0001 (waveguide crossing) from the MEMS switch GDS into a fully parametric cell (PCell) using GDSFactory. The PCell enables parameter sweeps and optimization for optical performance.

## Original Design (Shape 0001)

- **Type**: 50-point polygon waveguide crossing
- **Size**: 36.6 × 34.9 µm
- **Waveguide width**: ~3.0 µm at center
- **Input width**: 0.4 µm (fixed for Si photonics)
- **Layer**: 1/0 (Si device layer)

## Parametric Cell Design

### Architecture

The crossing uses **4-fold rotational symmetry**:
1. **One arm** is defined with tapered sections
2. **Rotated 90°, 180°, 270°** to create full crossing
3. **Central square** connects all four arms

### Key Parameters

```python
@gf.cell
def waveguide_crossing(
    input_width: float = 0.4,              # Input waveguide width (µm)
    num_taper_sections: int = 8,           # Number of taper stages
    taper_lengths: List[float] = None,     # Length of each taper section (µm)
    taper_widths: List[float] = None,      # Width at each taper position (µm)
    center_width: float = 3.0,             # Central square size (µm)
    layer: Tuple[int, int] = (1, 0)        # GDS layer
)
```

### Structure

For the **left arm** (duplicated and rotated for other arms):

```
Input WG → Section 1 → Section 2 → ... → Section N → Center Square
(0.4 µm)   (L₁, w₁)    (L₂, w₂)         (Lₙ, wₙ)    (center_width)
```

- **taper_lengths**: Horizontal distance between each taper section
- **taper_widths**: Vertical width at each position (N+1 values total)
- **Linear interpolation** used by default for smooth tapers

## Generated Files

### Main PCell Module
- **`waveguide_crossing_pcell.py`**: Core PCell implementation
  - `waveguide_crossing()`: Main PCell function
  - `extract_taper_params_from_shape_0001()`: Extract default parameters

### Example Scripts
- **`crossing_sweep_example.py`**: Parameter sweep examples
  - Center width sweep (9 variants)
  - Taper length sweep (7 variants)
  - Number of sections sweep (6 variants)
  - Custom non-linear taper (1 variant)

### Generated GDS Files

#### Default Design
- `waveguide_crossing_pcell.gds` - 8 taper sections, 3.0 µm center

#### Center Width Sweep (`outputs/sweeps/`)
- `crossing_cw_1.00um.gds` through `crossing_cw_5.00um.gds` (9 files)

#### Taper Length Sweep
- `crossing_tl_1.00um.gds` through `crossing_tl_4.00um.gds` (7 files)

#### Number of Sections Sweep
- `crossing_n02.gds` through `crossing_n12.gds` (6 files)

#### Custom Profiles
- `crossing_quadratic_taper.gds` - Quadratic taper profile

**Total: 23 GDS files** ready for optical simulation

## Usage Examples

### 1. Basic Usage

```python
from waveguide_crossing_pcell import waveguide_crossing

# Create crossing with default parameters
crossing = waveguide_crossing(
    input_width=0.4,
    num_taper_sections=8,
    center_width=3.0,
    layer=(1, 0)
)

# Save to GDS
crossing.write_gds("my_crossing.gds")
```

### 2. Custom Taper Profile

```python
import numpy as np

# Linear taper from 0.4 to 3.0 µm over 8 sections
taper_widths = np.linspace(0.4, 3.0, 9).tolist()
taper_lengths = [2.25] * 8  # Equal section lengths

crossing = waveguide_crossing(
    num_taper_sections=8,
    taper_lengths=taper_lengths,
    taper_widths=taper_widths,
    center_width=3.0
)
```

### 3. Parameter Sweep

```python
# Sweep center width from 1 to 5 µm
for cw in np.linspace(1.0, 5.0, 9):
    taper_widths = np.linspace(0.4, cw, 9).tolist()

    crossing = waveguide_crossing(
        taper_widths=taper_widths,
        center_width=cw
    )

    crossing.write_gds(f"crossing_cw_{cw:.2f}um.gds")
```

## Optimization Workflow

### 1. Generate Design Variants (✅ Complete)

```bash
python components/crossing_sweep_example.py
```

This creates 23 GDS files with different parameter combinations.

### 2. Optical Simulation (Next Step)

**Lumerical FDTD Setup:**

1. **Import GDS** for each variant
2. **Set up simulation:**
   - Source: TE/TM mode at one input port
   - Monitors: All four output ports
   - Wavelength: 1520-1580 nm (C-band)
   - Mesh: Auto non-uniform (min 20 nm in Si core)

3. **Extract S-parameters:**
   - **S21**: Through port transmission (minimize insertion loss)
   - **S31**: Cross port coupling (minimize crosstalk)
   - **S11**: Reflection (minimize back-reflection)

4. **Metrics:**
   - **Insertion Loss**: -10·log₁₀(|S21|²) [dB]
   - **Crosstalk**: -10·log₁₀(|S31|²) [dB]
   - **Target**: < 0.5 dB insertion loss, > 30 dB crosstalk suppression

### 3. Parameter Optimization

Based on simulation results:

1. **Identify best performers** from each sweep
2. **Refine parameter ranges** around optimal values
3. **Run focused sweeps** with finer resolution
4. **Consider multi-objective optimization**:
   - Minimize insertion loss
   - Minimize crosstalk
   - Maximize bandwidth
   - Minimize footprint

## Design Parameters Summary

### Default Configuration (8 sections)

| Parameter | Value | Unit |
|-----------|-------|------|
| Input width | 0.4 | µm |
| Center width | 3.0 | µm |
| Num sections | 8 | - |
| Section length | 2.25 | µm |
| Total arm length | 18.0 | µm |
| Total size | 39.0 × 39.0 | µm |

### Parameter Ranges (for sweeps)

| Parameter | Min | Max | Typical | Unit |
|-----------|-----|-----|---------|------|
| Center width | 1.0 | 5.0 | 3.0 | µm |
| Section length | 1.0 | 4.0 | 2.25 | µm |
| Num sections | 2 | 12 | 8 | - |

## Files Generated

```
outputs/
├── waveguide_crossing_pcell.gds          # Default design
├── waveguide_crossing_pcell.png          # Visualization
├── waveguide_crossing_sweep.png          # 6 variants comparison
├── crossing_analysis.png                 # Original Shape 0001 analysis
└── sweeps/                               # Parameter sweep GDS files
    ├── crossing_cw_*.gds                 # Center width variants (9)
    ├── crossing_tl_*.gds                 # Taper length variants (7)
    ├── crossing_n*.gds                   # Num sections variants (6)
    └── crossing_quadratic_taper.gds      # Custom taper (1)
```

**Total: 24 GDS files (1 default + 23 sweep variants)**

## Next Steps

1. ✅ **PCell Implementation** - Complete
2. ✅ **Parameter Sweep Generation** - Complete
3. ⏭️ **Optical Simulation** - Import GDS into Lumerical FDTD
4. ⏭️ **Performance Analysis** - Extract S-parameters
5. ⏭️ **Optimization** - Refine parameters based on simulation
6. ⏭️ **Final Design** - Select optimal configuration for tapeout

## References

- Original design from: Han et al., "32 × 32 silicon photonic MEMS switch..." (J. Optical Microsystems, 2021)
- Shape 0001 from: `layouts/mems_switch_unit.gds`
- Analysis data: `outputs/cell_analysis_20251031_104647/shape_0001_L1_0_info.txt`

---

**Generated**: October 31, 2025
**Status**: PCell implementation complete, ready for optical simulation
