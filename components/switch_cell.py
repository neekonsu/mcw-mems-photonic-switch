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

    # TODO Is there meaning tied to the layer numbers; should I look these up in some table to read more or are they arbitrary

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
    # WAVEGUIDE AND BEND parameters
    wg_width = 0.45          # 450 nm TODO optimize in lumerical
    wg_bend_radius = 5.0     # Typical for silicon photonics TODO optimize in lumerical

    # DIRECTIONAL COUPLER parameters
    coupler_length = 20.0    # μm TODO optimize in lumerical
    initial_gap = 0.55       # 550 nm (OFF state) TODO optimize in lumerical

    # COMB DRIVE parameters TODO use an optimal comb drive based on literature, forward design only
    comb_footprint = 88.0    # μm square TODO claude translated this from textual description, may not be a real design parameter; this is likely the footprint/realestate of the comb drive
    comb_finger_width = 0.3  # 300 nm TODO optimize in lumerical
    comb_finger_gap = 0.4    # 400 nm TODO optimize in lumerical
    comb_finger_pitch = comb_finger_width + comb_finger_gap  # 700 nm TODO optimize in lumerical
    num_finger_pairs = 44 # TODO optimize in lumerical
    comb_finger_length = 20.0  # Estimated from footprint TODO optimize in lumerical

    # SPRING parameters
    spring_width = 0.3       # 300 nm
    spring_length = 30.0     # μm per segment
    spring_turns = 4         # Number of turns in folded spring

    # GRATING COUPLER parameters
    # TODO use an optimal comb drive based on literature, forward design only

    # =========================================================================
    # GEOMETRY DEFINITION
    # =========================================================================

    # NOTE the center/origin is defined as the center of the 180um x 180um cell, so (90um,90um) is the top right and -(90um,90um) is the bottom left 

    # Waveguide crossing point: 50μm left and down from top-right corner
    # Cell centered at origin, so top-right is at (cell_size/2, cell_size/2) TODO remove old relative coordinate code
    # cross_x = cell_size/2 - 50.0  # 40 μm from center
    # cross_y = cell_size/2 - 50.0  # 40 μm from center
    cross_x, cross_y = (40.0, 40.0) # um <- tuple format more readable, hardcoding coordinates for robustness

    # Vertical waveguide from cross to top edge (drop1 output)
    # NOTE replaced relative coordinate for cell edge, reordered to match personal waveguide definition convention (short edge - short edge)
    # TODO make sure this is accessed, currently not
    drop1_wg = c.add_polygon([
        (cross_x - wg_width/2, cross_y),
        (cross_x + wg_width/2, cross_y),
        (cross_x - wg_width/2, 90.0),
        (cross_x + wg_width/2, 90.0)
    ], layer=LAYER_SI)

    # Horizontal waveguide from cross to right edge (through1 output)
    # NOTE replaced relative coordinate for cell edge, reordered to match personal waveguide definition convention (short edge - short edge)
    # TODO make sure this is accessed, currently not
    through1_wg = c.add_polygon([
        (cross_x, cross_y - wg_width/2),
        (cross_x, cross_y + wg_width/2),
        (90.0, cross_y - wg_width/2),
        (90.0, cross_y + wg_width/2)
    ], layer=LAYER_SI)

    # Vertical waveguide from cross extending down 50μm
    # NOTE replaced relative coordinate for cell edge, reordered to match personal waveguide definition convention (short edge - short edge)
    # TODO make sure this is accessed, currently not
    down_wg = c.add_polygon([
        (cross_x - wg_width/2, cross_y),
        (cross_x + wg_width/2, cross_y),
        (cross_x - wg_width/2, -10.0),
        (cross_x + wg_width/2, -10.0)
    ], layer=LAYER_SI)

    # Horizontal waveguide from cross extending left 50μm
    left_wg = c.add_polygon([
        (cross_x - 50.0, cross_y - wg_width/2),
        (cross_x, cross_y - wg_width/2),
        (cross_x, cross_y + wg_width/2),
        (cross_x - 50.0, cross_y + wg_width/2)
    ], layer=LAYER_SI)

    # Define diamond vertex points
    # TODO Don't prioritize until the first version of the complete cell is finished, but compare the Han 2021 paper to a few others and make this support structure accordingly
    diamond_top = (cross_x, 90.0)           # (40, 90)
    diamond_right = (90.0, cross_y)         # (90, 40)
    diamond_bottom = (cross_x, -10.0)     # (40, -10)
    diamond_left = (-10.0, cross_y)       # (-10, 40)

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
    # NOTE Renamed straight waveguide from crossing to s-bend for direction and unique number
    straight_left_1_start_x = -10.0            # diamond_left x-coordinate
    straight_left_1_start_y = cross_y          # diamond_left y-coordinate

    straight_left_1_end_x = straight_left_1_start_x - 10.0  # end of left straight wg, start of s-bend, x-coordinate
    straight_left_1_end_y = cross_y                         # end of left straight wg, start of s-bend, y-coordinate

    # TODO make sure this is accessed, currently not
    straight_wg_left = c.add_polygon([
        (straight_left_1_start_x, straight_left_1_start_y - wg_width/2),
        (straight_left_1_start_x, straight_left_1_start_y + wg_width/2),
        (straight_left_1_end_x, straight_left_1_end_y - wg_width/2),
        (straight_left_1_end_x, straight_left_1_end_y + wg_width/2)
    ], layer=LAYER_SI)

    # S-bend waveguide (10μm left + 10μm down)
    # Start: (-20, 40), End: (-30, 30)
    # Using curved S-bend with two opposing curves

    s_start_x = straight_end_x
    s_start_y = straight_end_y
    s_end_x = s_start_x - 10.0  # Total 10μm left
    s_end_y = s_start_y - 10.0  # Total 10μm down

    # Use GDSFactory's built-in S-bend component TODO determine if we can build our own or construct with multiple semi-circles or bézier curves; what is optimal bend shape?
    # TODO will optimize bend in Lumerical
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
        size=(10.0, -10.0),  # (horizontal offset, vertical offset) TODO this attribute should have signs flipped to match desired directionality of s-bends
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
    # ========================================================================= TODO apply above todos relevant to s-bends below
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

    # S-bend connecting from (30, -55) to (40, -65) - same type as left waveguide
    # 10μm right, 10μm down
    bottom_final_s_start_x = bottom_continue_end_x  # (30, -55)
    bottom_final_s_start_y = bottom_continue_end_y
    bottom_final_s_end_x = bottom_final_s_start_x + 10.0  # 10μm right
    bottom_final_s_end_y = bottom_final_s_start_y - 10.0  # 10μm down

    # Use same S-bend component as left waveguide
    bottom_final_s_component = gf.components.bend_s(
        size=(10.0, -10.0),  # 10μm right, 10μm down
        cross_section=gf.cross_section.cross_section(
            width=wg_width,
            layer=LAYER_SI,
            radius_min=3.0  # Same radius as left waveguide S-bends
        )
    )

    # Add to cell and position
    # First move to position, then rotate around that point
    bottom_final_s_ref = c << bottom_final_s_component
    bottom_final_s_ref.move((bottom_final_s_start_x, bottom_final_s_start_y))
    bottom_final_s_ref.rotate(180, center=(bottom_final_s_start_x, bottom_final_s_start_y))
    bottom_final_s_ref.rotate(-90, center=(bottom_final_s_start_x, bottom_final_s_start_y))

    # Flatten to avoid off-grid issues
    c.flatten()

    # Define final endpoint after S-bend
    s_bend_bottom_final = (bottom_final_s_end_x, bottom_final_s_end_y)  # (40, -65)

    # =========================================================================
    # FINAL EXTENSIONS AND PORT LABELS
    # =========================================================================

    # Extend left waveguide by 10μm and label as "in1" (input port)
    in1_start_x = s_bend_left_final[0]
    in1_start_y = s_bend_left_final[1]
    in1_end_x = in1_start_x - 10.0
    in1_end_y = in1_start_y

    final_wg_left = c.add_polygon([
        (in1_start_x - wg_width/2, in1_start_y - wg_width/2),
        (in1_end_x, in1_start_y - wg_width/2),
        (in1_end_x, in1_start_y + wg_width/2),
        (in1_start_x + wg_width/2, in1_start_y + wg_width/2)
    ], layer=LAYER_SI)

    # Add "in1" label at the end of left waveguide
    c.add_label(
        text="in1",
        position=(in1_end_x, in1_end_y),
        layer=LAYER_SI
    )

    # Extend bottom waveguide by 10μm and label as "drop2" (output port)
    drop2_start_x = s_bend_bottom_final[0]
    drop2_start_y = s_bend_bottom_final[1]
    drop2_end_x = drop2_start_x
    drop2_end_y = drop2_start_y - 10.0

    final_wg_bottom = c.add_polygon([
        (drop2_start_x - wg_width/2, drop2_start_y + wg_width/2),
        (drop2_end_x - wg_width/2, drop2_end_y),
        (drop2_end_x + wg_width/2, drop2_end_y),
        (drop2_start_x + wg_width/2, drop2_start_y - wg_width/2)
    ], layer=LAYER_SI)

    # Add "drop2" label at the end of bottom waveguide TODO determine how labelling ports of a cell works with gdsfactory
    c.add_label(
        text="drop2",
        position=(drop2_end_x, drop2_end_y),
        layer=LAYER_SI
    )


    return c


# Main execution block
if __name__ == "__main__":
    # Create single unit cell
    switch_unit = create_mems_switch_unit()

    # Save to GDS
    switch_unit.write_gds("mems_switch_unit.gds")

    # Show in viewer
    switch_unit.show()