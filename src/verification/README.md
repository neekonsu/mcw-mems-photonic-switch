# Bistable Spring Verification

Force-displacement analysis of the CCS bistable beam through snap-through transition.
Three independent methods provide cross-validation: analytical energy minimization,
scikit-fem (pure Python FEA), and CalculiX (industrial FEA solver). Each FEM method
runs in 2D plane strain first, then 3D extruded geometry.

## What we're simulating

A single full CCS beam (`make_ccs_beam` configuration) — both ends clamped at anchors,
displacement prescribed at center, extracting reaction force.

| Parameter        | Value           |
|------------------|-----------------|
| Span             | 40 µm           |
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

## File Structure

```
src/verification/
├── README.md                         # This file
├── beam_utils.py                     # Shared geometry extraction + material props
├── 1_analytical_model.ipynb          # Qiu/Pham energy minimization
├── 2a_fem_skfem_2d.ipynb             # scikit-fem 2D plane strain
├── 2b_fem_skfem_3d.ipynb             # scikit-fem 3D extruded
├── 3a_fem_calculix_2d.ipynb          # CalculiX 2D plane strain
├── 3b_fem_calculix_3d.ipynb          # CalculiX 3D extruded + comparison section
├── plots/                            # Saved figures (PNG)
└── results/                          # Saved data (CSV)
    └── ccx_2d/, ccx_3d/              # CalculiX working directories (.inp, .dat, .frd)
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

```python
from beam_utils import (
    POLY_SI,                        # {"E": 160e3, "nu": 0.22, "t": 0.5, ...}
    DEFAULT_BEAM_PARAMS,            # span=40, flex_ratio=0.3, ...
    get_beam_centerline,            # (x, y) arrays
    get_beam_width_profile,         # w(x) array
    get_beam_polygon,               # Nx2 closed polygon for meshing
    get_moment_of_inertia_profile,  # I(x) = w(x)*t³/12
)
```

## Notebook 1: Analytical Model

**Method**: Qiu, Lang & Slocum (JMEMS 2004) energy minimization with mode
decomposition. Beam deflection expanded in symmetric buckling modes
phi_n(x) = 0.5[1 - cos(2*n*pi*x/L)] for n = 1, 3, 5. For each prescribed
center displacement delta, total energy (bending + axial) is minimized over
free mode amplitudes (a3, a5), with constraint a1 + a3 + a5 = delta.
Force F = dU_min/d(delta).

For CCS variable-width beams, bending stiffness coefficients are computed by
numerical integration: beta_mn = E * integral of I(x) * phi_m''(x) * phi_n''(x) dx.
Cross-coupling terms included (modes are not orthogonal w.r.t. variable-I
inner product).

**Status**: Ran to completion. Produces plots and CSV results.

**Results (as run)**:

| Beam     | F_push (µN) | F_pop (µN) | \|F_pop/F_push\| |
|----------|-------------|------------|-------------------|
| Uniform  | 250.87      | -15.18     | 0.060             |
| CCS      | 382.37      | -17.54     | 0.046             |

**Known issue**: The push/pop force ratio is far from the expected values
(~0.76 for uniform, ~0.87 for CCS). The F(delta) curve shows a large initial
stiffness peak but weak negative (snap-back) force region. Root cause is likely
in the axial energy formulation — the initial shape used in the axial shortening
baseline S0 = pi² h²/(2L) assumes the initial shape is exactly a1 = h (pure
mode 1 cosine), but the CCS beam centerline is *not* a pure mode-1 cosine; it
has rigid straight segments that contribute different axial shortening. The mode
decomposition treats the initial state as a1⁰ = h, a3⁰ = a5⁰ = 0, which is
only exact for a pure cosine beam. For the CCS beam, the actual initial shape
should be projected onto the mode basis to get the correct initial amplitudes.

Additionally, the uniform beam result (ratio 0.06 vs expected 0.76) suggests
the issue is more fundamental — possibly the axial shortening formula
S = (pi²/2L) * sum(n² * an²) is only valid for beams where the *deflection
from flat* follows these modes, whereas the model is treating modes as the
*total* shape including the initial offset. The Qiu formulation defines w(x)
as the total position (not deflection from initial), so the axial terms need
the shortening of the *current* shape minus the shortening of the *initial*
shape. If the initial shape projection onto higher modes is nonzero (it
shouldn't be for a pure cosine beam, but numerical gradient effects could
cause issues), this would produce asymmetric F(delta).

**Next steps to fix**:
1. Verify the uniform-beam case against Qiu's exact closed-form expressions
   (their Eq. 10–12) to isolate whether the issue is in the energy terms or
   the minimization/gradient.
2. Check that `np.gradient` produces clean numerical derivatives — consider
   using a finer delta grid or analytic dU/d(delta).
3. For CCS beam, project the actual CCS initial centerline onto the mode
   basis to get correct a1⁰, a3⁰, a5⁰.

**Output files**:
- `plots/analytical_beam_geometry.png`
- `plots/analytical_force_displacement.png`
- `plots/analytical_energy_landscape.png`
- `plots/analytical_mode_amplitudes.png`
- `plots/analytical_deformed_shapes.png`
- `results/analytical_force_displacement.csv` (delta, F_uniform, F_ccs)
- `results/analytical_critical_values.csv`

## Notebook 2a: scikit-fem 2D Plane Strain

**Method**: Triangulate beam polygon with `triangle` library (6093 nodes,
10973 P2 triangles). Total Lagrangian formulation with Green-Lagrange strain
and St. Venant-Kirchhoff material. Newton-Raphson iteration at each
displacement step.

**Status**: Mesh generation and boundary ID succeeded. Linear and nonlinear
solves **failed** due to a DOF-indexing bug.

**Bug**: The `ElementVector(ElementTriP2())` basis has `Nbfun = 12` total DOFs
in the test, which is far too few for 6093 nodes. The issue is that `MeshTri`
construction from raw triangle output may not be creating the mesh correctly,
or the P2 mid-edge DOFs are not being generated. The code then tries to index
`anchor_nodes` (node indices like 100, 200, ...) into a size-12 DOF array,
causing `IndexError: index 12 is out of bounds for axis 0 with size 12`.

**Root cause**: The `Basis(mesh, ElementVector(elem))` total DOF count shows
only 12, which suggests the mesh has only 6 vertices (not 6093). The
`MeshTri(nodes.T, elems.T)` constructor likely silently truncated or
reindexed. Need to verify that `nodes.T` has shape `(2, N)` and `elems.T`
has shape `(3, M)` with correct dtype.

**Next steps to fix**:
1. Add shape/dtype assertions after MeshTri construction:
   `assert mesh.nvertices == len(nodes)`.
2. Ensure `nodes` and `elems` from triangle output have correct types
   (float64 and int32/int64).
3. The boundary node identification uses vertex indices directly as DOF
   indices — this is only correct for P1 elements. For P2, vertex DOFs are
   the first `nvertices` DOFs, which should work, but verify the DOF layout
   documentation for `ElementVector`.
4. Test with a simple rectangle mesh first to validate the nonlinear solver
   before applying to the beam polygon.

**Output files generated**:
- `plots/skfem_2d_mesh.png` (mesh looks correct in the plot)

## Notebook 2b: scikit-fem 3D Extruded

**Method**: Extrude beam polygon by t=0.5 µm using gmsh, create MeshTet,
apply 3D linear elasticity followed by Total Lagrangian nonlinear solve.

**Status**: Mesh generated via gmsh (plot exists at `plots/skfem_3d_mesh.png`).
Solves not yet attempted (blocked by 2a issues; same DOF-indexing pattern
used here).

**Next steps**: Fix 2a first, then apply same fixes here. The 3D solve will
be significantly more expensive — consider reducing to ~50 displacement steps
and using P1 (not P2) elements.

## Notebook 3a: CalculiX 2D Plane Strain

**Method**: Generate CPE3 (3-node plane strain triangle) mesh from same
triangle output. Write `.inp` files programmatically. Run `ccx` as subprocess
for each displacement step. Parse `.dat` output for reaction forces.

**Status**: ccx solves converge successfully (verified in test run output).
However, the **reaction force parser failed** — all forces in the CSV are zero.

**Bug**: The `.dat` output format is:

```
 total force (fx,fy,fz) for set CENTER and time  0.1000000E+01

       -1.703979E-08 -8.322464E+00  5.967588E-13
