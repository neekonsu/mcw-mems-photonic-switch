"""
Lumerical FDTD simulation setup for gap-adjustable directional coupler switch-cell.

This script defines the 3D geometry and simulation parameters for the switch-cell
device using Lumerical's Python API. The switch-cell is based on a gap-adjustable
directional coupler design as described in Han et al., Journal of Optical
Microsystems (2021).

The design features:
- Two directional couplers per unit cell
- MEMS comb-drive actuator for gap adjustment
- 450 nm wide waveguides on 220 nm SOI
- Gap adjustable from 550 nm to near-contact (~0 nm)
- Designed for TE polarization
"""

import numpy as np
import os

try:
    import lumapi
except ImportError:
    print("Warning: lumapi not found. Please ensure Lumerical is installed.")
    print("This script should be run from Lumerical's Python environment.")

# Import geometry definition
from geometry import get_geometry


# ==============================================================================
# FDTD Simulation Setup
# ==============================================================================

def setup_fdtd_simulation(fdtd, geom):
    """
    Set up the FDTD simulation region and parameters for the directional coupler.

    Args:
        fdtd: Lumerical FDTD session object
        geom: DirectionalCouplerGeometry instance
    """
    params = geom.get_parameters_dict()

    # Calculate total device dimensions
    total_length = (params['input_length'] + params['coupling_length'] +
                   params['output_length'] + 4e-6)  # Add 2um margins on each side
    total_width = (params['waveguide_width'] + params['coupling_gap'] +
                  params['waveguide_width'] + 4e-6)  # Add margins
    total_height = params['box_thickness'] + params['device_layer_thickness'] + 2e-6

    # Set up FDTD region
    fdtd.addfdtd()
    fdtd.set('dimension', '3D')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z', params['device_layer_thickness']/2)
    fdtd.set('x span', total_length)
    fdtd.set('y span', total_width)
    fdtd.set('z span', total_height)

    # Mesh settings - auto non-uniform for better performance
    fdtd.set('mesh type', 'auto non-uniform')
    fdtd.set('mesh accuracy', 4)  # High accuracy for coupling
    fdtd.set('min mesh step', 10e-9)  # 10 nm minimum

    # Boundary conditions - PML for all boundaries
    fdtd.set('x min bc', 'PML')
    fdtd.set('x max bc', 'PML')
    fdtd.set('y min bc', 'PML')
    fdtd.set('y max bc', 'PML')
    fdtd.set('z min bc', 'PML')
    fdtd.set('z max bc', 'PML')

    # PML settings
    fdtd.set('pml layers', 12)

    # Simulation time
    fdtd.set('simulation time', 2000e-15)  # 2000 fs for coupling analysis

    print(f"FDTD simulation region configured.")
    print(f"  Coupling gap: {params['coupling_gap']*1e9:.1f} nm ({params['gap_state']} state)")


