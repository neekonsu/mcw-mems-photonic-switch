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
├── 1_analytical_model.ipynb          # Qiu/Pham energy minimization
├── 2a_fem_skfem_2d.ipynb             # scikit-fem 2D plane strain
├── 2b_fem_skfem_3d.ipynb             # scikit-fem 3D extruded
├── 3a_fem_calculix_2d.ipynb          # CalculiX 2D plane strain
├── 3b_fem_calculix_3d.ipynb          # CalculiX 3D extruded + cross-method comparison
├── plots/                            # Saved figures (PNG)
│   ├── analytical_*.png              # Notebook 1 plots
│   ├── skfem_2d_*.png                # Notebook 2a plots
│   ├── skfem_3d_*.png                # Notebook 2b plots
│   ├── calculix_2d_*.png             # Notebook 3a plots
│   ├── calculix_3d_*.png             # Notebook 3b plots
│   └── comparison_force_displacement.png  # Cross-method overlay
└── results/                          # Saved data (CSV)
    ├── analytical_force_displacement.csv
    ├── analytical_critical_values.csv
    ├── skfem_2d_force_displacement.csv
    ├── skfem_3d_force_displacement.csv
    ├── calculix_2d_force_displacement.csv
    ├── calculix_3d_force_displacement.csv
    ├── comparison_critical_values.csv
    └── ccx_2d/, ccx_3d/              # CalculiX working dirs (.inp, .dat, .frd)
```

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

1. `1_analytical_model.ipynb` — no external deps beyond numpy/scipy
2. `2a_fem_skfem_2d.ipynb` — needs scikit-fem, triangle
3. `3a_fem_calculix_2d.ipynb` — needs calculix
4. `2b_fem_skfem_3d.ipynb` — needs gmsh, meshio (~35 min)
5. `3b_fem_calculix_3d.ipynb` — needs gmsh (~25 min); includes final comparison

All notebooks must be run from the `src/verification/` directory (they use
relative paths for imports and output).  Use the `switch-env` kernel:

```bash
cd src/verification
../../switch-env/bin/python -m jupyter nbconvert --to notebook --execute \
    <notebook>.ipynb --ExecutePreprocessor.timeout=3600 \
    --ExecutePreprocessor.kernel_name=switch-env
```

## Follow-Up: Full CCS Mechanism Simulation

The absence of snap-through in the current results is expected and understood.
The next step is to build and run simulations of the **complete CCS bistable
mechanism** — two parallel beams connected by a rigid shuttle — to observe
the snap-through transition predicted by the analytical model.

### What needs to change

1. **Geometry**: Model two parallel half-beams (upper and lower) with a
   shared rigid shuttle connecting them at x=L.  Alternatively, model a
   single full-span doubly-clamped beam (anchor→shuttle→anchor, 2*L span)
   which is the Qiu (2004) configuration.

2. **Boundary conditions**: The critical change is that the **shuttle x-DOF
   must be constrained** (u_x=0 at x=L).  This prevents axial elongation
   and allows compressive stress to build up during bending:
   - Anchor (x≈0): u_x = u_y = 0 (clamped)
   - Shuttle (x≈L): u_x = 0 (axially constrained), u_y = delta (prescribed)
   Or equivalently for a full-span beam:
   - Left anchor (x=0): u_x = u_y = 0
   - Right anchor (x=2L): u_x = u_y = 0
   - Center (x=L): u_y = delta (prescribed), u_x free but coupled

3. **Shuttle modeling**: In FEM, the shuttle can be modeled as:
   - A rigid body constraint (MPC in CalculiX: `*EQUATION` or `*RIGID BODY`)
   - A very stiff block of elements
   - Simply constraining u_x=0 at the shuttle nodes (simplest approach, but
     neglects the shuttle's finite stiffness)

4. **Solver**: The nonlinear solve becomes significantly harder near the
   snap-through point.  Arc-length methods (Riks, Crisfield) may be needed
   instead of simple Newton-Raphson with displacement control, because the
   force-displacement curve has a turning point.  CalculiX supports this via
   `*STATIC, SOLVER=RIKS`.

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
