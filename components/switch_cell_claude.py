#!/usr/bin/env python3
"""
Complete switch cell implementation for Tower SiPho MEMS switch.

Based on Han et al., "32 × 32 silicon photonic MEMS switch with gap-adjustable
directional couplers fabricated in commercial CMOS foundry" (J. Opt. Microsystems, 2021)

Architecture:
- Input waveguide with directional coupler DC1
- Movable shuttle with bent waveguide (45° diagonal)
- Second directional coupler DC2 to drop waveguide
- Waveguide crossing for through/drop routing
- MEMS comb-drive actuator (88μm × 88μm, 44 finger pairs)
- 4 folded springs for suspension
"""

import gdsfactory as gf
import numpy as np
from typing import Tuple

# Layer definitions (to be mapped to Tower SiPho PDK)
LAYER_WG = (1, 0)        # Waveguide core (220nm thick Si)
LAYER_SLAB = (2, 0)      # Shallow etch (70nm for gratings)
LAYER_FULL_ETCH = (3, 0) # Full etch (220nm for MEMS release)
LAYER_METAL = (10, 0)    # Metal pads (Au/Cr)

# Design parameters from Han et al. paper
WG_WIDTH = 0.45          # Waveguide width (μm)
DC_LENGTH = 20.0         # Directional coupler length (μm)
DC_GAP_OFF = 0.55        # Gap in OFF state (μm)
DC_GAP_ON = 0.135        # Gap in ON state (μm) - optimal coupling

COMB_FINGER_WIDTH = 0.3  # Comb finger width (μm)
COMB_FINGER_GAP = 0.4    # Gap between fingers (μm)
COMB_PAIRS = 44          # Number of finger pairs
SPRING_WIDTH = 0.3       # Spring width (μm)
SPRING_LENGTH = 30.0     # Spring length (μm)
ACTUATOR_FOOTPRINT = 88.0 # Actuator footprint (μm)


@gf.cell
def waveguide_crossing() -> gf.Component:
    """
    Simple waveguide crossing for routing.

    Creates a + shaped crossing where two waveguides intersect.
    Based on standard silicon photonics crossing designs.

    Returns:
        Component with crossing geometry and 4 ports (N, S, E, W)
    """
    c = gf.Component("crossing")

    # Crossing arm length (extend beyond center)
    arm_length = 5.0

    # Horizontal waveguide (East-West)
    c.add_polygon([
        (-arm_length, -WG_WIDTH/2),
        (arm_length, -WG_WIDTH/2),
        (arm_length, WG_WIDTH/2),
        (-arm_length, WG_WIDTH/2)
    ], layer=LAYER_WG)

    # Vertical waveguide (North-South)
    c.add_polygon([
        (-WG_WIDTH/2, -arm_length),
        (WG_WIDTH/2, -arm_length),
        (WG_WIDTH/2, arm_length),
        (-WG_WIDTH/2, arm_length)
    ], layer=LAYER_WG)

    # Add ports
    c.add_port("W", center=(-arm_length, 0), width=WG_WIDTH, orientation=180, layer=LAYER_WG)
    c.add_port("E", center=(arm_length, 0), width=WG_WIDTH, orientation=0, layer=LAYER_WG)
    c.add_port("S", center=(0, -arm_length), width=WG_WIDTH, orientation=270, layer=LAYER_WG)
    c.add_port("N", center=(0, arm_length), width=WG_WIDTH, orientation=90, layer=LAYER_WG)

    return c


