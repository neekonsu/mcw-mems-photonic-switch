import gdsfactory as gf
gf.gpdk.PDK.activate() # Activate generic PDK for version of layout not including custom PDK. Will replace references to generic PDK once custom PDK is implemented

# Definitions:
# Young's Modulus Doped PolySi, E: 160 GPa
# Spring/Comb Width,            b: 0.5 um
# Thickness Doped PolySi,       t: 1.5 um
# Length of Spring,             L: 60 um
# Gap of Comb,                  g: 0.3 um
# Voltage of Comb,              V: 10 V
# Permittivity of Free-Space,   e: 8.854 pF/m
# Displacement of Shuttle,      x: 0.55 um
# Number of Combs per CD,       n: 40

# Layers TODO update following placeholders once custom PDK created
DPOLY = (1,0) # doped poly
PSG = (2,0) # doped oxide, psg
UDPOLY = (3,0) # undoped poly
UDOXIDE = (4,0) # undoped oxide
METAL = (5,0) # metal
SOI = (6,0) # SOI Si


# Shuttle Code
shuttle = gf.Component() # Shuttle top-level component

# Longitudinal axis of shuttle
axis_outline = gf.Component()
axis_outline_pts = [(0,0),(11,0),(11,148),(0,148)] # 148um fits 14 10um etch holes at 10.5um pitch.
axis_outline.add_polygon(axis_outline_pts, layer=DPOLY)

# Single Etch Hole
etch_hole = gf.Component("Single Etch Hole")
etch_hole_pts = [(0.5,0.5),(10.5,0.5),(10.5,10.5),(0.5,10.5)]
etch_hole.add_polygon(etch_hole_pts, layer=DPOLY)

# Etch Hole Array
n_holes = 14
etch_holes = gf.Component("Etch Hole Array")
etch_holes.add_ref(etch_hole,
                   columns=1,
                   rows=n_holes,
                   column_pitch=10.5,
                   row_pitch=10.5)

shuttle = gf.boolean(A=axis_outline, B=etch_holes, operation="not", layer1=DPOLY, layer2=DPOLY, layer=DPOLY)

# Spring Code
spring = gf.Component()

# Linear Spring Code (uncomment to select)
spring_anchor = gf.Component()
spring_anchor_dpoly_pts = [(0,0),(5,0),(7.5,2.5),(5,5),(0,5)]
spring_anchor_psg_pts = [(1,1),(4,1),(4,4),(1,4)]
spring_anchor_rest_pts = [(0,0),(5,0),(5,5),(0,5)]
spring_anchor.add_polygon(spring_anchor_dpoly_pts, layer=DPOLY)
spring_anchor.add_polygon(spring_anchor_psg_pts, layer=PSG)
spring_anchor.add_polygon(spring_anchor_rest_pts, layer=UDPOLY)
spring_anchor.add_polygon(spring_anchor_rest_pts, layer=SOI)

spring_arm = gf.Component()
spring_arm_pts = [(6.5,2.25),(68.5,2.25),(68.5,2.75),(6.5,2.75)]
spring_arm.add_polygon(spring_arm_pts, layer=DPOLY)

spring_terminal = gf.Component()
spring_terminal_pts = [(67.5,2.5),(70,0),(70,5)]
spring_terminal.add_polygon(spring_terminal_pts, layer=DPOLY)

spring.add_ref(spring_anchor)
spring.add_ref(spring_arm)
spring.add_ref(spring_terminal)
spring.plot()

# Bistable Spring Code (uncomment to select) TODO

# Comb Drive Code
cd = gf.Component()

# Finger width: 0.5um
# Lateral Gap between fingers: 0.3 um
# Finger Pair Period: 2*0.5um + 2*0.3um = 1.6 um
# Width of 40 finger array: 40*1.6 = 64 um

cd_anchor = gf.Component()
cd_anchor_dpoly_pts = [(0,0),(64,0),(64,20),(0,20)]
cd_anchor_psg_pts = [(2,2),(62,2),(62,18),(2,18)]
cd_anchor_udpoly_pts = cd_anchor_dpoly_pts
cd_anchor_soi_pts = cd_anchor_dpoly_pts
cd_anchor.add_polygon(cd_anchor_dpoly_pts, layer=DPOLY)
cd_anchor.add_polygon(cd_anchor_psg_pts, layer=PSG)
cd_anchor.add_polygon(cd_anchor_udpoly_pts, layer=UDPOLY)
cd_anchor.add_polygon(cd_anchor_soi_pts, layer=SOI)

# Initial finger overlap = 3*g = 1 um approx
# Total displacement possible = 1.1um
# Finger length: (3*g + x) * 3 = 6 um approx

cd_finger = gf.Component()
cd_finger_pts = [(0,0),(0,-6),(0.5,-6),(0.5,0)]
cd_finger.add_polygon(cd_finger_pts, layer=DPOLY)

n_fingers = 40
cd.add_ref(cd_anchor)
cd.add_ref(cd_finger,
           columns=n_fingers,
           rows=1,
           column_pitch=1.6,
           row_pitch=1.6)

# Electrical Interconnect Code TODO determine max length of released poly interconnect by beam width
interconnect = gf.Component()

interconnect_pts = [(0,0),(50,0),(50, 1.5),(0,1.5)]
interconnect.add_polygon(interconnect_pts, layer=DPOLY)
anchor = gf.Component()
anchor_dpoly_pts = [(50,-1.75),(55,-1.75),(55,3.25),(50,3.25)]
anchor_psg_pts = [(51,-0.75),(54,-0.75),(54,2.25),(51,2.25)]
anchor_soi_pts = [(50,-1.75),(55,-1.75),(55,3.25),(50,3.25)]
anchor.add_polygon(anchor_dpoly_pts, layer=DPOLY)
anchor.add_polygon(anchor_psg_pts, layer=PSG)
anchor.add_polygon(anchor_soi_pts, layer=SOI)

interconnect.add_ref(anchor)

# Proof-Mass Code TODO ignoring for now
proof = gf.Component()

# Assemble MEMS Components



