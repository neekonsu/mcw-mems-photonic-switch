# Bistable Spring Verification Plan

## Context

Verify the CCS bistable spring design (`ccs_bistable_beam.py`, `bistable_spring_pair.py`) by computing force-displacement curves through the snap-through transition. Three independent methods provide cross-validation: (1) analytical energy minimization from Qiu et al., (2) scikit-fem pure-Python FEA, (3) CalculiX industrial FEA solver. Each FEM method runs in 2D plane strain first, then 3D extruded geometry.

**What we're simulating**: A single full CCS beam (the `make_ccs_beam` configuration) — both ends clamped at anchors, displacement prescribed at center, extracting reaction force. Parameters: span=40 µm, flex_ratio=0.3, flex_width=0.5 µm, rigid_width=0.9375 µm, initial_offset h=1.2 µm, thickness t=0.5 µm. Bistability Q = h/t = 2.4 > 2.31.

**Material**: Poly-Si, E = 160 GPa, ν = 0.22. Unit system: µm, µN, MPa (so E = 160,000 MPa).

## Package Installation

All packages pip-installable into `./switch-env/` (confirmed via dry-run):

```bash
./switch-env/bin/pip install scikit-fem triangle meshio gmsh
```

CalculiX via conda-forge (v2.22 available for osx-arm64):

```bash
conda install -c conda-forge calculix -p ./switch-env
```

## Directory Structure

```
src/verification/
├── beam_utils.py                     # Shared geometry extraction + material props
├── 1_analytical_model.ipynb          # Qiu/Pham energy minimization
├── 2a_fem_skfem_2d.ipynb             # scikit-fem 2D plane strain
├── 2b_fem_skfem_3d.ipynb             # scikit-fem 3D extruded
├── 3a_fem_calculix_2d.ipynb          # CalculiX 2D plane strain
├── 3b_fem_calculix_3d.ipynb          # CalculiX 3D extruded
├── plots/                            # Saved figures (PNG)
└── results/                          # Saved data (CSV/NPZ)
```

## File 1: `beam_utils.py` — Shared Utilities

Reuses existing geometry functions from `src/components/bistable_spring/ccs_bistable_beam.py`:

```python
# Key exports:
POLY_SI = {"E": 160e3, "nu": 0.22, "rho": 2330e-18, "t": 0.5}  # µm/µN units

def get_beam_polygon(span, flex_ratio, flex_width, rigid_width,
                     initial_offset, taper_length, n_points) -> np.ndarray:
    """Return Nx2 closed polygon of CCS beam outline (upper + lower edges).
    Calls _compute_ccs_centerline() and _compute_width_profile() from ccs_bistable_beam.py."""

def get_beam_centerline(span, flex_ratio, initial_offset, n_points) -> tuple:
    """Return (x, y) centerline arrays."""

def get_beam_width_profile(x, span, flex_ratio, flex_width, rigid_width, taper_length) -> np.ndarray:
    """Return width array."""

def get_moment_of_inertia_profile(x, span, flex_ratio, flex_width, rigid_width,
                                   taper_length, thickness) -> np.ndarray:
    """Return I(x) = w(x) * t^3 / 12 for CCS beam (variable width)."""

DEFAULT_BEAM_PARAMS = dict(span=40.0, flex_ratio=0.3, flex_width=0.5,
                           rigid_width=0.9375, initial_offset=1.2, taper_length=2.0)
```

Import mechanism: `sys.path.insert(0, "../components/bistable_spring")` to access the existing `_compute_ccs_centerline` and `_compute_width_profile` functions directly.

## File 2: `1_analytical_model.ipynb` — Analytical Force-Displacement

Based on Qiu, Lang & Slocum (JMEMS 2004) and extended for CCS beams per Baker (PNAS 2003).

### Approach: Energy Minimization with Mode Decomposition

The beam deflection is expanded in symmetric buckling modes:
```
w(x) = Σ aₙ · φₙ(x),   where φₙ(x) = ½[1 - cos(2nπx/L)],   n = 1, 3, 5
```

Initial cosine shape: `w₀(x) = h · φ₁(x)`, so a₁⁰ = h, a₃⁰ = a₅⁰ = 0.

**For uniform beam** (validation baseline):
- Bending energy: `U_bend = (2π⁴EI/L³) · Σ n⁴·aₙ²`
- Axial shortening: `S = (π²/2L) · Σ n²·aₙ²`, initial S₀ = (π²/2L)·h²
- Axial energy: `U_axial = ½·(EA/L)·(S - S₀)²`
- Center displacement: `δ = a₁ + a₃ + a₅`
- For each δ, minimize U_total over free amplitudes (a₃, a₅) with constraint δ = a₁ + a₃ + a₅
- Force: `F = dU_min/dδ` (numerical gradient)

