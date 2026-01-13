"""
Bistable Curved Beam Simulation
Replicating results from Qiu, Lang, Slocum (2004)
"A Curved-Beam Bistable Mechanism" - JMEMS Vol. 13, No. 2

This script simulates:
- Fig. 1: First three buckling mode shapes
- Fig. 3: Normalized force-displacement relations
- Fig. 4: Bistable f-d curve for high Q
- Beam shape evolution during snap-through
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

# =============================================================================
# SECTION 1: Mode Eigenvalues and Shape Functions
# =============================================================================

def find_even_mode_eigenvalues(n_modes=3):
    """
    Find eigenvalues for even modes by solving tan(N/2) = N/2
    From equation (4) in paper: sin(N/2)[tan(N/2) - N/2] = 0
    
    For even modes, we need tan(N/2) = N/2
    
    The solutions for x in tan(x) = x are approximately:
    x ≈ 4.493, 7.725, 10.904, ... (just past each π/2 + n*π)
    So N = 2x ≈ 8.987, 15.45, 21.81, ...
    In terms of π: N ≈ 2.86π, 4.92π, 6.94π, ...
    """
    eigenvalues = []
    # tan(x) = x has solutions just after x = (2k+1)*π/2 for k = 1, 2, 3...
    # First solution is around x ≈ 4.493 (just past 3π/2 ≈ 4.712... no, past π ≈ 3.14)
    # Actually, solutions are near x ≈ 4.493, 7.725, 10.904
    
    for k in range(n_modes):
        # Search in interval (k*π + π/2, (k+1)*π + π/2) but avoiding asymptotes
        # First root is between π and 3π/2
        if k == 0:
            x_low = np.pi + 0.1
            x_high = 1.5 * np.pi - 0.1
        else:
            x_low = k * np.pi + np.pi + 0.1
            x_high = k * np.pi + 1.5 * np.pi - 0.1
        
        try:
            x_root = brentq(lambda x: np.tan(x) - x, x_low, x_high)
            eigenvalues.append(2 * x_root)  # N = 2x
        except ValueError:
            # If brentq fails, use approximate values
            approx_roots = [4.4934, 7.7253, 10.9041]
            if k < len(approx_roots):
                eigenvalues.append(2 * approx_roots[k])
    
    return eigenvalues

# Compute mode eigenvalues
N1 = 2 * np.pi                          # Mode 1 (j=1): N = (j+1)π = 2π
even_eigenvalues = find_even_mode_eigenvalues(3)
N2 = even_eigenvalues[0]                 # Mode 2 (j=2): ≈ 2.86π
N3 = 4 * np.pi                          # Mode 3 (j=3): N = 4π

print("=" * 60)
print("MODE EIGENVALUES")
print("=" * 60)
print(f"N₁ = {N1:.4f} = {N1/np.pi:.4f}π  (Mode 1, symmetric)")
print(f"N₂ = {N2:.4f} = {N2/np.pi:.4f}π  (Mode 2, antisymmetric)")
print(f"N₃ = {N3:.4f} = {N3/np.pi:.4f}π  (Mode 3, symmetric)")
print()

def mode_shape_odd(X, N):
    """
    Mode shape for odd modes (j = 1, 3, 5, ...)
    Equation (17): W_j(X) = 1 - cos(N_j * X)
    
    These are symmetric modes (same shape on left and right of center)
    """
    return 1 - np.cos(N * X)

def mode_shape_even(X, N):
    """
    Mode shape for even modes (j = 2, 4, 6, ...)
    Equation (18): W_j(X) = 1 - 2X - cos(N_j*X) + 2*sin(N_j*X)/N_j
    
    These are antisymmetric modes (twisting/rotation at center)
    """
    return 1 - 2*X - np.cos(N * X) + 2*np.sin(N * X) / N


# =============================================================================
# SECTION 2: Force-Displacement Relations (Simplified Model)
# =============================================================================

def F1_simplified(Delta, Q):
    """
    First kind of solution - cubic force-displacement relation
    Equation (36) from paper (neglecting higher modes):
    
    F₁ = (3π⁴Q²/2) * Δ * (Δ - 3/2 + √(1/4 - 4/(3Q²))) * (Δ - 3/2 - √(1/4 - 4/(3Q²)))
    
    This represents the beam deflecting while maintaining first-mode shape.
    
    Parameters:
    -----------
    Delta : array-like
        Normalized displacement Δ = d/h
    Q : float
        Geometry parameter Q = h/t (apex height / beam thickness)
    
    Returns:
    --------
    F : array-like
        Normalized force F = f*l³/(EI*h)
    """
    Delta = np.atleast_1d(Delta)
    
    # Check if Q is large enough for bistability
    discriminant = 0.25 - 4/(3*Q**2)
    
    if discriminant < 0:
        # Q too small - no real solutions
        return np.full_like(Delta, np.nan, dtype=float)
    
    sqrt_term = np.sqrt(discriminant)
    coeff = 3 * np.pi**4 * Q**2 / 2
    
    # F₁ is a cubic with roots at Δ = 0, and two other roots
    root1 = 1.5 - sqrt_term  # First positive root (around Δ ≈ 1 for large Q)
    root2 = 1.5 + sqrt_term  # Second positive root (around Δ ≈ 2 for large Q)
    
    return coeff * Delta * (Delta - root1) * (Delta - root2)


def F2_simplified(Delta):
    """
    Second kind of solution - mode 2 FREE (linear)
    Equation (38) from paper:
    
    F₂ = (N₁²(N₂² - N₁²)/8) * (N₂²/(N₂² - N₁²) - Δ)
       ≈ 4.18π⁴ - 2.18π⁴Δ
    
    This is a straight line representing the force when the beam
    transitions to include second mode (twisting). Only relevant
    when second mode is NOT constrained (single beam case).
    """
    Delta = np.atleast_1d(Delta)
    
    coeff = N1**2 * (N2**2 - N1**2) / 8
    offset = N2**2 / (N2**2 - N1**2)
    
    return coeff * (offset - Delta)


def F3_simplified(Delta):
    """
    Third kind of solution - mode 2 CONSTRAINED (linear)
    Equation (39) from paper:
    
    F₃ = (N₁²(N₃² - N₁²)/8) * (N₃²/(N₃² - N₁²) - Δ)
       ≈ 8π⁴ - 6π⁴Δ
    
    This is a straight line representing the force when the beam
    transitions to third mode. This is the relevant curve for the
    bistable double-beam where second mode is mechanically constrained.
    
    Key values:
    - F₃(Δ=0) = 8π⁴ ≈ 779
    - F₃(Δ=4/3) = 0 (zero crossing)
    - Slope = -6π⁴ ≈ -584
    """
    Delta = np.atleast_1d(Delta)
    
    coeff = N1**2 * (N3**2 - N1**2) / 8
    offset = N3**2 / (N3**2 - N1**2)
    
    return coeff * (offset - Delta)


def compute_bistable_curve(Delta, Q):
    """
    Compute the actual bistable F-Δ curve for second-mode-constrained beam.
    
    For Q > Q_cr1 ≈ 2.31 (critical Q for bistability with mode 2 constrained),
    the beam follows the F₁ curve (cubic), which exhibits:
    - Positive stiffness region near Δ = 0 (first stable position)
    - Maximum force f_top at d_top
    - Negative stiffness region (unstable equilibrium)
    - Minimum force f_bot (negative) at d_bot  
    - Positive stiffness region near Δ = 2 (second stable position)
    
    The F₃ line represents the asymptotic limit as Q → ∞ for the 
    negative stiffness portion.
    """
    Delta = np.atleast_1d(Delta)
    return F1_simplified(Delta, Q)


# =============================================================================
# SECTION 3: Beam Shape During Deflection
# =============================================================================

def compute_A1_from_Delta(Delta):
    """
    Compute first mode amplitude from center displacement.
    
    From equation (21) simplified (neglecting higher modes):
    Δ = 1 - 2*A₁
    
    Therefore: A₁ = (1 - Δ)/2
    
    Physical meaning:
    - A₁ = 0.5: initial position (Δ = 0)
    - A₁ = 0: beam is flat (Δ = 1)  
    - A₁ = -0.5: inverted position (Δ = 2)
    """
    return (1 - Delta) / 2


def beam_shape_at_displacement(X, Delta):
    """
    Compute the deflected beam shape at a given center displacement.
    
    For the simplified model (second mode constrained, higher modes neglected):
    W(X) = A₁ * W₁(X)
    
    where W₁(X) = 1 - cos(2πX) is the first mode shape.
    
    The center height is:
    W(0.5) = A₁ * 2 = 1 - Δ
    
    So:
    - Δ = 0: center at height 1 (normalized initial apex)
    - Δ = 1: center at height 0 (flat)
    - Δ = 2: center at height -1 (inverted)
    """
    A1 = compute_A1_from_Delta(Delta)
    W1 = mode_shape_odd(X, N1)
    return A1 * W1


# =============================================================================
# SECTION 4: Plotting Functions
# =============================================================================

def plot_fig1_buckling_modes():
    """
    Replicate Figure 1: First three buckling mode shapes
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    X = np.linspace(0, 1, 500)
    
    # Compute mode shapes
    W1 = mode_shape_odd(X, N1)
    W2 = mode_shape_even(X, N2)
    W3 = mode_shape_odd(X, N3)
    
    # Normalize each mode to have max absolute value of 1 for display
    W1_norm = W1 / np.max(np.abs(W1))
    W2_norm = W2 / np.max(np.abs(W2))
    W3_norm = W3 / np.max(np.abs(W3))
    
    # Plot with offset for clarity (like in the paper)
    offset = 2.5
    ax.plot(X, W1_norm + 2*offset, 'b-', linewidth=2, label=f'Mode 1: p = p₁')
    ax.plot(X, W2_norm + offset, 'r-', linewidth=2, label=f'Mode 2: p = p₂')
    ax.plot(X, W3_norm, 'g-', linewidth=2, label=f'Mode 3: p = p₃')
    
    # Add baseline references
    ax.axhline(y=2*offset, color='b', linewidth=0.5, linestyle='--', alpha=0.5)
    ax.axhline(y=offset, color='r', linewidth=0.5, linestyle='--', alpha=0.5)
    ax.axhline(y=0, color='g', linewidth=0.5, linestyle='--', alpha=0.5)
    
    # Labels
    ax.set_xlabel('X = x/l', fontsize=12)
    ax.set_ylabel('W(X) (normalized, offset for clarity)', fontsize=12)
    ax.set_title('Figure 1: First Three Buckling Modes for Clamped-Clamped Beam', fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.set_xlim([0, 1])
    ax.grid(True, alpha=0.3)
    
    # Add annotations
    ax.annotate('Symmetric\n(1 hump)', xy=(0.5, 2*offset + 1), ha='center', fontsize=9)
    ax.annotate('Antisymmetric\n(S-shape twist)', xy=(0.5, offset + 0.5), ha='center', fontsize=9)
    ax.annotate('Symmetric\n(2 humps)', xy=(0.5, 1), ha='center', fontsize=9)
    
    plt.tight_layout()
    return fig


def plot_fig3_force_displacement():
    """
    Replicate Figure 3: Force-displacement relations for various Q values
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    Delta = np.linspace(0.001, 2, 500)
    
    # F₃ line (mode 2 constrained) - this is what matters for bistable operation
    F3_vals = F3_simplified(Delta)
    ax.plot(Delta, F3_vals, 'b-', linewidth=2.5, label='F₃ (mode 2 constrained)')
    
    # F₂ line (mode 2 free) - shown for reference
    F2_vals = F2_simplified(Delta)
    ax.plot(Delta, F2_vals, 'r--', linewidth=2, alpha=0.7, label='F₂ (mode 2 free)')
    
    # F₁ curves for different Q values
    Q_values = [3.0, 2.31, 1.67]
    colors = ['darkgreen', 'orange', 'purple']
    
    for Q, color in zip(Q_values, colors):
        F1_vals = F1_simplified(Delta, Q)
        ax.plot(Delta, F1_vals, color=color, linewidth=2, label=f'F₁, Q = {Q}')
    
    # Reference lines
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=1, color='gray', linewidth=0.5, linestyle=':', alpha=0.5)
    
    # Labels and formatting
    ax.set_xlabel('Δ = d/h (normalized displacement)', fontsize=12)
    ax.set_ylabel('F (normalized force)', fontsize=12)
    ax.set_title('Figure 3: Force-Displacement Relations for Curved Beam\n(Simplified model, neglecting higher modes)', fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 2])
    ax.set_ylim([-400, 800])
    
    # Add annotations for key Q thresholds
    ax.annotate('Q = 2.31: F₁ tangent to F₃ at Δ=1', 
                xy=(1, 0), xytext=(1.2, 200),
                arrowprops=dict(arrowstyle='->', color='gray'),
                fontsize=9, color='gray')
    ax.annotate('Q = 1.67: F₁ tangent to F₂ at Δ=1', 
                xy=(1, 0), xytext=(0.3, -200),
                arrowprops=dict(arrowstyle='->', color='gray'),
                fontsize=9, color='gray')
    
    plt.tight_layout()
    return fig


def plot_fig4_bistable_curve(Q=6):
    """
    Replicate Figure 4: Idealized bistable f-d curve for high Q
    
    For second-mode-constrained beam with Q >> 1, the curve shows:
    - Positive stiffness near Δ = 0 (first stable position)
    - Peak force f_top
    - Negative stiffness region (unstable)
    - Minimum force f_bot (negative)
    - Positive stiffness near Δ = 2 (second stable position)
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    Delta = np.linspace(0.001, 2, 1000)
    
    # Compute F₁ curve (the actual bistable curve for high Q)
    F1_vals = F1_simplified(Delta, Q)
    F3_vals = F3_simplified(Delta)
    
    # Plot the bistable F₁ curve
    ax.plot(Delta, F1_vals, 'b-', linewidth=3, label=f'F₁ bistable curve (Q={Q})')
    
    # Plot F₃ as reference (asymptotic limit in negative stiffness region)
    ax.plot(Delta, F3_vals, 'r--', linewidth=1.5, alpha=0.6, label='F₃ (mode 3 limit)')
    
    # Reference line
    ax.axhline(y=0, color='k', linewidth=0.5)
    
    # Find key points analytically
    # From paper: for high Q, roots of cubic are approximately at Δ = 0, ~1, ~2
    # The discriminant term sqrt(1/4 - 4/(3Q²)) ≈ 1/2 for large Q
    discriminant = 0.25 - 4/(3*Q**2)
    sqrt_term = np.sqrt(discriminant)
    root1 = 1.5 - sqrt_term  # ≈ 1 for large Q
    root2 = 1.5 + sqrt_term  # ≈ 2 for large Q
    
    # f_top: maximum force (between Δ=0 and first root)
    Delta_search = np.linspace(0.01, root1 - 0.01, 500)
    F_search = F1_simplified(Delta_search, Q)
    idx_max = np.argmax(F_search)
    d_top = Delta_search[idx_max]
    f_top = F_search[idx_max]
    
    # f_bot: minimum force (between roots)
    Delta_search2 = np.linspace(root1 + 0.01, root2 - 0.01, 500)
    F_search2 = F1_simplified(Delta_search2, Q)
    idx_min = np.argmin(F_search2)
    d_bot = Delta_search2[idx_min]
    f_bot = F_search2[idx_min]
    
    # Mark key points
    ax.plot(0, 0, 'go', markersize=12, zorder=5, label='Stable equilibria')
    ax.plot(2, 0, 'go', markersize=12, zorder=5)
    ax.plot(d_top, f_top, 'r^', markersize=10, zorder=5, label=f'f_top = {f_top:.0f}')
    ax.plot(d_bot, f_bot, 'rv', markersize=10, zorder=5, label=f'f_bot = {f_bot:.0f}')
    ax.plot(root1, 0, 'ko', markersize=8, zorder=5, alpha=0.7)
    ax.plot(root2, 0, 'ko', markersize=8, zorder=5, alpha=0.7)
    
    # Annotate
    ax.annotate(f'd_top ≈ {d_top:.2f}', xy=(d_top, f_top), 
                xytext=(d_top + 0.15, f_top + 20), fontsize=10,
                arrowprops=dict(arrowstyle='->', color='gray', alpha=0.7))
    ax.annotate(f'd_bot ≈ {d_bot:.2f}', xy=(d_bot, f_bot), 
                xytext=(d_bot + 0.15, f_bot - 60), fontsize=10,
                arrowprops=dict(arrowstyle='->', color='gray', alpha=0.7))
    ax.annotate('First zero\ncrossing', xy=(root1, 0), 
                xytext=(root1 - 0.25, 100), fontsize=9,
                arrowprops=dict(arrowstyle='->', color='gray', alpha=0.7))
    ax.annotate('Second zero\ncrossing', xy=(root2, 0), 
                xytext=(root2 - 0.05, 100), fontsize=9,
                arrowprops=dict(arrowstyle='->', color='gray', alpha=0.7))
    
    # Labels
    ax.set_xlabel('Δ = d/h (normalized displacement)', fontsize=12)
    ax.set_ylabel('F (normalized force)', fontsize=12)
    ax.set_title(f'Figure 4: Bistable Force-Displacement Curve\n(Second mode constrained, Q = {Q})', fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 2])
    
    # Shade regions to indicate stability
    # Positive stiffness = stable, negative stiffness = unstable
    ax.fill_between([0, d_top], ax.get_ylim()[0], ax.get_ylim()[1], 
                    alpha=0.1, color='green', label='Stable region')
    ax.fill_between([d_top, d_bot], ax.get_ylim()[0], ax.get_ylim()[1], 
                    alpha=0.1, color='red')
    ax.fill_between([d_bot, 2], ax.get_ylim()[0], ax.get_ylim()[1], 
                    alpha=0.1, color='green')
    
    # Add physical interpretation text
    textstr = '\n'.join([
        'Snap-through behavior:',
        f'1. Push from Δ=0: force increases to f_top',
        f'2. At d_top: snap-through initiated',  
        f'3. Beam rapidly moves through unstable region',
        f'4. Settles at Δ≈2 (second stable position)',
        f'',
        f'Key values:',
        f'  f_top = {f_top:.0f},  d_top = {d_top:.3f}',
        f'  f_bot = {f_bot:.0f},  d_bot = {d_bot:.3f}'
    ])
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.35, textstr, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    return fig


