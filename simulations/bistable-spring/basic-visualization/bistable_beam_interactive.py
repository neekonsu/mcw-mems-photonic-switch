"""
Interactive Bistable Curved Beam Visualization
with Sliders and Animation

Extends the static plots with:
- Interactive Q slider to see how geometry affects bistability
- Animation of snap-through process
- Real-time beam shape visualization
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.animation import FuncAnimation
import matplotlib.patches as mpatches

# =============================================================================
# COPY KEY FUNCTIONS FROM STATIC VERSION
# =============================================================================

N1 = 2 * np.pi   # Mode 1 eigenvalue
N3 = 4 * np.pi   # Mode 3 eigenvalue

def mode_shape_odd(X, N):
    """Mode shape for odd modes (j = 1, 3, 5, ...)"""
    return 1 - np.cos(N * X)

def F1_simplified(Delta, Q):
    """First kind of solution - cubic force-displacement relation"""
    Delta = np.atleast_1d(Delta)
    discriminant = 0.25 - 4/(3*Q**2)
    
    if discriminant < 0:
        return np.full_like(Delta, np.nan, dtype=float)
    
    sqrt_term = np.sqrt(discriminant)
    coeff = 3 * np.pi**4 * Q**2 / 2
    root1 = 1.5 - sqrt_term
    root2 = 1.5 + sqrt_term
    
    return coeff * Delta * (Delta - root1) * (Delta - root2)

def F3_simplified(Delta):
    """Third kind of solution - mode 2 CONSTRAINED (linear)"""
    Delta = np.atleast_1d(Delta)
    coeff = N1**2 * (N3**2 - N1**2) / 8
    offset = N3**2 / (N3**2 - N1**2)
    return coeff * (offset - Delta)

def compute_A1_from_Delta(Delta):
    """Compute first mode amplitude from center displacement."""
    return (1 - Delta) / 2

def beam_shape_at_displacement(X, Delta):
    """Compute the deflected beam shape at a given center displacement."""
    A1 = compute_A1_from_Delta(Delta)
    W1 = mode_shape_odd(X, N1)
    return A1 * W1


# =============================================================================
# INTERACTIVE VISUALIZATION WITH Q SLIDER
# =============================================================================

def create_interactive_plot():
    """
    Create an interactive plot with a slider to adjust Q value
    and see how it affects the force-displacement curve.
    """
    # Initial parameters
    Q_init = 6.0
    
    # Create figure and axes
    fig = plt.figure(figsize=(14, 6))
    
    # Main F-Δ plot
    ax1 = fig.add_axes([0.05, 0.25, 0.4, 0.65])
    # Beam shape plot
    ax2 = fig.add_axes([0.55, 0.25, 0.4, 0.65])
    # Slider axis
    ax_slider = fig.add_axes([0.15, 0.08, 0.3, 0.03])
    # Delta slider axis  
    ax_delta_slider = fig.add_axes([0.55, 0.08, 0.3, 0.03])
    
    # Data
    Delta = np.linspace(0.001, 2, 500)
    X = np.linspace(0, 1, 200)
    
    # Initial plot
    F_vals = F1_simplified(Delta, Q_init)
    F3_vals = F3_simplified(Delta)
    
    line_F1, = ax1.plot(Delta, F_vals, 'b-', linewidth=2, label=f'F₁ (Q={Q_init})')
    line_F3, = ax1.plot(Delta, F3_vals, 'r--', linewidth=1, alpha=0.5, label='F₃ limit')
    ax1.axhline(y=0, color='k', linewidth=0.5)
    ax1.set_xlabel('Δ = d/h', fontsize=11)
    ax1.set_ylabel('F (normalized force)', fontsize=11)
    ax1.set_title('Force-Displacement Curve', fontsize=12)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 2])
    
    # Current position marker
    Delta_current = 0.0
    point_marker, = ax1.plot(Delta_current, 0, 'go', markersize=12, zorder=5)
    
    # Beam shape plot
    W = beam_shape_at_displacement(X, Delta_current)
    beam_fill = ax2.fill_between(X, 0, W, alpha=0.3, color='blue')
    beam_line, = ax2.plot(X, W, 'b-', linewidth=2)
    ax2.axhline(y=0, color='k', linewidth=0.5)
    ax2.set_xlabel('X = x/l', fontsize=11)
    ax2.set_ylabel('W(X)', fontsize=11)
    ax2.set_title('Beam Shape', fontsize=12)
    ax2.set_xlim([0, 1])
    ax2.set_ylim([-1.5, 2.5])
    ax2.grid(True, alpha=0.3)
    
    # Text annotation for beam shape
    text_annotation = ax2.text(0.05, 2.2, f'Δ = {Delta_current:.2f}\nA₁ = {0.5:.2f}', fontsize=10)
    
    # Track fill object for updates
    beam_fill_obj = ax2.fill_between(X, 0, beam_shape_at_displacement(X, 0), alpha=0.3, color='blue')
    
    # Create sliders
    slider_Q = Slider(ax_slider, 'Q = h/t', 2.4, 15.0, valinit=Q_init, valstep=0.1)
    slider_Delta = Slider(ax_delta_slider, 'Δ', 0.0, 2.0, valinit=Delta_current, valstep=0.01)
    
    def update_Q(val):
        nonlocal beam_fill_obj
        Q = slider_Q.val
        F_vals = F1_simplified(Delta, Q)
        line_F1.set_ydata(F_vals)
        line_F1.set_label(f'F₁ (Q={Q:.1f})')
        ax1.legend(loc='upper right')
        
        # Update y limits based on new curve
        valid_F = F_vals[~np.isnan(F_vals)]
        if len(valid_F) > 0:
            y_margin = 0.1 * (np.max(valid_F) - np.min(valid_F))
            ax1.set_ylim([np.min(valid_F) - y_margin, np.max(valid_F) + y_margin])
        
        # Update marker position
        update_Delta(slider_Delta.val)
        fig.canvas.draw_idle()
    
    def update_Delta(val):
        nonlocal beam_fill_obj
        Delta_current = slider_Delta.val
        Q = slider_Q.val
        
        # Update marker on F-Δ curve
        F_current = F1_simplified(np.array([Delta_current]), Q)[0]
        point_marker.set_data([Delta_current], [F_current])
        
        # Update beam shape
        W = beam_shape_at_displacement(X, Delta_current)
        
        # Remove old fill and create new one
        if beam_fill_obj is not None:
            beam_fill_obj.remove()
        beam_fill_obj = ax2.fill_between(X, 0, W, alpha=0.3, color='blue')
        beam_line.set_ydata(W)
        
        # Update text
        A1 = compute_A1_from_Delta(Delta_current)
        F_str = f'{F_current:.0f}' if not np.isnan(F_current) else 'N/A'
        text_annotation.set_text(f'Δ = {Delta_current:.2f}\nA₁ = {A1:.2f}\nF = {F_str}')
        
        fig.canvas.draw_idle()
    
    slider_Q.on_changed(update_Q)
    slider_Delta.on_changed(update_Delta)
    
    # Initial update
    update_Q(Q_init)
    
    plt.suptitle('Interactive Bistable Beam Visualization\n(Use sliders to explore)', fontsize=14, y=0.98)
    
    return fig, slider_Q, slider_Delta


# =============================================================================
# ANIMATION OF SNAP-THROUGH
# =============================================================================

def create_snapthrough_animation(Q=6, save_gif=True):
    """
    Create an animation showing the snap-through process.
    
    The animation shows:
    1. Beam being pushed from Δ=0 towards Δ=2
    2. Force increasing, reaching f_top
    3. Rapid snap-through
    4. Settling at second stable position
    """
    # Set up figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Data
    Delta_full = np.linspace(0, 2, 500)
    X = np.linspace(0, 1, 200)
    F_curve = F1_simplified(Delta_full, Q)
    
    # Find key points for realistic animation timing
    valid_mask = ~np.isnan(F_curve)
    discriminant = 0.25 - 4/(3*Q**2)
    sqrt_term = np.sqrt(discriminant)
    d_top = Delta_full[np.argmax(F_curve[valid_mask])]  # Peak force
    d_bot = Delta_full[valid_mask][np.argmin(F_curve[valid_mask])]  # Min force
    
    # Animation frames:
    # - Slow push from 0 to d_top (loading phase)
    # - Fast snap from d_top to beyond d_bot (snap-through)
    # - Slow settle to Δ=2 (settling phase)
    
    n_frames_load = 60      # Frames for loading
    n_frames_snap = 20      # Frames for snap-through (fast)
    n_frames_settle = 30    # Frames for settling
    
    Delta_load = np.linspace(0, d_top, n_frames_load)
    Delta_snap = np.linspace(d_top, 1.8, n_frames_snap)
    Delta_settle = np.linspace(1.8, 2.0, n_frames_settle)
    
    Delta_animation = np.concatenate([Delta_load, Delta_snap, Delta_settle])
    n_frames = len(Delta_animation)
    
    # Plot static F-Δ curve
    ax1.plot(Delta_full, F_curve, 'b-', linewidth=2, alpha=0.5)
    ax1.axhline(y=0, color='k', linewidth=0.5)
    ax1.set_xlabel('Δ = d/h', fontsize=11)
    ax1.set_ylabel('F (normalized force)', fontsize=11)
    ax1.set_title(f'Force-Displacement (Q={Q})', fontsize=12)
    ax1.set_xlim([0, 2])
    ax1.grid(True, alpha=0.3)
    
    # Initialize animated elements
    marker, = ax1.plot([], [], 'ro', markersize=12, zorder=5)
    trace, = ax1.plot([], [], 'r-', linewidth=2, alpha=0.7)
    
    # Beam shape axes
    ax2.set_xlabel('X = x/l', fontsize=11)
    ax2.set_ylabel('W(X)', fontsize=11)
    ax2.set_title('Beam Shape', fontsize=12)
    ax2.set_xlim([0, 1])
    ax2.set_ylim([-1.5, 2.0])
    ax2.axhline(y=0, color='k', linewidth=0.5)
    ax2.grid(True, alpha=0.3)
    
    beam_line, = ax2.plot([], [], 'b-', linewidth=2)
    # Create initial fill that we'll update
    W_init = beam_shape_at_displacement(X, 0)
    beam_fill = ax2.fill_between(X, 0, W_init, alpha=0.3, color='blue')
    
    # Text for current state
    time_text = ax1.text(0.02, 0.95, '', transform=ax1.transAxes, fontsize=10,
                         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat'))
    
    # Store trace data
    trace_Delta = []
    trace_F = []
    
    def init():
        marker.set_data([], [])
        trace.set_data([], [])
        beam_line.set_data(X, W_init)
        time_text.set_text('')
        trace_Delta.clear()
        trace_F.clear()
        return marker, trace, beam_line, time_text
    
    def animate(frame):
        nonlocal beam_fill
        
        Delta_current = Delta_animation[frame]
        F_current = F1_simplified(np.array([Delta_current]), Q)[0]
        
        # Update marker
        marker.set_data([Delta_current], [F_current])
        
        # Update trace
        trace_Delta.append(Delta_current)
        trace_F.append(F_current)
        trace.set_data(trace_Delta, trace_F)
        
        # Update beam shape
        W = beam_shape_at_displacement(X, Delta_current)
        beam_line.set_data(X, W)
        
        # Update fill - remove old and create new
        beam_fill.remove()
        color = 'blue' if frame < n_frames_load else ('red' if frame < n_frames_load + n_frames_snap else 'green')
        beam_fill = ax2.fill_between(X, 0, W, alpha=0.3, color=color)
        
        # Update text
        A1 = compute_A1_from_Delta(Delta_current)
        phase = 'Loading' if frame < n_frames_load else ('SNAP!' if frame < n_frames_load + n_frames_snap else 'Settling')
        time_text.set_text(f'Phase: {phase}\nΔ = {Delta_current:.3f}\nF = {F_current:.0f}\nA₁ = {A1:.3f}')
        
        return marker, trace, beam_line, time_text, beam_fill
    
    anim = FuncAnimation(fig, animate, init_func=init, frames=n_frames,
                        interval=50, blit=False, repeat=True)
    
    plt.suptitle('Snap-Through Animation', fontsize=14)
    plt.tight_layout()
    
    if save_gif:
        print("Saving animation as GIF (this may take a moment)...")
        anim.save('./snapthrough_animation.gif', writer='pillow', fps=20, dpi=100)
        print("Saved: snapthrough_animation.gif")
    
    return fig, anim


# =============================================================================
# ANIMATION: VARYING Q TO SHOW TRANSITION TO/FROM BISTABILITY
# =============================================================================

def create_Q_sweep_animation(save_gif=True):
    """
    Animation showing how the F-Δ curve changes as Q varies.
    This illustrates the critical Q values for bistability.
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    
    Delta = np.linspace(0.001, 2, 500)
    
    # Q values to sweep through
    Q_values = np.concatenate([
        np.linspace(2.0, 10.0, 80),  # Sweep up
        np.linspace(10.0, 2.0, 80)   # Sweep back down
    ])
    
    # Critical Q values
    Q_cr1 = 2.31  # Critical Q for bistability with mode 2 constrained
    
    # Static F₃ reference line
    F3_vals = F3_simplified(Delta)
    ax.plot(Delta, F3_vals, 'r--', linewidth=1, alpha=0.5, label='F₃ (mode 3 limit)')
    ax.axhline(y=0, color='k', linewidth=0.5)
    
    # Initialize F₁ curve
    line_F1, = ax.plot([], [], 'b-', linewidth=2)
    
    # Text annotation
    text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat'))
    
    ax.set_xlabel('Δ = d/h', fontsize=12)
    ax.set_ylabel('F (normalized force)', fontsize=12)
    ax.set_title('Effect of Q on Force-Displacement Curve', fontsize=14)
    ax.set_xlim([0, 2])
    ax.set_ylim([-2500, 6000])
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    
    def init():
        line_F1.set_data([], [])
        text.set_text('')
        return line_F1, text
    
    def animate(frame):
        Q = Q_values[frame]
        F_vals = F1_simplified(Delta, Q)
        
        line_F1.set_data(Delta, F_vals)
        
        # Determine bistability status
        if Q < Q_cr1:
            status = "NOT BISTABLE\n(Q too small)"
            color = 'red'
        else:
            status = "BISTABLE\n(snap-through possible)"
            color = 'green'
        
        text.set_text(f'Q = {Q:.2f}\n{status}')
        text.set_bbox(dict(boxstyle='round', facecolor='lightyellow' if Q >= Q_cr1 else 'lightcoral'))
        
        return line_F1, text
    
    anim = FuncAnimation(fig, animate, init_func=init, frames=len(Q_values),
                        interval=50, blit=False, repeat=True)
    
    plt.tight_layout()
    
    if save_gif:
        print("Saving Q sweep animation...")
        anim.save('./Q_sweep_animation.gif', writer='pillow', fps=20, dpi=100)
        print("Saved: Q_sweep_animation.gif")
    
    return fig, anim


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CREATING INTERACTIVE VISUALIZATIONS")
    print("=" * 60)
    
    # Create snap-through animation
    print("\n1. Creating snap-through animation...")
    fig_snap, anim_snap = create_snapthrough_animation(Q=6, save_gif=True)
    
    # Create Q sweep animation
    print("\n2. Creating Q sweep animation...")
    fig_Q, anim_Q = create_Q_sweep_animation(save_gif=True)
    
    # Create static frame of interactive plot (for saving)
    print("\n3. Creating interactive plot preview...")
    fig_interactive, _, _ = create_interactive_plot()
    fig_interactive.savefig('./interactive_preview.png', dpi=150, bbox_inches='tight')
    print("   Saved: interactive_preview.png")
    
    print("\n" + "=" * 60)
    print("OUTPUTS CREATED:")
    print("=" * 60)
    print("- snapthrough_animation.gif : Animation of snap-through process")
    print("- Q_sweep_animation.gif : Animation showing effect of Q parameter")  
    print("- interactive_preview.png : Preview of interactive plot")
    print("\nNote: Interactive plots require running in a GUI environment.")
    print("The GIF animations can be viewed in any image viewer.")
    
    plt.show()
    print("\nDone!")
