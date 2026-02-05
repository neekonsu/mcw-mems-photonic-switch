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
axis_outline_pts = [(0,0),(11,0),(11,150),(0,150)]
axis_outline.add_polygon(axis_outline_pts, layer=DPOLY)



# Spring Code
spring = gf.Component()

# Linear Spring Code (uncomment to select)

# Bistable Spring Code (uncomment to select)

# Comb Drive Code
cd = gf.Component()

# Electrical Interconnect Code
interconnect = gf.Component()

# Anchor Code
anchor = gf.Component()

# Proof-Mass Code
proof = gf.Component()

# Assemble MEMS Components



