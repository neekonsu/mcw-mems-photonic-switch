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
from datetime import datetime
import gdsfactory as gf
import klayout.db as db

# Configure matplotlib for headless operation (no display)
import matplotlib
matplotlib.use('Agg')  # Must be before importing pyplot
import matplotlib.pyplot as plt

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
GDS_FILE = PROJECT_ROOT / "layouts" / "mems_switch_unit.gds"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

def ensure_output_dir():
    """Create outputs directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

def get_timestamp():
    """Generate timestamp string for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

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
    """Generate visualizations using GDSFactory and matplotlib."""
    print("\n" + "="*60)
    print("GENERATING VISUALIZATIONS")
    print("="*60)

    timestamp = get_timestamp()

    # Method 1: Use gdsfactory's plot method with matplotlib
    try:
        print("\nGenerating matplotlib visualization...")
        fig = component.plot()
        output_png = OUTPUT_DIR / f"mems_switch_layout_{timestamp}.png"
        plt.savefig(output_png, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"✓ Saved layout visualization: {output_png}")
    except Exception as e:
        print(f"✗ Matplotlib visualization failed: {e}")

    # Method 2: Create a detailed plot with layer statistics
    try:
        print("\nGenerating layer statistics visualization...")

        # Create a figure showing layer information
        layout = component.kcl
        layers = {}
        for layer_index in layout.layer_indices():
            layer_info = layout.get_info(layer_index)
            layer_key = f"{layer_info.layer}/{layer_info.datatype}"

            # Count shapes on this layer
            cell = component.kdb_cell
            shapes = cell.shapes(layer_index)
            num_shapes = shapes.size()

            if num_shapes > 0:
                layers[layer_key] = num_shapes

        if layers:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Create bar chart of shapes per layer
            layer_names = list(layers.keys())
            shape_counts = list(layers.values())

            ax.bar(range(len(layer_names)), shape_counts, color='steelblue', alpha=0.7)
            ax.set_xticks(range(len(layer_names)))
            ax.set_xticklabels(layer_names, rotation=45, ha='right')
            ax.set_xlabel('Layer (layer/datatype)', fontsize=12)
            ax.set_ylabel('Number of Shapes', fontsize=12)
            ax.set_title('Layer Statistics for MEMS Switch Unit', fontsize=14, fontweight='bold')
            ax.grid(True, axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout()

            output_png = OUTPUT_DIR / f"mems_switch_layer_stats_{timestamp}.png"
            plt.savefig(output_png, dpi=300, bbox_inches='tight')
            plt.close(fig)
            print(f"✓ Saved layer statistics: {output_png}")
        else:
            print(f"Note: No layer data found for statistics")
    except Exception as e:
        print(f"Note: Layer statistics visualization skipped: {e}")

    # Method 3: Export using KLayout's image capabilities (if available)
    try:
        print("\nGenerating KLayout PNG export...")
        # Import KLayout's layout view for image export
        import klayout.lay as lay

        layout = component.kcl
        cell = component.kdb_cell

        # Create a layout view
        lv = lay.LayoutView()
        lv.load_layout(str(GDS_FILE), True)
        lv.max_hier()

        # Save as PNG
        output_png = OUTPUT_DIR / f"mems_switch_klayout_{timestamp}.png"

        # Set image size and save
        lv.save_image(str(output_png), 2000, 2000)
        print(f"✓ Saved KLayout PNG: {output_png}")
    except ImportError:
        print(f"Note: KLayout LAY module not available for PNG export")
    except Exception as e:
        print(f"Note: KLayout PNG export not available: {e}")

    # Write a copy of the GDS to outputs for reference
    try:
        output_gds = OUTPUT_DIR / f"mems_switch_unit_{timestamp}.gds"
        component.write_gds(str(output_gds))
        print(f"✓ Saved GDS copy: {output_gds}")
    except Exception as e:
        print(f"✗ Failed to save GDS copy: {e}")

def export_cell_hierarchy(layout, output_file=None):
    """Export the cell hierarchy to a text file."""
    if output_file is None:
        timestamp = get_timestamp()
        output_file = f"cell_hierarchy_{timestamp}.txt"
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

def create_summary_report(component, layout, top_cells):
    """Create a summary report with key statistics."""
    timestamp = get_timestamp()
    output_file = OUTPUT_DIR / f"analysis_summary_{timestamp}.txt"

    with open(output_file, 'w') as f:
        f.write("="*60 + "\n")
        f.write("GDS FILE ANALYSIS SUMMARY\n")
        f.write("="*60 + "\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"GDS File: {GDS_FILE}\n\n")

        # Component info (GDSFactory)
        f.write("-" * 60 + "\n")
        f.write("COMPONENT INFORMATION (GDSFactory)\n")
        f.write("-" * 60 + "\n")
        f.write(f"Component name: {component.name}\n")

        bbox = component.bbox()
        if bbox and not bbox.empty():
            width = bbox.width()
            height = bbox.height()
            f.write(f"Bounding box: {bbox}\n")
            f.write(f"Width: {width:.3f} µm\n")
            f.write(f"Height: {height:.3f} µm\n")
            f.write(f"Area: {width * height:.3f} µm²\n")

        f.write(f"Number of ports: {len(component.ports)}\n")

        # Layout info (KLayout)
        f.write("\n" + "-" * 60 + "\n")
        f.write("LAYOUT INFORMATION (KLayout)\n")
        f.write("-" * 60 + "\n")
        f.write(f"Database unit: {layout.dbu} µm\n")
        f.write(f"Number of top cells: {len(top_cells)}\n")
        f.write(f"Total cells: {layout.cells()}\n")

        # Layer information
        layers = set()
        for layer_index in layout.layer_indices():
            layer_info = layout.get_info(layer_index)
            layers.add((layer_info.layer, layer_info.datatype))

        f.write(f"Number of layers: {len(layers)}\n")
        f.write("Layers (layer/datatype): ")
        f.write(", ".join([f"{l}/{d}" for l, d in sorted(layers)]))
        f.write("\n")

        # Top cell details
        for top_cell in top_cells:
            f.write(f"\nTop Cell: {top_cell.name}\n")
            bbox = top_cell.bbox()
            if not bbox.empty():
                width_um = bbox.width() * layout.dbu
                height_um = bbox.height() * layout.dbu
                f.write(f"  Size: {width_um:.3f} × {height_um:.3f} µm\n")

            # Count instances
            num_instances = sum(1 for _ in top_cell.each_inst())
            f.write(f"  Instances: {num_instances}\n")

        f.write("\n" + "="*60 + "\n")
        f.write("API VERIFICATION: SUCCESS\n")
        f.write("Both GDSFactory and KLayout APIs loaded the GDS file successfully.\n")
        f.write("="*60 + "\n")

    print(f"\n✓ Saved analysis summary: {output_file}")
    return output_file

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

    # Create summary report
    summary_file = create_summary_report(component, layout, top_cells)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print(f"\n✓ GDS file successfully loaded and analyzed!")
    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    print(f"\nGenerated files:")
    print(f"  • Layout visualization (PNG): mems_switch_layout_*.png")
    print(f"  • Layer statistics (PNG): mems_switch_layer_stats_*.png")
    print(f"  • KLayout export (PNG): mems_switch_klayout_*.png")
    print(f"  • GDS copy: mems_switch_unit_*.gds")
    print(f"  • Cell hierarchy: cell_hierarchy_*.txt")
    print(f"  • Analysis summary: {summary_file.name}")
    print(f"\n🔬 Next steps:")
    print(f"  1. Review the visualizations to verify GDS loading")
    print(f"  2. Check analysis_summary_*.txt for API verification status")
    print(f"  3. Extract components to convert to parametric cells (PCells)")
    print(f"  4. Use gdsfactory to run sweeps/optimizations")

if __name__ == "__main__":
    main()