def plot_beam_shape_evolution(Q=6):
    """
    Visualize beam shape W(X) at various displacement stages
    
    This helps build intuition for the force-displacement relationship
    by showing how the beam physically deforms during snap-through.
    """
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    X = np.linspace(0, 1, 500)
    
    # Key displacement values to visualize
    Delta_values = [0, 0.3, 0.7, 1.0, 1.5, 2.0]
    titles = [
        'Initial position\n(first stable state)',
        'Pushed down\n(positive F, increasing)',
        'Near peak force\n(approaching f_top)',
        'Flat configuration\n(near inflection)',
        'Past inflection\n(negative F region)',
        'Second stable state\n(inverted position)'
    ]
    colors = ['blue', 'green', 'orange', 'gold', 'purple', 'blue']
    
    # Compute F values for each displacement
    F_vals = F1_simplified(np.array(Delta_values), Q)
    
    for ax, Delta_val, title, color, F_val in zip(axes.flat, Delta_values, titles, colors, F_vals):
        # Compute beam shape
        W = beam_shape_at_displacement(X, Delta_val)
        A1 = compute_A1_from_Delta(Delta_val)
        
        # Plot beam shape
        ax.fill_between(X, 0, W, alpha=0.3, color=color)
        ax.plot(X, W, color=color, linewidth=2)
        
        # Reference: initial shape (dashed)
        W_initial = beam_shape_at_displacement(X, 0)
        ax.plot(X, W_initial, 'k--', linewidth=1, alpha=0.3, label='Initial shape')
        
        # Baseline
        ax.axhline(y=0, color='k', linewidth=0.5)
        
        # Mark center point
        center_height = 1 - Delta_val
        ax.plot(0.5, center_height, 'ko', markersize=8)
        
        # Formatting
        F_str = f'{F_val:.0f}' if not np.isnan(F_val) else 'N/A'
        ax.set_title(f'{title}\nΔ = {Delta_val:.2f}, F = {F_str}', fontsize=10)
        ax.set_xlabel('X = x/l')
        ax.set_ylabel('W(X)')
        ax.set_xlim([0, 1])
        ax.set_ylim([-1.5, 2.5])
        ax.grid(True, alpha=0.3)
        
        # Add amplitude annotation
        ax.annotate(f'A₁ = {A1:.2f}', xy=(0.05, 2.0), fontsize=9)
    
    plt.suptitle(f'Beam Shape Evolution During Snap-Through (Q={Q})\n(Second Mode Constrained, Simplified Model)', 
                 fontsize=14, y=1.02)
    plt.tight_layout()
    return fig


