import gdsfactory as gf
import numpy as np
from gdsfactory import Component

@gf.cell
def create_mems_switch_unit():
    """
    Creates a complete unit cell of the 32x32 silicon photonic MEMS switch
    with gap-adjustable directional couplers based on the paper specifications.
    
    Key dimensions from the paper:
    - Unit cell: 166 μm pitch
    - Directional coupler: 20 μm length, 450 nm width, 220 nm thick
    - Initial gap: 550 nm (OFF state), can close to 135 nm (ON state)
    - Comb drive: 88 μm × 88 μm footprint
    - Comb fingers: 300 nm width, 400 nm spacing, 44 pairs
    - Springs: 300 nm width, 30 μm length (4 folded springs)
    - Switching voltage: 9.45V
    """
    
    c = Component()
    
    # Layer definitions
    LAYER_SI = (1, 0)  # Silicon device layer (220nm thick) - full etch
    LAYER_SI_PARTIAL = (2, 0)  # Shallow etch (70nm for gratings)
    LAYER_METAL = (41, 0)  # Metal pads (Au/Cr)
    
    # Critical dimensions from paper
    unit_cell_pitch = 166.0  # μm
    
    # Waveguide parameters
    wg_width = 0.45  # 450 nm
    wg_bend_radius = 5.0  # Typical for silicon photonics
    
    # Directional coupler parameters
    coupler_length = 20.0  # μm
    initial_gap = 0.55  # 550 nm (OFF state)
    
    # Comb drive parameters
    comb_footprint = 88.0  # μm square
    comb_finger_width = 0.3  # 300 nm
    comb_finger_gap = 0.4  # 400 nm
    comb_finger_pitch = comb_finger_width + comb_finger_gap  # 700 nm
    num_finger_pairs = 44
    comb_finger_length = 20.0  # Estimated from footprint
    
    # Spring parameters
    spring_width = 0.3  # 300 nm
    spring_length = 30.0  # μm per segment
    spring_turns = 4  # Number of turns in folded spring
    
    # Center of the unit cell
    center_x, center_y = 0, 0
    
    # =========================================================================
    # FIXED WAVEGUIDES (Non-moving input/output structures)
    # =========================================================================
    
    # Calculate positions for two parallel waveguides
    wg_separation = 80.0  # Separation between upper and lower paths
    upper_wg_y = wg_separation / 2
    lower_wg_y = -wg_separation / 2
    
    # Upper fixed waveguide sections
    # Input section (left)
    upper_input = c.add_polygon([
        (-unit_cell_pitch/2, upper_wg_y - wg_width/2),
        (-coupler_length/2 - 2, upper_wg_y - wg_width/2),
        (-coupler_length/2 - 2, upper_wg_y + wg_width/2),
        (-unit_cell_pitch/2, upper_wg_y + wg_width/2)
    ], layer=LAYER_SI)
    
    # Output section (right)
    upper_output = c.add_polygon([
        (coupler_length/2 + 2, upper_wg_y - wg_width/2),
        (unit_cell_pitch/2, upper_wg_y - wg_width/2),
        (unit_cell_pitch/2, upper_wg_y + wg_width/2),
        (coupler_length/2 + 2, upper_wg_y + wg_width/2)
    ], layer=LAYER_SI)
    
    # Lower fixed waveguide sections
    # Input section (left)
    lower_input = c.add_polygon([
        (-unit_cell_pitch/2, lower_wg_y - wg_width/2),
        (-coupler_length/2 - 2, lower_wg_y - wg_width/2),
        (-coupler_length/2 - 2, lower_wg_y + wg_width/2),
        (-unit_cell_pitch/2, lower_wg_y + wg_width/2)
    ], layer=LAYER_SI)
    
    # Output section (right)
    lower_output = c.add_polygon([
        (coupler_length/2 + 2, lower_wg_y - wg_width/2),
        (unit_cell_pitch/2, lower_wg_y - wg_width/2),
        (unit_cell_pitch/2, lower_wg_y + wg_width/2),
        (coupler_length/2 + 2, lower_wg_y + wg_width/2)
    ], layer=LAYER_SI)
    
    # =========================================================================
    # WAVEGUIDE CROSSING
    # =========================================================================
    
    # Create the cross-connect waveguides through the center
    # Upper-left to lower-right
    crossing_1 = gf.Path()
    crossing_1.append(gf.path.straight(length=30))
    crossing_1.append(gf.path.euler(radius=wg_bend_radius, angle=-45))
    crossing_1.append(gf.path.straight(length=wg_separation * np.sqrt(2)))
    crossing_1.append(gf.path.euler(radius=wg_bend_radius, angle=-45))
    crossing_1.append(gf.path.straight(length=30))
    
    cross_1 = c.add_ref(gf.path.extrude(crossing_1, width=wg_width, layer=LAYER_SI))
    cross_1.move((coupler_length/2 + 2, upper_wg_y))
    
    # Lower-left to upper-right
    crossing_2 = gf.Path()
    crossing_2.append(gf.path.straight(length=30))
    crossing_2.append(gf.path.euler(radius=wg_bend_radius, angle=45))
    crossing_2.append(gf.path.straight(length=wg_separation * np.sqrt(2)))
    crossing_2.append(gf.path.euler(radius=wg_bend_radius, angle=45))
    crossing_2.append(gf.path.straight(length=30))
    
    cross_2 = c.add_ref(gf.path.extrude(crossing_2, width=wg_width, layer=LAYER_SI))
    cross_2.move((coupler_length/2 + 2, lower_wg_y))
    
    # =========================================================================
    # MOVABLE STRUCTURE (Directional couplers + comb drive)
    # =========================================================================
    
    # Create movable coupling sections
    # Upper movable coupler waveguide
    upper_movable_y = upper_wg_y - initial_gap - wg_width
    upper_movable = c.add_polygon([
        (-coupler_length/2, upper_movable_y - wg_width/2),
        (coupler_length/2, upper_movable_y - wg_width/2),
        (coupler_length/2, upper_movable_y + wg_width/2),
        (-coupler_length/2, upper_movable_y + wg_width/2)
    ], layer=LAYER_SI)
    
    # Lower movable coupler waveguide
    lower_movable_y = lower_wg_y + initial_gap + wg_width
    lower_movable = c.add_polygon([
        (-coupler_length/2, lower_movable_y - wg_width/2),
        (coupler_length/2, lower_movable_y - wg_width/2),
        (coupler_length/2, lower_movable_y + wg_width/2),
        (-coupler_length/2, lower_movable_y + wg_width/2)
    ], layer=LAYER_SI)
    
    # Connect movable waveguides to central shuttle
    # Upper tether
    tether_width = 2.0  # Wider for mechanical strength
    upper_tether = c.add_polygon([
        (-tether_width/2, upper_movable_y + wg_width/2),
        (tether_width/2, upper_movable_y + wg_width/2),
        (tether_width/2, 10),
        (-tether_width/2, 10)
    ], layer=LAYER_SI)
    
    # Lower tether
    lower_tether = c.add_polygon([
        (-tether_width/2, lower_movable_y - wg_width/2),
        (tether_width/2, lower_movable_y - wg_width/2),
        (tether_width/2, -10),
        (-tether_width/2, -10)
    ], layer=LAYER_SI)
    
    # Central shuttle that connects both movable sections
    shuttle = c.add_polygon([
        (-15, -10),
        (15, -10),
        (15, 10),
        (-15, 10)
    ], layer=LAYER_SI)
    
    # =========================================================================
    # COMB DRIVE ACTUATOR
    # =========================================================================
    
    # Position comb drive to the side of the waveguides
    comb_x_offset = -50  # Position to the left of center
    comb_y_offset = 0
    
    # Fixed comb fingers (anchored to substrate)
    # Create base/anchor for fixed combs
    fixed_anchor = c.add_polygon([
        (comb_x_offset - comb_footprint/2, comb_y_offset - 5),
        (comb_x_offset - comb_footprint/2 + 5, comb_y_offset - 5),
        (comb_x_offset - comb_footprint/2 + 5, comb_y_offset + 5),
        (comb_x_offset - comb_footprint/2, comb_y_offset + 5)
    ], layer=LAYER_SI)
    
    # Add fixed comb fingers
    for i in range(num_finger_pairs):
        finger_y = comb_y_offset - (num_finger_pairs * comb_finger_pitch) / 2 + i * comb_finger_pitch
        
        fixed_finger = c.add_polygon([
            (comb_x_offset - comb_footprint/2 + 5, finger_y - comb_finger_width/2),
            (comb_x_offset - comb_footprint/2 + 5 + comb_finger_length, finger_y - comb_finger_width/2),
            (comb_x_offset - comb_footprint/2 + 5 + comb_finger_length, finger_y + comb_finger_width/2),
            (comb_x_offset - comb_footprint/2 + 5, finger_y + comb_finger_width/2)
        ], layer=LAYER_SI)
    
    # Moving comb fingers (connected to shuttle)
    # Create backbone for moving combs
    moving_backbone = c.add_polygon([
        (comb_x_offset - comb_footprint/2 + 30, comb_y_offset - 20),
        (comb_x_offset - comb_footprint/2 + 35, comb_y_offset - 20),
        (comb_x_offset - comb_footprint/2 + 35, comb_y_offset + 20),
        (comb_x_offset - comb_footprint/2 + 30, comb_y_offset + 20)
    ], layer=LAYER_SI)
    
    # Add moving comb fingers (interdigitated with fixed fingers)
    for i in range(num_finger_pairs):
        finger_y = comb_y_offset - (num_finger_pairs * comb_finger_pitch) / 2 + i * comb_finger_pitch + comb_finger_pitch/2
        
        if finger_y < comb_y_offset + 20:  # Keep within backbone bounds
            moving_finger = c.add_polygon([
                (comb_x_offset - comb_footprint/2 + 10, finger_y - comb_finger_width/2),
                (comb_x_offset - comb_footprint/2 + 10 + comb_finger_length, finger_y - comb_finger_width/2),
                (comb_x_offset - comb_footprint/2 + 10 + comb_finger_length, finger_y + comb_finger_width/2),
                (comb_x_offset - comb_footprint/2 + 10, finger_y + comb_finger_width/2)
            ], layer=LAYER_SI)
    
    # Connect moving combs to shuttle
    connection_bar = c.add_polygon([
        (comb_x_offset - comb_footprint/2 + 30, -2),
        (-15, -2),
        (-15, 2),
        (comb_x_offset - comb_footprint/2 + 30, 2)
    ], layer=LAYER_SI)
    
    # =========================================================================
    # FOLDED SPRINGS (4 springs as per paper)
    # =========================================================================
    
    def create_folded_spring(x_pos, y_pos, orientation='horizontal'):
        """Create a folded spring at specified position"""
        spring_spacing = 1.0
        
        points = []
        if orientation == 'horizontal':
            # Create serpentine spring pattern
            for i in range(spring_turns):
                if i % 2 == 0:
                    points.extend([
                        (x_pos + i*3, y_pos - spring_spacing),
                        (x_pos + i*3 + 3, y_pos - spring_spacing),
                        (x_pos + i*3 + 3, y_pos + spring_spacing),
                    ])
                else:
                    points.extend([
                        (x_pos + i*3 + 3, y_pos + spring_spacing),
                        (x_pos + i*3, y_pos + spring_spacing),
                        (x_pos + i*3, y_pos - spring_spacing),
                    ])
            
            # Create spring path
            spring_path = gf.Path()
            for i in range(len(points)-1):
                dx = points[i+1][0] - points[i][0]
                dy = points[i+1][1] - points[i][1]
                length = np.sqrt(dx**2 + dy**2)
                if length > 0:
                    spring_path.append(gf.path.straight(length=length, 
                                                       angle=np.degrees(np.arctan2(dy, dx))))
            
            return gf.path.extrude(spring_path, width=spring_width, layer=LAYER_SI)
        
        return None
    
    # Add four folded springs at corners of shuttle
    spring_positions = [
        (-25, 8, 'horizontal'),   # Top-left
        (20, 8, 'horizontal'),    # Top-right
        (-25, -8, 'horizontal'),  # Bottom-left
        (20, -8, 'horizontal')    # Bottom-right
    ]
    
    for x, y, orient in spring_positions:
        spring = create_folded_spring(x, y, orient)
        if spring:
            c.add_ref(spring)
    
    # =========================================================================
    # ANCHOR POINTS for springs (connected to substrate)
    # =========================================================================
    
    anchor_size = 5.0
    anchor_positions = [
        (-25 - spring_turns*3, 8),    # Left-top anchor
        (20 + spring_turns*3, 8),     # Right-top anchor
        (-25 - spring_turns*3, -8),   # Left-bottom anchor
        (20 + spring_turns*3, -8)     # Right-bottom anchor
    ]
    
    for x, y in anchor_positions:
        anchor = c.add_polygon([
            (x - anchor_size/2, y - anchor_size/2),
            (x + anchor_size/2, y - anchor_size/2),
            (x + anchor_size/2, y + anchor_size/2),
            (x - anchor_size/2, y + anchor_size/2)
        ], layer=LAYER_SI)
    
    # =========================================================================
    # METAL PADS for electrical connection
    # =========================================================================
    
    pad_size = 30.0
    pad_positions = [
        (comb_x_offset - comb_footprint/2 - 20, 0),  # Fixed comb pad
        (60, 0)  # Movable structure pad
    ]
    
    for x, y in pad_positions:
        metal_pad = c.add_polygon([
            (x - pad_size/2, y - pad_size/2),
            (x + pad_size/2, y - pad_size/2),
            (x + pad_size/2, y + pad_size/2),
            (x - pad_size/2, y + pad_size/2)
        ], layer=LAYER_METAL)
    
    # Add metal traces connecting pads to actuators
    # Trace to fixed combs
    trace1 = c.add_polygon([
        (comb_x_offset - comb_footprint/2 - 20 + pad_size/2, -1),
        (comb_x_offset - comb_footprint/2, -1),
        (comb_x_offset - comb_footprint/2, 1),
        (comb_x_offset - comb_footprint/2 - 20 + pad_size/2, 1)
    ], layer=LAYER_METAL)
    
    # Trace to moving structure
    trace2 = c.add_polygon([
        (60 - pad_size/2, -1),
        (15, -1),
        (15, 1),
        (60 - pad_size/2, 1)
    ], layer=LAYER_METAL)
    
    # =========================================================================
    # LABELS AND ALIGNMENT MARKS
    # =========================================================================
    
    # Add cell labels
    c.add_label("MEMS_SWITCH_UNIT", position=(0, -unit_cell_pitch/2 + 10), layer=LAYER_SI)
    c.add_label(f"Gap: {initial_gap*1000:.0f}nm", position=(0, upper_movable_y), layer=LAYER_SI)
    
    # Add alignment crosses at corners
    cross_positions = [
        (-unit_cell_pitch/2 + 10, unit_cell_pitch/2 - 10),
        (unit_cell_pitch/2 - 10, unit_cell_pitch/2 - 10),
        (-unit_cell_pitch/2 + 10, -unit_cell_pitch/2 + 10),
        (unit_cell_pitch/2 - 10, -unit_cell_pitch/2 + 10)
    ]
    
    for x, y in cross_positions:
        cross = gf.components.cross(length=5, width=0.5, layer=LAYER_SI)
        c.add_ref(cross).move((x, y))
    
    return c