```

The header "total force (fx,fy,fz)..." is on one line, and the actual values
are on the **next** line (indented, with three floats). The parser was looking
for `'total' in line.lower()` and trying to parse numbers from the same line,
but the "total force" line contains no numbers — they're on the following line.

The test run at delta = -1.2 µm actually produced RF_y = -8.32 µN (the value
is there in the .dat file, just not being parsed).

**Next steps to fix**:
1. Update `parse_ccx_reaction_force()` to read the line *after* the "total
   force" header:
   ```python
   for i, line in enumerate(lines):
       if 'total force' in line.lower():
           # Values are on the next line
           parts = lines[i + 1].split()
           rf_y = float(parts[1])  # fy is second column
   ```
2. Return the **last** total force entry (final converged increment at
   time=1.0), not the first one.
3. Re-run the sweep — ccx already produced all the .dat files in
   `results/ccx_2d/step_*.dat`, so re-parsing without re-running ccx is
   possible.

**Output files generated**:
- `plots/calculix_2d_mesh.png`
- `plots/calculix_2d_force_displacement.png` (flat line at F=0 due to parser bug)
- `plots/calculix_2d_deformed_shapes.png`
- `results/ccx_2d/step_*.inp` (50 input files)
- `results/ccx_2d/step_*.dat` (50 output files with correct data)
- `results/ccx_2d/step_*.frd` (50 binary result files)

## Notebook 3b: CalculiX 3D Extruded

**Method**: Extrude beam polygon via gmsh, generate C3D10 (10-node tet)
elements, write `.inp`, run ccx with NLGEOM.

**Status**: Not yet run (blocked by 3a parser fix — same parser function
is used).

**Next steps**: Fix 3a parser first, verify 2D results, then run 3D.

## Comparison Section (in 3b)

The final cells in `3b_fem_calculix_3d.ipynb` load all CSV results and produce:
- **Overlay plot**: All F(delta) curves on one figure
- **Critical values table**: F_push, F_pop, ratio for each method
- Saved as `plots/comparison_force_displacement.png`,
  `results/comparison_critical_values.csv`

Not yet runnable — needs upstream results.

## Execution Order

Run notebooks in this order (each depends on the previous completing):

1. `1_analytical_model.ipynb` — no external deps beyond numpy/scipy
2. `2a_fem_skfem_2d.ipynb` — needs scikit-fem, triangle
3. `3a_fem_calculix_2d.ipynb` — needs calculix
4. `2b_fem_skfem_3d.ipynb` — needs gmsh, meshio
5. `3b_fem_calculix_3d.ipynb` — needs gmsh; includes final comparison

All notebooks should be run from the `src/verification/` directory (they use
relative paths for imports and output).

## Summary of Open Issues

| # | Notebook | Issue | Severity | Fix Effort |
|---|----------|-------|----------|------------|
| 1 | 1_analytical | Push/pop ratio ~0.05 instead of ~0.76/0.87 | High | Medium — verify against Qiu closed-form, check energy terms |
| 2 | 2a_skfem_2d | DOF indexing crash (size-12 array) | Blocking | Low — verify MeshTri construction from triangle output |
| 3 | 3a_calculix_2d | Reaction force parser returns None | Blocking | Low — fix 2-line parse pattern for "total force" output |
| 4 | 2b, 3b | Not yet run | Blocked | — depends on 2a and 3a fixes |

## Key Source Files

| File | Role |
|------|------|
| `src/components/bistable_spring/ccs_bistable_beam.py` | Geometry: `_compute_ccs_centerline`, `_compute_width_profile` |
| `src/components/bistable_spring/bistable_spring_pair.py` | Spring pair assembly (reference, not simulated directly) |
| `src/libraries/mcw_custom_optical_mems_pdk.py` | LAYER definitions, LAYER_STACK |

## References

- Qiu, Lang & Slocum, "A Centrally-Clamped Parallel-Beam Bistable MEMS Mechanism," JMEMS 13(2), 2004
- Ma et al., "Nonvolatile Silicon Photonic MEMS Switch Based on Centrally-Clamped Stepped Bistable Mechanical Beams," Zhejiang University, 2024
- Baker, "How the cricket chirps," PNAS 100(12), 2003