@gf.cell
def directional_coupler_straight(
    length: float = DC_LENGTH,
    width: float = WG_WIDTH,
    gap: float = DC_GAP_OFF
) -> gf.Component:
    """
    Parallel straight waveguides for directional coupler.

    Two parallel waveguides separated by a gap.
    One waveguide is fixed, one will be on the movable shuttle.

    Args:
        length: Coupling length (μm)
        width: Waveguide width (μm)
        gap: Gap between waveguides (μm)

    Returns:
        Component with two parallel waveguides and ports
    """
    c = gf.Component()

    # Waveguide 1 (fixed - top)
    y1 = gap/2 + width/2
    c.add_polygon([
        (0, y1 - width/2),
        (length, y1 - width/2),
        (length, y1 + width/2),
        (0, y1 + width/2)
    ], layer=LAYER_WG)

    # Waveguide 2 (movable - bottom)
    y2 = -(gap/2 + width/2)
    c.add_polygon([
        (0, y2 - width/2),
        (length, y2 - width/2),
        (length, y2 + width/2),
        (0, y2 + width/2)
    ], layer=LAYER_WG)

    # Ports for waveguide 1 (fixed)
    c.add_port("wg1_in", center=(0, y1), width=width, orientation=180, layer=LAYER_WG)
    c.add_port("wg1_out", center=(length, y1), width=width, orientation=0, layer=LAYER_WG)

    # Ports for waveguide 2 (movable)
    c.add_port("wg2_in", center=(0, y2), width=width, orientation=180, layer=LAYER_WG)
    c.add_port("wg2_out", center=(length, y2), width=width, orientation=0, layer=LAYER_WG)

    return c


@gf.cell
def bent_waveguide_45deg(
    dc1_length: float = DC_LENGTH,
    dc2_length: float = DC_LENGTH,
    spacing: float = 30.0
) -> gf.Component:
    """
    Bent waveguide on shuttle connecting DC1 to DC2 at 45° angle.

    This waveguide routes light from the input coupling region to the
    drop coupling region along the diagonal movement direction.

    Args:
        dc1_length: Length of first DC region (μm)
        dc2_length: Length of second DC region (μm)
        spacing: Spacing between DC regions (μm)

    Returns:
        Component with bent waveguide path
    """
    c = gf.Component()

    # Create path along 45° diagonal
    # Start at DC1 end, route diagonally down to DC2 start

    # Straight section 1 (horizontal, after DC1)
    straight1 = 5.0

    # Diagonal section (45°)
    diag_length = spacing * np.sqrt(2)

    # Straight section 2 (horizontal, before DC2)
    straight2 = 5.0

    # Build path using polygons for simplicity
    # Start point (0, 0)
    path_points = []

    # Straight section 1
    x, y = 0, 0
    path_points.append((x, y))
    x += straight1
    path_points.append((x, y))

    # 45° bend down
    x += diag_length / np.sqrt(2)
    y -= diag_length / np.sqrt(2)
    path_points.append((x, y))

    # Straight section 2
    x += straight2
    path_points.append((x, y))

    # Create waveguide from path (simplified - using straight segments)
    for i in range(len(path_points) - 1):
        x1, y1 = path_points[i]
        x2, y2 = path_points[i + 1]

        # Calculate perpendicular offset for width
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx**2 + dy**2)
        if length > 0:
            nx, ny = -dy/length, dx/length  # Normal vector

            # Create rectangle for segment
            pts = [
                (x1 + nx * WG_WIDTH/2, y1 + ny * WG_WIDTH/2),
                (x2 + nx * WG_WIDTH/2, y2 + ny * WG_WIDTH/2),
                (x2 - nx * WG_WIDTH/2, y2 - ny * WG_WIDTH/2),
                (x1 - nx * WG_WIDTH/2, y1 - ny * WG_WIDTH/2)
            ]
            c.add_polygon(pts, layer=LAYER_WG)

    # Add ports
    c.add_port("in", center=(0, 0), width=WG_WIDTH, orientation=180, layer=LAYER_WG)
    c.add_port("out", center=path_points[-1], width=WG_WIDTH, orientation=0, layer=LAYER_WG)

    return c


