"""Shared utilities for full bistable spring verification.

Wraps geometry functions from ccs_bistable_beam.py and beam_utils.py to
produce merged 2D polygons and 3D meshes of the complete doubly-clamped
spring mechanism (two beams + shuttle).

The full spring geometry has both left and right anchors clamped, with
the shuttle providing axial coupling.  This enables snap-through
bistability that cannot be observed with a single free-ended half-beam.

Uses the **half-beam** geometry (make_ccs_half_beam configuration) as
the building block, mirrored and offset for upper/lower + left/right.
"""

import sys
import os
import numpy as np

# Import geometry functions from existing modules
_beam_dir = os.path.join(os.path.dirname(__file__), "../components/bistable_spring")
sys.path.insert(0, _beam_dir)
from ccs_bistable_beam import (
    _compute_ccs_half_centerline,
    _compute_half_width_profile,
)

# Re-export material properties from beam_utils
sys.path.insert(0, os.path.dirname(__file__))
from beam_utils import POLY_SI, DEFAULT_BEAM_PARAMS

# ---------------------------------------------------------------------------
# Default full spring parameters
# ---------------------------------------------------------------------------
DEFAULT_FULL_SPRING_PARAMS = dict(
    anchor_distance=80.0,
    beam_spacing=10.0,
    shuttle_length=7.0,
    shuttle_height=12.0,
    half_span=36.5,       # derived: (anchor_distance - shuttle_length) / 2
    flex_ratio=0.3,
    flex_width=0.5,
    rigid_width=0.9375,
    initial_offset=1.2,
    taper_length=2.0,
)


# ---------------------------------------------------------------------------
# 2D polygon generation
# ---------------------------------------------------------------------------

def _half_beam_polygon(half_span, flex_ratio, flex_width, rigid_width,
                       initial_offset, taper_length, n_points=400):
    """Return Nx2 closed polygon for a single CCS half-beam.

    Anchor at (0,0), shuttle end at (half_span, initial_offset).
    """
    x_c, y_c = _compute_ccs_half_centerline(half_span, flex_ratio,
                                             initial_offset, n_points)
    w = _compute_half_width_profile(x_c, half_span, flex_ratio, flex_width,
                                    rigid_width, taper_length)

    upper = np.column_stack([x_c, y_c + w / 2.0])
    lower = np.column_stack([x_c[::-1], (y_c - w / 2.0)[::-1]])
    poly = np.vstack([upper, lower])

    # Close
    if not np.allclose(poly[0], poly[-1]):
        poly = np.vstack([poly, poly[0]])
    return poly


