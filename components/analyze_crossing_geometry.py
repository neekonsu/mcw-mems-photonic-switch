#!/usr/bin/env python3
"""
Analyze the waveguide crossing geometry to identify key parameters.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# The 50 points extracted from Shape 0001
points = [
    (40.170, 23.534), (39.954, 23.540), (39.771, 23.535), (39.771, 23.546),
    (39.477, 28.541), (39.175, 31.442), (38.464, 34.032), (38.464, 38.493),
    (31.985, 38.493), (29.395, 39.204), (26.494, 39.506), (21.499, 39.800),
    (21.486, 39.800), (21.492, 40.016), (21.487, 40.199), (21.498, 40.199),
    (26.493, 40.493), (29.394, 40.795), (31.984, 41.506), (38.464, 41.506),
    (38.464, 41.847), (38.476, 41.847), (38.476, 47.967), (39.187, 50.557),
    (39.489, 53.458), (39.783, 58.453), (39.783, 58.466), (39.999, 58.460),
    (40.182, 58.465), (40.182, 58.454), (40.476, 53.459), (40.778, 50.558),
    (41.489, 47.968), (41.489, 41.524), (47.546, 41.524), (50.136, 40.813),
    (53.037, 40.511), (58.032, 40.217), (58.045, 40.217), (58.039, 40.001),
    (58.044, 39.818), (58.033, 39.818), (53.038, 39.524), (50.137, 39.222),
    (47.547, 38.511), (41.477, 38.511), (41.477, 34.033), (40.766, 31.443),
    (40.464, 28.542), (40.170, 23.547)
]

# Calculate centroid
xs = [p[0] for p in points]
ys = [p[1] for p in points]
cx = sum(xs) / len(xs)
cy = sum(ys) / len(ys)

print("="*70)
print("WAVEGUIDE CROSSING GEOMETRY ANALYSIS")
print("="*70)

print(f"\nCentroid: ({cx:.3f}, {cy:.3f}) µm")

# Identify key dimensions by analyzing segments
print("\n" + "="*70)
print("KEY DIMENSIONS")
print("="*70)

# Analyze horizontal segments (constant y, varying x)
horizontal_segs = []
for i in range(len(points)):
    p1 = points[i]
    p2 = points[(i+1) % len(points)]

    # Check if y is approximately constant
    if abs(p1[1] - p2[1]) < 0.1:
        length = abs(p2[0] - p1[0])
        if length > 0.5:  # Ignore tiny segments
            horizontal_segs.append({
                'y': p1[1],
                'x_start': min(p1[0], p2[0]),
                'x_end': max(p1[0], p2[0]),
                'length': length,
                'points': (i, (i+1) % len(points))
            })

# Analyze vertical segments (constant x, varying y)
vertical_segs = []
for i in range(len(points)):
    p1 = points[i]
    p2 = points[(i+1) % len(points)]

    # Check if x is approximately constant
    if abs(p1[0] - p2[0]) < 0.1:
        length = abs(p2[1] - p1[1])
        if length > 0.5:  # Ignore tiny segments
            vertical_segs.append({
                'x': p1[0],
                'y_start': min(p1[1], p2[1]),
                'y_end': max(p1[1], p2[1]),
                'length': length,
                'points': (i, (i+1) % len(points))
            })

print(f"\nHorizontal segments found: {len(horizontal_segs)}")
for i, seg in enumerate(horizontal_segs):
    print(f"  H{i}: y={seg['y']:.3f}, x=[{seg['x_start']:.3f}, {seg['x_end']:.3f}], length={seg['length']:.3f} µm")

print(f"\nVertical segments found: {len(vertical_segs)}")
for i, seg in enumerate(vertical_segs):
    print(f"  V{i}: x={seg['x']:.3f}, y=[{seg['y_start']:.3f}, {seg['y_end']:.3f}], length={seg['length']:.3f} µm")

# Try to identify waveguide width
print("\n" + "="*70)
print("INFERRED PARAMETERS")
print("="*70)

# Look for pairs of parallel segments that might represent waveguide edges
# Horizontal waveguide (along y-axis direction)
h_pairs = []
for i, s1 in enumerate(horizontal_segs):
    for j, s2 in enumerate(horizontal_segs[i+1:], i+1):
        # Check if they overlap in x and are close in y
        x_overlap = min(s1['x_end'], s2['x_end']) - max(s1['x_start'], s2['x_start'])
        y_gap = abs(s1['y'] - s2['y'])
        if x_overlap > 5 and y_gap < 5:
            h_pairs.append({
                'segments': (i, j),
                'width': y_gap,
                'y_mid': (s1['y'] + s2['y']) / 2
            })

# Vertical waveguide (along x-axis direction)
v_pairs = []
for i, s1 in enumerate(vertical_segs):
    for j, s2 in enumerate(vertical_segs[i+1:], i+1):
        # Check if they overlap in y and are close in x
        y_overlap = min(s1['y_end'], s2['y_end']) - max(s1['y_start'], s2['y_start'])
        x_gap = abs(s1['x'] - s2['x'])
        if y_overlap > 5 and x_gap < 5:
            v_pairs.append({
                'segments': (i, j),
                'width': x_gap,
                'x_mid': (s1['x'] + s2['x']) / 2
            })

if h_pairs:
    print(f"\nHorizontal waveguide candidates:")
    for p in h_pairs:
        print(f"  Width: {p['width']:.3f} µm at y={p['y_mid']:.3f}")

if v_pairs:
    print(f"\nVertical waveguide candidates:")
    for p in v_pairs:
        print(f"  Width: {p['width']:.3f} µm at x={p['x_mid']:.3f}")

# Overall dimensions
x_min, x_max = min(xs), max(xs)
y_min, y_max = min(ys), max(ys)
total_width = x_max - x_min
total_height = y_max - y_min

print(f"\nOverall bounding box:")
print(f"  Width: {total_width:.3f} µm")
print(f"  Height: {total_height:.3f} µm")

print("\n" + "="*70)
print("RECOMMENDED PCELL PARAMETERS")
print("="*70)

# Estimate waveguide width from the pairs
if h_pairs or v_pairs:
    all_widths = [p['width'] for p in h_pairs] + [p['width'] for p in v_pairs]
    avg_width = sum(all_widths) / len(all_widths)
    print(f"\nEstimated waveguide width: {avg_width:.3f} µm")

# Estimate taper region
# The crossing extends from center to edges
crossing_extent_x = max(abs(x_max - cx), abs(x_min - cx))
crossing_extent_y = max(abs(y_max - cy), abs(y_min - cy))

print(f"Crossing extent from center:")
print(f"  X direction: ±{crossing_extent_x:.3f} µm")
print(f"  Y direction: ±{crossing_extent_y:.3f} µm")

# Save visualization
fig, ax = plt.subplots(figsize=(10, 10))
xs_closed = xs + [xs[0]]
ys_closed = ys + [ys[0]]
ax.fill(xs_closed, ys_closed, alpha=0.3, color='steelblue')
ax.plot(xs_closed, ys_closed, 'o-', color='navy', markersize=4)

# Mark centroid
ax.plot(cx, cy, 'r*', markersize=15, label='Centroid')

# Number the points
for i, (x, y) in enumerate(points[::5]):  # Show every 5th point to avoid clutter
    ax.text(x, y, str(i*5), fontsize=8, color='red')

ax.set_xlabel('X (µm)')
ax.set_ylabel('Y (µm)')
ax.set_title('Waveguide Crossing - Shape 0001\nwith Point Indices (every 5th)')
ax.grid(True, alpha=0.3)
ax.legend()
ax.set_aspect('equal')

output_file = Path(__file__).parent.parent / 'outputs' / 'crossing_analysis.png'
plt.savefig(output_file, dpi=200, bbox_inches='tight')
print(f"\n✓ Saved visualization: {output_file}")
print("\n" + "="*70)
