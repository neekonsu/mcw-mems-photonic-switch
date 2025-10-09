"""
Lumerical FDTD simulation setup for comb-drive component.

This script defines the 3D geometry and simulation parameters for the comb-drive
device using Lumerical's Python API.
"""

import numpy as np
import os

try:
    import lumapi
except ImportError:
    print("Warning: lumapi not found. Please ensure Lumerical is installed.")
    print("This script should be run from Lumerical's Python environment.")


# ==============================================================================
# Geometry Parameters
# ==============================================================================

def get_geometry_params():
    """
    Define the geometry parameters for the comb-drive structure.

    Returns:
        dict: Geometry parameters for the comb-drive
    """
    params = {
        # Comb finger dimensions
        'finger_width': 500e-9,      # 500 nm finger width
        'finger_length': 10e-6,      # 10 um finger length
        'finger_gap': 200e-9,        # 200 nm gap between fingers
        'num_fingers': 10,           # Number of comb fingers
        'finger_height': 220e-9,     # 220 nm device layer thickness

        # Base/anchor dimensions
        'anchor_width': 2e-6,        # 2 um anchor width
        'anchor_length': 5e-6,       # 5 um anchor length

        # Material properties
        'material': 'Si (Silicon) - Palik',  # Silicon for device layer
        'substrate_material': 'SiO2 (Glass) - Palik',  # Oxide substrate
        'index_cladding': 1.0,       # Air cladding

        # Simulation wavelength
        'wavelength': 1550e-9,       # 1550 nm wavelength
    }

    return params


# ==============================================================================
# FDTD Simulation Setup
# ==============================================================================

def setup_fdtd_simulation(fdtd, params):
    """
    Set up the FDTD simulation region and parameters.

    Args:
        fdtd: Lumerical FDTD session object
        params (dict): Geometry parameters
    """
    # Calculate simulation region size
    total_length = params['finger_length'] + params['anchor_length'] + 2e-6  # Add margins
    total_width = (params['num_fingers'] * (params['finger_width'] + params['finger_gap']) +
                   params['anchor_width'] + 2e-6)
    total_height = 3e-6  # 3 um in z-direction

    # Set up FDTD region
    fdtd.addfdtd()
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z', 0)
    fdtd.set('x span', total_length)
    fdtd.set('y span', total_width)
    fdtd.set('z span', total_height)

    # Mesh settings
    fdtd.set('mesh type', 'auto non-uniform')
    fdtd.set('mesh accuracy', 3)  # Higher accuracy
    fdtd.set('min mesh step', 10e-9)  # 10 nm minimum mesh

    # Boundary conditions
    fdtd.set('x min bc', 'PML')
    fdtd.set('x max bc', 'PML')
    fdtd.set('y min bc', 'PML')
    fdtd.set('y max bc', 'PML')
    fdtd.set('z min bc', 'PML')
    fdtd.set('z max bc', 'PML')

    # Simulation time
    fdtd.set('simulation time', 1000e-15)  # 1000 fs

    print("FDTD simulation region configured.")


def create_comb_geometry(fdtd, params):
    """
    Create the comb-drive geometry in FDTD.

    Args:
        fdtd: Lumerical FDTD session object
        params (dict): Geometry parameters
    """
    finger_width = params['finger_width']
    finger_length = params['finger_length']
    finger_gap = params['finger_gap']
    num_fingers = params['num_fingers']
    finger_height = params['finger_height']
    material = params['material']

    # Create substrate
    fdtd.addrect()
    fdtd.set('name', 'substrate')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z', -500e-9)  # Below device layer
    fdtd.set('x span', 50e-6)
    fdtd.set('y span', 50e-6)
    fdtd.set('z span', 2e-6)
    fdtd.set('material', params['substrate_material'])

    # Create anchor structure
    fdtd.addrect()
    fdtd.set('name', 'anchor')
    fdtd.set('x', -params['anchor_length']/2)
    fdtd.set('y', 0)
    fdtd.set('z', finger_height/2)
    fdtd.set('x span', params['anchor_length'])
    fdtd.set('y span', params['anchor_width'])
    fdtd.set('z span', finger_height)
    fdtd.set('material', material)

    # Create comb fingers
    for i in range(num_fingers):
        y_position = -(num_fingers - 1) * (finger_width + finger_gap) / 2 + i * (finger_width + finger_gap)

        fdtd.addrect()
        fdtd.set('name', f'finger_{i+1}')
        fdtd.set('x', finger_length/2)
        fdtd.set('y', y_position)
        fdtd.set('z', finger_height/2)
        fdtd.set('x span', finger_length)
        fdtd.set('y span', finger_width)
        fdtd.set('z span', finger_height)
        fdtd.set('material', material)

    print(f"Created comb-drive geometry with {num_fingers} fingers.")


