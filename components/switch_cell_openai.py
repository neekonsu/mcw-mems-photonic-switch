# mems_switch_cell.py
# One-cell layout for the Han et al. silicon photonic MEMS switch (gap-tunable DC + comb drive).
# Paper-derived defaults are cited in the accompanying message.

import gdsfactory as gf
from gdsfactory.typings import LayerSpec
from math import ceil

# --------------------------
# Layers (feel free to map to your PDK)
# --------------------------
LAYER = dict(
    WG=(1, 0),          # full etch 220 nm
    SLAB=(2, 0),        # shallow 70 nm
    METAL=(3, 0),       # Au/Cr pad
    OPEN=(4, 0),        # release/opening
    MECH=(10, 0),       # combs, shuttle, springs (same Si device layer)
    MARK=(99, 0),       # fiducials
)

# --------------------------
# Global process parameters (paper-derived defaults)
# --------------------------
SI_THICK = 0.22           # um, SOI device thickness (paper)
BOX_THICK = 3.0           # um, BOX (paper)
WG_W = 0.45               # um, waveguide width (paper)
COUPLER_LEN = 20.0        # um (paper)
GAP_INIT = 0.55           # um, initial DC gap before actuation (paper)
GAP_ON = 0.135            # um, "on" gap used in simulation (paper)
TILE = 166.0              # um, waveguide pitch/tiling envelope (paper)
ACT_FOOT = (88.0, 88.0)   # um x um, comb-drive footprint (paper)

# Comb drive / springs (paper)
FINGER_W = 0.30           # um (paper)
FINGER_G = 0.40           # um (paper)
N_PAIRS   = 44            # (paper)
SPRING_W  = 0.30          # um (paper)
SPRING_L  = 30.0          # um (paper)

# --------------------------
# Reasonable assumptions (parametric)
# --------------------------
FINGER_L = 25.0           # um, finger length (assumed)
SHUTTLE_W = 3.0           # um, shuttle rail width (assumed)
SHUTTLE_LEN = ACT_FOOT[0] - 10.0   # um, shuttle length inside the actuator (assumed)
COUPLER_TO_CROSSING_GAP = 6.0      # um, clearance from crossing to each coupler (assumed)
ROUTE_CLEAR = 2.0         # um, clearance for S-bends (assumed)
PAD_SIZE = (35.0, 35.0)   # um, metal pad (assumed)
CROSSING_SIZE = 8.0       # um, crossing box length (assumed)

# --------------------------
# Cross-sections
# --------------------------
xs = gf.cross_section.strip(width=WG_W, layer=LAYER["WG"])

@gf.cell
def plus_crossing(
    wg_width: float = WG_W,
    length: float = 8.0,
    layer: LayerSpec = LAYER["WG"],
) -> gf.Component:
    """Version-agnostic waveguide crossing made from two straights.
    Ports: o1=West, o2=South, o3=East, o4=North (to match the original script)."""
    c = gf.Component("plus_crossing")
    xs_local = gf.cross_section.strip(width=wg_width, layer=layer)

    h = c << gf.components.straight(length=length, cross_section=xs_local)   # W↔E
    v = c << gf.components.straight(length=length, cross_section=xs_local)   # S↔N
    v.rotate(90)

    h.center = (0, 0)
    v.center = (0, 0)

    # Re-export ports with the same names/orientations we used before
    c.add_port("o1", port=h.ports["o1"])  # West
    c.add_port("o3", port=h.ports["o2"])  # East
    c.add_port("o2", port=v.ports["o1"])  # South
    c.add_port("o4", port=v.ports["o2"])  # North
    return c

@gf.cell
def coupler_gap_adjustable(
    length: float = COUPLER_LEN,
    gap: float = GAP_INIT,
    wg_width: float = WG_W,
    layer: LayerSpec = LAYER["WG"],
) -> gf.Component:
    """Two parallel straights separated by 'gap' to form a gap-tunable directional coupler."""
    c = gf.Component()
    xs_local = gf.cross_section.strip(width=wg_width, layer=layer)

    # centers of the two rails
    dy = 0.5 * (gap + wg_width)
    top = c << gf.components.straight(length=length, cross_section=xs_local)
    bot = c << gf.components.straight(length=length, cross_section=xs_local)
    top.movey(+dy)
    bot.movey(-dy)

    # expose ports: left/right of each rail
    c.add_port(name="a1", port=top.ports["o1"])  # top left
    c.add_port(name="b1", port=top.ports["o2"])  # top right
    c.add_port(name="a2", port=bot.ports["o1"])  # bottom left
    c.add_port(name="b2", port=bot.ports["o2"])  # bottom right
    return c