@gf.cell
def create_grating_coupler():
    """
    Create a grating coupler based on paper specifications.
    - 640 nm pitch
    - 50% duty cycle
    - 70 nm etch depth (partial etch)
    - 30 nm bandwidth
    - TE polarization optimized
    """
    c = Component()
    
    LAYER_SI = (1, 0)
    LAYER_SI_PARTIAL = (2, 0)
    
    # Grating parameters from paper
    pitch = 0.64  # 640 nm
    duty_cycle = 0.5  # 50%
    num_periods = 25  # Typical for fiber coupling
    grating_length = num_periods * pitch
    taper_length = 10.0  # Taper from waveguide to grating
    
    # Waveguide width
    wg_width = 0.45  # 450 nm
    grating_width = 12.0  # Width of grating region
    
    # Create input taper
    taper = c.add_polygon([
        (0, -wg_width/2),
        (taper_length, -grating_width/2),
        (taper_length, grating_width/2),
        (0, wg_width/2)
    ], layer=LAYER_SI)
    
    # Create grating teeth (shallow etched regions)
    for i in range(num_periods):
        x_start = taper_length + i * pitch
        tooth = c.add_polygon([
            (x_start, -grating_width/2),
            (x_start + pitch * duty_cycle, -grating_width/2),
            (x_start + pitch * duty_cycle, grating_width/2),
            (x_start, grating_width/2)
        ], layer=LAYER_SI_PARTIAL)
    
    # Add full silicon region under grating
    grating_base = c.add_polygon([
        (taper_length, -grating_width/2),
        (taper_length + grating_length, -grating_width/2),
        (taper_length + grating_length, grating_width/2),
        (taper_length, grating_width/2)
    ], layer=LAYER_SI)
    
    return c


