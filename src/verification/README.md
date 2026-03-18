# Bistable Spring Verification

Force-displacement analysis of the CCS bistable spring using analytical,
scikit-fem, and CalculiX methods. Notebooks progress from single half-beam
validation (1–3b) through full doubly-clamped spring simulation (4a–5b) to
the production geometry with fillets and parameter sweeps (4aa).

Verified GDS layouts are exported by notebook 4aa to `src/components/verified/`.

## Notebooks

| # | File | Description |
|---|------|-------------|
| 1 | `1_analytical_model.ipynb` | Qiu/Pham energy minimization (half-beam) |
| 2a | `2a_fem_skfem_2d.ipynb` | scikit-fem 2D plane strain (half-beam) |
| 2b | `2b_fem_skfem_3d.ipynb` | scikit-fem 3D extruded (half-beam, ~35 min) |
| 3a | `3a_fem_calculix_2d.ipynb` | CalculiX 2D plane strain (half-beam) |
| 3b | `3b_fem_calculix_3d.ipynb` | CalculiX 3D extruded + half-beam cross-method comparison (~25 min) |
| 4a | `4a_fem_skfem_2d_full.ipynb` | scikit-fem 2D full spring (doubly-clamped, 3 mesh densities) |
| **4aa** | **`4aa_fem_skfem_2d_full_fillet.ipynb`** | **scikit-fem 2D full spring with fillets, junction widening, parameter sweeps; exports GDS to `../components/verified/`** |
| 4b | `4b_fem_skfem_3d_full.ipynb` | scikit-fem 3D full spring |
| 5a | `5a_fem_calculix_2d_full.ipynb` | CalculiX 2D full spring |
| 5b | `5b_fem_calculix_3d_full.ipynb` | CalculiX 3D full spring + cross-method comparison |
| 6 | `6_results_viewer.ipynb` | Results viewer |

## Running

All notebooks must be run from `src/verification/` (relative import paths).

```bash
cd src/verification

# Interactive
../../switch-env/bin/python -m jupyter notebook <notebook>.ipynb

# Batch execution
../../switch-env/bin/python -m jupyter nbconvert --to notebook --execute \
    <notebook>.ipynb --ExecutePreprocessor.timeout=3600 \
    --ExecutePreprocessor.kernel_name=switch-env
```

## File Structure

```
src/verification/
├── README.md
├── beam_utils.py                     # Shared half-beam geometry + material
├── full_spring_utils.py              # Full spring polygon (Shapely merge) + BC utils
├── 1_analytical_model.ipynb
├── 2a_fem_skfem_2d.ipynb
├── 2b_fem_skfem_3d.ipynb
├── 3a_fem_calculix_2d.ipynb
├── 3b_fem_calculix_3d.ipynb
├── 4a_fem_skfem_2d_full.ipynb
├── 4aa_fem_skfem_2d_full_fillet.ipynb
├── 4b_fem_skfem_3d_full.ipynb
├── 5a_fem_calculix_2d_full.ipynb
├── 5b_fem_calculix_3d_full.ipynb
├── 6_results_viewer.ipynb
├── plots/                            # PNG outputs from all notebooks
└── results/                          # CSV outputs + CalculiX working dirs
    ├── *.csv
    ├── ccx_2d/, ccx_3d/              # Half-beam CalculiX artifacts
    └── ccx_2d_full_*/, ccx_3d_full_*/  # Full spring CalculiX artifacts
```

**Note**: `.frd`, `.inp`, and `.msh` files in `results/` are gitignored (large
simulation artifacts). Only `.csv` and `.dat` files are tracked.

## GDS Output

Notebook 4aa exports FEM-verified bistable spring components to:

```
src/components/verified/
├── verified_bs_ad100_h1.50_fr0.20_rw1.50_fw0.50_bs10_sl7.gds
├── bistable_spring_ad120_h2.00_fr0.15_rw1.00_fw0.50_bs10_sl7.gds
└── bistable_spring_ad100_h1.50_fr0.20_rw1.50_fw0.50_bs10_sl7.gds
```

Filenames encode the spring parameters (anchor distance, apex height, flex ratio,
rigid width, flex width, beam spacing, shuttle length).

## Dependencies

All installed into `./switch-env/`:

```bash
./switch-env/bin/pip install scikit-fem triangle meshio gmsh
conda install -c conda-forge calculix -p ./switch-env
```
