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


# Comb Drive Code

# Finger width: 0.5um
# Lateral Gap between fingers: 0.3 um
# Finger Pair Period: 2*0.5um + 2*0.3um = 1.6 um
# Width of 40 finger array: 40*1.6 = 64 um

cd_mov_anchor = gf.Component()
cd_mov_anchor_dpoly_pts = [(0,0),(69.5,0),(69.5,11),(0,11)]
cd_mov_anchor.add_polygon(cd_mov_anchor_dpoly_pts, layer=DPOLY)

etch_holes_cd = gf.Component()
etch_holes_cd.add_ref(etch_hole,
                      columns=7,
                      rows=1,
                      column_pitch=10.5,
                      row_pitch=10.5)

# Initial finger overlap = 3*g = 1 um approx
# Total displacement possible = 1.1um
# Finger length: (3*g + x) * 3 = 6 um approx

cd_finger = gf.Component()
cd_finger_pts = [(0,0),(0,-6),(0.5,-6),(0.5,0)]
cd_finger.add_polygon(cd_finger_pts, layer=DPOLY)

n_fingers = 40
cd_mov = gf.boolean(A=cd_mov_anchor, B=etch_holes_cd, operation="not", layer1=DPOLY, layer2=DPOLY, layer=DPOLY)
cd_mov.add_ref(cd_finger,
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

interconnect_long = gf.Component()

interconnect_long_pts = [(0,0),(100,0),(100, 1.5),(0,1.5)]
interconnect_long.add_polygon(interconnect_long_pts, layer=DPOLY)
anchor_long = gf.Component()
anchor_long_dpoly_pts = [(100,-1.75),(105,-1.75),(105,3.25),(100,3.25)]
anchor_long_psg_pts = [(101,-0.75),(104,-0.75),(104,2.25),(101,2.25)]
anchor_long_soi_pts = [(100,-1.75),(105,-1.75),(105,3.25),(100,3.25)]
anchor_long.add_polygon(anchor_long_dpoly_pts, layer=DPOLY)
anchor_long.add_polygon(anchor_long_psg_pts, layer=PSG)
anchor_long.add_polygon(anchor_long_soi_pts, layer=SOI)

interconnect_long.add_ref(anchor_long)

# Proof-Mass Code TODO ignoring for now
proof = gf.Component()

# Assemble MEMS Components
mems = gf.Component()

mems.add_ref(shuttle)

s1a = mems.add_ref(spring)
s1b = mems.add_ref(spring)
s2a = mems.add_ref(spring)
s2b = mems.add_ref(spring)

cd1a = mems.add_ref(cd)
cd1b = mems.add_ref(cd)
cd2a = mems.add_ref(cd)
cd2b = mems.add_ref(cd)

cdm1a = mems.add_ref(cd_mov)
cdm1b = mems.add_ref(cd_mov)
cdm2a = mems.add_ref(cd_mov)
cdm2b = mems.add_ref(cd_mov)

ic1 = mems.add_ref(interconnect)
ic2 = mems.add_ref(interconnect)
ic3 = mems.add_ref(interconnect)
ic4 = mems.add_ref(interconnect_long)

# Move Springs
s1a.move(origin=(0,0),destination=(-70,134))
s2a.move(origin=(0,0),destination=(-70,8.5))
s1b.mirror_x().move(origin=(0,0),destination=(81,134))
s2b.mirror_x().move(origin=(0,0),destination=(81,8.5))

# Move Comb Drives
cd1a.move(origin=(0,0),destination=(-70,110))
cd2a.move(origin=(0,0),destination=(-70,60))
cd1b.mirror_x().move(origin=(0,0),destination=(81,110))
cd2b.mirror_x().move(origin=(0,0),destination=(81,60))

# Move Comb Drive Complements
cdm1a.mirror_y().move(origin=(0,0),destination=(-69.25,101.5))
cdm2a.mirror_y().move(origin=(0,0),destination=(-69.25,51.5))
cdm1b.mirror_x().mirror_y().move(origin=(0,0),destination=(80.25,101.5))
cdm2b.mirror_x().mirror_y().move(origin=(0,0),destination=(80.25,51.5))

# Move Interconnects
ic1.move(origin=(0,0),destination=(81,135.75))
ic2.mirror_x().move(origin=(0,0),destination=(-70,135.75))
ic3.move(origin=(0,0),destination=(96,123.5))
ic4.move(origin=(0,0.75),destination=(148.5,122.75)).rotate(angle=-90,center=(148.5,122.75))

# Comb-Drive Node
cdn = gf.Component()
cdn_pts = [(81,125),(96,125),(96,-25),(-85,-25),(-85,125),(-70,125),(-70,115),(-75,115),(-75,75),(-70,75),(-70,65),(-75,65),(-75,-5),(86,-5),(86,65),(81,65),(81,75),(86,75),(86,115),(81,115)]
cdn_psg_pts = [(83,122),(93,122),(93,-22),(-82,-22),(-82,122),(-73,122),(-73,118),(-78,118),(-78,72),(-73,72),(-73,68),(-78,68),(-78,-8),(89,-8),(89,68),(83,68),(83,72),(89,72),(89,118),(83,118)]
cdn.add_polygon(cdn_pts, layer=DPOLY)
cdn.add_polygon(cdn_psg_pts, layer=PSG)
cdn.add_polygon(cdn_pts, layer=SOI)
mems.add_ref(cdn)

if __name__ == "__main__":
    mems.write_gds("./mems.gds")
    mems.show()