@gf.cell
def create_full_switch_matrix(size=32):
    """
    Create the full 32x32 switch matrix.
    Total area: 5.9mm x 5.9mm for switch matrix
    Additional 0.7mm x 8.4mm for grating couplers and routing
    """
    c = Component()
    
    unit_pitch = 166.0  # μm
    
    # Create the switch matrix
    for i in range(size):
        for j in range(size):
            unit = create_mems_switch_unit()
            unit_ref = c.add_ref(unit)
            unit_ref.move((i * unit_pitch, j * unit_pitch))
    
    # Add grating couplers for inputs and outputs
    gc = create_grating_coupler()
    
    # Input grating couplers (left side)
    for i in range(size):
        gc_ref = c.add_ref(gc)
        gc_ref.rotate(180)  # Point towards chip
        gc_ref.move((-200, i * unit_pitch))
    
    # Output grating couplers (right side)
    for i in range(size):
        gc_ref = c.add_ref(gc)
        gc_ref.move((size * unit_pitch + 200, i * unit_pitch))
    
    # Add chip label
    c.add_label(f"{size}x{size} MEMS SWITCH", 
                position=(size * unit_pitch / 2, -100), 
                layer=(1, 0))
    
    return c


# Create and display the switch unit cell
if __name__ == "__main__":
    # Create single unit cell
    switch_unit = create_mems_switch_unit()
    
    # Create grating coupler
    grating = create_grating_coupler()
    
    # Create small 3x3 matrix for visualization (full 32x32 would be very large)
    small_matrix = create_full_switch_matrix(size=3)
    
    # Show the unit cell
    switch_unit.show()
    
    # Save to GDS files
    switch_unit.write_gds("mems_switch_unit.gds")
    grating.write_gds("grating_coupler.gds")
    small_matrix.write_gds("switch_matrix_3x3.gds")
    
    # Print device statistics
    print(f"Unit cell size: {166} μm x {166} μm")
    print(f"Full 32x32 matrix size: {32*166/1000:.1f} mm x {32*166/1000:.1f} mm")
    print(f"Switching voltage: 9.45V")
    print(f"Number of comb finger pairs: 44")
    print(f"Gap range: 550nm (OFF) to 135nm (ON)")
    print(f"Extinction ratio: 50.8 dB")