def add_sources_and_monitors(fdtd, params):
    """
    Add optical sources and field monitors to the simulation.

    Args:
        fdtd: Lumerical FDTD session object
        params (dict): Geometry parameters
    """
    wavelength = params['wavelength']

    # Add dipole source (for excitation)
    fdtd.adddipole()
    fdtd.set('name', 'dipole_source')
    fdtd.set('x', -params['anchor_length'])
    fdtd.set('y', 0)
    fdtd.set('z', params['finger_height']/2)
    fdtd.set('theta', 0)  # Polarization angle
    fdtd.set('phi', 0)
    fdtd.set('wavelength start', wavelength - 100e-9)
    fdtd.set('wavelength stop', wavelength + 100e-9)

    # Add mesh override region around comb fingers
    fdtd.addmesh()
    fdtd.set('name', 'mesh_override_comb')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z', params['finger_height']/2)
    fdtd.set('x span', params['finger_length'] + 1e-6)
    fdtd.set('y span', params['num_fingers'] * (params['finger_width'] + params['finger_gap']))
    fdtd.set('z span', params['finger_height'] + 500e-9)
    fdtd.set('dx', 20e-9)  # 20 nm mesh
    fdtd.set('dy', 20e-9)
    fdtd.set('dz', 20e-9)

    # Add field monitor (required for optimization)
    fdtd.addpower()
    fdtd.set('name', 'opt_fields')
    fdtd.set('monitor type', '3D')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z', params['finger_height']/2)
    fdtd.set('x span', params['finger_length'] + 2e-6)
    fdtd.set('y span', params['num_fingers'] * (params['finger_width'] + params['finger_gap']) + 1e-6)
    fdtd.set('z span', params['finger_height'] + 1e-6)

    # Add profile monitor for field visualization
    fdtd.addprofile()
    fdtd.set('name', 'profile_xy')
    fdtd.set('monitor type', '2D Z-normal')
    fdtd.set('x', 0)
    fdtd.set('y', 0)
    fdtd.set('z', params['finger_height']/2)
    fdtd.set('x span', params['finger_length'] + 2e-6)
    fdtd.set('y span', params['num_fingers'] * (params['finger_width'] + params['finger_gap']) + 1e-6)

    print("Sources and monitors added.")


# ==============================================================================
# Main Simulation Function
# ==============================================================================

def run_comb_drive_simulation(save_path=None, hide_gui=True):
    """
    Run the complete comb-drive FDTD simulation.

    Args:
        save_path (str): Path to save the simulation file
        hide_gui (bool): Run in background without GUI

    Returns:
        dict: Simulation results
    """
    # Initialize FDTD session
    fdtd = lumapi.FDTD(hide=hide_gui)

    # Get geometry parameters
    params = get_geometry_params()

    # Setup simulation
    setup_fdtd_simulation(fdtd, params)

    # Create geometry
    create_comb_geometry(fdtd, params)

    # Add sources and monitors
    add_sources_and_monitors(fdtd, params)

    # Save simulation file
    if save_path:
        fdtd.save(save_path)
        print(f"Simulation saved to: {save_path}")

    # Run simulation
    print("Running FDTD simulation...")
    fdtd.run()
    print("Simulation complete.")

    # Extract results
    results = {
        'E_field': fdtd.getresult('opt_fields', 'E'),
        'H_field': fdtd.getresult('opt_fields', 'H'),
        'profile': fdtd.getresult('profile_xy', 'E'),
    }

    # Close session
    fdtd.close()

    return results


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Comb-Drive FDTD Simulation")
    print("=" * 70)

    # Create results directory
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # Run simulation
    save_file = os.path.join(results_dir, "comb_drive.fsp")

    try:
        results = run_comb_drive_simulation(save_path=save_file, hide_gui=False)
        print("\nSimulation completed successfully!")
        print(f"Results saved to: {results_dir}")
    except Exception as e:
        print(f"\nError during simulation: {e}")
        raise