**For CCS beam** (actual design):
- Replace uniform `β(n) = 2n⁴π⁴EI/L³` with CCS-specific coefficient:
  `β_CCS(n) = E · ∫₀ᴸ I(x)·[φₙ″(x)]² dx` (numerical integration)
- `I(x) = w(x)·t³/12` varies with the stepped width profile
- Everything else (axial energy, constraint, minimization) stays the same

### Notebook cells:
1. Imports + path setup, load beam_utils
2. **Beam geometry visualization**: plot initial centerline, width profile, I(x) profile
3. **Uniform cosine beam** (literature validation):
   - Implement energy minimization for uniform beam (I = const)
   - Plot F(δ) curve, verify snap-through/snap-back shape
   - Compare critical force ratio with Qiu's R ≈ 2 for uniform beam
4. **CCS beam** (actual design):
   - Compute β_CCS(n) using numerical integration of I(x)·φₙ″²
   - Run same energy minimization with CCS coefficients
   - Plot F(δ) showing improved (more symmetric) snap-through
   - Report: F_push, F_pop, ratio, snap-through displacement, total travel
5. **Energy landscape**: plot U(δ) showing double-well potential
6. **Mode amplitudes**: plot a₁, a₃, a₅ vs δ
7. **Deformed shapes**: beam shape at δ = 0 (initial), δ_snap, δ = 2h (snapped)
8. **Save all plots** to `plots/` and numerical results to `results/`

### Key outputs saved:
- `plots/analytical_beam_geometry.png`
- `plots/analytical_force_displacement.png`
- `plots/analytical_energy_landscape.png`
- `plots/analytical_mode_amplitudes.png`
- `plots/analytical_deformed_shapes.png`
- `results/analytical_force_displacement.csv` (δ, F columns)
- `results/analytical_critical_values.csv` (F_push, F_pop, δ_snap, etc.)

## File 3: `2a_fem_skfem_2d.ipynb` — scikit-fem 2D Plane Strain

### Approach

Use `scikit-fem` (pure Python FEA library, depends only on numpy/scipy) with `triangle` for mesh generation from the beam polygon.

### Mesh generation
1. Extract beam polygon vertices from beam_utils (Nx2 array)
2. Use `triangle.triangulate()` with quality constraints to create 2D triangular mesh
3. Tag boundaries: left anchor face, right anchor face, center region
4. Construct `skfem.MeshTri` from triangle output

