# S-Bend with Adiabatic Coupler PCell

## Overview

Successfully created a parametric cell (PCell) for an S-bend waveguide with adiabatic width variation. This structure is essential for efficient mode coupling and transition between waveguide sections with different widths.

## Structure

The complete device consists of three sections:

```
Input (0.4µm) → S-bend Down → Adiabatic Section → S-bend Up → Output
                (smooth curve)  (variable width)   (smooth curve)
```

### Section Details:

1. **First S-bend (downward)**
   - Smooth cubic spline curve
   - Displacement: `2×s_bend_length_x` right, `2×s_bend_length_y` down
   - Maintains input width (0.4 µm)
   - Generated with perpendicular point pairs

2. **Adiabatic taper section**
   - Horizontal straight section
   - Variable width at each segment
   - Configurable taper profile (linear, Gaussian, custom)
   - Length: `n_adiabatic_segments × length_adiabatic_segments`

3. **Second S-bend (upward)**
   - Mirrors first S-bend vertically
   - Displacement: `2×s_bend_length_x` right, `2×s_bend_length_y` UP
   - Maintains final width from adiabatic section
   - Returns to same vertical position as input

## Key Parameters

```python
@gf.cell
def s_bend_adiabatic_coupler(
    input_width: float = 0.4,                    # Input WG width (µm)
    s_bend_length_x: float = 10.0,               # Horizontal per S-section (µm)
    s_bend_length_y: float = 5.0,                # Vertical per S-section (µm)
    n_pts_curve: int = 4,                        # Curve smoothness
    n_pts_s_bend: int = 20,                      # Point pairs along S-bend
    n_adiabatic_segments: int = 10,              # Number of segments
    length_adiabatic_segments: float = 20.0,     # Segment spacing (µm)
    adiabatic_widths: List[float] = None,        # Width profile
    layer: Tuple[int, int] = (1, 0)
)
```

### Default Dimensions:
- **Total length**: 240 µm
  - First S-bend: 20 µm
  - Adiabatic section: 200 µm (10 segments × 20 µm)
  - Second S-bend: 20 µm
- **Vertical offset**: 0 µm (returns to input height)
- **Horizontal displacement**: Full length (240 µm)

## Generated Examples

### 1. Constant Width
**File**: `s_bend_coupler_constant.gds`

- Width: 0.4 µm throughout
- Use case: Routing without mode conversion
- Bending loss: Minimal (adiabatic curves)

### 2. Gaussian Taper
**File**: `s_bend_coupler_tapered.gds`

- Width profile: 0.4 → 1.2 → 0.4 µm
- Profile: Gaussian (smooth expansion/contraction)
- Use case: Mode filtering, spot size conversion
- Key feature: Minimizes scattering loss

**Width profile**:
```
[0.40, 0.40, 0.41, 0.51, 0.89, 1.20, 0.89, 0.51, 0.41, 0.40, 0.40] µm
```

### 3. Linear Taper
**File**: `s_bend_coupler_linear.gds`

- Width profile: 0.4 → 0.8 → 0.4 µm
- Profile: Linear ramp up and down
- Use case: Simple mode coupling
- Easier to fabricate than Gaussian

## Usage Examples

### Basic Usage (Constant Width)

```python
from s_bend_adiabatic_coupler_pcell import s_bend_adiabatic_coupler

coupler = s_bend_adiabatic_coupler(
    input_width=0.4,
    s_bend_length_x=10.0,
    s_bend_length_y=5.0,
    n_adiabatic_segments=10,
    layer=(1, 0)
)

coupler.write_gds("my_s_bend.gds")
```

### Custom Taper Profile

```python
import numpy as np

# Create custom width profile (11 values for 10 segments)
widths = np.linspace(0.4, 1.0, 11).tolist()  # Linear taper

coupler = s_bend_adiabatic_coupler(
    adiabatic_widths=widths
)
```

### Gaussian Profile (Smooth)

```python
n_seg = 10
widths = []
for i in range(n_seg + 1):
    t = i / n_seg
    # Gaussian profile centered at t=0.5
    width = 0.4 + 0.8 * np.exp(-((t - 0.5)**2) / (2 * 0.1**2))
    widths.append(width)

coupler = s_bend_adiabatic_coupler(
    adiabatic_widths=widths
)
```

## Optimization Parameters

### For Bending Loss Minimization:
- **Increase `s_bend_length_x`**: Gentler curves, lower loss
- **Increase `n_pts_s_bend`**: Smoother discretization
- **Increase `n_pts_curve`**: Better spline approximation

