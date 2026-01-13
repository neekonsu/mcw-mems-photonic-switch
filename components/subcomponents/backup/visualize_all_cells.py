#!/usr/bin/env python3
"""
Visualize all individual shapes in a GDS file.

This script loads a GDS file and generates a separate visualization for each
individual shape (polygon, path, text, etc.), saving them in a timestamped folder.
This helps understand the primitive geometric elements of the design and plan
component extraction.

Features:
- Creates timestamped output folder
- Generates individual PNG for each shape
- Creates shape metadata files
- Produces an index/summary HTML file organized by layer
- Shows shape types, coordinates, and geometry details
"""

import os
from pathlib import Path
from datetime import datetime
import gdsfactory as gf
import klayout.db as db

# Configure matplotlib for headless operation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
GDS_FILE = PROJECT_ROOT / "layouts" / "mems_switch_unit.gds"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

def get_timestamp():
    """Generate timestamp string for folder names."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def create_output_folder():
    """Create timestamped output folder for this analysis run."""
    timestamp = get_timestamp()
    folder_name = f"cell_analysis_{timestamp}"
    output_path = OUTPUT_DIR / folder_name
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Created output folder: {output_path}")
    return output_path

def sanitize_filename(name):
    """Sanitize cell name for use as filename."""
    # Replace characters that might cause issues in filenames
    safe_name = name.replace("/", "_").replace("\\", "_").replace(":", "_")
    safe_name = safe_name.replace(" ", "_").replace("<", "_").replace(">", "_")
    return safe_name

def get_shape_type_name(shape):
    """Get human-readable name for shape type."""
    if shape.is_polygon():
        return "Polygon"
    elif shape.is_path():
        return "Path"
    elif shape.is_box():
        return "Box"
    elif shape.is_text():
        return "Text"
    elif shape.is_edge():
        return "Edge"
    else:
        return "Unknown"

def get_shape_points(shape, dbu):
    """Extract points from a shape and convert to microns."""
    points = []

    if shape.is_polygon():
        polygon = shape.polygon
        # Access hull points for KLayout Polygon
        for point in polygon.each_point_hull():
            points.append((point.x * dbu, point.y * dbu))
    elif shape.is_box():
        box = shape.box
        # Convert box to polygon manually
        polygon = db.Polygon(box)
        for point in polygon.each_point_hull():
            points.append((point.x * dbu, point.y * dbu))
    elif shape.is_path():
        path = shape.path
        # Access points for KLayout Path
        for point in path.each_point():
            points.append((point.x * dbu, point.y * dbu))
    elif shape.is_edge():
        edge = shape.edge
        points.append((edge.x1 * dbu, edge.y1 * dbu))
        points.append((edge.x2 * dbu, edge.y2 * dbu))

    return points

def visualize_shape(shape, shape_id, layer_info, layout, output_folder):
    """Generate visualization of a single shape using matplotlib."""
    output_png = output_folder / f"shape_{shape_id:04d}_L{layer_info[0]}_{layer_info[1]}.png"

    try:
        fig, ax = plt.subplots(figsize=(8, 8))

        # Get shape points
        points = get_shape_points(shape, layout.dbu)

        if not points:
            plt.close('all')
            return False, None

        # Extract x and y coordinates
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        # Plot the shape
        shape_type = get_shape_type_name(shape)

        if shape.is_polygon() or shape.is_box():
            # Close the polygon for plotting
            xs_closed = xs + [xs[0]]
            ys_closed = ys + [ys[0]]
            ax.fill(xs_closed, ys_closed, alpha=0.6, color='steelblue', edgecolor='navy', linewidth=2)
            ax.plot(xs_closed, ys_closed, 'o-', color='navy', markersize=4)
        elif shape.is_path():
            ax.plot(xs, ys, 'o-', color='steelblue', linewidth=2, markersize=4)
        elif shape.is_edge():
            ax.plot(xs, ys, 'o-', color='red', linewidth=2, markersize=6)

        # Calculate bounds for consistent view
        if xs and ys:
            x_range = max(xs) - min(xs)
            y_range = max(ys) - min(ys)
            margin = max(x_range, y_range) * 0.1 if max(x_range, y_range) > 0 else 1

            ax.set_xlim(min(xs) - margin, max(xs) + margin)
            ax.set_ylim(min(ys) - margin, max(ys) + margin)

        # Add title and labels
        ax.set_title(f"Shape {shape_id:04d} | Layer {layer_info[0]}/{layer_info[1]} | {shape_type}\n" +
                    f"Points: {len(points)}",
                    fontsize=11, fontweight='bold')
        ax.set_xlabel("X (µm)", fontsize=10)
        ax.set_ylabel("Y (µm)", fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_aspect('equal')

        plt.tight_layout()
        plt.savefig(output_png, dpi=200, bbox_inches='tight')
        plt.close('all')

        return True, output_png.name
    except Exception as e:
        plt.close('all')
        print(f"  Warning: Visualization failed for shape {shape_id}: {e}")
        return False, None

def get_shape_metadata(shape, shape_id, layer_info, cell_name, layout):
    """Extract metadata about a shape."""
    dbu = layout.dbu
    shape_type = get_shape_type_name(shape)
    points = get_shape_points(shape, dbu)

    metadata = {
        'shape_id': shape_id,
        'cell_name': cell_name,
        'layer': layer_info[0],
        'datatype': layer_info[1],
        'type': shape_type,
        'num_points': len(points),
        'points': points,
        'bbox': None,
        'width_um': 0,
        'height_um': 0,
        'area_um2': 0,
        'perimeter_um': 0
    }

    # Calculate bounding box
    if points:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        metadata['bbox'] = f"({min_x:.3f}, {min_y:.3f}) to ({max_x:.3f}, {max_y:.3f})"
        metadata['width_um'] = max_x - min_x
        metadata['height_um'] = max_y - min_y

    # Calculate area and perimeter for polygons and boxes
    if shape.is_polygon():
        polygon = shape.polygon
        # Area in square microns
        metadata['area_um2'] = polygon.area() * (dbu ** 2)
        # Perimeter in microns
        metadata['perimeter_um'] = polygon.perimeter() * dbu
    elif shape.is_box():
        box = shape.box
        # Convert box to polygon for area/perimeter
        polygon = db.Polygon(box)
        metadata['area_um2'] = polygon.area() * (dbu ** 2)
        metadata['perimeter_um'] = polygon.perimeter() * dbu

    return metadata

def save_shape_metadata(metadata, output_folder):
    """Save shape metadata to a text file."""
    output_file = output_folder / f"shape_{metadata['shape_id']:04d}_L{metadata['layer']}_{metadata['datatype']}_info.txt"

    with open(output_file, 'w') as f:
        f.write("="*60 + "\n")
        f.write(f"SHAPE METADATA: Shape {metadata['shape_id']:04d}\n")
        f.write("="*60 + "\n\n")

        f.write(f"Shape ID: {metadata['shape_id']:04d}\n")
        f.write(f"Cell: {metadata['cell_name']}\n")
        f.write(f"Layer: {metadata['layer']}/{metadata['datatype']}\n")
        f.write(f"Type: {metadata['type']}\n\n")

        f.write("GEOMETRY:\n")
        f.write("-" * 60 + "\n")
        if metadata['bbox']:
            f.write(f"Bounding Box: {metadata['bbox']}\n")
            f.write(f"Width: {metadata['width_um']:.3f} µm\n")
            f.write(f"Height: {metadata['height_um']:.3f} µm\n")

        if metadata['area_um2'] > 0:
            f.write(f"Area: {metadata['area_um2']:.6f} µm²\n")
        if metadata['perimeter_um'] > 0:
            f.write(f"Perimeter: {metadata['perimeter_um']:.3f} µm\n")

        f.write(f"\nNumber of Points: {metadata['num_points']}\n")

        if metadata['points'] and metadata['num_points'] <= 20:
            f.write("\nCoordinates (µm):\n")
            for i, (x, y) in enumerate(metadata['points']):
                f.write(f"  Point {i}: ({x:.3f}, {y:.3f})\n")
        elif metadata['num_points'] > 20:
            f.write("\nCoordinates (first 10 and last 10 points in µm):\n")
            for i, (x, y) in enumerate(metadata['points'][:10]):
                f.write(f"  Point {i}: ({x:.3f}, {y:.3f})\n")
            f.write(f"  ... ({metadata['num_points'] - 20} points omitted) ...\n")
            for i, (x, y) in enumerate(metadata['points'][-10:], metadata['num_points']-10):
                f.write(f"  Point {i}: ({x:.3f}, {y:.3f})\n")

        f.write("\n" + "="*60 + "\n")

    return output_file.name

def create_index_html(shape_data_list, output_folder, gds_file):
    """Create an HTML index file for easy navigation of all shapes."""
    html_file = output_folder / "index.html"

    # Organize shapes by layer
    shapes_by_layer = {}
    for shape_data in shape_data_list:
        layer_key = f"{shape_data['metadata']['layer']}/{shape_data['metadata']['datatype']}"
        if layer_key not in shapes_by_layer:
            shapes_by_layer[layer_key] = []
        shapes_by_layer[layer_key].append(shape_data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GDS Shape Analysis - {gds_file.name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007acc;
            padding-bottom: 10px;
        }}
        .metadata {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .shape-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .shape-card {{
            background: white;
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .shape-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .shape-name {{
            font-size: 16px;
            font-weight: bold;
            color: #007acc;
            margin-bottom: 8px;
        }}
        .shape-info {{
            font-size: 13px;
            color: #666;
            margin: 3px 0;
        }}
        .shape-image {{
            margin-top: 10px;
        }}
        .shape-image img {{
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
        }}
        .layer-section {{
            margin-bottom: 40px;
        }}
        .layer-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .layer-title {{
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }}
        .layer-stats {{
            font-size: 14px;
            margin-top: 5px;
            opacity: 0.9;
        }}
        .links {{
            margin-top: 10px;
            font-size: 12px;
        }}
        .links a {{
            color: #007acc;
            text-decoration: none;
            margin-right: 10px;
        }}
        .links a:hover {{
            text-decoration: underline;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }}
        .stat-box {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #007acc;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        .shape-type {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 5px;
        }}
    </style>
</head>
<body>
    <h1>GDS Shape Analysis</h1>

    <div class="metadata">
        <h2>File Information</h2>
        <p><strong>GDS File:</strong> {gds_file}</p>
        <p><strong>Analysis Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Shapes:</strong> {len(shape_data_list)}</p>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{len(shape_data_list)}</div>
                <div class="stat-label">Total Shapes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(shapes_by_layer)}</div>
                <div class="stat-label">Layers</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{sum(1 for s in shape_data_list if s['metadata']['type'] == 'Polygon')}</div>
                <div class="stat-label">Polygons</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{sum(1 for s in shape_data_list if s['metadata']['type'] == 'Path')}</div>
                <div class="stat-label">Paths</div>
            </div>
        </div>
    </div>
"""

    # Add shapes organized by layer
    for layer_key in sorted(shapes_by_layer.keys()):
        layer_shapes = shapes_by_layer[layer_key]
        html_content += f"""
    <div class="layer-section">
        <div class="layer-header">
            <h2 class="layer-title">Layer {layer_key}</h2>
            <div class="layer-stats">{len(layer_shapes)} shapes</div>
        </div>
        <div class="shape-grid">
"""

        for shape_data in layer_shapes:
            meta = shape_data['metadata']
            shape_type_label = f'<span class="shape-type">{meta["type"]}</span>'

            html_content += f"""
            <div class="shape-card">
                <div class="shape-name">Shape {meta['shape_id']:04d} {shape_type_label}</div>
                <div class="shape-info">Size: {meta['width_um']:.2f} × {meta['height_um']:.2f} µm</div>
                <div class="shape-info">Points: {meta['num_points']}</div>
"""

            if meta['area_um2'] > 0:
                html_content += f"""                <div class="shape-info">Area: {meta['area_um2']:.3f} µm²</div>
"""

            # Add image
            if shape_data['image']:
                html_content += f"""
                <div class="shape-image">
                    <img src="{shape_data['image']}" alt="Shape {meta['shape_id']:04d}" onclick="window.open('{shape_data['image']}', '_blank')">
                </div>
"""

            # Add link to metadata file
            html_content += f"""
                <div class="links">
                    <a href="{shape_data['metadata_file']}" target="_blank">📄 View Details</a>
                </div>
            </div>
"""

        html_content += """
        </div>
    </div>
"""

    html_content += """
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; text-align: center;">
        Generated by visualize_all_cells.py | Tower Semiconductor MEMS Switch Tapeout
    </div>
</body>
</html>
"""

    with open(html_file, 'w') as f:
        f.write(html_content)

    print(f"\n✓ Created HTML index: {html_file.name}")
    return html_file

