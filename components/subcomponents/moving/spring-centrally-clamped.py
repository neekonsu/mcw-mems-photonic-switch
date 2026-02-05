#!/usr/bin/env python3
"""
Centrally Clamped Bistable Spring (MEMS)

This creates a centrally clamped bistable spring based on 
Alexander Slocum 2004 and Daoxin Dai 2023
"""

import gdsfactory as gf
import numpy as np
from typing import List, Tuple
from pathlib import Path

@gf.cell
def ccs_spring(
    l: float = 40.0,
    t_flex: float = 0.3,
    t_rigid: float = 0.4,
    h: float = 1.2,
    d: float = 1.0,
    flex_rigid_ratio: float = 0.428,
    youngs_modulus: float = 169.0,
    pre_strain: float = 0,
) -> gf.Component:
    """
    ccs_spring: Centrally Clamped, Stepped Spring.
    
    Returns a component representing a bistable MEMS spring using a 
    stepped beam design to optimize switching force and energy.

    Parameters
    ----------
    l : float
        Beam span (total length) between anchor points [μm].
    t_flex : float
        In-plane width of the flexible (cosine-shaped) sections [μm].
    t_rigid : float
        In-plane width of the rigid (straight stepped) sections [μm].
    h : float
        Initial apex height; maximum initial offset in y-direction [μm].
    d : float
        Beam depth; out-of-plane height, MEMS layer thickness [μm].
    flex_rigid_ratio : float
        Ratio of the length of flexible segments to rigid segments in x-direction.
    youngs_modulus : float
        Material stiffness (default is Silicon in <110> direction) [GPa].
    pre_strain : float
        Estimated residual compressive pre-strain in the device layer.

    Notes
    -----
    - Bistability Condition: Requires the geometry constant Q = h/t_flex > 2.31
    - Transition: Uses a smooth profile with continuous first derivatives between 
      flexible and rigid segments to minimize stress concentration.
    - From Daoxin Dai 2023, length of flexible to length of rigit segment ratio is 3:7
    - Initial implementation fixes (Q = 4) => (h = Q * t_flex = 4 * t_flex)
    """

