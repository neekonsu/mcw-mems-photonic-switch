import gdsfactory as gf
from gdsfactory.typings import LayerSpec
import numpy as np

# --- Layer Definition ---
# Based on the fabrication process described in Fig. 3 of the paper.
class Layers:
    WG_FULL = (1, 0)  # 220 nm full silicon etch for waveguides, MEMS
    METAL = (2, 0)    # Au/Cr metal pads for electrical contact
    UNDERCUT = (3, 0) # Layer defining the area for HF vapor release
    FLOORPLAN = (99, 0) # For component boundaries, not for fabrication

L = Layers()

# --- Component Functions ---

def create_folded_spring(
    width: float = 0.3,
    beam_length: float = 30.0,
    truss_length: float = 10.0,
    layer: LayerSpec = L.WG_FULL,
) -> gf.Component:
    """Creates a folded-beam spring."""
    c = gf.Component("folded_spring")
    beam = gf.components.rectangle(size=(beam_length, width), layer=layer)
    truss = gf.components.rectangle(size=(width, truss_length), layer=layer)

    # Main beams
    beam1_ref = c << beam
    beam2_ref = c << beam
    beam1_ref.xmin = width
    beam2_ref.xmin = width
    beam2_ref.movey(truss_length - width)

    # Connecting trusses
    truss1_ref = c << truss
    truss2_ref = c << truss
    truss1_ref.movex(0)
    truss2_ref.movex(beam_length)
    
    c.add_port("anchor", midpoint=(truss1_ref.centerx, truss_length/2), width=width, orientation=180, layer=layer)
    c.add_port("shuttle", midpoint=(truss2_ref.centerx, truss_length/2), width=width, orientation=0, layer=layer)
    return c


def create_comb_drive_pair(
    finger_width: float = 0.3,
    finger_gap: float = 0.4,
    finger_engagement: float = 8.0,
    n_pairs: int = 44,
    layer: LayerSpec = L.WG_FULL,
) -> gf.Component:
    """Creates a complete comb drive with fixed and moving sides."""
    c = gf.Component(f"comb_drive_{n_pairs}_pairs")
    
    finger_pitch = 2 * (finger_width + finger_gap)
    array_height = (n_pairs - 1) * finger_pitch + finger_width
    
    finger = gf.components.rectangle(size=(finger_engagement, finger_width), layer=layer)
    
    # Create arrays of fingers
    fixed_fingers = c.add_array(finger, columns=1, rows=n_pairs, spacing=(0, finger_pitch))
    moving_fingers = c.add_array(finger, columns=1, rows=n_pairs, spacing=(0, finger_pitch))
    moving_fingers.movex(finger_engagement + finger_gap)
    moving_fingers.movey(finger_pitch / 2 - (finger_width+finger_gap))
    
    # Add backbones
    backbone_width = 5.0
    fixed_backbone = c << gf.components.rectangle(size=(backbone_width, array_height), layer=layer)
    fixed_backbone.right = fixed_fingers.xmin
    fixed_backbone.y = fixed_fingers.y
    
    moving_backbone = c << gf.components.rectangle(size=(backbone_width, array_height), layer=layer)
    moving_backbone.left = moving_fingers.xmax
    moving_backbone.y = fixed_fingers.y
    
    c.add_port("fixed", center=fixed_backbone.center, orientation=180, layer=layer)
    c.add_port("moving", center=moving_backbone.center, orientation=0, layer=layer)
    return c


def create_mems_switch_unit_cell() -> gf.Component:
    """Assembles the complete MEMS photonic switch unit cell."""
    
    # --- Parameters from Paper ---
    wg_width = 0.45
    coupler_length = 20.0
    initial_gap = 0.55
    num_comb_pairs = 44
    spring_width = 0.3
    spring_beam_length = 30.0
    actuator_footprint = 88.0

    c = gf.Component("MEMS_Switch")
    wg_xs = gf.cross_section.cross_section(width=wg_width, layer=L.WG_FULL)
    
    # 1. Static Waveguides and Anchors
    # --- FIX: Pass width and layer directly to the crossing component ---
    crossing = c << gf.components.crossing(width=wg_width, layer=L.WG_FULL)
    
    anchor = gf.components.rectangle(size=(20, 20), layer=L.WG_FULL)
    anchor_tl = c << anchor
    anchor_tr = c << anchor
    anchor_bl = c << anchor
    anchor_br = c << anchor

    anchor_tl.topleft = (-actuator_footprint/2, actuator_footprint/2)
    anchor_tr.topright = (actuator_footprint/2, actuator_footprint/2)
    anchor_bl.bottomleft = (-actuator_footprint/2, -actuator_footprint/2)
    anchor_br.bottomright = (actuator_footprint/2, -actuator_footprint/2)
    
    # 2. Movable Shuttle
    shuttle = c << gf.components.rectangle(size=(actuator_footprint, actuator_footprint*0.4), layer=L.WG_FULL)
    shuttle.center = (0, 0)
    
    # 3. Assemble MEMS components
    spring = create_folded_spring(width=spring_width, beam_length=spring_beam_length)
    s_tl = c << spring
    s_tr = c << spring
    s_bl = c << spring
    s_br = c << spring
    
    s_tl.connect("shuttle", shuttle.ports["e4"])
    s_tr.connect("shuttle", shuttle.ports["e2"])
    s_bl.connect("shuttle", shuttle.ports["e4"], mirror=True)
    s_br.connect("shuttle", shuttle.ports["e2"], mirror=True)

    comb_drive = create_comb_drive_pair(n_pairs=num_comb_pairs)
    cd_top = c << comb_drive
    cd_bot = c << comb_drive
    cd_top.connect("moving", shuttle.ports["e3"])
    cd_bot.connect("moving", shuttle.ports["e1"])

    # This entire MEMS assembly should be rotated 45 degrees
    mems_assembly = c.extract(layers=(L.WG_FULL,))
    mems_assembly.rotate(-45)
    
    # Final cell composition
    final_cell = gf.Component("Final_MEMS_Switch_Cell")
    final_cell << mems_assembly.move((100, 60))
    final_cell << crossing.move((124.5, 30))

    final_cell.add_ports(crossing.ports)
    return final_cell


# --- Main Execution ---
if __name__ == "__main__":
    mems_switch = create_mems_switch_unit_cell()
    mems_switch.show(show_ports=True)