def main():
    """Main function to visualize all shapes in the GDS file."""
    print("="*60)
    print("GDS SHAPE VISUALIZATION TOOL")
    print("="*60)
    print(f"\nGDS File: {GDS_FILE}")

    if not GDS_FILE.exists():
        print(f"ERROR: GDS file not found at {GDS_FILE}")
        return

    # Create output folder
    output_folder = create_output_folder()

    # Load the GDS file with KLayout
    print("\nLoading GDS file with KLayout...")
    layout = db.Layout()
    layout.read(str(GDS_FILE))

    # Count total shapes across all cells
    total_shapes = 0
    shapes_by_layer = {}

    for cell in layout.each_cell():
        for layer_index in layout.layer_indices():
            shapes = cell.shapes(layer_index)
            num_shapes = shapes.size()
            if num_shapes > 0:
                layer_info = layout.get_info(layer_index)
                layer_key = f"{layer_info.layer}/{layer_info.datatype}"
                shapes_by_layer[layer_key] = shapes_by_layer.get(layer_key, 0) + num_shapes
                total_shapes += num_shapes

    print(f"Found {total_shapes} total shapes across {len(shapes_by_layer)} layers")
    for layer_key, count in sorted(shapes_by_layer.items()):
        print(f"  Layer {layer_key}: {count} shapes")

    # Collect all shape data
    shape_data_list = []
    shape_counter = 0

    print("\nProcessing shapes...")
    print("-" * 60)

    # Iterate through all cells
    for cell in layout.each_cell():
        print(f"\nProcessing cell: {cell.name}")

        # Iterate through all layers
        for layer_index in layout.layer_indices():
            layer_info_obj = layout.get_info(layer_index)
            layer_info = (layer_info_obj.layer, layer_info_obj.datatype)

            shapes = cell.shapes(layer_index)
            if shapes.size() == 0:
                continue

            # Iterate through all shapes on this layer
            for shape in shapes.each():
                shape_counter += 1

                if shape_counter % 10 == 0:
                    print(f"  Processing shape {shape_counter}/{total_shapes}...", end='\r')

                # Get shape metadata
                metadata = get_shape_metadata(shape, shape_counter, layer_info, cell.name, layout)

                # Save metadata file
                metadata_file = save_shape_metadata(metadata, output_folder)

                # Visualize the shape
                success, image_file = visualize_shape(shape, shape_counter, layer_info, layout, output_folder)

                # Store shape data for index
                shape_data_list.append({
                    'metadata': metadata,
                    'metadata_file': metadata_file,
                    'image': image_file if success else None
                })

    print(f"\n  Processed all {shape_counter} shapes!")

    # Create HTML index
    print("\n" + "="*60)
    print("CREATING INDEX")
    print("="*60)
    html_file = create_index_html(shape_data_list, output_folder, GDS_FILE)

    # Final summary
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print(f"\n✓ All shapes visualized successfully!")
    print(f"\n📁 Output folder: {output_folder}")
    print(f"\n📊 Summary:")
    print(f"  • Total shapes processed: {len(shape_data_list)}")

    # Count shape types
    shape_types = {}
    for shape_data in shape_data_list:
        shape_type = shape_data['metadata']['type']
        shape_types[shape_type] = shape_types.get(shape_type, 0) + 1

    for shape_type, count in sorted(shape_types.items()):
        print(f"  • {shape_type}s: {count}")

    print(f"  • Layers: {len(shapes_by_layer)}")

    print(f"\n🌐 Open the index file to view all shapes:")
    print(f"  open {output_folder}/index.html")
    print(f"\n🔬 Next steps:")
    print(f"  1. Review index.html to see all shapes organized by layer")
    print(f"  2. Identify groups of shapes that form functional components")
    print(f"  3. Note shape IDs and coordinates for component extraction")
    print(f"  4. Use gdsfactory to select and recreate components as PCells")

if __name__ == "__main__":
    main()