@gf.cell
def comb_drive_diagonal(
    n_pairs=N_PAIRS,
    finger_w=FINGER_W,
    finger_g=FINGER_G,
    finger_l=FINGER_L,
    shuttle_w=SHUTTLE_W,
    spring_w=SPRING_W,
    spring_l=SPRING_L,
    footprint=ACT_FOOT,
    layer: LayerSpec = LAYER["MECH"],
) -> gf.Component:
    """
    Simplified diagonal comb-drive within a square footprint.
    Draws interdigitated fingers (n_pairs) and a central shuttle connected by four folded springs.
    Geometry is schematic (for mask iteration you can refine anchors/overlaps in this cell only).
    """
    c = gf.Component()

    W, H = footprint
    # Draw an outer reference frame (for visual alignment)
    frame = c << gf.components.rectangle(size=(W, H), layer=LAYER["MARK"])
    frame.move((-W/2, -H/2))

    pitch = finger_w + finger_g
    n_fingers_each_side = n_pairs  # moving vs fixed
    span = n_fingers_each_side * pitch

    # Shuttle bar (diagonal)
    shuttle = c << gf.components.rectangle(size=(SHUTTLE_LEN, shuttle_w), layer=layer)
    shuttle.center = (0, 0)
    shuttle.rotate(45)  # diagonal motion

    # Build interdigitated fingers aligned with the shuttle (approximate, schematic)
    # We'll place rows of vertical fingers on two sides of the shuttle bounding box.
    # For simplicity, align fingers unrotated and bias placement to suggest diagonal overlap.
    start_y = -span/2 + finger_w/2
    x_left  = -W/2 + 5.0
    x_right = +W/2 - 5.0 - finger_l

    for i in range(n_fingers_each_side):
        y = start_y + i * pitch
        # left, fixed fingers (pointing +x)
        rect_l = gf.components.rectangle(size=(finger_l, finger_w), layer=layer, centered=False)
        ref_l = c << rect_l
        ref_l.move((x_left, y))
        # right, moving fingers (pointing -x)
        rect_r = gf.components.rectangle(size=(finger_l, finger_w), layer=layer, centered=False)
        ref_r = c << rect_r
        ref_r.move((x_right, y))

    # Four folded springs to anchors (schematic "Π" shape segments)
    def folded_spring(cx, cy):
        s = gf.Component()
        # three rectangles to emulate a folded spring, using explicit reference and move
        rect_mid = gf.components.rectangle(size=(spring_w, spring_l), layer=layer, centered=True)
        ref_mid = s << rect_mid

        rect_top = gf.components.rectangle(size=(spring_l*0.5, spring_w), layer=layer, centered=True)
        ref_top = s << rect_top
        ref_top.movey(+spring_l/2 - spring_w/2)

        rect_bot = gf.components.rectangle(size=(spring_l*0.5, spring_w), layer=layer, centered=True)
        ref_bot = s << rect_bot
        ref_bot.movey(-spring_l/2 + spring_w/2)

        ref = c << s
        ref.center = (cx, cy)
        return ref

    s_offset = 0.35 * min(W, H)
    folded_spring(-s_offset, -s_offset)
    folded_spring(+s_offset, -s_offset)
    folded_spring(-s_offset, +s_offset)
    folded_spring(+s_offset, +s_offset)

    return c

def switch_cell() -> gf.Component:
    """
    One MEMS-photonic switch unit cell:
    - Crossing at center
    - Two tunable couplers placed SW->NE diagonal and NW->SE diagonal
    - Comb-drive actuator below-right, oriented for diagonal pull
    - Simple metal pads and release window
    """
    c = gf.Component("mems_switch_cell")

    # Cell outline for tiling
    outline = c << gf.components.rectangle(size=(TILE, TILE), layer=LAYER["MARK"])
    outline.move((-TILE/2, -TILE/2))

    # 1) Waveguide crossing at origin
    xing = c << plus_crossing(wg_width=WG_W, length=CROSSING_SIZE, layer=LAYER["WG"])
    xing.center = (0, 0)

    # 2) Couplers: place two, one serving horizontal arm, one serving vertical arm
    dc1 = c << coupler_gap_adjustable(length=COUPLER_LEN, gap=GAP_INIT, wg_width=WG_W, layer=LAYER["WG"])   # west/east arm
    dc2 = c << coupler_gap_adjustable(length=COUPLER_LEN, gap=GAP_INIT, wg_width=WG_W, layer=LAYER["WG"])   # south/north arm
    # Position relative to crossing with some clearance
    dc1.center = (-COUPLER_LEN/2 - COUPLER_TO_CROSSING_GAP, +COUPLER_LEN/2)  # NW
    dc2.rotate(90)
    dc2.center = (+COUPLER_LEN/2 + COUPLER_TO_CROSSING_GAP, -COUPLER_LEN/2)  # SE

    # Short straights to hint connection (schematic S-bends avoided for clarity)
    for portname in ("o1", "o2", "o3", "o4"):
        p = xing.ports[portname]
        seg = c << gf.components.straight(length=ROUTE_CLEAR, cross_section=xs)
        seg.connect("o1", p)
        seg.x = p.x + (ROUTE_CLEAR if p.orientation == 0 else -ROUTE_CLEAR if p.orientation == 180 else 0)
        seg.y = p.y + (ROUTE_CLEAR if p.orientation == 90 else -ROUTE_CLEAR if p.orientation == 270 else 0)

    # 3) Comb drive (diagonal) placed bottom-right of crossing, as in the figures
    comb = c << comb_drive_diagonal()
    comb.center = ( +TILE*0.20, -TILE*0.20 )

    # 4) Release window covering MEMS area
    rw = c << gf.components.rectangle(size=(ACT_FOOT[0]+8.0, ACT_FOOT[1]+8.0), layer=LAYER["OPEN"])
    rw.center = comb.center

    # 5) Metal pads (two) for actuation, placed near bottom edge
    pad1 = c << gf.components.rectangle(size=PAD_SIZE, layer=LAYER["METAL"])
    pad2 = c << gf.components.rectangle(size=PAD_SIZE, layer=LAYER["METAL"])
    pad_y = -TILE/2 + PAD_SIZE[1]/2 + 6.0
    pad1.center = (-TILE/4, pad_y)
    pad2.center = (+TILE/4, pad_y)

    # 6) Export optical ports for array stitching (left/right/top/bottom bus)
    # Use the crossing ports so the cell tiles cleanly in a grid if needed.
    for name, p in xing.ports.items():
        c.add_port(name=name, port=p)

    return c

if __name__ == "__main__":
    c = switch_cell()
    c.show()
    # To write GDS:
    # c.write_gds("mems_switch_cell.gds")