def create_switch_geometry(fdtd, geom):
    """
    Create the gap-adjustable directional coupler geometry in FDTD.

    Args:
        fdtd: Lumerical FDTD session object
        geom: DirectionalCouplerGeometry instance
    """
    params = geom.get_parameters_dict()
    structures = geom.get_waveguide_structures()

    wg_width = params['waveguide_width']
    wg_height = params['waveguide_height']
    gap = params['coupling_gap']
    coupling_length = params['coupling_length']

    # Add Si substrate
    fdtd.addrect()
    fdtd.set('name', 'Si_substrate')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z min', -params['box_thickness'] - params['substrate_thickness']/2)
    fdtd.set('z max', -params['box_thickness'])
    fdtd.set('x span', 100e-6)
    fdtd.set('y span', 100e-6)
    fdtd.set('material', params['substrate_material'])

    # Add BOX layer (buried oxide - 3 μm)
    fdtd.addrect()
    fdtd.set('name', 'BOX')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z min', -params['box_thickness'])
    fdtd.set('z max', 0)
    fdtd.set('x span', 100e-6)
    fdtd.set('y span', 100e-6)
    fdtd.set('material', params['box_material'])

    # Add top cladding (air or oxide)
    fdtd.addrect()
    fdtd.set('name', 'cladding')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z min', 0)
    fdtd.set('z max', 2e-6)
    fdtd.set('x span', 100e-6)
    fdtd.set('y span', 100e-6)
    fdtd.set('index', params['cladding_index'])

    # Waveguide positions (centered at y=0, separated by gap)
    y_offset = (wg_width + gap) / 2

    # ==== Waveguide 1 (top) ====
    # Input section
    fdtd.addrect()
    fdtd.set('name', 'wg1_input')
    fdtd.set('x', -coupling_length/2 - params['input_length']/2)
    fdtd.set('y', y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', params['input_length'])
    fdtd.set('y span', wg_width)
    fdtd.set('z span', wg_height)
    fdtd.set('material', params['core_material'])

    # Coupling section
    fdtd.addrect()
    fdtd.set('name', 'wg1_coupling')
    fdtd.set('x', 0)
    fdtd.set('y', y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', coupling_length)
    fdtd.set('y span', wg_width)
    fdtd.set('z span', wg_height)
    fdtd.set('material', params['core_material'])

    # Output section
    fdtd.addrect()
    fdtd.set('name', 'wg1_output')
    fdtd.set('x', coupling_length/2 + params['output_length']/2)
    fdtd.set('y', y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', params['output_length'])
    fdtd.set('y span', wg_width)
    fdtd.set('z span', wg_height)
    fdtd.set('material', params['core_material'])

    # ==== Waveguide 2 (bottom) ====
    # Input section
    fdtd.addrect()
    fdtd.set('name', 'wg2_input')
    fdtd.set('x', -coupling_length/2 - params['input_length']/2)
    fdtd.set('y', -y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', params['input_length'])
    fdtd.set('y span', wg_width)
    fdtd.set('z span', wg_height)
    fdtd.set('material', params['core_material'])

    # Coupling section
    fdtd.addrect()
    fdtd.set('name', 'wg2_coupling')
    fdtd.set('x', 0)
    fdtd.set('y', -y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', coupling_length)
    fdtd.set('y span', wg_width)
    fdtd.set('z span', wg_height)
    fdtd.set('material', params['core_material'])

    # Output section
    fdtd.addrect()
    fdtd.set('name', 'wg2_output')
    fdtd.set('x', coupling_length/2 + params['output_length']/2)
    fdtd.set('y', -y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', params['output_length'])
    fdtd.set('y span', wg_width)
    fdtd.set('z span', wg_height)
    fdtd.set('material', params['core_material'])

    print(f"Gap-adjustable directional coupler geometry created.")
    print(f"  Waveguide width: {wg_width*1e9:.0f} nm")
    print(f"  Coupling length: {coupling_length*1e6:.0f} μm")
    print(f"  Coupling gap: {gap*1e9:.0f} nm")


def add_sources_and_monitors(fdtd, geom):
    """
    Add mode sources and monitors for coupling analysis.

    Args:
        fdtd: Lumerical FDTD session object
        geom: DirectionalCouplerGeometry instance
    """
    params = geom.get_parameters_dict()

    wg_width = params['waveguide_width']
    wg_height = params['waveguide_height']
    gap = params['coupling_gap']
    y_offset = geom.y_offset

    # Add mode source at input waveguide 1 (top)
    fdtd.addmode()
    fdtd.set('name', 'source')
    fdtd.set('injection axis', 'x-axis')
    fdtd.set('direction', 'Forward')
    fdtd.set('x', -params['coupling_length']/2 - params['input_length'] + 1e-6)
    fdtd.set('y', y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('y span', wg_width + 1e-6)
    fdtd.set('z span', wg_height + 1.5e-6)
    fdtd.set('mode selection', 'fundamental TE mode')
    fdtd.set('wavelength start', params['wavelength_center'] - params['wavelength_span']/2)
    fdtd.set('wavelength stop', params['wavelength_center'] + params['wavelength_span']/2)

    # Add field monitor for optimization (covers entire coupling region)
    fdtd.addpower()
    fdtd.set('name', 'opt_fields')
    fdtd.set('monitor type', '3D')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', params['coupling_length'] + 4e-6)
    fdtd.set('y span', 2 * y_offset + 2e-6)
    fdtd.set('z span', wg_height + 1e-6)

    # Add mode expansion monitors at outputs for transmission measurement
    # Output port 1 (through port - top waveguide)
    fdtd.addmodeexpansion()
    fdtd.set('name', 'output_through')
    fdtd.set('monitor type', '2D X-normal')
    fdtd.set('x', params['coupling_length']/2 + params['output_length'] - 1e-6)
    fdtd.set('y', y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('y span', wg_width + 1e-6)
    fdtd.set('z span', wg_height + 1.5e-6)
    fdtd.set('mode selection', 'fundamental TE mode')

    # Output port 2 (cross port - bottom waveguide)
    fdtd.addmodeexpansion()
    fdtd.set('name', 'output_cross')
    fdtd.set('monitor type', '2D X-normal')
    fdtd.set('x', params['coupling_length']/2 + params['output_length'] - 1e-6)
    fdtd.set('y', -y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('y span', wg_width + 1e-6)
    fdtd.set('z span', wg_height + 1.5e-6)
    fdtd.set('mode selection', 'fundamental TE mode')

    # Add XY profile monitor at mid-height for field visualization
    fdtd.addprofile()
    fdtd.set('name', 'profile_xy')
    fdtd.set('monitor type', '2D Z-normal')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', params['coupling_length'] + params['input_length'] + params['output_length'])
    fdtd.set('y span', 2 * y_offset + 2e-6)

    # Add XZ profile monitor to see vertical confinement
    fdtd.addprofile()
    fdtd.set('name', 'profile_xz')
    fdtd.set('monitor type', '2D Y-normal')
    fdtd.set('x', 0)
    fdtd.set('y', y_offset)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', params['coupling_length'] + 2e-6)
    fdtd.set('z span', params['box_thickness'] + wg_height + 1e-6)

    # Add fine mesh override in coupling region for accurate coupling calculation
    fdtd.addmesh()
    fdtd.set('name', 'mesh_coupling')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z', wg_height/2)
    fdtd.set('x span', params['coupling_length'] + 1e-6)
    fdtd.set('y span', 2 * y_offset + 1e-6)
    fdtd.set('z span', wg_height + 500e-9)
    fdtd.set('dx', 15e-9)  # 15 nm mesh in coupling region
    fdtd.set('dy', 15e-9)
    fdtd.set('dz', 15e-9)

    print("Sources and monitors added.")
    print(f"  Mode source: TE mode at {params['wavelength_center']*1e9:.0f} nm")
    print(f"  Monitors: through port and cross port transmission")


# ==============================================================================
# Main Simulation Function
# ==============================================================================

def run_switch_cell_simulation(gap_state='off', save_path=None, hide_gui=True):
    """
    Run the complete gap-adjustable directional coupler FDTD simulation.

    Args:
        gap_state (str): 'off' (550nm gap) or 'on' (near-contact gap)
        save_path (str): Path to save the simulation file
        hide_gui (bool): Run in background without GUI

    Returns:
        dict: Simulation results including transmission coefficients
    """
    # Initialize FDTD session
    fdtd = lumapi.FDTD(hide=hide_gui)

    # Get geometry definition
    geom = get_geometry(gap_state=gap_state)
    params = geom.get_parameters_dict()

    # Setup simulation
    setup_fdtd_simulation(fdtd, geom)

    # Create geometry
    create_switch_geometry(fdtd, geom)

    # Add sources and monitors
    add_sources_and_monitors(fdtd, geom)

    # Save simulation file
    if save_path:
        fdtd.save(save_path)
        print(f"Simulation saved to: {save_path}")

    # Run simulation
    print("\nRunning FDTD simulation...")
    fdtd.run()
    print("Simulation complete.")

    # Extract results
    print("\nExtracting results...")
    results = {
        'transmission_through': fdtd.getresult('output_through', 'expansion for output_through'),
        'transmission_cross': fdtd.getresult('output_cross', 'expansion for output_cross'),
        'E_field': fdtd.getresult('opt_fields', 'E'),
        'profile_xy': fdtd.getresult('profile_xy', 'E'),
        'profile_xz': fdtd.getresult('profile_xz', 'E'),
        'gap_state': gap_state,
        'coupling_gap': params['coupling_gap'],
    }

    # Close session
    fdtd.close()

    return results


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Gap-Adjustable Directional Coupler FDTD Simulation")
    print("Based on Han et al., J. Optical Microsystems (2021)")
    print("=" * 70)

    # Create results directory
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # You can simulate either OFF state (550nm gap) or ON state (50nm gap)
    # Change gap_state to 'on' to simulate the ON state
    gap_state = 'off'  # Options: 'off' or 'on'

    # Run simulation
    save_file = os.path.join(results_dir, f"switch_cell_{gap_state}.fsp")

    try:
        print(f"\nSimulating {gap_state.upper()} state...")
        results = run_switch_cell_simulation(
            gap_state=gap_state,
            save_path=save_file,
            hide_gui=False
        )
        print("\nSimulation completed successfully!")
        print(f"Results saved to: {results_dir}")
        print(f"Coupling gap: {results['coupling_gap']*1e9:.1f} nm")
    except Exception as e:
        print(f"\nError during simulation: {e}")
        raise