### Plane strain formulation
- 2D with plane strain assumption (ε_zz = 0)
- **Linear elastic with displacement stepping** (geometric nonlinearity via updated Lagrangian approach or direct Neo-Hookean if needed)
- Start with **linear elastic**: assemble K using `skfem.models.elasticity.linear_elasticity(λ, μ)`
- For each displacement step δᵢ: fix anchor DOFs, prescribe y-displacement at center, solve, extract reaction force
- If linear results are insufficient (they won't capture snap-through properly for large deformations), implement geometric nonlinearity via Newton iteration with Green-Lagrange strain

### Displacement sweep
- δ from 0 to -2.4 µm in ~200 steps
- At each step, solve and record reaction force at center
- Also record max stress for contour plots

### Notebook cells:
1. Imports + install check (`import skfem, triangle`)
2. Extract beam polygon, create mesh, visualize mesh
3. Define material (λ, μ from E, ν), element type (P2 triangles)
4. Set up boundary conditions
5. Linear elasticity sweep (quick validation)
6. Nonlinear (geometrically) sweep with Newton iteration
7. Plot: force-displacement curve
8. Plot: deformed shapes at key δ values (overlay on original)
9. Plot: von Mises stress contour at snap-through
10. Save plots and data

### Key outputs:
- `plots/skfem_2d_mesh.png`
- `plots/skfem_2d_force_displacement.png`
- `plots/skfem_2d_deformed_shapes.png`
- `plots/skfem_2d_stress_contour.png`
- `results/skfem_2d_force_displacement.csv`

## File 4: `2b_fem_skfem_3d.ipynb` — scikit-fem 3D

### Approach

Same as 2a but with 3D extruded geometry:
1. Use `gmsh` Python API to create 3D mesh: define beam polygon as 2D surface, extrude by t=0.5 µm in z
2. Import mesh into scikit-fem (`MeshTet` from gmsh output via meshio)
3. 3D linear elastic (no plane strain assumption needed — full 3D)
4. Same displacement sweep and force extraction

### Mesh:
- ~5 elements through 0.5 µm thickness
- Same in-plane density as 2D case
- Element size ~0.1 µm near flex regions, coarser in rigid regions

### Key outputs:
- `plots/skfem_3d_mesh.png`
- `plots/skfem_3d_force_displacement.png`
- `plots/skfem_3d_deformed_shape.png`
- `plots/skfem_3d_stress.png`
- `results/skfem_3d_force_displacement.csv`

## File 5: `3a_fem_calculix_2d.ipynb` — CalculiX 2D Plane Strain

### Approach

Generate CalculiX `.inp` input files directly from Python. Run `ccx` as subprocess. Parse `.frd` output for reaction forces.

### Mesh generation
1. Same polygon → `triangle` or `gmsh` mesh as scikit-fem
2. Convert to CalculiX node/element format (CPE8 or CPE4 plane strain elements)
3. Write `.inp` file with material, BCs, and `*STEP, NLGEOM`

### CalculiX input structure:
```
*NODE → beam mesh nodes
*ELEMENT, TYPE=CPE4 → plane strain quads (or CPE3 for triangles)
*NSET → FIXED (anchor nodes), CENTER (center nodes)
*MATERIAL, NAME=POLYSI / *ELASTIC → E, ν
*SOLID SECTION → assign material to elements
*STEP, NLGEOM, INC=1000
  *STATIC → 0.01, 1.0, 1e-6, 0.1
  *BOUNDARY → FIXED: u=v=0; CENTER: v=δᵢ
  *NODE FILE → U, RF (displacements and reaction forces)
*END STEP
```

### Displacement sweep strategy
Run CalculiX once per displacement increment (or use multiple `*STEP` blocks in one .inp). Parse `.frd` binary output or use `*NODE PRINT` for ASCII reaction forces.

### Notebook cells:
1. Imports, verify `ccx` is available (`subprocess.run(["ccx", "-v"])`)
2. Generate mesh (reuse from 2a mesh generation)
3. Write .inp file generation function
4. Run displacement sweep (multiple ccx calls)
5. Parse results (.frd or .dat files)
6. Plot: force-displacement curve
7. Plot: deformed shapes, stress contours
8. Save all outputs

### Key outputs:
- `plots/calculix_2d_mesh.png`
- `plots/calculix_2d_force_displacement.png`
- `plots/calculix_2d_deformed_shapes.png`
- `plots/calculix_2d_stress.png`
- `results/calculix_2d_force_displacement.csv`

## File 6: `3b_fem_calculix_3d.ipynb` — CalculiX 3D

### Approach

Same as 3a but with 3D mesh:
1. Gmsh extrude polygon → 3D tetrahedral/hex mesh
2. Convert to CalculiX format (C3D10 or C3D20R elements)
3. `*STEP, NLGEOM` with 3D BCs
4. Same sweep and parsing

### Key outputs:
- `plots/calculix_3d_mesh.png`
- `plots/calculix_3d_force_displacement.png`
- `plots/calculix_3d_deformed_shape.png`
- `plots/calculix_3d_stress.png`
- `results/calculix_3d_force_displacement.csv`

## Comparison (Final cells in each notebook or separate summary)

The 3b notebook ends with a comparison section that loads all results and creates:
- **Overlay plot**: All 5 F(δ) curves on one figure (analytical uniform, analytical CCS, 2D skfem, 2D ccx, 3D skfem, 3D ccx)
- **Critical values table**: F_push, F_pop, F_push/F_pop ratio, δ_snap for each method
- **Saved as**: `plots/comparison_force_displacement.png`, `results/comparison_critical_values.csv`

## Critical Source Files

| File | Role |
|------|------|
| `src/components/bistable_spring/ccs_bistable_beam.py` | Geometry functions: `_compute_ccs_centerline`, `_compute_width_profile`, `_compute_ccs_half_centerline`, `_compute_half_width_profile` |
| `src/components/bistable_spring/bistable_spring_pair.py` | Spring pair assembly (reference, not simulated directly) |
| `src/libraries/mcw_custom_optical_mems_pdk.py` | LAYER definitions, LAYER_STACK for 3D export |

## Implementation Order

1. `beam_utils.py` — shared geometry extraction (reuses existing functions)
2. `1_analytical_model.ipynb` — analytical curves (no external deps beyond numpy/scipy)
3. `2a_fem_skfem_2d.ipynb` — 2D scikit-fem (after `pip install scikit-fem triangle`)
4. `3a_fem_calculix_2d.ipynb` — 2D CalculiX (after `conda install calculix`)
5. `2b_fem_skfem_3d.ipynb` — 3D scikit-fem (after `pip install gmsh meshio`)
6. `3b_fem_calculix_3d.ipynb` — 3D CalculiX (uses same gmsh mesh)

## Verification

1. Run `1_analytical_model.ipynb` — confirm N-shaped F(δ) curve with two zero crossings
2. Run `2a_fem_skfem_2d.ipynb` — F(δ) should qualitatively match analytical
3. Run `3a_fem_calculix_2d.ipynb` — F(δ) should match scikit-fem 2D
4. Run `2b/3b` 3D notebooks — should be close to 2D results (beam is slender)
5. Check: all methods agree on snap-through force within ~10% of each other
6. Check: push/pop ratio ≈ 0.87 for CCS (vs ~0.76 for uniform cosine)