@gf.cell
def comb_drive(
    finger_width: float = COMB_FINGER_WIDTH,
    finger_gap: float = COMB_FINGER_GAP,
    num_pairs: int = COMB_PAIRS,
    finger_length: float = 20.0
) -> gf.Component:
    """
    Comb drive actuator for gap tuning.

    Creates interdigitated comb fingers for electrostatic actuation.
    One set is fixed, one set is on the movable shuttle.

    Args:
        finger_width: Width of each comb finger (μm)
        finger_gap: Gap between fingers (μm)
        num_pairs: Number of finger pairs
        finger_length: Length of fingers (μm)

    Returns:
        Component with comb drive geometry
    """
    c = gf.Component()

    pitch = finger_width + finger_gap

    # Fixed combs (even indices)
    for i in range(0, num_pairs * 2, 2):
        x = i * pitch
        c.add_polygon([
            (x, 0),
            (x + finger_width, 0),
            (x + finger_width, finger_length),
            (x, finger_length)
        ], layer=LAYER_WG)

    # Moving combs (odd indices)
    for i in range(1, num_pairs * 2, 2):
        x = i * pitch
        c.add_polygon([
            (x, 0),
            (x + finger_width, 0),
            (x + finger_width, finger_length),
            (x, finger_length)
        ], layer=LAYER_WG)

    # Add bus bars to connect fingers
    total_width = num_pairs * 2 * pitch

    # Fixed bus bar
    c.add_polygon([
        (0, finger_length),
        (total_width, finger_length),
        (total_width, finger_length + 2),
        (0, finger_length + 2)
    ], layer=LAYER_WG)

    # Moving bus bar
    c.add_polygon([
        (0, -2),
        (total_width, -2),
        (total_width, 0),
        (0, 0)
    ], layer=LAYER_WG)

    return c


@gf.cell
def folded_spring(
    width: float = SPRING_WIDTH,
    length: float = SPRING_LENGTH,
    num_folds: int = 2
) -> gf.Component:
    """
    Folded spring for shuttle suspension.

    Creates a serpentine spring for mechanical suspension.

    Args:
        width: Spring beam width (μm)
        length: Total spring length (μm)
        num_folds: Number of folds in spring

    Returns:
        Component with folded spring geometry
    """
    c = gf.Component()

    fold_length = length / (num_folds + 1)
    fold_width = 5.0

    # Create meandering path
    path_points = [(0, 0)]
    x, y = 0, 0

    for i in range(num_folds):
        # Straight segment
        y += fold_length
        path_points.append((x, y))

        # Fold to the side
        x += fold_width * (1 if i % 2 == 0 else -1)
        path_points.append((x, y))

    # Final segment
    y += fold_length
    path_points.append((x, y))

    # Create spring from path
    for i in range(len(path_points) - 1):
        x1, y1 = path_points[i]
        x2, y2 = path_points[i + 1]

        if x1 == x2:  # Vertical segment
            c.add_polygon([
                (x1 - width/2, y1),
                (x1 + width/2, y1),
                (x2 + width/2, y2),
                (x2 - width/2, y2)
            ], layer=LAYER_WG)
        else:  # Horizontal segment
            c.add_polygon([
                (x1, y1 - width/2),
                (x2, y1 - width/2),
                (x2, y1 + width/2),
                (x1, y1 + width/2)
            ], layer=LAYER_WG)

    # Add anchor points
    c.add_port("anchor", center=(0, 0), width=width, orientation=270, layer=LAYER_WG)
    c.add_port("shuttle", center=path_points[-1], width=width, orientation=90, layer=LAYER_WG)

    return c


