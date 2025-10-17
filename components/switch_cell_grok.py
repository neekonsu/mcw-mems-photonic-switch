import gdsfactory as gf

# Define layers
WG_LAYER = (1, 0)  # Full etch for waveguides and MEMS structures
SLAB_LAYER = (2, 0)  # Partial etch for gratings and crossings
METAL_LAYER = (3, 0)  # Metal pads

# Parameters from the paper
waveguide_width = 0.45  # μm
coupler_length = 20.0  # μm
initial_gap = 0.55  # μm
center_to_center = waveguide_width + initial_gap  # 1.0 μm
comb_finger_width = 0.3  # μm
comb_finger_gap = 0.4  # μm
num_comb_pairs = 44
spring_width = 0.3  # μm
spring_length = 30.0  # μm
cell_pitch = 166.0  # μm
actuator_footprint = 88.0  # μm
bend_radius = 10.0  # μm, inferred to fit the connection

# Define custom cross_sections for consistency
xs_wg = gf.cross_section.cross_section(width=waveguide_width, layer=WG_LAYER)
xs_spring = gf.cross_section.cross_section(width=spring_width, layer=WG_LAYER)

@gf.cell
def crossing():
    # Simple tapered crossing for illustration; in practice, use a low-loss design
    c = gf.Component()
    taper_length = 10.0
    wide_width = 1.5
    taper1 = gf.components.taper(length=taper_length, width1=waveguide_width, width2=wide_width, layer=WG_LAYER)
    taper2 = gf.components.taper(length=taper_length, width1=wide_width, width2=waveguide_width, layer=WG_LAYER)
    
    # Horizontal tapers
    t1h = c << taper1
    t1h.move((-taper_length - wide_width/2, -waveguide_width/2))
    t2h = c << taper2
    t2h.move((wide_width/2, -waveguide_width/2))
    
    # Vertical tapers
    t1v = c << taper1
    t1v.rotate(90)
    t1v.move((-waveguide_width/2, -taper_length - wide_width/2))
    t2v = c << taper2
    t2v.rotate(90)
    t2v.move((-waveguide_width/2, wide_width/2))
    
    # Center cross region (multimode)
    cross = gf.components.rectangle(size=(wide_width, wide_width), layer=SLAB_LAYER, centered=True)
    c << cross
    return c

@gf.cell
def folded_spring():
    # Simple folded spring representation
    c = gf.Component()
    beam = gf.components.straight(length=spring_length / 2, cross_section=xs_spring)
    for i in range(4):  # 4 folds approximation
        b = c << beam
        b.move((i % 2 * 5, i // 2 * spring_width * 2))  # Rough layout
        if i % 2 == 1:
            b.mirror()
    return c

@gf.cell
def comb_drive():
    # Comb drive with fixed and moving combs
    c = gf.Component()
    finger_length = 5.0  # Inferred from typical designs ~5-10 μm
    # Fixed comb
    fixed = gf.Component("fixed_comb")
    for i in range(num_comb_pairs + 1):  # Extra for alignment
        finger = gf.components.rectangle(size=(comb_finger_width, finger_length), layer=WG_LAYER)
        f = fixed << finger
        f.move((i * (comb_finger_width + comb_finger_gap), 0))
    
    # Moving comb, offset by finger_gap / 2 or something, but initial interdigitated
    moving = gf.Component("moving_comb")
    for i in range(num_comb_pairs):
        finger = gf.components.rectangle(size=(comb_finger_width, finger_length), layer=WG_LAYER)
        f = moving << finger
        f.move(((i + 0.5) * (comb_finger_width + comb_finger_gap), -0.1))  # Slight overlap offset
    
    f_comb = c << fixed
    m_comb = c << moving
    m_comb.move((0, -finger_length + 0.3))  # Interdigitated position
    return c

@gf.cell
def unit_cell_switch():
    c = gf.Component("unit_cell_switch")
    
    # Fixed horizontal waveguide
    horiz_fixed_length = cell_pitch
    horiz_fixed_comp = gf.components.straight(length=horiz_fixed_length, cross_section=xs_wg)
    h_fixed = c << horiz_fixed_comp
    h_fixed.move((-horiz_fixed_length/2, 0))
    
    # Fixed vertical waveguide
    vert_fixed_comp = gf.components.straight(length=horiz_fixed_length, cross_section=xs_wg)
    v_fixed = c << vert_fixed_comp
    v_fixed.rotate(90)
    v_fixed.move((0, -horiz_fixed_length/2))
    
    # Crossing at center
    cross = c << crossing()
    
    # Moving L-shaped waveguide
    # Horizontal part (positioned relative to actuator for better fit)
    horiz_moving_comp = gf.components.straight(length=coupler_length, cross_section=xs_wg)
    h_moving = c << horiz_moving_comp
    h_moving.move((-actuator_footprint / 2 - coupler_length / 2, -center_to_center))
    
    # Bend connecting to horizontal
    bend_comp = gf.components.bend_euler(angle=90, cross_section=xs_wg, radius=bend_radius)
    b = c << bend_comp
    b.connect("o1", h_moving.ports["o2"])
    
    # Vertical part connected to bend
    vert_moving_comp = gf.components.straight(length=coupler_length, cross_section=xs_wg)
    v_moving = c << vert_moving_comp
    v_moving.connect("o1", b.ports["o2"])  # Automatically rotates and positions
    
    # Actuator
    actuator_comp = comb_drive()
    actuator = c << actuator_comp
    actuator.rotate(45)
    actuator.move((-actuator_footprint / 2, -actuator_footprint / 2))  # Better bottom-left positioning
    
    # Springs, place 4 folded springs
    for pos in [(-actuator_footprint / 2 + 10, -actuator_footprint / 2 + 10), 
                (-actuator_footprint / 2 + 10, -actuator_footprint / 2 - 10), 
                (-actuator_footprint / 2 - 10, -actuator_footprint / 2 + 10), 
                (-actuator_footprint / 2 - 10, -actuator_footprint / 2 - 10)]:
        spring_comp = folded_spring()
        spring = c << spring_comp
        spring.rotate(45)
        spring.move(pos)
    
    # Metal pads
    pad_size = (20, 20)
    ground_pad = gf.components.rectangle(size=pad_size, layer=METAL_LAYER)
    signal_pad = gf.components.rectangle(size=pad_size, layer=METAL_LAYER)
    g_pad = c << ground_pad
    g_pad.move((-actuator_footprint / 2 - 10, -actuator_footprint / 2 - 30))
    s_pad = c << signal_pad
    s_pad.move((-actuator_footprint / 2 + 20, -actuator_footprint / 2 - 30))
    
    return c

# Generate the component
switch = unit_cell_switch()

# Show or write to GDS
switch.show()  # If in interactive mode
# switch.write_gds("unit_cell_switch.gds")