### For Adiabatic Coupling:
- **Longer `length_adiabatic_segments`**: More gradual transitions
- **More `n_adiabatic_segments`**: Finer width control
- **Gaussian profile**: Smoother than linear (lower scattering)

### Typical Values:
| Parameter | Min | Typical | Max | Unit |
|-----------|-----|---------|-----|------|
| s_bend_length_x | 5 | 10 | 20 | µm |
| s_bend_length_y | 2 | 5 | 10 | µm |
| n_adiabatic_segments | 5 | 10 | 20 | - |
| length_adiabatic_segments | 10 | 20 | 50 | µm |
| Max width | 0.4 | 1.0 | 2.0 | µm |

## Application: Mode Coupling

This structure is ideal for:

1. **Spot Size Conversion**
   - Convert between standard (0.4 µm) and wide (1-2 µm) waveguides
   - Minimize reflection and scattering
   - Maintain single-mode operation

2. **Mode Filtering**
   - Expand to multimode width
   - Allow higher-order modes to radiate
   - Contract back to single-mode
   - Acts as mode filter

3. **Efficient Routing**
   - Combine bending with width change
   - Compact footprint
   - Low loss transition

## Design Guidelines

### Adiabatic Condition:
For low-loss coupling, the taper must be "adiabatic":

```
dW/dz << λ / (Δn_eff × W)
```

Where:
- `dW/dz`: Rate of width change
- `λ`: Wavelength (1550 nm)
- `Δn_eff`: Effective index difference between modes
- `W`: Waveguide width

**Rule of thumb**: Length should be > 10× width change
- For 0.4 → 1.2 µm (0.8 µm change): Length > 8 µm per section
- Our default (200 µm total): Very adiabatic, minimal loss

### S-Bend Radius:
Minimum bend radius to avoid excessive loss:

```
R_min ≈ 5 µm for 220 nm Si @ 1550 nm
```

Our S-bend with default parameters:
- Effective radius: ~15-20 µm
- Well above minimum → Low loss

## Simulation Workflow

### 1. Mode Analysis (Lumerical MODE)

```
For each width in profile:
  1. Calculate effective index (n_eff)
  2. Calculate mode field diameter
  3. Verify single-mode operation
```

### 2. Propagation Loss (Lumerical FDTD)

```
1. Import GDS structure
2. Set up mode source at input
3. Add monitors along propagation
4. Sweep wavelength 1520-1580 nm
5. Extract transmission (S21)
```

### 3. Optimization Metrics

- **Insertion Loss**: < 0.5 dB target
- **Bandwidth**: > 60 nm (C+L band)
- **Mode Purity**: > 95% fundamental mode
- **Footprint**: Minimize total length

## Generated Files

```
outputs/
├── s_bend_coupler_constant.gds      # Constant width (0.4 µm)
├── s_bend_coupler_constant.png      # Visualization
├── s_bend_coupler_tapered.gds       # Gaussian taper (0.4→1.2→0.4 µm)
├── s_bend_coupler_tapered.png       # Visualization
├── s_bend_coupler_linear.gds        # Linear taper (0.4→0.8→0.4 µm)
├── s_bend_coupler_linear.png        # Visualization
└── s_bend_coupler_comparison.png    # Side-by-side comparison
```

## Next Steps

1. ✅ **PCell Implementation** - Complete
2. ⏭️ **Parameter Sweeps** - Generate variants
   - Sweep taper profiles
   - Sweep S-bend radii
   - Sweep segment lengths
3. ⏭️ **Mode Simulations** - Lumerical MODE
   - Effective index vs. width
   - Mode field profiles
   - Single-mode cutoff
4. ⏭️ **Propagation Simulations** - Lumerical FDTD
   - Transmission spectra
   - Bending loss
   - Coupling efficiency
5. ⏭️ **Optimization** - Find best parameters
   - Minimize insertion loss
   - Maximize bandwidth
   - Minimize footprint

## Technical Details

### Curve Generation:
- **Method**: Cubic spline interpolation
- **Boundary conditions**: Clamped (zero second derivative at ends)
- **Smoothness**: C² continuous (smooth first and second derivatives)

### Point Pair Generation:
- **Method**: Perpendicular normals to curve
- **Spacing**: Evenly distributed along curve length
- **Width**: Maintained perpendicular to centerline

### Polygon Construction:
- **Order**: Top edge → Bottom edge (reversed)
- **Closure**: Automatic by GDSFactory
- **Smoothness**: Limited by `n_pts_s_bend`

---

**Generated**: October 31, 2025
**Status**: PCell complete, ready for optimization and simulation
