"""
Geometry definition for the gap-adjustable directional coupler switch-cell.

This module defines the device geometry in a reusable format that can be accessed
by both the Lumerical FDTD simulation and visualization scripts.

Based on Han et al., Journal of Optical Microsystems (2021).
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class SOIPlatform:
    """Standard SOI platform specifications."""
    device_layer_thickness: float = 220e-9      # 220 nm Si device layer
    box_thickness: float = 3e-6                 # 3 μm buried oxide
    substrate_thickness: float = 500e-6         # 500 μm Si substrate

    # Materials
    device_material: str = 'Si (Silicon) - Palik'
    box_material: str = 'SiO2 (Glass) - Palik'
    substrate_material: str = 'Si (Silicon) - Palik'
    cladding_index: float = 1.0                 # Air (or 1.444 for SiO2)


@dataclass
class WaveguideSpec:
    """Waveguide specifications for the directional coupler."""
    width: float = 450e-9                       # 450 nm waveguide width
    height: float = 220e-9                      # 220 nm height (= device layer)
    coupling_length: float = 20e-6              # 20 μm coupling region

    # Waveguide pitch for crossbar (from paper: 166 μm pitch)
    waveguide_pitch: float = 166e-6             # 166 μm between parallel waveguides


@dataclass
class CombDriveSpec:
    """MEMS comb-drive actuator specifications from paper."""
    # Comb finger dimensions (from paper: 300nm width, 400nm spacing, 44 pairs)
    finger_width: float = 300e-9                # 300 nm comb finger width
    finger_spacing: float = 400e-9              # 400 nm spacing between fingers
    num_finger_pairs: int = 44                  # 44 pairs of comb fingers
    finger_height: float = 220e-9               # 220 nm height (device layer)

    # Spring dimensions (from paper: 300nm width, 30μm length)
    spring_width: float = 300e-9                # 300 nm spring width
    spring_length: float = 30e-6                # 30 μm spring length
    num_springs: int = 4                        # 4 folded springs

    # Actuator footprint (from paper: 88μm × 88μm)
    footprint_x: float = 88e-6                  # 88 μm
    footprint_y: float = 88e-6                  # 88 μm

    # Moving mass dimensions
    shuttle_width: float = 10e-6                # 10 μm shuttle width
    shuttle_length: float = 40e-6               # 40 μm shuttle length

    # Anchor dimensions
    anchor_width: float = 5e-6                  # 5 μm anchor width
    anchor_length: float = 10e-6                # 10 μm anchor length


@dataclass
class GapSpec:
    """Gap specifications for MEMS-tunable coupler."""
    gap_off: float = 550e-9                     # 550 nm (OFF state - weak coupling)
    gap_on: float = 50e-9                       # 50 nm (ON state - strong coupling)
    gap_contact: float = 0e-9                   # 0 nm (contact state)

    def get_gap(self, state: str) -> float:
        """Get gap distance for a given state."""
        if state == 'off':
            return self.gap_off
        elif state == 'on':
            return self.gap_on
        elif state == 'contact':
            return self.gap_contact
        else:
            return self.gap_off  # Default to OFF


@dataclass
class GratingCouplerSpec:
    """Grating coupler specifications (from paper)."""
    pitch: float = 640e-9                       # 640 nm pitch
    duty_cycle: float = 0.5                     # 50% duty cycle
    etch_depth: float = 70e-9                   # 70 nm etch depth
    bandwidth: float = 30e-9                    # 30 nm bandwidth


@dataclass
class OpticalSpec:
    """Optical simulation parameters."""
    wavelength_center: float = 1550e-9          # 1550 nm telecom wavelength
    wavelength_span: float = 100e-9             # 100 nm simulation span
    polarization: str = 'TE'                    # Transverse electric
    mode_number: int = 1                        # Fundamental mode


class DirectionalCouplerGeometry:
    """
    Complete geometry definition for the gap-adjustable directional coupler.

    This class provides methods to query all geometric parameters and generate
    structure definitions for both simulation and visualization.
    """

    def __init__(self, gap_state: str = 'off'):
        """
        Initialize the directional coupler geometry.

        Args:
            gap_state: 'off' (550nm), 'on' (50nm), or 'contact' (0nm)
        """
        self.soi = SOIPlatform()
        self.waveguide = WaveguideSpec()
        self.gap = GapSpec()
        self.grating = GratingCouplerSpec()
        self.optical = OpticalSpec()
        self.comb_drive = CombDriveSpec()
        self.gap_state = gap_state

    @property
    def current_gap(self) -> float:
        """Get the current gap distance based on state."""
        return self.gap.get_gap(self.gap_state)

    @property
    def y_offset(self) -> float:
        """Calculate the y-offset for waveguide positioning."""
        return (self.waveguide.width + self.current_gap) / 2

    def get_parameters_dict(self) -> Dict:
        """
        Export all parameters as a dictionary for Lumerical simulation.

        Returns:
            Dictionary of all geometry parameters
        """
        return {
            # SOI platform
            'device_layer_thickness': self.soi.device_layer_thickness,
            'box_thickness': self.soi.box_thickness,
            'substrate_thickness': self.soi.substrate_thickness,
            'core_material': self.soi.device_material,
            'box_material': self.soi.box_material,
            'substrate_material': self.soi.substrate_material,
            'cladding_index': self.soi.cladding_index,

            # Waveguide dimensions
            'waveguide_width': self.waveguide.width,
            'waveguide_height': self.waveguide.height,
            'coupling_length': self.waveguide.coupling_length,
            'input_length': self.waveguide.input_length,
            'output_length': self.waveguide.output_length,

            # Gap specifications
            'coupling_gap': self.current_gap,
            'coupling_gap_off': self.gap.gap_off,
            'coupling_gap_on': self.gap.gap_on,
            'gap_state': self.gap_state,

            # Grating coupler
            'grating_pitch': self.grating.pitch,
            'grating_duty_cycle': self.grating.duty_cycle,
            'grating_etch_depth': self.grating.etch_depth,
            'grating_bandwidth': self.grating.bandwidth,

            # Optical properties
            'wavelength_center': self.optical.wavelength_center,
            'wavelength_span': self.optical.wavelength_span,
            'polarization': self.optical.polarization,
            'mode_number': self.optical.mode_number,
        }

    def get_complete_switch_structures(self) -> List[Dict]:
        """
        Get the complete switch cell with two directional couplers and diagonal comb-drive.

        Based on paper description:
        - Each switch cell has TWO directional couplers
        - Couplers are tethered to a common comb-drive actuator
        - Actuator moves in diagonal direction
        - This controls both couplers simultaneously

        Returns:
            List of structure dictionaries
        """
        structures = []
        wg_w = self.waveguide.width
        wg_h = self.waveguide.height

        # Add substrate layers
        structures.extend(self._create_substrate_layers())

        # Create TWO directional couplers oriented diagonally
        # Coupler 1: upper-left to lower-right diagonal
        structures.extend(self._create_directional_coupler(
            center_x=-30e-6,
            center_y=30e-6,
            angle=45,  # 45 degree rotation
            coupler_id=1
        ))

        # Coupler 2: lower-left to upper-right diagonal
        structures.extend(self._create_directional_coupler(
            center_x=-30e-6,
            center_y=-30e-6,
            angle=-45,  # -45 degree rotation
            coupler_id=2
        ))

        # Create comb-drive actuator in center (diagonal orientation)
        structures.extend(self._create_comb_drive_diagonal())

        return structures

    def _create_substrate_layers(self) -> List[Dict]:
        """Create substrate, BOX, and cladding layers."""
        return [
            {
                'name': 'Si_substrate',
                'x': 0, 'y': 0,
                'z': -self.soi.box_thickness - self.soi.substrate_thickness/2,
                'x_span': 200e-6, 'y_span': 200e-6,
                'z_span': self.soi.substrate_thickness,
                'material': 'Si',
                'type': 'substrate',
            },
            {
                'name': 'BOX',
                'x': 0, 'y': 0,
                'z': -self.soi.box_thickness/2,
                'x_span': 200e-6, 'y_span': 200e-6,
                'z_span': self.soi.box_thickness,
                'material': 'SiO2',
                'type': 'substrate',
            },
            {
                'name': 'cladding',
                'x': 0, 'y': 0,
                'z': self.soi.device_layer_thickness + 1e-6,
                'x_span': 200e-6, 'y_span': 200e-6,
                'z_span': 2e-6,
                'material': 'Air',
                'type': 'substrate',
            },
        ]

    def _create_directional_coupler(self, center_x: float, center_y: float,
                                   angle: float, coupler_id: int) -> List[Dict]:
        """
        Create a single directional coupler at given position and angle.

        Args:
            center_x, center_y: Position of coupler center
            angle: Rotation angle in degrees
            coupler_id: Identifier for this coupler (1 or 2)
        """
        structures = []
        wg_w = self.waveguide.width
        wg_h = self.waveguide.height
        coupling_len = self.waveguide.coupling_length
        gap = self.current_gap

        # For simplicity, create straight (non-rotated) couplers
        # In reality these would be rotated, but that requires rotation matrices

        y_offset = (wg_w + gap) / 2

        # Waveguide pair for this coupler
        structures.append({
            'name': f'coupler{coupler_id}_wg1',
            'x': center_x,
            'y': center_y + y_offset,
            'z': wg_h/2,
            'x_span': coupling_len,
            'y_span': wg_w,
            'z_span': wg_h,
            'material': 'Si',
            'type': 'waveguide',
        })

        structures.append({
            'name': f'coupler{coupler_id}_wg2',
            'x': center_x,
            'y': center_y - y_offset,
            'z': wg_h/2,
            'x_span': coupling_len,
            'y_span': wg_w,
            'z_span': wg_h,
            'material': 'Si',
            'type': 'waveguide',
        })

        return structures

    def _create_comb_drive_diagonal(self) -> List[Dict]:
        """Create the diagonal comb-drive actuator connecting both couplers."""
        structures = []
        wg_h = self.waveguide.height

        # Position comb-drive in center, oriented diagonally
        comb_center_x = 0
        comb_center_y = 0

        # Anchor (fixed)
        structures.append({
            'name': 'comb_anchor',
            'x': comb_center_x - 20e-6,
            'y': comb_center_y - 20e-6,
            'z': wg_h/2,
            'x_span': self.comb_drive.anchor_length,
            'y_span': self.comb_drive.anchor_width,
            'z_span': wg_h,
            'material': 'Si',
            'type': 'anchor',
        })

        # Moving shuttle (displacement in diagonal direction)
        shuttle_displacement = 0 if self.gap_state == 'off' else (self.gap.gap_off - self.current_gap)
        # Diagonal displacement (both x and y)
        diag_factor = 0.707  # cos(45°)

        structures.append({
            'name': 'comb_shuttle',
            'x': comb_center_x + shuttle_displacement * diag_factor,
            'y': comb_center_y + shuttle_displacement * diag_factor,
            'z': wg_h/2,
            'x_span': self.comb_drive.shuttle_length,
            'y_span': self.comb_drive.shuttle_width,
            'z_span': wg_h,
            'material': 'Si',
            'type': 'shuttle',
        })

        # Comb fingers oriented diagonally
        finger_w = self.comb_drive.finger_width
        finger_spacing = self.comb_drive.finger_spacing
        finger_pitch = finger_w + finger_spacing
        num_pairs = self.comb_drive.num_finger_pairs

        # Create comb fingers along diagonal axis
        for i in range(num_pairs):
            offset = -num_pairs * finger_pitch / 2 + i * finger_pitch

            # Fixed comb fingers (attached to anchor)
            structures.append({
                'name': f'comb_fixed_{i}',
                'x': comb_center_x - 15e-6 + offset * diag_factor,
                'y': comb_center_y - 15e-6 - offset * diag_factor,
                'z': wg_h/2,
                'x_span': 8e-6,
                'y_span': finger_w,
                'z_span': wg_h,
                'material': 'Si',
                'type': 'comb',
            })

            # Moving comb fingers (attached to shuttle)
            structures.append({
                'name': f'comb_moving_{i}',
                'x': comb_center_x - 10e-6 + offset * diag_factor + shuttle_displacement * diag_factor,
                'y': comb_center_y - 10e-6 - offset * diag_factor + shuttle_displacement * diag_factor,
                'z': wg_h/2,
                'x_span': 8e-6,
                'y_span': finger_w,
                'z_span': wg_h,
                'material': 'Si',
                'type': 'comb',
            })

        # Add springs (connecting shuttle to anchor)
        spring_positions = [
            (-10e-6, 10e-6),
            (10e-6, -10e-6),
            (-5e-6, 15e-6),
            (15e-6, -5e-6),
        ]

        for idx, (dx, dy) in enumerate(spring_positions):
            structures.append({
                'name': f'spring_{idx}',
                'x': comb_center_x + dx,
                'y': comb_center_y + dy,
                'z': wg_h/2,
                'x_span': self.comb_drive.spring_length,
                'y_span': self.comb_drive.spring_width,
                'z_span': wg_h,
                'material': 'Si',
                'type': 'spring',
            })

        return structures

    def get_waveguide_structures(self) -> List[Dict]:
        """
        Get list of all device structures including waveguides and MEMS actuator.

        This is the main method called by visualization and simulation scripts.
        It returns the complete switch cell design from the paper.

        Returns:
            List of dictionaries, each containing structure information:
            - name: structure name
            - x, y, z: center position
            - x_span, y_span, z_span: dimensions
            - material: material type ('Si', 'SiO2', 'Air')
            - type: 'substrate', 'waveguide', 'comb', 'spring', 'anchor', 'shuttle'
        """
        return self.get_complete_switch_structures()

    def get_device_bounds(self) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        """
        Get the bounding box of the entire device.

        Returns:
            ((x_min, x_max), (y_min, y_max), (z_min, z_max))
        """
        # Get all structures and calculate bounds from actual geometry
        structures = self.get_complete_switch_structures()

        x_coords = []
        y_coords = []

        for struct in structures:
            if struct['name'] not in ['Si_substrate', 'BOX', 'cladding']:
                x_coords.extend([
                    struct['x'] - struct['x_span']/2,
                    struct['x'] + struct['x_span']/2
                ])
                y_coords.extend([
                    struct['y'] - struct['y_span']/2,
                    struct['y'] + struct['y_span']/2
                ])

        x_bounds = (min(x_coords) - 5e-6, max(x_coords) + 5e-6)
        y_bounds = (min(y_coords) - 5e-6, max(y_coords) + 5e-6)
        z_bounds = (-self.soi.box_thickness - self.soi.substrate_thickness,
                   self.soi.device_layer_thickness + 2e-6)

        return (x_bounds, y_bounds, z_bounds)

    def print_summary(self):
        """Print a human-readable summary of the geometry."""
        print("=" * 70)
        print("Directional Coupler Geometry Summary")
        print("=" * 70)
        print(f"\nSOI Platform:")
        print(f"  Device layer: {self.soi.device_layer_thickness*1e9:.0f} nm")
        print(f"  BOX layer: {self.soi.box_thickness*1e6:.1f} μm")
        print(f"  Substrate: {self.soi.substrate_thickness*1e6:.0f} μm")

        print(f"\nWaveguide Specifications:")
        print(f"  Width: {self.waveguide.width*1e9:.0f} nm")
        print(f"  Height: {self.waveguide.height*1e9:.0f} nm")
        print(f"  Coupling length: {self.waveguide.coupling_length*1e6:.0f} μm")
        print(f"  Input length: {self.waveguide.input_length*1e6:.0f} μm")
        print(f"  Output length: {self.waveguide.output_length*1e6:.0f} μm")

        print(f"\nCoupling Gap:")
        print(f"  Current state: {self.gap_state.upper()}")
        print(f"  Current gap: {self.current_gap*1e9:.0f} nm")
        print(f"  OFF state gap: {self.gap.gap_off*1e9:.0f} nm")
        print(f"  ON state gap: {self.gap.gap_on:.0f} nm")

        print(f"\nOptical Properties:")
        print(f"  Wavelength: {self.optical.wavelength_center*1e9:.0f} nm")
        print(f"  Polarization: {self.optical.polarization}")
        print("=" * 70)


# Convenience function for quick access
def get_geometry(gap_state: str = 'off') -> DirectionalCouplerGeometry:
    """
    Get a DirectionalCouplerGeometry instance.

    Args:
        gap_state: 'off', 'on', or 'contact'

    Returns:
        DirectionalCouplerGeometry instance
    """
    return DirectionalCouplerGeometry(gap_state=gap_state)


if __name__ == "__main__":
    # Example usage
    geom = get_geometry(gap_state='off')
    geom.print_summary()

    print("\nStructure count:", len(geom.get_waveguide_structures()))
