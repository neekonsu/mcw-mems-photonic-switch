import gdsfactory as gf
from gdsfactory import Component

@gf.cell
def create_mems_switch_unit():
    """
    Creates a complete unit cell of the 32x32 silicon photonic MEMS switch
    with gap-adjustable directional couplers.

    Reference dimensions (from paper):
    - Unit cell: 166 μm pitch
    - Directional coupler: 20 μm length, 450 nm width, 220 nm thick
    - Initial gap: 550 nm (OFF state), can close to 135 nm (ON state)
    - Comb drive: 88 μm × 88 μm footprint
    - Comb fingers: 300 nm width, 400 nm spacing, 44 pairs
    - Springs: 300 nm width, 30 μm length (4 folded springs)
    - Switching voltage: 9.45V
    """

    c = Component()

    # =========================================================================
    # LAYER DEFINITIONS
    # =========================================================================
    LAYER_SI = (1, 0)           # Silicon device layer (220nm thick) - full etch
    LAYER_SI_PARTIAL = (2, 0)   # Shallow etch (70nm for gratings)
    LAYER_BOX = (10, 0)         # BOX layer (buried oxide / release etch)
    LAYER_METAL = (41, 0)       # Metal pads (Au/Cr)

    # =========================================================================
    # CELL PARAMETERS (measured design)
    # =========================================================================
    cell_size = 180.0  # μm × 180 μm unit cell (repeatable in matrix)

    # Port structure (2×2 switch cell):
    # Inputs:  in1, drop1
    # Outputs: through1, drop2

    # =========================================================================
    # REFERENCE PARAMETERS (from paper - for reference only)
    # =========================================================================
    # Waveguide parameters
    wg_width = 0.45          # 450 nm
    wg_bend_radius = 5.0     # Typical for silicon photonics

    # Directional coupler parameters
    coupler_length = 20.0    # μm
    initial_gap = 0.55       # 550 nm (OFF state)

    # Comb drive parameters
    comb_footprint = 88.0    # μm square
    comb_finger_width = 0.3  # 300 nm
    comb_finger_gap = 0.4    # 400 nm
    comb_finger_pitch = comb_finger_width + comb_finger_gap  # 700 nm
    num_finger_pairs = 44
    comb_finger_length = 20.0  # Estimated from footprint

    # Spring parameters
    spring_width = 0.3       # 300 nm
    spring_length = 30.0     # μm per segment
    spring_turns = 4         # Number of turns in folded spring

    # =========================================================================
    # GEOMETRY DEFINITION
    # =========================================================================

    # Waveguide crossing point: 50μm left and down from top-right corner
    # Cell centered at origin, so top-right is at (cell_size/2, cell_size/2)
    cross_x = cell_size/2 - 50.0  # 40 μm from center
    cross_y = cell_size/2 - 50.0  # 40 μm from center

    # Vertical waveguide from cross to top edge (drop1 output)
    drop1_wg = c.add_polygon([
        (cross_x - wg_width/2, cross_y),
        (cross_x + wg_width/2, cross_y),
        (cross_x + wg_width/2, cell_size/2),
        (cross_x - wg_width/2, cell_size/2)
    ], layer=LAYER_SI)

    # Horizontal waveguide from cross to right edge (through1 output)
    through1_wg = c.add_polygon([
        (cross_x, cross_y - wg_width/2),
        (cell_size/2, cross_y - wg_width/2),
        (cell_size/2, cross_y + wg_width/2),
        (cross_x, cross_y + wg_width/2)
    ], layer=LAYER_SI)

    # Vertical waveguide from cross extending down 50μm
    down_wg = c.add_polygon([
        (cross_x - wg_width/2, cross_y - 50.0),
        (cross_x + wg_width/2, cross_y - 50.0),
        (cross_x + wg_width/2, cross_y),
        (cross_x - wg_width/2, cross_y)
    ], layer=LAYER_SI)

    # Horizontal waveguide from cross extending left 50μm
    left_wg = c.add_polygon([
        (cross_x - 50.0, cross_y - wg_width/2),
        (cross_x, cross_y - wg_width/2),
        (cross_x, cross_y + wg_width/2),
        (cross_x - 50.0, cross_y + wg_width/2)
    ], layer=LAYER_SI)

    # Define diamond vertex points
    diamond_top = (cross_x, cell_size/2)           # (40, 90)
    diamond_right = (cell_size/2, cross_y)         # (90, 40)
    diamond_bottom = (cross_x, cross_y - 50.0)     # (40, -10)
    diamond_left = (cross_x - 50.0, cross_y)       # (-10, 40)

    # Diamond (rotated square) with side length 50√2 μm
    diamond = c.add_polygon([
        diamond_top,      # Top vertex (at drop1 wg end)
        diamond_right,    # Right vertex (at through1 wg end)
        diamond_bottom,   # Bottom vertex (at down wg end)
        diamond_left      # Left vertex (at left wg end)
    ], layer=LAYER_BOX)

    # =========================================================================
    # WAVEGUIDE EXTENSION FROM DIAMOND_LEFT WITH S-BEND
    # =========================================================================
    # Starting point: diamond_left = (cross_x - 50.0, cross_y) = (-10, 40)
    # Straight section: 10μm left
    # S-bend: 10μm left + 10μm down
    # Final position: 20μm left of diamond_left, 10μm down = (-30, 30)

    # Straight waveguide extension (10μm left from diamond_left)
    straight_start_x = cross_x - 50.0  # diamond_left x-coordinate
    straight_start_y = cross_y         # diamond_left y-coordinate
    straight_end_x = straight_start_x - 10.0
    straight_end_y = straight_start_y

    straight_wg_left = c.add_polygon([
        (straight_start_x - wg_width/2, straight_start_y - wg_width/2),
        (straight_end_x, straight_start_y - wg_width/2),
        (straight_end_x, straight_start_y + wg_width/2),
        (straight_start_x + wg_width/2, straight_start_y + wg_width/2)
    ], layer=LAYER_SI)

    # S-bend waveguide (10μm left + 10μm down)
    # Start: (-20, 40), End: (-30, 30)
    # Using curved S-bend with two opposing curves

    s_start_x = straight_end_x
    s_start_y = straight_end_y
    s_end_x = s_start_x - 10.0  # Total 10μm left
    s_end_y = s_start_y - 10.0  # Total 10μm down

    # Use GDSFactory's built-in S-bend component
    # S-bend with horizontal and vertical offsets
    # Set radius_min to 3.0μm for tight bends (typical for Si photonics)
    s_bend_component = gf.components.bend_s(
        size=(10.0, -10.0),  # (horizontal offset, vertical offset)
        cross_section=gf.cross_section.cross_section(
            width=wg_width,
            layer=LAYER_SI,
            radius_min=3.0  # Allow tighter bends for compact S-bend
        )
    )

    # Add the S-bend to the cell and position it
    s_bend_ref = c << s_bend_component
    s_bend_ref.mirror((0, 1))  # Mirror horizontally to flip the S-bend
    s_bend_ref.move((s_start_x, s_start_y))

    # Flatten the component to avoid off-grid issues
    c.flatten()

    # Define s_bend_left endpoint for reference
    s_bend_left = (s_end_x, s_end_y)  # (-30, 30)

    # =========================================================================
    # WAVEGUIDE EXTENSION FROM DIAMOND_BOTTOM WITH S-BEND
    # =========================================================================
    # Starting point: diamond_bottom = (cross_x, cross_y - 50.0) = (40, -10)
    # Straight section: 10μm down
    # S-bend: 10μm down + 10μm left
    # Final position: 20μm down and 10μm left = (30, -30)

    # Straight waveguide extension (10μm down from diamond_bottom)
    bottom_straight_start_x = cross_x
    bottom_straight_start_y = cross_y - 50.0  # diamond_bottom y-coordinate
    bottom_straight_end_x = bottom_straight_start_x
    bottom_straight_end_y = bottom_straight_start_y - 10.0

    straight_wg_bottom = c.add_polygon([
        (bottom_straight_start_x - wg_width/2, bottom_straight_start_y + wg_width/2),
        (bottom_straight_end_x - wg_width/2, bottom_straight_end_y),
        (bottom_straight_end_x + wg_width/2, bottom_straight_end_y),
        (bottom_straight_start_x + wg_width/2, bottom_straight_start_y - wg_width/2)
    ], layer=LAYER_SI)

    # S-bend waveguide (10μm down + 10μm left)
    # Start: (40, -20), End: (30, -30)
    bottom_s_start_x = bottom_straight_end_x
    bottom_s_start_y = bottom_straight_end_y
    bottom_s_end_x = bottom_s_start_x - 10.0  # Total 10μm left
    bottom_s_end_y = bottom_s_start_y - 10.0  # Total 10μm down

    # Use GDSFactory's built-in S-bend component
    bottom_s_bend_component = gf.components.bend_s(
        size=(10.0, -10.0),  # (horizontal offset, vertical offset)
        cross_section=gf.cross_section.cross_section(
            width=wg_width,
            layer=LAYER_SI,
            radius_min=3.0  # Allow tighter bends for compact S-bend
        )
    )

    # Add the S-bend to the cell and position it
    # Rotate 90 degrees clockwise to orient it downward-left
    bottom_s_bend_ref = c << bottom_s_bend_component
    bottom_s_bend_ref.rotate(-90, center=(0, 0))  # Rotate to go down
    bottom_s_bend_ref.move((bottom_s_start_x, bottom_s_start_y))

    # Flatten the component to avoid off-grid issues
    c.flatten()

    # Define s_bend_bottom endpoint for reference
    s_bend_bottom = (bottom_s_end_x, bottom_s_end_y)  # (30, -30)

    # =========================================================================
    # CONTINUE FROM S_BEND_LEFT: 25μm STRAIGHT + REVERSE S-BEND (LEFT & UP)
    # =========================================================================
    # Current position: s_bend_left = (-30, 30)
    # Extend left 25μm to (-55, 30)
    # Then S-bend left 10μm and up 10μm to (-65, 40) - cancels original down shift

    # Straight section (25μm left from s_bend_left)
    left_continue_start_x = s_bend_left[0]
    left_continue_start_y = s_bend_left[1]
    left_continue_end_x = left_continue_start_x - 25.0
    left_continue_end_y = left_continue_start_y

    straight_wg_left_continue = c.add_polygon([
        (left_continue_start_x - wg_width/2, left_continue_start_y - wg_width/2),
        (left_continue_end_x, left_continue_start_y - wg_width/2),
        (left_continue_end_x, left_continue_start_y + wg_width/2),
        (left_continue_start_x + wg_width/2, left_continue_start_y + wg_width/2)
    ], layer=LAYER_SI)

    # Reverse S-bend (10μm left + 10μm up)
    left_reverse_s_start_x = left_continue_end_x
    left_reverse_s_start_y = left_continue_end_y
    left_reverse_s_end_x = left_reverse_s_start_x - 10.0
    left_reverse_s_end_y = left_reverse_s_start_y + 10.0

    # Use S-bend component going left and up (opposite of original)
    left_reverse_s_component = gf.components.bend_s(
        size=(10.0, 10.0),  # (horizontal offset, vertical offset) - positive to go up
        cross_section=gf.cross_section.cross_section(
            width=wg_width,
            layer=LAYER_SI,
            radius_min=3.0
        )
    )

    left_reverse_s_ref = c << left_reverse_s_component
    left_reverse_s_ref.mirror((0, 1))  # Mirror horizontally to go left instead of right
    left_reverse_s_ref.move((left_reverse_s_start_x, left_reverse_s_start_y))

    # Flatten to avoid off-grid issues
    c.flatten()

    # Define final endpoint
    s_bend_left_final = (left_reverse_s_end_x, left_reverse_s_end_y)  # (-65, 40)

    # =========================================================================
    # CONTINUE FROM S_BEND_BOTTOM: 25μm STRAIGHT + REVERSE S-BEND (RIGHT & DOWN)
    # =========================================================================
    # Current position: s_bend_bottom = (30, -30)
    # Extend down 25μm to (30, -55)
    # Then S-bend right 10μm and down 10μm to (40, -65) - cancels original left shift

    # Straight section (25μm down from s_bend_bottom)
    bottom_continue_start_x = s_bend_bottom[0]
    bottom_continue_start_y = s_bend_bottom[1]
    bottom_continue_end_x = bottom_continue_start_x
    bottom_continue_end_y = bottom_continue_start_y - 25.0

    straight_wg_bottom_continue = c.add_polygon([
        (bottom_continue_start_x - wg_width/2, bottom_continue_start_y + wg_width/2),
        (bottom_continue_end_x - wg_width/2, bottom_continue_end_y),
        (bottom_continue_end_x + wg_width/2, bottom_continue_end_y),
        (bottom_continue_start_x + wg_width/2, bottom_continue_start_y - wg_width/2)
    ], layer=LAYER_SI)

    # Reverse S-bend (10μm right + 10μm down)
    bottom_reverse_s_start_x = bottom_continue_end_x
    bottom_reverse_s_start_y = bottom_continue_end_y
    bottom_reverse_s_end_x = bottom_reverse_s_start_x + 10.0
    bottom_reverse_s_end_y = bottom_reverse_s_start_y - 10.0

    # Use S-bend component going right and down (opposite of original left shift)
    bottom_reverse_s_component = gf.components.bend_s(
        size=(10.0, -10.0),  # (horizontal offset positive = right, vertical offset negative = down)
        cross_section=gf.cross_section.cross_section(
            width=wg_width,
            layer=LAYER_SI,
            radius_min=3.0
        )
    )

    bottom_reverse_s_ref = c << bottom_reverse_s_component
    bottom_reverse_s_ref.rotate(-90, center=(0, 0))  # Rotate 90° CW to go down and right
    bottom_reverse_s_ref.move((bottom_reverse_s_start_x, bottom_reverse_s_start_y))

    # Flatten to avoid off-grid issues
    c.flatten()

    # Define final endpoint
    s_bend_bottom_final = (bottom_reverse_s_end_x, bottom_reverse_s_end_y)  # (40, -65)


    return c


# Main execution block
if __name__ == "__main__":
    # Create single unit cell
    switch_unit = create_mems_switch_unit()

    # Save to GDS
    switch_unit.write_gds("mems_switch_unit.gds")

    # Show in viewer
    switch_unit.show()