def plot_combined_visualization(Q=6):
    """
    Create a combined figure showing F-Δ curve with beam shapes
    """
    fig = plt.figure(figsize=(14, 10))
    
    # Main F-Δ plot on the left
    ax_main = fig.add_subplot(1, 2, 1)
    Delta = np.linspace(0.001, 2, 1000)
    F_vals = F1_simplified(Delta, Q)
    
    ax_main.plot(Delta, F_vals, 'b-', linewidth=2.5)
    ax_main.axhline(y=0, color='k', linewidth=0.5)
    ax_main.set_xlabel('Δ = d/h', fontsize=12)
    ax_main.set_ylabel('F (normalized force)', fontsize=12)
    ax_main.set_title(f'Force-Displacement Curve (Q={Q})', fontsize=12)
    ax_main.grid(True, alpha=0.3)
    ax_main.set_xlim([0, 2])
    
    # Mark points corresponding to beam shape snapshots
    Delta_snapshots = [0, 0.3, 0.7, 1.0, 1.5, 2.0]
    F_snapshots = F1_simplified(np.array(Delta_snapshots), Q)
    colors = ['blue', 'green', 'orange', 'gold', 'purple', 'cyan']
    
    for i, (d, f, c) in enumerate(zip(Delta_snapshots, F_snapshots, colors)):
        if not np.isnan(f):
            ax_main.plot(d, f, 'o', color=c, markersize=12, zorder=5)
            ax_main.annotate(str(i+1), xy=(d, f), xytext=(5, 5), 
                            textcoords='offset points', fontsize=10, fontweight='bold')
    
    # Beam shape snapshots on the right
    X = np.linspace(0, 1, 200)
    
    for i, (Delta_val, color) in enumerate(zip(Delta_snapshots, colors)):
        ax = fig.add_subplot(3, 4, 4*(i//3) + (i%3) + 2)
        
        W = beam_shape_at_displacement(X, Delta_val)
        ax.fill_between(X, 0, W, alpha=0.3, color=color)
        ax.plot(X, W, color=color, linewidth=2)
        ax.axhline(y=0, color='k', linewidth=0.5)
        ax.set_xlim([0, 1])
        ax.set_ylim([-1.5, 2.2])
        ax.set_title(f'({i+1}) Δ = {Delta_val:.2f}', fontsize=10)
        ax.set_xticks([0, 0.5, 1])
        ax.set_yticks([-1, 0, 1, 2])
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GENERATING FIGURES")
    print("=" * 60)
    
    Q_default = 6  # Good value to see bistable behavior
    
    # Create output directory marker
    print("\n1. Generating Figure 1: Buckling Modes...")
    fig1 = plot_fig1_buckling_modes()
    fig1.savefig('/home/claude/fig1_buckling_modes.png', dpi=150, bbox_inches='tight')
    print("   Saved: fig1_buckling_modes.png")
    
    print("\n2. Generating Figure 3: Force-Displacement Relations...")
    fig3 = plot_fig3_force_displacement()
    fig3.savefig('/home/claude/fig3_force_displacement.png', dpi=150, bbox_inches='tight')
    print("   Saved: fig3_force_displacement.png")
    
    print(f"\n3. Generating Figure 4: Bistable Curve (Q={Q_default})...")
    fig4 = plot_fig4_bistable_curve(Q=Q_default)
    fig4.savefig('/home/claude/fig4_bistable_curve.png', dpi=150, bbox_inches='tight')
    print("   Saved: fig4_bistable_curve.png")
    
    print(f"\n4. Generating Beam Shape Evolution (Q={Q_default})...")
    fig5 = plot_beam_shape_evolution(Q=Q_default)
    fig5.savefig('/home/claude/fig5_beam_shapes.png', dpi=150, bbox_inches='tight')
    print("   Saved: fig5_beam_shapes.png")
    
    print(f"\n5. Generating Combined Visualization (Q={Q_default})...")
    fig6 = plot_combined_visualization(Q=Q_default)
    fig6.savefig('/home/claude/fig6_combined.png', dpi=150, bbox_inches='tight')
    print("   Saved: fig6_combined.png")
    
    print("\n" + "=" * 60)
    print("KEY RESULTS (Simplified Model)")
    print("=" * 60)
    
    # Print theoretical values
    print(f"\nForce values at Δ = 0:")
    print(f"  F₃(0) = 8π⁴ = {8*np.pi**4:.1f}")
    
    print(f"\nZero crossing of F₃:")
    print(f"  Δ_mid = 4/3 = {4/3:.4f}")
    
    print(f"\nFor Q >> 1, the bistable curve shows:")
    print(f"  - Maximum force (f_top) near Δ ≈ 0.15-0.2")
    print(f"  - Minimum force (f_bot, negative) near Δ ≈ 1.8-1.9")
    print(f"  - Stable positions at Δ = 0 and Δ = 2")
    
    print("\n" + "=" * 60)
    print("THEORETICAL vs PAPER VALUES (Eqs. 40-41)")
    print("=" * 60)
    print("Simplified model (neglecting higher modes):")
    print(f"  f_top ≈ 8π⁴ EIh/l³ = {8*np.pi**4:.0f} (normalized)")
    print(f"  f_bot ≈ 4π⁴ EIh/l³ = {4*np.pi**4:.0f} (normalized)")
    print(f"  d_mid = (4/3)h")
    print("\nWith higher modes (Eqs. 43-44, matches FEA):")
    print(f"  f_top ≈ 740 EIh/l³")
    print(f"  f_bot ≈ 370 EIh/l³")
    
    plt.show()
    print("\nDone!")
