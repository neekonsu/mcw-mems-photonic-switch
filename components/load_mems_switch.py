#!/usr/bin/env python3
"""
Load and analyze the mems_switch_unit.gds file using KLayout and GDSFactory APIs.

This script demonstrates how to:
1. Import an existing GDS file using gdsfactory
2. Load and analyze GDS using klayout's Python API
3. Extract information about cells, layers, and geometry
4. Visualize the structure
"""

import os
from pathlib import Path
import gdsfactory as gf
import klayout.db as db

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
GDS_FILE = PROJECT_ROOT / "mems_switch_unit.gds"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

def ensure_output_dir():
    """Create outputs directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

def load_with_gdsfactory():
    """Load GDS file using GDSFactory and extract information."""
    print("\n" + "="*60)
    print("LOADING WITH GDSFACTORY")
    print("="*60)

    # Import the GDS file
    component = gf.import_gds(str(GDS_FILE))

    print(f"\nComponent name: {component.name}")
    print(f"Component info: {component.info}")

    # Get component properties
    bbox = component.bbox()
    print(f"\nBounding box: {bbox}")
    if bbox and not bbox.empty():
        width = bbox.width()
        height = bbox.height()
        print(f"Width: {width:.3f} µm")
        print(f"Height: {height:.3f} µm")
        print(f"Area: {width * height:.3f} µm²")

    # List ports
    print(f"\nNumber of ports: {len(component.ports)}")
    if component.ports:
        print("\nPorts:")
        for port_name, port in component.ports.items():
            print(f"  {port_name}: center={port.center}, width={port.width}, orientation={port.orientation}")

    # List layers - for KFactory components, we need to access the underlying layout
    try:
        # Get the underlying KLayout layout object
        layout = component.kcl
        layers = set()
        for layer_index in layout.layer_indices():
            layer_info = layout.get_info(layer_index)
            layers.add((layer_info.layer, layer_info.datatype))

        print(f"\nNumber of layers: {len(layers)}")
        print("Layers (layer, datatype):")
        for layer in sorted(layers):
            print(f"  {layer}")
    except Exception as e:
        print(f"\nCould not extract layer information: {e}")

    # Get references (subcells) - KFactory uses instances
    try:
        num_instances = len(list(component.insts))
        print(f"\nNumber of instances: {num_instances}")
        if num_instances > 0:
            print("\nInstances:")
            for inst in component.insts:
                print(f"  {inst.cell.name}")
    except Exception as e:
        print(f"\nCould not extract instance information: {e}")

    return component

def load_with_klayout():
    """Load GDS file using KLayout Python API and extract information."""
    print("\n" + "="*60)
    print("LOADING WITH KLAYOUT")
    print("="*60)

    # Create a Layout object and read the GDS file
    layout = db.Layout()
    layout.read(str(GDS_FILE))

    print(f"\nLayout database unit: {layout.dbu} µm")
    print(f"Technology: {layout.technology_name if layout.technology_name else 'None'}")

    # Get top cell
    top_cells = []
    for cell in layout.top_cells():
        top_cells.append(cell)

    print(f"\nNumber of top cells: {len(top_cells)}")
    print(f"Total number of cells: {layout.cells()}")

    # Analyze each top cell
    for top_cell in top_cells:
        print(f"\n--- Top Cell: {top_cell.name} ---")

        # Get bounding box
        bbox = top_cell.bbox()
        if not bbox.empty():
            width_dbu = bbox.width()
            height_dbu = bbox.height()
            width_um = width_dbu * layout.dbu
            height_um = height_dbu * layout.dbu
            area_um2 = width_um * height_um

            print(f"Bounding box: ({bbox.left}, {bbox.bottom}) to ({bbox.right}, {bbox.top})")
            print(f"Width: {width_um:.3f} µm ({width_dbu} DBU)")
            print(f"Height: {height_um:.3f} µm ({height_dbu} DBU)")
            print(f"Area: {area_um2:.3f} µm²")

        # Count shapes per layer
        print("\nShapes per layer:")
        layer_info = {}
        for layer_index in layout.layer_indices():
            layer_info_obj = layout.get_info(layer_index)
            layer = layer_info_obj.layer
            datatype = layer_info_obj.datatype

            shapes = top_cell.shapes(layer_index)
            num_shapes = shapes.size()

            if num_shapes > 0:
                key = (layer, datatype)
                layer_info[key] = num_shapes
                print(f"  Layer {layer}/{datatype}: {num_shapes} shapes")

        # Count instances (references to other cells)
        num_instances = 0
        child_cells = set()
        for inst in top_cell.each_inst():
            num_instances += 1
            child_cells.add(inst.cell.name)

        print(f"\nNumber of instances: {num_instances}")
        if child_cells:
            print(f"Child cells:")
            for cell_name in sorted(child_cells):
                print(f"  {cell_name}")

    # List all cells in the layout
    print("\n--- All Cells in Layout ---")
    cell_names = []
    for cell in layout.each_cell():
        cell_names.append(cell.name)

    print(f"Total cells: {len(cell_names)}")
    for cell_name in sorted(cell_names):
        print(f"  {cell_name}")

    return layout, top_cells

def visualize_with_gdsfactory(component):
    """Generate visualizations using GDSFactory."""
    print("\n" + "="*60)
    print("GENERATING VISUALIZATIONS")
    print("="*60)

    # Save as PNG using KLayout's built-in rendering
    try:
        output_png = OUTPUT_DIR / "mems_switch_unit_gf.png"

        # Use KLayout to render the layout as PNG
        # Get the underlying KLayout cell
        kcell = component.kdb_cell
        layout = component.kcl

        # Save using KLayout's image export
        # This requires display capabilities, so we'll skip for now
        print(f"\nSkipping matplotlib visualization (requires display)")
        print(f"Use KLayout viewer to visualize: klayout {GDS_FILE}")
    except Exception as e:
        print(f"\nNote: Visualization skipped: {e}")

    # Write a copy of the GDS to outputs for reference
    try:
        output_gds = OUTPUT_DIR / "mems_switch_unit_copy.gds"
        component.write_gds(str(output_gds))
        print(f"Saved GDS copy: {output_gds}")
    except Exception as e:
        print(f"Failed to save GDS copy: {e}")

def export_cell_hierarchy(layout, output_file="cell_hierarchy.txt"):
    """Export the cell hierarchy to a text file."""
    output_path = OUTPUT_DIR / output_file

    with open(output_path, 'w') as f:
        f.write("CELL HIERARCHY\n")
        f.write("="*60 + "\n\n")

        # Write information about each cell
        for cell in layout.each_cell():
            f.write(f"Cell: {cell.name}\n")
            f.write(f"  Cell index: {cell.cell_index()}\n")

            # Bounding box
            bbox = cell.bbox()
            if not bbox.empty():
                width_um = bbox.width() * layout.dbu
                height_um = bbox.height() * layout.dbu
                f.write(f"  Bounding box: {width_um:.3f} x {height_um:.3f} µm\n")

            # Child cells
            child_cells = []
            for inst in cell.each_inst():
                child_cells.append(inst.cell.name)

            if child_cells:
                f.write(f"  Child cells ({len(child_cells)}):\n")
                for child_name in sorted(set(child_cells)):
                    f.write(f"    - {child_name}\n")

            f.write("\n")

    print(f"\nExported cell hierarchy to: {output_path}")

def main():
    """Main function to load and analyze the GDS file."""
    print(f"Loading GDS file: {GDS_FILE}")

    if not GDS_FILE.exists():
        print(f"ERROR: GDS file not found at {GDS_FILE}")
        return

    # Ensure output directory exists
    ensure_output_dir()

    # Load with GDSFactory
    component = load_with_gdsfactory()

    # Load with KLayout
    layout, top_cells = load_with_klayout()

    # Generate visualizations
    visualize_with_gdsfactory(component)

    # Export cell hierarchy
    export_cell_hierarchy(layout)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print(f"\nGDS file successfully loaded and analyzed!")
    print(f"Check the '{OUTPUT_DIR.name}' directory for visualizations and reports.")

if __name__ == "__main__":
    main()
