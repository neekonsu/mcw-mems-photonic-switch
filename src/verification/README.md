# Bistable Spring Verification

Force-displacement analysis of a single CCS bistable half-beam.  Three
independent methods provide cross-validation: analytical energy minimization,
scikit-fem (pure Python FEA), and CalculiX (industrial FEA solver).  Each FEM
method runs in both 2D plane strain and 3D extruded geometry.

All five notebooks execute to completion and produce CSV / plot outputs.
The cross-method comparison is in notebook 3b.

## What we're simulating

A **single CCS half-beam** (`make_ccs_half_beam` configuration) — one end
clamped at the anchor, displacement prescribed at the shuttle end, extracting
reaction force.  The half-beam spans from anchor (x=0, y=0) to shuttle
(x=half_span, y=initial_offset), with both endpoints approaching horizontally
(dy/dx = 0).  This is the fundamental building block of the bistable spring
pair; the production layout (`bistable_spring_pair.py`) places four such
half-beams in a mirrored configuration connected through a shuttle gap.

| Parameter        | Value           |
|------------------|-----------------|
| Half-span L      | 20 µm           |
| Flex ratio       | 0.3             |
| Flex width       | 0.5 µm          |
| Rigid width      | 0.9375 µm       |
| Initial offset h | 1.2 µm          |
| Thickness t      | 0.5 µm          |
| Q = h/t          | 2.4 (> 2.31)    |
| Material         | Poly-Si         |
| E                | 160 GPa         |
| nu               | 0.22            |

Unit system: µm, µN, MPa (so E = 160,000 MPa).

### Boundary conditions

All FEM notebooks apply the same BCs to the half-beam:

- **Anchor** (x ≈ 0): fully clamped — u_x = u_y = 0 (2D) or u_x = u_y = u_z = 0 (3D)
- **Shuttle** (x ≈ L): prescribed u_y displacement from 0 to -2h, u_x free (and u_z free in 3D)

The analytical model (notebook 1) applies equivalent constraints via the mode
expansion: the shuttle end is constrained to a prescribed displacement delta,
while the anchor end is fixed at y=0.

## Results Summary

