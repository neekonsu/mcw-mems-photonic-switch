#!/usr/bin/env python3
"""
Visualize all parameter sweep variants and generate an interactive HTML index.

This script loads all GDS files from the sweeps/ folder, generates visualizations,
and creates an HTML index for easy comparison and selection.
"""

import os
from pathlib import Path
from datetime import datetime
import gdsfactory as gf

# Configure matplotlib for headless operation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
SWEEPS_DIR = PROJECT_ROOT / "outputs" / "sweeps"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "sweep_visualization"

def get_timestamp():
    """Generate timestamp string for folder names."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def create_output_folder():
    """Create timestamped output folder for visualizations."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    return OUTPUT_DIR

def parse_filename(filename):
    """Extract sweep parameters from filename."""
    stem = filename.stem

    # Parse different filename patterns
    if stem.startswith("crossing_cw_"):
        # Center width sweep
        param = stem.replace("crossing_cw_", "").replace("um", "")
        return {
            'type': 'center_width',
            'value': param,
            'display': f"Center Width: {param} µm",
            'sort_key': float(param)
        }
    elif stem.startswith("crossing_tl_"):
        # Taper length sweep
        param = stem.replace("crossing_tl_", "").replace("um", "")
        return {
            'type': 'taper_length',
            'value': param,
            'display': f"Taper Length: {param} µm",
            'sort_key': float(param)
        }
    elif stem.startswith("crossing_n"):
        # Number of sections sweep
        param = stem.replace("crossing_n", "").replace(".gds", "")
        return {
            'type': 'num_sections',
            'value': param,
            'display': f"{int(param)} Taper Sections",
            'sort_key': int(param)
        }
    elif "quadratic" in stem:
        return {
            'type': 'custom',
            'value': 'quadratic',
            'display': "Quadratic Taper Profile",
            'sort_key': 0
        }
    else:
        return {
            'type': 'unknown',
            'value': stem,
            'display': stem,
            'sort_key': 0
        }

def visualize_crossing(gds_file, output_folder):
    """Generate visualization of a crossing GDS file."""
    try:
        # Load the GDS
        component = gf.import_gds(str(gds_file))

        # Generate plot
        fig = component.plot()

        # Customize
        ax = plt.gca()
        ax.set_title(f"{gds_file.stem}", fontsize=12, fontweight='bold')
        ax.set_xlabel("X (µm)", fontsize=10)
        ax.set_ylabel("Y (µm)", fontsize=10)
        ax.grid(True, alpha=0.3)

        # Save
        output_png = output_folder / f"{gds_file.stem}.png"
        plt.savefig(output_png, dpi=200, bbox_inches='tight')
        plt.close('all')

        return True, output_png.name
    except Exception as e:
        print(f"  Warning: Failed to visualize {gds_file.name}: {e}")
        plt.close('all')
        return False, None

def get_gds_metadata(gds_file):
    """Extract metadata from GDS file."""
    try:
        component = gf.import_gds(str(gds_file))
        bbox = component.bbox()

        if bbox and not bbox.empty():
            width = bbox.width()
            height = bbox.height()
            return {
                'width': width,
                'height': height,
                'area': width * height,
                'num_polygons': len(component.get_polygons()),
                'num_ports': len(list(component.ports))
            }
        else:
            return None
    except Exception as e:
        print(f"  Warning: Failed to extract metadata from {gds_file.name}: {e}")
        return None

