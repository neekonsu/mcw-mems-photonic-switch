#!/usr/bin/env python3
"""
Extract all coordinates from Shape 0001 and analyze its geometry.
"""

from pathlib import Path
import klayout.db as db

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
GDS_FILE = PROJECT_ROOT / "layouts" / "mems_switch_unit.gds"

def main():
    # Load GDS
    layout = db.Layout()
    layout.read(str(GDS_FILE))

    # Get the first cell
    cell = layout.top_cell()

    # Find layer 1/0
    layer_index = layout.find_layer(1, 0)
    if layer_index is None:
        print("ERROR: Layer 1/0 not found")
        return

    # Get shapes on this layer
    shapes = cell.shapes(layer_index)

    # Get the first shape (Shape 0001)
    shape_counter = 0
    for shape in shapes.each():
        shape_counter += 1

        if shape_counter == 1:  # This is Shape 0001
            print("="*60)
            print("SHAPE 0001 - COMPLETE COORDINATES")
            print("="*60)

            # Extract all points
            if shape.is_polygon():
                polygon = shape.polygon
                dbu = layout.dbu

                points = []
                for point in polygon.each_point_hull():
                    points.append((point.x * dbu, point.y * dbu))

                print(f"\nTotal points: {len(points)}")
                print(f"Database unit: {dbu} µm\n")

                print("All coordinates (µm):")
                for i, (x, y) in enumerate(points):
                    print(f"  Point {i:2d}: ({x:8.3f}, {y:8.3f})")

                # Analyze geometry
                print("\n" + "="*60)
                print("GEOMETRY ANALYSIS")
                print("="*60)

                xs = [p[0] for p in points]
                ys = [p[1] for p in points]

                print(f"\nX range: {min(xs):.3f} to {max(xs):.3f} µm (width: {max(xs)-min(xs):.3f} µm)")
                print(f"Y range: {min(ys):.3f} to {max(ys):.3f} µm (height: {max(ys)-min(ys):.3f} µm)")

                # Calculate centroid
                cx = sum(xs) / len(xs)
                cy = sum(ys) / len(ys)
                print(f"Centroid: ({cx:.3f}, {cy:.3f}) µm")

                # Try to identify symmetry and structure
                print("\n" + "="*60)
                print("PARAMETRIC ANALYSIS")
                print("="*60)

                # Check for 4-fold rotational symmetry (typical for crossings)
                # Group points by quadrant relative to centroid
                quadrants = {'Q1': [], 'Q2': [], 'Q3': [], 'Q4': []}
                for x, y in points:
                    dx, dy = x - cx, y - cy
                    if dx >= 0 and dy >= 0:
                        quadrants['Q1'].append((x, y))
                    elif dx < 0 and dy >= 0:
                        quadrants['Q2'].append((x, y))
                    elif dx < 0 and dy < 0:
                        quadrants['Q3'].append((x, y))
                    else:
                        quadrants['Q4'].append((x, y))

                for q, pts in quadrants.items():
                    print(f"{q}: {len(pts)} points")

            break

if __name__ == "__main__":
    main()