def get_full_spring_polygon(
    anchor_distance=80.0,
    beam_spacing=10.0,
    shuttle_length=7.0,
    shuttle_height=12.0,
    flex_ratio=0.3,
    flex_width=0.5,
    rigid_width=0.9375,
    initial_offset=1.2,
    taper_length=2.0,
    n_points=400,
):
    """Return Nx2 closed polygon of the complete spring (merged outline).

    Geometry: 4 half-beams + solid shuttle rectangle, merged via Shapely
    boolean union into a single outline suitable for meshing.

    The shuttle is solid (no etch holes) because it is orders of magnitude
    stiffer than the beams and holes don't affect structural behavior.

    Coordinate system:
      - Left anchors at x=0
      - Right anchors at x=anchor_distance
      - Upper beams at y = +beam_spacing/2
      - Lower beams at y = -beam_spacing/2
      - Beams curve in +y direction

    Returns:
        Nx2 numpy array of exterior polygon coordinates (closed).
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    half_span = (anchor_distance - shuttle_length) / 2.0
    half_sp = beam_spacing / 2.0

    # Generate one half-beam polygon
    hb = _half_beam_polygon(half_span, flex_ratio, flex_width, rigid_width,
                            initial_offset, taper_length, n_points)

    polys = []

    # 4 half-beams: left-upper, left-lower, right-upper, right-lower
    for sign_x, sign_y in [(-1, +1), (-1, -1), (+1, +1), (+1, -1)]:
        pts = hb.copy()

        if sign_x > 0:
            # Mirror in x about x=anchor_distance/2... actually mirror about x=0
            # then shift to right side
            pts[:, 0] = -pts[:, 0] + anchor_distance

        # Shift in y
        pts[:, 1] += sign_y * half_sp

        polys.append(Polygon(pts))

    # Shuttle rectangle (solid, no holes)
    # x: from half_span to half_span + shuttle_length
    # y: centered at initial_offset, spanning both beams
    sx0 = half_span
    sx1 = half_span + shuttle_length
    sy_center = initial_offset
    sy_half = shuttle_height / 2.0
    shuttle_rect = Polygon([
        (sx0, sy_center - sy_half),
        (sx1, sy_center - sy_half),
        (sx1, sy_center + sy_half),
        (sx0, sy_center + sy_half),
    ])
    polys.append(shuttle_rect)

    # Merge all into single outline
    merged = unary_union(polys)

    # Extract exterior coordinates
    coords = np.array(merged.exterior.coords)
    return coords


# ---------------------------------------------------------------------------
# Boundary condition identification
# ---------------------------------------------------------------------------

def identify_bc_nodes_2d(nodes, anchor_distance=80.0, half_span=36.5,
                         shuttle_length=7.0, tol=0.05):
    """Identify boundary condition node sets for 2D full spring mesh.

    Args:
        nodes: Nx2 array of node coordinates.
        anchor_distance: Total span between anchors (um).
        half_span: Half-beam span (um).
        shuttle_length: Shuttle x-extent (um).
        tol: Position tolerance (um).

    Returns:
        Dict with keys:
          'left_anchor':  node indices at x < tol
          'right_anchor': node indices at x > anchor_distance - tol
          'shuttle':      node indices in shuttle region
    """
    x = nodes[:, 0] if nodes.ndim == 2 else nodes[0]

    left = np.where(x < tol)[0]
    right = np.where(x > anchor_distance - tol)[0]

    # Shuttle region: half_span < x < half_span + shuttle_length
    shuttle = np.where((x > half_span - tol) & (x < half_span + shuttle_length + tol))[0]

    return {
        'left_anchor': left,
        'right_anchor': right,
        'shuttle': shuttle,
    }


def identify_bc_nodes_3d(points, anchor_distance=80.0, half_span=36.5,
                         shuttle_length=7.0, tol=0.05):
    """Identify boundary condition node sets for 3D full spring mesh.

    Same as 2D but operates on Nx3 point array.

    Returns:
        Dict with keys: 'left_anchor', 'right_anchor', 'shuttle'
    """
    x = points[:, 0] if points.ndim == 2 else points[0]

    left = np.where(x < tol)[0]
    right = np.where(x > anchor_distance - tol)[0]
    shuttle = np.where((x > half_span - tol) & (x < half_span + shuttle_length + tol))[0]

    return {
        'left_anchor': left,
        'right_anchor': right,
        'shuttle': shuttle,
    }


# ---------------------------------------------------------------------------
# 3D mesh generation
# ---------------------------------------------------------------------------

def get_full_spring_3d_mesh(polygon=None, thickness=0.5,
                            lc_flex=0.3, lc_rigid=0.5,
                            n_layers_z=3,
                            anchor_distance=80.0,
                            half_span=None,
                            flex_ratio=0.3,
                            **spring_kwargs):
    """Extrude 2D polygon into 3D tetrahedral mesh via gmsh.

    Args:
        polygon:          Nx2 closed polygon (if None, generates from defaults).
        thickness:        Extrusion thickness in z (um).
        lc_flex:          Mesh characteristic length in flex regions.
        lc_rigid:         Mesh characteristic length in rigid regions.
        n_layers_z:       Number of element layers through thickness.
        anchor_distance:  Total span (um), for mesh size grading.
        half_span:        Half-beam span (um), for flex region identification.
        flex_ratio:       Flex ratio, for flex region identification.
        **spring_kwargs:  Passed to get_full_spring_polygon if polygon is None.

    Returns:
        (points, tets): points is Nx3, tets is Mx4 (or Mx10 for 2nd order).
    """
    import gmsh
    import meshio

    if polygon is None:
        polygon = get_full_spring_polygon(
            anchor_distance=anchor_distance,
            flex_ratio=flex_ratio,
            **spring_kwargs
        )

    # Remove closing point if present
    if np.allclose(polygon[0], polygon[-1]):
        polygon = polygon[:-1]

    # Derive half_span if not provided
    if half_span is None:
        shuttle_length = spring_kwargs.get('shuttle_length', 7.0)
        half_span = (anchor_distance - shuttle_length) / 2.0

    # Flex region x-extents (both left and right sides)
    L_flex_beam = flex_ratio * half_span
    shuttle_x0 = half_span
    shuttle_x1 = anchor_distance - half_span

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("full_spring_3d")

    point_tags = []
    for x, y in polygon:
        # Determine if point is in flex region
        in_flex = (x < L_flex_beam + 1) or \
                  (abs(x - shuttle_x0) < L_flex_beam + 1) or \
                  (abs(x - shuttle_x1) < L_flex_beam + 1) or \
                  (x > anchor_distance - L_flex_beam - 1)
        lc = lc_flex if in_flex else lc_rigid
        tag = gmsh.model.occ.addPoint(x, y, 0, lc)
        point_tags.append(tag)

    line_tags = []
    n_pts = len(point_tags)
    for i in range(n_pts):
        j = (i + 1) % n_pts
        tag = gmsh.model.occ.addLine(point_tags[i], point_tags[j])
        line_tags.append(tag)

    wire = gmsh.model.occ.addCurveLoop(line_tags)
    surf = gmsh.model.occ.addPlaneSurface([wire])

    gmsh.model.occ.extrude([(2, surf)], 0, 0, thickness,
                            numElements=[n_layers_z], recombine=False)

    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(3)

    tmp_msh = '/tmp/full_spring_3d.msh'
    gmsh.write(tmp_msh)
    gmsh.finalize()

    msh = meshio.read(tmp_msh)

    # Find tetrahedral cells
    tet_cells = None
    for cb in msh.cells:
        if cb.type == 'tetra':
            tet_cells = cb.data
            break

    if tet_cells is None:
        raise RuntimeError("No tetrahedral elements found in mesh")

    return msh.points, tet_cells


def get_full_spring_3d_mesh_order2(polygon=None, thickness=0.5,
                                   lc_flex=0.4, lc_rigid=0.7,
                                   n_layers_z=3,
                                   anchor_distance=80.0,
                                   half_span=None,
                                   flex_ratio=0.3,
                                   **spring_kwargs):
    """Extrude 2D polygon into 3D 2nd-order tetrahedral mesh via gmsh.

    Same as get_full_spring_3d_mesh but generates C3D10 (10-node tet) elements.

    Returns:
        (points, tets, elem_type): points Nx3, tets Mx10, elem_type str.
    """
    import gmsh
    import meshio

    if polygon is None:
        polygon = get_full_spring_polygon(
            anchor_distance=anchor_distance,
            flex_ratio=flex_ratio,
            **spring_kwargs
        )

    if np.allclose(polygon[0], polygon[-1]):
        polygon = polygon[:-1]

    # Derive half_span if not provided
    if half_span is None:
        shuttle_length = spring_kwargs.get('shuttle_length', 7.0)
        half_span = (anchor_distance - shuttle_length) / 2.0

    L_flex_beam = flex_ratio * half_span
    shuttle_x0 = half_span
    shuttle_x1 = anchor_distance - half_span

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("full_spring_3d_o2")

    point_tags = []
    for x, y in polygon:
        in_flex = (x < L_flex_beam + 1) or \
                  (abs(x - shuttle_x0) < L_flex_beam + 1) or \
                  (abs(x - shuttle_x1) < L_flex_beam + 1) or \
                  (x > anchor_distance - L_flex_beam - 1)
        lc = lc_flex if in_flex else lc_rigid
        tag = gmsh.model.occ.addPoint(x, y, 0, lc)
        point_tags.append(tag)

    line_tags = []
    n_pts = len(point_tags)
    for i in range(n_pts):
        j = (i + 1) % n_pts
        tag = gmsh.model.occ.addLine(point_tags[i], point_tags[j])
        line_tags.append(tag)

    wire = gmsh.model.occ.addCurveLoop(line_tags)
    surf = gmsh.model.occ.addPlaneSurface([wire])

    gmsh.model.occ.extrude([(2, surf)], 0, 0, thickness,
                            numElements=[n_layers_z], recombine=False)

    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)

    tmp_msh = '/tmp/full_spring_3d_o2.msh'
    gmsh.write(tmp_msh)
    gmsh.finalize()

    msh = meshio.read(tmp_msh)

    tet_cells = None
    elem_type = 'C3D4'
    for cb in msh.cells:
        if cb.type == 'tetra10':
            tet_cells = cb.data
            elem_type = 'C3D10'
            break
        elif cb.type == 'tetra':
            tet_cells = cb.data
            break

    if tet_cells is None:
        raise RuntimeError("No tetrahedral elements found in mesh")

    return msh.points, tet_cells, elem_type