def create_index_html(sweep_data, output_folder):
    """Create HTML index for all sweep variants."""
    html_file = output_folder / "index.html"

    # Organize by sweep type
    sweeps_by_type = {}
    for data in sweep_data:
        sweep_type = data['params']['type']
        if sweep_type not in sweeps_by_type:
            sweeps_by_type[sweep_type] = []
        sweeps_by_type[sweep_type].append(data)

    # Sort each sweep type by sort_key
    for sweep_type in sweeps_by_type:
        sweeps_by_type[sweep_type].sort(key=lambda x: x['params']['sort_key'])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waveguide Crossing Parameter Sweeps</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1600px;
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
        .sweep-section {{
            margin-bottom: 40px;
        }}
        .sweep-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .sweep-title {{
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }}
        .sweep-stats {{
            font-size: 14px;
            margin-top: 5px;
            opacity: 0.9;
        }}
        .design-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .design-card {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .design-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .design-name {{
            font-size: 16px;
            font-weight: bold;
            color: #007acc;
            margin-bottom: 10px;
        }}
        .design-info {{
            font-size: 13px;
            color: #666;
            margin: 5px 0;
        }}
        .design-image {{
            margin-top: 10px;
        }}
        .design-image img {{
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
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
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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
        .comparison-link {{
            display: inline-block;
            background: #007acc;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            margin-top: 10px;
            transition: background 0.2s;
        }}
        .comparison-link:hover {{
            background: #005a9c;
        }}
    </style>
</head>
<body>
    <h1>Waveguide Crossing Parameter Sweeps</h1>

    <div class="metadata">
        <h2>Sweep Summary</h2>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Designs:</strong> {len(sweep_data)}</p>
        <p><strong>Sweep Types:</strong> {len(sweeps_by_type)}</p>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{len(sweep_data)}</div>
                <div class="stat-label">Total Designs</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(sweeps_by_type)}</div>
                <div class="stat-label">Sweep Types</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{sum(len(v) for v in sweeps_by_type.values())}</div>
                <div class="stat-label">Variants</div>
            </div>
        </div>
    </div>
"""

    # Add each sweep type section
    sweep_type_names = {
        'center_width': 'Center Width Sweep',
        'taper_length': 'Taper Length Sweep',
        'num_sections': 'Number of Sections Sweep',
        'custom': 'Custom Designs',
        'unknown': 'Other Designs'
    }

    for sweep_type in sorted(sweeps_by_type.keys()):
        designs = sweeps_by_type[sweep_type]
        sweep_name = sweep_type_names.get(sweep_type, sweep_type.replace('_', ' ').title())

        html_content += f"""
    <div class="sweep-section">
        <div class="sweep-header">
            <h2 class="sweep-title">{sweep_name}</h2>
            <div class="sweep-stats">{len(designs)} variants</div>
        </div>
        <div class="design-grid">
"""

        for design in designs:
            params = design['params']
            metadata = design['metadata']
            image = design['image']
            gds_file = design['gds_file']

            html_content += f"""
            <div class="design-card">
                <div class="design-name">{params['display']}</div>
"""

            if metadata:
                html_content += f"""
                <div class="design-info">Size: {metadata['width']:.1f} × {metadata['height']:.1f} µm</div>
                <div class="design-info">Area: {metadata['area']:.1f} µm²</div>
                <div class="design-info">Polygons: {metadata['num_polygons']}</div>
"""

            if image:
                html_content += f"""
                <div class="design-image">
                    <img src="{image}" alt="{params['display']}" onclick="window.open('{image}', '_blank')">
                </div>
"""

            html_content += f"""
                <div class="links">
                    <a href="../sweeps/{gds_file}" download>⬇ Download GDS</a>
                </div>
            </div>
"""

        html_content += """
        </div>
    </div>
"""

    html_content += """
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; text-align: center;">
        <p><strong>Next Steps:</strong></p>
        <ol style="text-align: left; max-width: 600px; margin: 20px auto;">
            <li>Download GDS files for designs of interest</li>
            <li>Import into Lumerical FDTD Solutions</li>
            <li>Run optical simulations (TE/TM mode, 1520-1580 nm)</li>
            <li>Extract S-parameters (S21: transmission, S31: crosstalk)</li>
            <li>Compare performance across parameter space</li>
            <li>Select optimal design for tapeout</li>
        </ol>
        <p style="margin-top: 20px;">Generated by visualize_sweeps.py | Tower Semiconductor MEMS Switch Tapeout</p>
    </div>
</body>
</html>
"""

    with open(html_file, 'w') as f:
        f.write(html_content)

    print(f"\n✓ Created HTML index: {html_file.name}")
    return html_file

def main():
    """Main function to visualize all sweep variants."""
    print("="*70)
    print("WAVEGUIDE CROSSING SWEEP VISUALIZER")
    print("="*70)

    # Check if sweeps directory exists
    if not SWEEPS_DIR.exists():
        print(f"\nERROR: Sweeps directory not found: {SWEEPS_DIR}")
        print("Run 'python components/crossing_sweep_example.py' first to generate sweeps.")
        return

    # Get all GDS files
    gds_files = sorted(SWEEPS_DIR.glob("*.gds"))

    if not gds_files:
        print(f"\nERROR: No GDS files found in {SWEEPS_DIR}")
        return

    print(f"\nFound {len(gds_files)} GDS files in sweeps directory")

    # Create output folder
    output_folder = create_output_folder()

    # Process each GDS file
    sweep_data = []

    print("\nProcessing designs...")
    print("-" * 70)

    for idx, gds_file in enumerate(gds_files, 1):
        print(f"\n[{idx}/{len(gds_files)}] Processing: {gds_file.name}")

        # Parse filename
        params = parse_filename(gds_file)
        print(f"  Type: {params['type']}, Value: {params['value']}")

        # Get metadata
        metadata = get_gds_metadata(gds_file)
        if metadata:
            print(f"  Size: {metadata['width']:.1f} × {metadata['height']:.1f} µm")
            print(f"  Polygons: {metadata['num_polygons']}")

        # Visualize
        success, image_file = visualize_crossing(gds_file, output_folder)
        if success:
            print(f"  ✓ Saved visualization: {image_file}")

        # Store data
        sweep_data.append({
            'gds_file': gds_file.name,
            'params': params,
            'metadata': metadata,
            'image': image_file if success else None
        })

    # Create HTML index
    print("\n" + "="*70)
    print("CREATING HTML INDEX")
    print("="*70)
    html_file = create_index_html(sweep_data, output_folder)

    # Final summary
    print("\n" + "="*70)
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print(f"\n✓ All designs visualized successfully!")
    print(f"\n📁 Output folder: {output_folder}")
    print(f"\n📊 Summary:")
    print(f"  • Total designs: {len(sweep_data)}")
    print(f"  • Visualizations: {sum(1 for d in sweep_data if d['image'])}")

    # Count by type
    types = {}
    for d in sweep_data:
        t = d['params']['type']
        types[t] = types.get(t, 0) + 1

    print(f"\n  Designs by type:")
    for sweep_type, count in sorted(types.items()):
        print(f"    • {sweep_type}: {count}")

    print(f"\n🌐 Open the index file to browse all designs:")
    print(f"  open {output_folder}/index.html")

    print(f"\n🔬 Next steps:")
    print(f"  1. Review designs in the interactive HTML browser")
    print(f"  2. Download GDS files for interesting variants")
    print(f"  3. Import into Lumerical FDTD for optical simulation")
    print(f"  4. Compare insertion loss and crosstalk performance")

if __name__ == "__main__":
    main()