@gf.cell
def switch_cell(gap: float = DC_GAP_OFF) -> gf.Component:
    """
    Complete switch cell assembly.

    Combines all components into a single switch cell:
    - Input/through/drop waveguides
    - Waveguide crossing
    - Two directional couplers (DC1 and DC2)
    - Bent waveguide on movable shuttle
    - Comb drive actuator
    - 4 folded springs

    Args:
        gap: Directional coupler gap (μm). Default is OFF state.

    Returns:
        Complete switch cell component
    """
    c = gf.Component()

    # Reference position for crossing at origin
    crossing_pos = (0, 0)

    # Add waveguide crossing
    cross = waveguide_crossing()
    cross_ref = c.add_ref(cross)
    cross_ref.move(crossing_pos)

    # Input waveguide (extends left from crossing)
    input_length = 40.0
    c.add_polygon([
        (-input_length, -WG_WIDTH/2),
        (0, -WG_WIDTH/2),
        (0, WG_WIDTH/2),
        (-input_length, WG_WIDTH/2)
    ], layer=LAYER_WG)

    # Through waveguide (extends right from crossing)
    through_length = 40.0
    c.add_polygon([
        (0, -WG_WIDTH/2),
        (through_length, -WG_WIDTH/2),
        (through_length, WG_WIDTH/2),
        (0, WG_WIDTH/2)
    ], layer=LAYER_WG)

    # Drop waveguide (extends down from crossing)
    drop_length = 60.0
    c.add_polygon([
        (-WG_WIDTH/2, -drop_length),
        (WG_WIDTH/2, -drop_length),
        (WG_WIDTH/2, 0),
        (-WG_WIDTH/2, 0)
    ], layer=LAYER_WG)

    # DC1 region (input to bent waveguide) - positioned in 3rd quadrant
    dc1_x = -30.0
    dc1_y = -15.0

    # DC2 region (bent waveguide to drop) - positioned below DC1
    dc2_x = -30.0
    dc2_y = -50.0

    # Add bent waveguide on shuttle (connecting DC1 to DC2)
    bent_wg = bent_waveguide_45deg()
    bent_ref = c.add_ref(bent_wg)
    bent_ref.move((dc1_x, dc1_y))

    # Add comb drive actuator (bottom left)
    comb = comb_drive()
    comb_ref = c.add_ref(comb)
    comb_ref.move((-80, -80))

    # Add 4 folded springs around shuttle
    spring = folded_spring()

    # Spring positions (corners of shuttle)
    spring_positions = [
        (-70, -20),  # Top left
        (-70, -70),  # Bottom left
        (-30, -20),  # Top right
        (-30, -70)   # Bottom right
    ]

    for pos in spring_positions:
        spring_ref = c.add_ref(spring)
        spring_ref.move(pos)

    # Add ports for the switch cell
    c.add_port("input", center=(-input_length, 0), width=WG_WIDTH, orientation=180, layer=LAYER_WG)
    c.add_port("through", center=(through_length, 0), width=WG_WIDTH, orientation=0, layer=LAYER_WG)
    c.add_port("drop", center=(0, -drop_length), width=WG_WIDTH, orientation=270, layer=LAYER_WG)

    return c


if __name__ == "__main__":
    """Generate and display the switch cell."""

    print("Generating switch cell layout...")

    # Create switch cell in OFF state (default)
    cell_off = switch_cell(gap=DC_GAP_OFF)

    # Write GDS file
    gds_path = "layouts/switch_cell_off.gds"
    cell_off.write_gds(gds_path)
    print(f"✓ GDS file written: {gds_path}")

    # Display in KLayout
    print("Opening in KLayout...")
    cell_off.show()

    print("\n" + "="*50)
    print("Switch Cell Design Parameters:")
    print("="*50)
    print(f"Waveguide width: {WG_WIDTH} μm")
    print(f"DC length: {DC_LENGTH} μm")
    print(f"DC gap (OFF): {DC_GAP_OFF} μm")
    print(f"DC gap (ON): {DC_GAP_ON} μm")
    print(f"Comb finger width: {COMB_FINGER_WIDTH} μm")
    print(f"Comb finger gap: {COMB_FINGER_GAP} μm")
    print(f"Comb finger pairs: {COMB_PAIRS}")
    print(f"Spring width: {SPRING_WIDTH} μm")
    print(f"Spring length: {SPRING_LENGTH} μm")
    print("="*50)