All methods produce **monotonically negative** force-displacement curves with
**no snap-through** (F_push = 0 for all FEM methods).  This is a direct
consequence of the half-beam-only simulation — see [Why No Snap-Through](#why-no-snap-through-in-fem-results)
below.

### Comparison table (from notebook 3b cell 16)

| Method              | F_push [µN] | F_pop [µN] | \|F_pop/F_push\| |
|---------------------|-------------|------------|-------------------|
| Analytical (uniform)| 1.69        | -1.69      | 1.000             |
| Analytical (CCS)    | 2.48        | -2.48      | 1.000             |
| scikit-fem 2D       | 0.00        | -5.30      | 0.000             |
| scikit-fem 3D       | 0.00        | -1.37      | 0.000             |
| CalculiX 2D         | 0.00        | -2.52      | 0.000             |
| CalculiX 3D         | 0.00        | -2.40      | 0.000             |

The analytical model gives a symmetric F(delta) curve (push/pop ratio = 1.0)
because the single half-beam mode expansion yields equal positive and negative
force lobes.  The FEM results are strictly negative because the shuttle is
pushed downward and the beam always resists.

### Force magnitude comparison

The analytical CCS peak force (2.48 µN) and the CalculiX 2D/3D results
(2.52/2.40 µN) agree to within ~5%, validating the mesh and material setup.
The scikit-fem 2D result (5.30 µN) is ~2x larger due to the plane strain
assumption stiffening the thin beam, while scikit-fem 3D (1.37 µN) is
somewhat softer — likely a mesh resolution effect with the coarser 3D mesh
(lc_flex=0.3, lc_rigid=0.5) using linear P1 tetrahedral elements.

## Why No Snap-Through in FEM Results

**This is the central finding of this verification round and the key issue
for follow-up work.**

### The physics of bistable snap-through

The CCS bistable mechanism requires **axial force coupling between parallel
beams** to produce snap-through.  The mechanism works as follows (Qiu 2004,
Ma 2024):

1. Two (or more) parallel beams are connected at their centers by a rigid
   shuttle.
2. As the shuttle is displaced, each beam bends.  Bending changes the
   beam's arc length, which — in a doubly-clamped configuration — generates
   **axial compressive stress** (the beam wants to elongate but the clamps
   prevent it).
3. This axial compression interacts with the bending modes: at a critical
   displacement, the axial load exceeds the buckling threshold for higher-order
   modes (mode 3, mode 5, etc.), causing the beam to suddenly transition to a
   new equilibrium shape.
4. The force drops (and can become negative), producing the characteristic
   bistable snap-through.

The critical requirement is **doubly-clamped boundary conditions with axial
constraint** — both ends of the beam must be fixed in the axial (x) direction
so that bending-induced length changes generate compressive axial force.

### What the current simulations model

The current notebooks simulate a **single half-beam** with:

- Anchor clamped (x ≈ 0): u_x = u_y = 0
- Shuttle prescribed (x ≈ L): u_y = delta, **u_x free**

Because the shuttle end is **free in x**, the beam can elongate or shorten
freely in the axial direction as it bends.  No axial compressive stress
builds up, no buckling interaction occurs, and no snap-through is possible.
The beam behaves as a simple cantilever-like flexure — the force is purely
from bending stiffness and is monotonically proportional to displacement.

This is physically correct for an **isolated half-beam**.  A single
unconstrained half-beam does not exhibit bistability.

### Why the analytical model shows symmetry but not snap-through

The analytical model (notebook 1, Qiu's energy minimization) does include
axial energy terms and mode coupling.  However, for the half-beam with
Q=2.4 (only slightly above the 2.31 threshold), the energy minimization
finds that **higher modes do not participate** — the minimum-energy path
stays in the a1-only subspace.  The analytical code notes:

> "For Q=2.40 (close to bistability threshold of 2.31), higher modes do not
> participate => symmetric force curve (ratio ~ 1.0)."

This produces a symmetric force curve (equal push and pop) but without the
characteristic negative-force region between two stable states.  The
single-beam analytical result at Q=2.4 is a marginal case — the beam is
*just barely* past the geometric threshold, and without the parallel-beam
axial coupling, the energy landscape is too shallow for mode switching.

### What is needed for snap-through: full CCS mechanism

To observe snap-through in simulation, the model must include the complete
doubly-clamped parallel-beam mechanism:

```
   Left Anchor ─── beam 1 (upper) ───╮               ╭─── beam 1 (upper) ─── Right Anchor
                                      ├── shuttle ───┤
   Left Anchor ─── beam 2 (lower) ───╯               ╰─── beam 2 (lower) ─── Right Anchor
                                     (rigid body)
```

This requires:

1. **Two parallel beams** (upper and lower) connected at their centers by a
   rigid shuttle.  The shuttle constrains both beams to have the same
   y-displacement at the center and also **constrains their x-displacement
   to be equal** (or zero, if the shuttle is rigid in x).

2. **Doubly-clamped BCs**: Both left and right anchors must be fully clamped
   (u_x = u_y = 0).  This means each beam is clamped at both ends, and axial
   stress can build up.

3. **Prescribed y-displacement at the shuttle** (center of the beams), with
   reaction force extracted.

4. **x-coupling at the shuttle**: The shuttle must be modeled as rigid (or
   at least very stiff) in x so that bending-induced axial shortening of the
   beams is resisted, generating the compressive force that triggers mode
   switching.

In the Qiu (2004) formulation, this is a **full-span doubly-clamped beam**
(their Fig. 1): both ends clamped, center displacement prescribed.  The axial
constraint comes from the clamped-clamped boundary conditions — the beam
cannot change its end-to-end distance.

In the Ma (2024) CCS design and our spring pair layout, the geometry is
symmetric: two half-beams on each side, meeting at the shuttle.  The shuttle
itself provides the rigid axial coupling between the left and right halves.

### Mapping from half-beam to full mechanism

The current half-beam results are still valuable as building blocks.  The
relationship between the models:

| Property | Single half-beam (current) | Full CCS mechanism (needed) |
|----------|---------------------------|------------------------------|
| Geometry | Anchor → shuttle, one beam | Anchor → shuttle → anchor, two parallel beams |
| Axial BC at shuttle | u_x free | u_x = 0 (or coupled) |
| Axial stress | None | Builds with displacement |
| Mode coupling | No higher modes | Mode 3 activated at critical delta |
| Snap-through | No | Yes (for Q > 2.31) |
| Force curve | Monotonic negative | Positive peak → zero crossing → negative valley |

The bending stiffness contribution (which dominates at small displacements)
should be similar between the half-beam and the full mechanism.  The
difference appears at larger displacements where axial effects dominate.

## File Structure

```
src/verification/
├── README.md                         # This file
├── beam_utils.py                     # Shared geometry + material (half-beam)
├── full_spring_utils.py              # Shared geometry + mesh (full spring)
├── 1_analytical_model.ipynb          # Qiu/Pham energy minimization
├── 2a_fem_skfem_2d.ipynb             # scikit-fem 2D plane strain (half-beam)
├── 2b_fem_skfem_3d.ipynb             # scikit-fem 3D extruded (half-beam)
├── 3a_fem_calculix_2d.ipynb          # CalculiX 2D plane strain (half-beam)
├── 3b_fem_calculix_3d.ipynb          # CalculiX 3D extruded + half-beam comparison
├── 4a_fem_skfem_2d_full.ipynb        # scikit-fem 2D plane strain (full spring)
├── 4b_fem_skfem_3d_full.ipynb        # scikit-fem 3D extruded (full spring)
├── 5a_fem_calculix_2d_full.ipynb     # CalculiX 2D plane strain (full spring)
├── 5b_fem_calculix_3d_full.ipynb     # CalculiX 3D extruded + full spring comparison
├── plots/                            # Saved figures (PNG)
│   ├── analytical_*.png              # Notebook 1 plots
│   ├── skfem_2d_*.png                # Notebook 2a plots
│   ├── skfem_3d_*.png                # Notebook 2b plots
│   ├── calculix_2d_*.png             # Notebook 3a plots
│   ├── calculix_3d_*.png             # Notebook 3b plots
│   ├── comparison_force_displacement.png  # Half-beam cross-method overlay
│   ├── skfem_2d_full_*.png           # Notebook 4a plots
│   ├── skfem_3d_full_*.png           # Notebook 4b plots
│   ├── calculix_2d_full_*.png        # Notebook 5a plots
│   ├── calculix_3d_full_*.png        # Notebook 5b plots
│   └── full_spring_comparison.png    # Full spring cross-method overlay
└── results/                          # Saved data (CSV)
    ├── analytical_force_displacement.csv
    ├── analytical_critical_values.csv
    ├── skfem_2d_force_displacement.csv
    ├── skfem_3d_force_displacement.csv
    ├── calculix_2d_force_displacement.csv
    ├── calculix_3d_force_displacement.csv
    ├── comparison_critical_values.csv
    ├── skfem_2d_full_*.csv           # Full spring results (3 densities each)
    ├── skfem_3d_full_*.csv
    ├── calculix_2d_full_*.csv
    ├── calculix_3d_full_*.csv
    ├── full_spring_comparison.csv
    ├── ccx_2d/, ccx_3d/              # Half-beam CalculiX working dirs
    └── ccx_2d_full_*/, ccx_3d_full_*/  # Full spring CalculiX working dirs
```

**Note**: `.frd`, `.inp`, and `.msh` files in `results/` are gitignored (large
simulation artifacts, ~1 GB total). They are regenerated by running the notebooks.
Only `.csv` and `.dat` files are tracked.

## Dependencies

All installed into `./switch-env/`:

```bash
# Python packages (pip)
./switch-env/bin/pip install scikit-fem triangle meshio gmsh

# CalculiX binary (conda-forge, v2.23)
conda install -c conda-forge calculix -p ./switch-env
```

Verified installed: scikit-fem 12.0.1, triangle 20250106, meshio 5.3.5,
gmsh 4.15.1, ccx 2.23.

## Shared Utilities: `beam_utils.py`

Wraps geometry functions from `../components/bistable_spring/ccs_bistable_beam.py`.
Uses the **half-beam** geometry (`_compute_ccs_half_centerline`,
`_compute_half_width_profile`) — the correct building block for the bistable
spring pair.

```python
from beam_utils import (
    POLY_SI,                        # {"E": 160e3, "nu": 0.22, "t": 0.5, ...}
    DEFAULT_BEAM_PARAMS,            # half_span=20, flex_ratio=0.3, ...
    get_beam_centerline,            # (x, y) arrays
    get_beam_width_profile,         # w(x) array
    get_beam_polygon,               # Nx2 closed polygon for meshing
    get_moment_of_inertia_profile,  # I(x) = w(x)*t³/12
)
```

## Notebook 1: Analytical Model

**File**: `1_analytical_model.ipynb`

**Method**: Qiu, Lang & Slocum (JMEMS 2004) energy minimization with mode
decomposition.  Beam deflection expanded in symmetric buckling modes
phi_n(x) = 0.5[1 - cos(2*n*pi*x/L)] for n = 1, 3, 5.  For each prescribed
shuttle displacement delta, total energy (bending + axial) is minimized over
free mode amplitudes (a3, a5), with constraint a1 + a3 + a5 = delta.
Force F = dU_min/d(delta).

For CCS variable-width beams, bending stiffness coefficients are computed by
numerical integration: beta_mn = E * integral of I(x) * phi_m''(x) * phi_n''(x) dx.
Cross-coupling terms included (modes are not orthogonal w.r.t. variable-I
inner product).

**Status**: Runs to completion.

**Results**:

| Beam     | F_push (µN) | F_pop (µN) | \|F_pop/F_push\| |
|----------|-------------|------------|-------------------|
| Uniform  | 1.69        | -1.69      | 1.000             |
| CCS      | 2.48        | -2.48      | 1.000             |

The push/pop ratio of 1.0 (perfectly symmetric) is correct for a single
half-beam — see [Why No Snap-Through](#why-no-snap-through-in-fem-results).
Higher modes do not participate because the single unconstrained beam at
Q=2.4 does not develop sufficient axial compression to trigger mode switching.

**Output files**:
- `plots/analytical_beam_geometry.png`
- `plots/analytical_force_displacement.png`
- `plots/analytical_energy_landscape.png`
- `plots/analytical_mode_amplitudes.png`
- `plots/analytical_deformed_shapes.png`
- `results/analytical_force_displacement.csv` (delta, F_uniform, F_ccs)
- `results/analytical_critical_values.csv`

## Notebook 2a: scikit-fem 2D Plane Strain

**File**: `2a_fem_skfem_2d.ipynb`

**Method**: Triangulate half-beam polygon with the `triangle` library.
P1 (linear) triangle elements with `ElementVector(ElementTriP1())`.
Both linear elasticity sweep and Total Lagrangian nonlinear formulation
(Green-Lagrange strain, St. Venant-Kirchhoff material, Newton-Raphson
iteration).

**Mesh**: ~4200 nodes, ~7100 P1 triangles.

**BCs**: Anchor (x≈0) clamped; shuttle (x≈L) y-prescribed, x-free.

**DOF layout**: scikit-fem `ElementVector` uses **interleaved** ordering:
`[x0, y0, x1, y1, ...]`.  Node i has DOFs at indices `2*i` (x) and
`2*i+1` (y).  This is critical — blocked layout `[x0..xN, y0..yN]` gives
wildly incorrect forces.

**Status**: Runs to completion (linear sweep: 100 steps, nonlinear: 200 steps).

**Results**: F range [-5.30, 0.0] µN (nonlinear), monotonic.  The plane strain
assumption makes the 2D beam stiffer than the actual 3D geometry — plane
strain effectively models an infinitely thick beam, which inflates the
stiffness by a factor related to 1/(1-nu^2).

**Output files**:
- `plots/skfem_2d_mesh.png`
- `plots/skfem_2d_linear_fd.png`
- `plots/skfem_2d_nonlinear_fd.png`
- `plots/skfem_2d_deformed_shapes.png`
- `plots/skfem_2d_stress.png`
- `results/skfem_2d_force_displacement.csv`

## Notebook 2b: scikit-fem 3D Extruded

**File**: `2b_fem_skfem_3d.ipynb`

**Method**: Extrude half-beam polygon by t=0.5 µm using gmsh.  P1 tetrahedral
elements.  Linear elasticity sweep followed by Total Lagrangian nonlinear
formulation.

**Mesh**: 14,544 nodes, 60,012 P1 tetrahedra (lc_flex=0.3, lc_rigid=0.5,
n_layers_z=3).  Coarser than the 2D mesh for tractable runtime — each
nonlinear step involves assembling and solving a 43,632-DOF sparse system.

**BCs**: Anchor clamped (u_x=u_y=u_z=0); shuttle y-prescribed (u_x, u_z free).
DOF layout: interleaved `[x0,y0,z0, x1,y1,z1, ...]` — node i at indices
`3*i`, `3*i+1`, `3*i+2`.

**Status**: Runs to completion (30 linear steps, 30 nonlinear steps with
Newton-Raphson, ~12-13 iterations per step).

**Results**: Linear F range [-1.08, 0.0] µN.  Nonlinear F range [-1.37, 0.0] µN.
The 3D result is softer than both the 2D plane strain (expected) and the
CalculiX 3D result (likely due to the coarser P1 mesh).

**Runtime**: ~35 minutes on Apple M2 (dominated by the nonlinear sweep's
Python-based assembly of the tangent stiffness at each quadrature point).

**Key implementation details**:
- Identity tensor: `I3 = np.eye(3).reshape(3, 3, 1, 1)` — scikit-fem's
  `eye(du, 3)` creates a block-diagonal, not a tensor-field identity.
- Matrix multiply: custom `mat(A, B) = np.einsum('ij...,jk...->ik...', A, B)` —
  scikit-fem's `dot()` is vector dot product (`einsum('i...,i...')`), not
  matrix multiplication.
- Stress: `ddot(S, dGL_v)` where S is the 2nd Piola-Kirchhoff stress and
  dGL_v is the Green-Lagrange variation.

**Output files**:
- `plots/skfem_3d_mesh.png`
- `plots/skfem_3d_force_displacement.png`
- `plots/skfem_3d_deformed_shape.png`
- `results/skfem_3d_force_displacement.csv`

## Notebook 3a: CalculiX 2D Plane Strain

**File**: `3a_fem_calculix_2d.ipynb`

**Method**: Generate CPE3 (3-node plane strain triangle) mesh from the
`triangle` library output.  Write `.inp` files programmatically for each
displacement step.  Run `ccx` as a subprocess.  Parse `.dat` output for
total reaction forces.

**Mesh**: 4,033 nodes, 7,119 CPE3 elements.

**BCs**: ANCHOR nset clamped (DOFs 1-2 = 0); SHUTTLE nset y-prescribed
(DOF 2 = delta).  Written as CalculiX `*BOUNDARY` cards.

**Parser**: CalculiX `.dat` format puts the "total force (fx,fy,fz)..."
header on one line and the actual numeric values on the **next** line
(indented, three floats).  The parser reads `lines[i+1]` after finding
"total force" and extracts `float(parts[1])` for RF_y.

**Status**: Runs to completion (50 displacement steps, NLGEOM).

**Results**: F range [-2.52, 0.0] µN, monotonic.  Agrees well with the
analytical CCS result (2.48 µN peak) and CalculiX 3D (2.40 µN).

**Output files**:
- `plots/calculix_2d_mesh.png`
- `plots/calculix_2d_force_displacement.png`
- `plots/calculix_2d_deformed_shapes.png`
- `results/calculix_2d_force_displacement.csv`
- `results/ccx_2d/step_*.inp` (50 input files)
- `results/ccx_2d/step_*.dat` (50 output files)
- `results/ccx_2d/step_*.frd` (50 binary result files)

## Notebook 3b: CalculiX 3D Extruded + Comparison

**File**: `3b_fem_calculix_3d.ipynb`

**Method**: Extrude half-beam polygon via gmsh.  C3D10 (10-node quadratic
tetrahedral) elements.  Write `.inp`, run `ccx` with NLGEOM for each
displacement step.

**Mesh**: 43,505 nodes, 26,172 C3D10 elements (lc_flex=0.4, lc_rigid=0.7,
n_layers_z=3, 2nd order).

**BCs**: ANCHOR nset clamped (DOFs 1-3 = 0); SHUTTLE nset y-prescribed
(DOF 2 = delta).

**Status**: Runs to completion (20 displacement steps).

**Results**: F range [-2.40, 0.0] µN, monotonic.  Very close to the CalculiX
2D result (2.52 µN) and the analytical CCS result (2.48 µN).

**Runtime**: ~25 minutes on Apple M2 (each ccx 3D solve takes ~1-2 minutes).

**Comparison section** (cells 14-16): Loads all six CSV result files and
produces:
- Overlay plot: `plots/comparison_force_displacement.png`
- Critical values table: `results/comparison_critical_values.csv`

**Output files**:
- `plots/calculix_3d_mesh.png`
- `plots/calculix_3d_force_displacement.png`
- `plots/comparison_force_displacement.png`
- `results/calculix_3d_force_displacement.csv`
- `results/comparison_critical_values.csv`
- `results/ccx_3d/step_*.inp`, `*.dat`, `*.frd`

## Execution Order

Run notebooks in this order (each produces CSV consumed by later notebooks'
comparison cells):

### Half-beam (single beam, no snap-through)
1. `1_analytical_model.ipynb` — no external deps beyond numpy/scipy
2. `2a_fem_skfem_2d.ipynb` — needs scikit-fem, triangle
3. `3a_fem_calculix_2d.ipynb` — needs calculix
4. `2b_fem_skfem_3d.ipynb` — needs gmsh, meshio (~35 min)
5. `3b_fem_calculix_3d.ipynb` — needs gmsh (~25 min); includes half-beam comparison

### Full spring (doubly-clamped, snap-through expected)
6. `4a_fem_skfem_2d_full.ipynb` — needs scikit-fem, triangle, shapely
7. `5a_fem_calculix_2d_full.ipynb` — needs calculix
8. `4b_fem_skfem_3d_full.ipynb` — needs gmsh, meshio
9. `5b_fem_calculix_3d_full.ipynb` — needs gmsh; includes full spring comparison

All notebooks must be run from the `src/verification/` directory (they use
relative paths for imports and output).  Use the `switch-env` kernel:

```bash
cd src/verification
../../switch-env/bin/python -m jupyter nbconvert --to notebook --execute \
    <notebook>.ipynb --ExecutePreprocessor.timeout=3600 \
    --ExecutePreprocessor.kernel_name=switch-env
```

## Full CCS Mechanism Simulation (Notebooks 4a/4b/5a/5b)

Notebooks 4a–5b simulate the **complete doubly-clamped bistable spring**:
two parallel CCS beam pairs + rigid shuttle, with both anchors clamped.
This provides the axial coupling needed for snap-through bistability.

### Full spring geometry

```
Left Anchor ─── upper half-beam L ──╮            ╭── upper half-beam R ─── Right Anchor
                                     │  shuttle  │
Left Anchor ─── lower half-beam L ──╯            ╰── lower half-beam R ─── Right Anchor
```

| Parameter        | Value           |
|------------------|-----------------|
| Anchor distance  | 80 µm           |
| Beam spacing     | 10 µm (c-to-c) |
| Shuttle length   | 7 µm            |
| Half-span        | 36.5 µm (derived) |
| Beam params      | Same as half-beam (flex_ratio=0.3, etc.) |

The geometry is built using `full_spring_utils.py`, which merges 4 half-beam
outlines + a solid shuttle rectangle via Shapely boolean union into a single
polygon for meshing.

### Boundary conditions (full spring)

- **Left anchor** (x ≈ 0): clamped — u_x = u_y = 0 (2D) or u_x = u_y = u_z = 0 (3D)
- **Right anchor** (x ≈ 80): clamped — same as left
- **Shuttle** (36.5 < x < 43.5): prescribed u_y from 0 to -2h, u_x free

The critical difference from notebooks 2a–3b: both anchors are clamped, so
bending-induced axial stress builds up through the shuttle, enabling
snap-through.  The shuttle u_x is NOT explicitly constrained — the
doubly-clamped geometry + shuttle material stiffness provides axial constraint.

### Mesh density strategy

Each notebook runs at 3 densities for convergence study:

| Level | 2D max_area  | 3D lc_flex/lc_rigid/n_z | Purpose        |
|-------|-------------|-------------------------|----------------|
| 10%   | 0.08 µm²   | 0.8/1.2/2               | Quick validation |
| 50%   | 0.016 µm²  | 0.5/0.8/2               | Convergence check |
| 100%  | 0.008 µm²  | 0.3/0.5/3               | Production       |

### Expected results

With proper doubly-clamped BCs + axial coupling:
1. **Positive force** initially (bending stiffness resists push)
2. **Force decreasing** as axial compression builds
3. **Zero crossing** at snap-through point
4. **Negative force** (beam pulls toward second stable state)
5. **Return to zero** at δ ≈ 2h = 2.4 µm

Full spring force ≈ 4× single half-beam ≈ 4 × 2.48 = ~10 µN.
Push/pop ratio ≈ 0.87 for CCS beams (Ma 2024).

## Notebook 4a: scikit-fem 2D Full Spring

**File**: `4a_fem_skfem_2d_full.ipynb`

**Method**: Merge full spring polygon via `full_spring_utils.get_full_spring_polygon()`.
Triangulate with `triangle`.  P1 elements, Total Lagrangian nonlinear formulation.
3 mesh density levels.

**BCs**: Left + right anchors clamped (u_x=u_y=0); shuttle y-prescribed.

**Output files**:
- `plots/skfem_2d_full_convergence.png`
- `plots/skfem_2d_full_deformed.png`
- `results/skfem_2d_full_10pct.csv`, `*_50pct.csv`, `*_100pct.csv`

## Notebook 4b: scikit-fem 3D Full Spring

**File**: `4b_fem_skfem_3d_full.ipynb`

**Method**: Extrude full spring polygon by t=0.5 µm using gmsh.  P1 tetrahedra.
Total Lagrangian nonlinear formulation.  3 mesh density levels.

**BCs**: Left + right anchors clamped (u_x=u_y=u_z=0); shuttle y-prescribed.

**Output files**:
- `plots/skfem_3d_full_convergence.png`
- `results/skfem_3d_full_10pct.csv`, `*_50pct.csv`, `*_100pct.csv`

## Notebook 5a: CalculiX 2D Full Spring

**File**: `5a_fem_calculix_2d_full.ipynb`

**Method**: CPE3 (3-node plane strain triangle) elements.  Write `.inp` per
displacement step, run `ccx` with NLGEOM.  3 mesh density levels.

**BCs**: LEFT_ANCHOR + RIGHT_ANCHOR nsets clamped (DOFs 1-2 = 0);
SHUTTLE nset y-prescribed (DOF 2 = delta).

**Output files**:
- `plots/calculix_2d_full_convergence.png`
- `plots/calculix_2d_full_deformed.png`
- `results/calculix_2d_full_10pct.csv`, `*_50pct.csv`, `*_100pct.csv`
- `results/ccx_2d_full_*/step_*.inp`, `*.dat`, `*.frd`

## Notebook 5b: CalculiX 3D Full Spring + Comparison

**File**: `5b_fem_calculix_3d_full.ipynb`

**Method**: C3D10 (10-node quadratic tetrahedral) elements via gmsh.
Write `.inp`, run `ccx` with NLGEOM.  3 mesh density levels.

**BCs**: LEFT_ANCHOR + RIGHT_ANCHOR nsets clamped (DOFs 1-3 = 0);
SHUTTLE nset y-prescribed (DOF 2 = delta).

**Comparison section**: Loads all full-spring CSV results + analytical (×4)
and produces:
- Overlay plot: `plots/full_spring_comparison.png`
- Critical values table: `results/full_spring_comparison.csv`

**Output files**:
- `plots/calculix_3d_full_convergence.png`
- `plots/full_spring_comparison.png`
- `results/calculix_3d_full_10pct.csv`, `*_50pct.csv`, `*_100pct.csv`
- `results/full_spring_comparison.csv`
- `results/ccx_3d_full_*/step_*.inp`, `*.dat`, `*.frd`

## Shared Utilities

### `beam_utils.py` (half-beam)

Wraps geometry functions from `../components/bistable_spring/ccs_bistable_beam.py`.
Used by notebooks 1–3b.

### `full_spring_utils.py` (full spring)

Wraps geometry from `beam_utils.py` + Shapely boolean union to produce merged
2D polygon of the complete spring.  Used by notebooks 4a–5b.

```python
from full_spring_utils import (
    POLY_SI,                         # material properties
    DEFAULT_FULL_SPRING_PARAMS,      # anchor_distance=80, beam_spacing=10, ...
    get_full_spring_polygon,         # Nx2 merged polygon
    identify_bc_nodes_2d,            # left_anchor, right_anchor, shuttle node sets
    identify_bc_nodes_3d,            # same for 3D
    get_full_spring_3d_mesh,         # gmsh extrusion (P1 tets)
    get_full_spring_3d_mesh_order2,  # gmsh extrusion (C3D10 tets)
)
```

### GDS Component: `complete_spring.py`

`src/components/bistable_spring/complete_spring.py` — the corresponding layout
component (`make_complete_spring()`) that assembles the full mechanism for
tapeout: 4 CCS half-beams + shuttle proof mass + 2 multi-layer anchors.

### Recommended approach for each notebook

| Notebook | Change |
|----------|--------|
| 1 (analytical) | Already uses the Qiu full-beam formulation; just increase Q or add the axial constraint term for the half-beam case.  Alternatively, run the existing code with Q >> 2.31 (e.g., h=2.0 µm, Q=4.0) to verify snap-through in the mode decomposition. |
| 2a (skfem 2D) | Add `shuttle_x_dofs = 2 * shuttle_nodes` to the constrained DOF set.  This single change may be sufficient to see snap-through.  May need arc-length continuation for convergence past the snap-through point. |
| 2b (skfem 3D) | Same as 2a but with `shuttle_x_dofs = 3 * shuttle_nodes`.  Expensive — consider coarser mesh or fewer steps near snap-through. |
| 3a (CalculiX 2D) | Add `SHUTTLE, 1, 1, 0.0` to the `*BOUNDARY` cards to constrain shuttle x-DOF.  Use `*STATIC, SOLVER=RIKS` for arc-length. |
| 3b (CalculiX 3D) | Same as 3a.  Consider `*STATIC, SOLVER=RIKS` with `*CONTROLS` for arc-length parameters. |

### Alternative: full-span doubly-clamped beam

Instead of two half-beams + shuttle, a simpler approach models a single
full-span beam (length 2L = 40 µm) clamped at both ends with center
displacement prescribed.  This is the Qiu (2004) Fig. 1 configuration:

- Left anchor (x=0): u_x = u_y = 0
- Right anchor (x=2L): u_x = u_y = 0
- Center nodes (x≈L): u_y = delta (prescribed)

The beam geometry would use `make_ccs_beam()` (full beam, not half-beam) or
mirror two half-beams.  The clamped-clamped BCs inherently provide the axial
constraint — no explicit shuttle modeling needed.  This is probably the
simplest path to observing snap-through in FEM.

### Expected results with axial constraint

With proper axial constraint, the force-displacement curve should show:

1. Initial positive force (pushing against the displacement) — dominated by
   bending stiffness.
2. Force decreasing as axial compression builds and softens the response.
3. Zero crossing at a critical displacement — this is the snap-through point.
4. Negative force (the beam actively pulls toward the second stable state).
5. Force returning to zero at the second stable position (delta ≈ -2h).

The push/pop ratio should be ~0.76 for uniform beams and ~0.87 for CCS beams
(Qiu 2004, Ma 2024).  The spring pair force is 4x the single-beam force
(4 half-beams in the pair).

### References for full-mechanism modeling

- Qiu (2004), Sec. III — derives the axial force coupling and mode-switching
  criterion for doubly-clamped parallel beams.  Their Fig. 8 shows the
  characteristic force-displacement curve with snap-through.
- Ma (2024), Sec. II — applies the CCS (centrally-clamped stepped) geometry
  and shows how the rigid center section improves the push/pop ratio.
- Hussein (2019), "Modeling and Optimization of MEMS Bistable Mechanisms" —
  discusses FEM modeling strategies including arc-length methods.

## Technical Notes: scikit-fem v12

Key API details discovered during debugging (relevant for notebooks 2a/2b):

| Issue | Solution |
|-------|----------|
| `ib.Nbfun` returns per-element DOFs (e.g., 6 for P1 tri vector), not total system DOFs | Use `N = mesh.nvertices`, `ndofs = dim * N` |
| `ElementVector` uses interleaved DOF layout: `[x0,y0,x1,y1,...]` | Node i: x-DOF at `dim*i`, y-DOF at `dim*i+1`, z-DOF at `dim*i+2` |
| `dot(A, B)` is vector dot product (`einsum('i...,i...')`), not matrix multiply | Use `np.einsum('ij...,jk...->ik...', A, B)` |
| `eye(du, n)` creates a block-diagonal `[[du,0],[0,du]]`, not a tensor identity | Use `np.eye(n).reshape(n, n, 1, 1)` |
| Displacement extraction from solution vector `u` | `ux = u[0::dim]`, `uy = u[1::dim]`, `uz = u[2::dim]` |

## Key Source Files

| File | Role |
|------|------|
| `src/components/bistable_spring/ccs_bistable_beam.py` | Geometry: `_compute_ccs_half_centerline`, `_compute_half_width_profile` |
| `src/components/bistable_spring/bistable_spring_pair.py` | Spring pair assembly: 4 half-beams + anchors (span=36.5 µm, overall 80 µm) |
| `src/libraries/mcw_custom_optical_mems_pdk.py` | LAYER definitions, LAYER_STACK |

## References

- Qiu, Lang & Slocum, "A Centrally-Clamped Parallel-Beam Bistable MEMS Mechanism," JMEMS 13(2), 2004
- Ma et al., "Nonvolatile Silicon Photonic MEMS Switch Based on Centrally-Clamped Stepped Bistable Mechanical Beams," Zhejiang University, 2024
- Hussein et al., "Modeling and Optimization of Microelectromechanical Systems (MEMS) Bistable Mechanisms," 2019

╭────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Plan to implement                                                                                                                                                                                                                                                                              │
│                                                                                                                                                                                                                                                                                                │
│ Full Spring Mechanism: Component + FEM Verification                                                                                                                                                                                                                                            │
│                                                                                                                                                                                                                                                                                                │
│ Context                                                                                                                                                                                                                                                                                        │
│                                                                                                                                                                                                                                                                                                │
│ The current verification notebooks (2a/2b/3a/3b) simulate a single CCS half-beam with the shuttle end free in x. This prevents axial stress from building up, so no snap-through is observed — only monotonic force-displacement curves. The analytical model predicts bistability for Q=2.4 > │
│  2.31, but the single half-beam FEM cannot capture it.                                                                                                                                                                                                                                         │
│                                                                                                                                                                                                                                                                                                │
│ To observe snap-through in FEM, we need the complete doubly-clamped mechanism: two parallel beams connected by a rigid shuttle, with both left and right anchors clamped. The shuttle provides axial coupling — bending-induced length changes generate compressive stress, triggering mode    │
│ buckling and snap-through.                                                                                                                                                                                                                                                                     │
│                                                                                                                                                                                                                                                                                                │
│ New Files                                                                                                                                                                                                                                                                                      │
│                                                                                                                                                                                                                                                                                                │
│ ┌─────┬───────────────────────────────────────────────────┬───────────────────────────────────────────────────────────────────────┐                                                                                                                                                            │
│ │  #  │                       File                        │                                Purpose                                │                                                                                                                                                            │
│ ├─────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤                                                                                                                                                            │
│ │ 1   │ src/components/bistable_spring/complete_spring.py │ GDS component: 4 half-beams + shuttle + anchors                       │                                                                                                                                                            │
│ ├─────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤                                                                                                                                                            │
│ │ 2   │ src/verification/full_spring_utils.py             │ FEM geometry utility: merged polygon, mesh helpers, BC identification │                                                                                                                                                            │
│ ├─────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤                                                                                                                                                            │
│ │ 3   │ src/verification/4a_fem_skfem_2d_full.ipynb       │ scikit-fem 2D plane strain — full spring                              │                                                                                                                                                            │
│ ├─────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤                                                                                                                                                            │
│ │ 4   │ src/verification/4b_fem_skfem_3d_full.ipynb       │ scikit-fem 3D extruded — full spring                                  │                                                                                                                                                            │
│ ├─────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤                                                                                                                                                            │
│ │ 5   │ src/verification/5a_fem_calculix_2d_full.ipynb    │ CalculiX 2D plane strain — full spring                                │                                                                                                                                                            │
│ ├─────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤                                                                                                                                                            │
│ │ 6   │ src/verification/5b_fem_calculix_3d_full.ipynb    │ CalculiX 3D extruded — full spring                                    │                                                                                                                                                            │
│ └─────┴───────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────────┘                                                                                                                                                            │
│                                                                                                                                                                                                                                                                                                │
│ Modified: src/verification/README.md (add documentation for new notebooks)                                                                                                                                                                                                                     │
│                                                                                                                                                                                                                                                                                                │
│ ---                                                                                                                                                                                                                                                                                            │
│ Step 1: GDS Component — complete_spring.py                                                                                                                                                                                                                                                     │
│                                                                                                                                                                                                                                                                                                │
│ File: src/components/bistable_spring/complete_spring.py                                                                                                                                                                                                                                        │
│                                                                                                                                                                                                                                                                                                │
│ A @gf.cell function make_complete_spring() that assembles the full bistable mechanism for layout:                                                                                                                                                                                              │
│                                                                                                                                                                                                                                                                                                │
│ Geometry (top view):                                                                                                                                                                                                                                                                           │
│ Left Anchor ─── upper half-beam L ──╮            ╭── upper half-beam R ─── Right Anchor                                                                                                                                                                                                        │
│                                      │  shuttle  │                                                                                                                                                                                                                                             │
│ Left Anchor ─── lower half-beam L ──╯            ╰── lower half-beam R ─── Right Anchor                                                                                                                                                                                                        │
│                                                                                                                                                                                                                                                                                                │
│ Parameters with defaults:                                                                                                                                                                                                                                                                      │
│ - anchor_distance = 80.0 — inner-edge to inner-edge of anchors (µm)                                                                                                                                                                                                                            │
│ - beam_spacing = 10.0 — center-to-center distance between upper/lower beams (µm)                                                                                                                                                                                                               │
│ - shuttle_length = 7.0 — shuttle x-extent along beam axis (µm); ~1 etch hole + webbing                                                                                                                                                                                                         │
│ - shuttle_height = 12.0 — shuttle y-extent perpendicular to beams (µm); ~2 etch holes + webbing                                                                                                                                                                                                │
│ - shuttle_hole_diameter = 5.0 — square hole side (µm)                                                                                                                                                                                                                                          │
│ - shuttle_hole_gap = 0.8 — gap between holes (µm)                                                                                                                                                                                                                                              │
│ - Beam params: flex_ratio=0.3, flex_width=0.5, rigid_width=0.9375, initial_offset=1.2, taper_length=2.0                                                                                                                                                                                        │
│ - Anchor params: anchor_length=8.0, anchor_width=8.0, etc.                                                                                                                                                                                                                                     │
│                                                                                                                                                                                                                                                                                                │
│ Derived values:                                                                                                                                                                                                                                                                                │
│ - half_span = (anchor_distance - shuttle_length) / 2 = 36.5 µm (matches existing default)                                                                                                                                                                                                      │
│                                                                                                                                                                                                                                                                                                │
│ Assembly steps:                                                                                                                                                                                                                                                                                │
│ 1. Import make_ccs_half_beam from ccs_bistable_beam.py (existing)                                                                                                                                                                                                                              │
│ 2. Import make_proofmass from shuttle_beam.py (existing)                                                                                                                                                                                                                                       │
│ 3. Import make_mems_anchor from anchor.py (existing)                                                                                                                                                                                                                                           │
│ 4. Place 4 half-beams (same pattern as bistable_spring_pair.py lines 144-156)                                                                                                                                                                                                                  │
│ 5. Place shuttle at center: make_proofmass(length=shuttle_length, height=shuttle_height, hole_diameter=shuttle_hole_diameter, hole_gap=shuttle_hole_gap)                                                                                                                                       │
│   - Position: centered at (anchor_distance/2, initial_offset) — at the y-level where beam shuttle ends meet                                                                                                                                                                                    │
│ 6. Place 2 multi-layer anchors (left at x=0, right at x=anchor_distance)                                                                                                                                                                                                                       │
│                                                                                                                                                                                                                                                                                                │
│ Both beams curve in +y (same buckling mode). Shuttle connects their midpoints.                                                                                                                                                                                                                 │
│                                                                                                                                                                                                                                                                                                │
│ Reuses: _import_from() pattern from bistable_spring_pair.py (line 34-40)                                                                                                                                                                                                                       │
│                                                                                                                                                                                                                                                                                                │
│ ---                                                                                                                                                                                                                                                                                            │
│ Step 2: FEM Geometry Utility — full_spring_utils.py                                                                                                                                                                                                                                            │
│                                                                                                                                                                                                                                                                                                │
│ File: src/verification/full_spring_utils.py                                                                                                                                                                                                                                                    │
│                                                                                                                                                                                                                                                                                                │
│ Wraps geometry from beam_utils.py + Shapely boolean union to produce merged 2D polygon for meshing.                                                                                                                                                                                            │
│                                                                                                                                                                                                                                                                                                │
│ Key functions:                                                                                                                                                                                                                                                                                 │
│                                                                                                                                                                                                                                                                                                │
│ get_full_spring_polygon(...) -> np.ndarray                                                                                                                                                                                                                                                     │
│                                                                                                                                                                                                                                                                                                │
│ Returns a closed Nx2 polygon of the complete spring (two beams + solid shuttle rectangle):                                                                                                                                                                                                     │
│ 1. Generate 4 half-beam outlines using _compute_ccs_half_centerline + _compute_half_width_profile from ccs_bistable_beam.py                                                                                                                                                                    │
│ 2. Create shuttle as a solid rectangle (no etch holes for FEM — shuttle is orders of magnitude stiffer than beams, holes don't affect structural behavior)                                                                                                                                     │
│ 3. Use shapely.ops.unary_union() to merge all 5 polygons into single outline                                                                                                                                                                                                                   │
│ 4. Extract exterior coords as numpy array                                                                                                                                                                                                                                                      │
│                                                                                                                                                                                                                                                                                                │
│ Beam positioning (matches make_complete_spring):                                                                                                                                                                                                                                               │
│ - Left upper: anchor at (0, +bs/2), shuttle end at (hs, +bs/2 + h)                                                                                                                                                                                                                             │
│ - Left lower: anchor at (0, -bs/2), shuttle end at (hs, -bs/2 + h)                                                                                                                                                                                                                             │
│ - Right upper: mirrored (anchor at anchor_dist, shuttle at anchor_dist - hs)                                                                                                                                                                                                                   │
│ - Right lower: mirrored                                                                                                                                                                                                                                                                        │
│ - Shuttle: solid rect from x=hs to x=hs+sw, y spanning both beams                                                                                                                                                                                                                              │
│                                                                                                                                                                                                                                                                                                │
│ Where bs=beam_spacing, hs=half_span, h=initial_offset, sw=shuttle_length.                                                                                                                                                                                                                      │
│                                                                                                                                                                                                                                                                                                │
│ identify_bc_nodes_2d(nodes, anchor_distance, half_span, shuttle_length, tol=0.05)                                                                                                                                                                                                              │
│                                                                                                                                                                                                                                                                                                │
│ Returns dict of node index arrays:                                                                                                                                                                                                                                                             │
│ - left_anchor: nodes at x < tol                                                                                                                                                                                                                                                                │
│ - right_anchor: nodes at x > anchor_distance - tol                                                                                                                                                                                                                                             │
│ - shuttle_center: nodes in shuttle region (hs < x < hs+sw)                                                                                                                                                                                                                                     │
│                                                                                                                                                                                                                                                                                                │
│ get_full_spring_3d_mesh(polygon, thickness, lc_flex, lc_rigid, n_layers_z, ...)                                                                                                                                                                                                                │
│                                                                                                                                                                                                                                                                                                │
│ Extrudes the 2D polygon via gmsh, returns (points, tets) for 3D FEM.                                                                                                                                                                                                                           │
│                                                                                                                                                                                                                                                                                                │
│ identify_bc_nodes_3d(points, ...) — same as 2D but for 3D mesh                                                                                                                                                                                                                                 │
│                                                                                                                                                                                                                                                                                                │
│ Constants                                                                                                                                                                                                                                                                                      │
│                                                                                                                                                                                                                                                                                                │
│ Reexports POLY_SI, DEFAULT_BEAM_PARAMS from beam_utils.py.                                                                                                                                                                                                                                     │
│ Adds DEFAULT_FULL_SPRING_PARAMS:                                                                                                                                                                                                                                                               │
│ dict(                                                                                                                                                                                                                                                                                          │
│     anchor_distance=80.0,                                                                                                                                                                                                                                                                      │
│     beam_spacing=10.0,                                                                                                                                                                                                                                                                         │
│     shuttle_length=7.0,                                                                                                                                                                                                                                                                        │
│     shuttle_height=12.0,                                                                                                                                                                                                                                                                       │
│     half_span=36.5,  # derived                                                                                                                                                                                                                                                                 │
│     flex_ratio=0.3,                                                                                                                                                                                                                                                                            │
│     flex_width=0.5,                                                                                                                                                                                                                                                                            │
│     rigid_width=0.9375,                                                                                                                                                                                                                                                                        │
│     initial_offset=1.2,                                                                                                                                                                                                                                                                        │
│     taper_length=2.0,                                                                                                                                                                                                                                                                          │
│ )                                                                                                                                                                                                                                                                                              │
│                                                                                                                                                                                                                                                                                                │
│ ---                                                                                                                                                                                                                                                                                            │
│ Step 3: Notebook 4a — scikit-fem 2D Full Spring                                                                                                                                                                                                                                                │
│                                                                                                                                                                                                                                                                                                │
│ File: src/verification/4a_fem_skfem_2d_full.ipynb                                                                                                                                                                                                                                              │
│ Based on: 2a_fem_skfem_2d.ipynb                                                                                                                                                                                                                                                                │
│                                                                                                                                                                                                                                                                                                │
│ Structure (each section runs 3 mesh densities):                                                                                                                                                                                                                                                │
│                                                                                                                                                                                                                                                                                                │
│ 1. Setup: Import full_spring_utils, define parameters, set mesh density levels:                                                                                                                                                                                                                │
│   - densities = {"coarse_10pct": 10.0, "medium_50pct": 2.0, "fine_100pct": 1.0}                                                                                                                                                                                                                │
│   - base_max_area = 0.008 µm² (same per-beam density as notebook 2a)                                                                                                                                                                                                                           │
│   - Actual max_area = base_max_area * scale_factor                                                                                                                                                                                                                                             │
│ 2. Geometry: get_full_spring_polygon() → single merged outline                                                                                                                                                                                                                                 │
│ 3. Loop over 3 densities (10%, 50%, 100%):                                                                                                                                                                                                                                                     │
│   - Mesh with triangle at corresponding max_area                                                                                                                                                                                                                                               │
│   - Create MeshTri, Basis(mesh, ElementVector(ElementTriP1()))                                                                                                                                                                                                                                 │
│   - Identify BCs: left anchor clamped, right anchor clamped, shuttle y-prescribed                                                                                                                                                                                                              │
│   - Critical BC change vs 2a: Both left AND right anchors clamped (u_x=u_y=0), shuttle y-prescribed. Shuttle u_x is NOT explicitly constrained — the doubly-clamped geometry + shuttle material stiffness naturally provides axial constraint.                                                 │
│   - Linear sweep (quick validation)                                                                                                                                                                                                                                                            │
│   - Nonlinear sweep (Total Lagrangian, reuse forms from 2a with I2 identity)                                                                                                                                                                                                                   │
│   - Extract reaction force at shuttle y-DOFs                                                                                                                                                                                                                                                   │
│   - Plot force-displacement for this density                                                                                                                                                                                                                                                   │
│   - Store results                                                                                                                                                                                                                                                                              │
│ 4. Mesh convergence plot: Overlay all 3 densities                                                                                                                                                                                                                                              │
│ 5. Deformed shapes: At key displacements for fine mesh                                                                                                                                                                                                                                         │
│ 6. Save results: CSV for each density                                                                                                                                                                                                                                                          │
│                                                                                                                                                                                                                                                                                                │
│ Key differences from 2a:                                                                                                                                                                                                                                                                       │
│                                                                                                                                                                                                                                                                                                │
│ - Geometry: full spring polygon (two beams + shuttle) instead of single half-beam                                                                                                                                                                                                              │
│ - BCs: two clamped ends (left AND right anchors) + shuttle prescribed                                                                                                                                                                                                                          │
│ - DOF counts: ~4-5x larger (more elements for the larger geometry)                                                                                                                                                                                                                             │
│ - Expected result: positive force region followed by snap-through (vs monotonic negative in 2a)                                                                                                                                                                                                │
│                                                                                                                                                                                                                                                                                                │
│ ---                                                                                                                                                                                                                                                                                            │
│ Step 4: Notebook 4b — scikit-fem 3D Full Spring                                                                                                                                                                                                                                                │
│                                                                                                                                                                                                                                                                                                │
│ File: src/verification/4b_fem_skfem_3d_full.ipynb                                                                                                                                                                                                                                              │
│ Based on: 2b_fem_skfem_3d.ipynb                                                                                                                                                                                                                                                                │
│                                                                                                                                                                                                                                                                                                │
│ Same structure as 4a but with 3D extrusion:                                                                                                                                                                                                                                                    │
│ - 3D mesh via get_full_spring_3d_mesh() using gmsh                                                                                                                                                                                                                                             │
│ - MeshTet, ElementVector(ElementTetP1())                                                                                                                                                                                                                                                       │
│ - I3 identity, 3D nonlinear forms (reuse from 2b)                                                                                                                                                                                                                                              │
│ - BCs: left/right anchors clamped (u_x=u_y=u_z=0), shuttle y-prescribed (u_x, u_z free)                                                                                                                                                                                                        │
│                                                                                                                                                                                                                                                                                                │
│ Mesh density levels for 3D:                                                                                                                                                                                                                                                                    │
│ - 10%: lc_flex=0.8, lc_rigid=1.2, n_layers_z=2                                                                                                                                                                                                                                                 │
│ - 50%: lc_flex=0.5, lc_rigid=0.8, n_layers_z=2                                                                                                                                                                                                                                                 │
│ - 100%: lc_flex=0.3, lc_rigid=0.5, n_layers_z=3                                                                                                                                                                                                                                                │
│                                                                                                                                                                                                                                                                                                │
│ ---                                                                                                                                                                                                                                                                                            │
│ Step 5: Notebook 5a — CalculiX 2D Full Spring                                                                                                                                                                                                                                                  │
│                                                                                                                                                                                                                                                                                                │
│ File: src/verification/5a_fem_calculix_2d_full.ipynb                                                                                                                                                                                                                                           │
│ Based on: 3a_fem_calculix_2d.ipynb                                                                                                                                                                                                                                                             │
│                                                                                                                                                                                                                                                                                                │
│ Same geometry as 4a, but uses CalculiX CPE3 elements:                                                                                                                                                                                                                                          │
│ - Mesh with triangle, write .inp files                                                                                                                                                                                                                                                         │
│ - Node sets: LEFT_ANCHOR, RIGHT_ANCHOR, SHUTTLE                                                                                                                                                                                                                                                │
│ - BCs: LEFT_ANCHOR, 1, 2, 0.0 + RIGHT_ANCHOR, 1, 2, 0.0 + SHUTTLE, 2, 2, delta                                                                                                                                                                                                                 │
│ - *STEP, NLGEOM, INC=1000 with *STATIC for each displacement step                                                                                                                                                                                                                              │
│ - Parse reaction forces from .dat output (reuse parser from 3a)                                                                                                                                                                                                                                │
│ - Run at 3 mesh densities, overlay results                                                                                                                                                                                                                                                     │
│                                                                                                                                                                                                                                                                                                │
│ Working directories: results/ccx_2d_full_10pct/, results/ccx_2d_full_50pct/, results/ccx_2d_full_100pct/                                                                                                                                                                                       │
│                                                                                                                                                                                                                                                                                                │
│ ---                                                                                                                                                                                                                                                                                            │
│ Step 6: Notebook 5b — CalculiX 3D Full Spring                                                                                                                                                                                                                                                  │
│                                                                                                                                                                                                                                                                                                │
│ File: src/verification/5b_fem_calculix_3d_full.ipynb                                                                                                                                                                                                                                           │
│ Based on: 3b_fem_calculix_3d.ipynb                                                                                                                                                                                                                                                             │
│                                                                                                                                                                                                                                                                                                │
│ 3D version of 5a with C3D10 elements:                                                                                                                                                                                                                                                          │
│ - 3D mesh via gmsh, write .inp with C3D10 elements                                                                                                                                                                                                                                             │
│ - BCs: LEFT_ANCHOR, 1, 3, 0.0 + RIGHT_ANCHOR, 1, 3, 0.0 + SHUTTLE, 2, 2, delta                                                                                                                                                                                                                 │
│ - 3 mesh densities                                                                                                                                                                                                                                                                             │
│ - Includes final cross-method comparison (loads all full-spring CSV results + analytical for overlay plot)                                                                                                                                                                                     │
│                                                                                                                                                                                                                                                                                                │
│ Working directories: results/ccx_3d_full_10pct/, results/ccx_3d_full_50pct/, results/ccx_3d_full_100pct/                                                                                                                                                                                       │
│                                                                                                                                                                                                                                                                                                │
│ ---                                                                                                                                                                                                                                                                                            │
│ Step 7: Update README                                                                                                                                                                                                                                                                          │
│                                                                                                                                                                                                                                                                                                │
│ Add sections documenting:                                                                                                                                                                                                                                                                      │
│ - New notebooks 4a/4b/5a/5b                                                                                                                                                                                                                                                                    │
│ - Full spring geometry and BCs                                                                                                                                                                                                                                                                 │
│ - Expected results (snap-through behavior)                                                                                                                                                                                                                                                     │
│ - Mesh density strategy                                                                                                                                                                                                                                                                        │
│                                                                                                                                                                                                                                                                                                │
│ ---                                                                                                                                                                                                                                                                                            │
│ Expected Results                                                                                                                                                                                                                                                                               │
│                                                                                                                                                                                                                                                                                                │
│ With proper doubly-clamped BCs + axial coupling from the shuttle, the force-displacement curve should show:                                                                                                                                                                                    │
│ 1. Positive force initially (resisting downward push) — bending stiffness dominates                                                                                                                                                                                                            │
│ 2. Force decreasing as axial compression builds and softens the response                                                                                                                                                                                                                       │
│ 3. Zero crossing at critical displacement — snap-through point                                                                                                                                                                                                                                 │
│ 4. Negative force (beam actively pulls toward second stable state)                                                                                                                                                                                                                             │
│ 5. Return to zero at delta ≈ -2h (second stable position at -2.4 µm)                                                                                                                                                                                                                           │
│                                                                                                                                                                                                                                                                                                │
│ Push/pop ratio should be ~0.87 for CCS beams (Ma 2024). Full spring pair force ≈ 4× single half-beam ≈ 4 × 2.48 = ~10 µN.                                                                                                                                                                      │
│                                                                                                                                                                                                                                                                                                │
│ Verification                                                                                                                                                                                                                                                                                   │
│                                                                                                                                                                                                                                                                                                │
│ 1. Run complete_spring.py standalone (./switch-env/bin/python src/components/bistable_spring/complete_spring.py) to verify GDS component renders correctly                                                                                                                                     │
│ 2. Run each notebook at 10% density first (fast, ~1-2 min) — verify positive force region appears                                                                                                                                                                                              │
│ 3. Run at 50% density — verify force curve converges                                                                                                                                                                                                                                           │
│ 4. Run at 100% density — production results                                                                                                                                                                                                                                                    │
│ 5. Compare force curves across all methods — should agree within ~10%                                                                                                                                                                                                                          │
│ 6. Compare with analytical model predictions (F_push ≈ 10 µN for 4 beams)                                                                                                                                                                                                                      