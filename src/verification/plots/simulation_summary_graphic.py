"""Generate a minimal B&W table-format summary of material properties and
boundary conditions used in notebooks 3a and 4a.

Output: simulation_summary.pdf / .png  (Keynote basic template ready)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# ── Figure ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6.8), facecolor='white')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# ── Title ────────────────────────────────────────────────────────────────
ax.text(0.50, 0.96, 'FEA Verification — Material Properties & Boundary Conditions',
        ha='center', va='center', fontsize=14.5, fontweight='bold',
        family='sans-serif')

# ── Table drawing helpers ────────────────────────────────────────────────
def draw_table(ax, x0, y0, col_widths, row_height, headers, rows,
               title=None, title_size=12, header_size=10.5, body_size=10,
               pad_x=0.012):
    """Draw a simple lined table with optional title row."""
    n_cols = len(col_widths)
    n_rows = len(rows)
    total_w = sum(col_widths)
    total_h = row_height * (n_rows + 1)  # +1 for header
    if title:
        total_h += row_height * 0.8

    y_cursor = y0

    # Title row
    if title:
        h_title = row_height * 0.8
        ax.fill_between([x0, x0 + total_w], y_cursor - h_title, y_cursor,
                        color='0.15', edgecolor='black', linewidth=0.8)
        ax.text(x0 + total_w / 2, y_cursor - h_title / 2, title,
                ha='center', va='center', fontsize=title_size,
                fontweight='bold', family='sans-serif', color='white')
        y_cursor -= h_title

    # Header row
    ax.fill_between([x0, x0 + total_w], y_cursor - row_height, y_cursor,
                    color='0.88', edgecolor='black', linewidth=0.8)
    cx = x0
    for j, (hdr, cw) in enumerate(zip(headers, col_widths)):
        ax.text(cx + pad_x, y_cursor - row_height / 2, hdr,
                ha='left', va='center', fontsize=header_size,
                fontweight='bold', family='sans-serif')
        # Vertical line between columns
        if j > 0:
            ax.plot([cx, cx], [y_cursor, y_cursor - row_height * (n_rows + 1)],
                    'k-', linewidth=0.5)
        cx += cw
    y_cursor -= row_height

    # Body rows
    for i, row in enumerate(rows):
        bg = 'white' if i % 2 == 0 else '0.96'
        ax.fill_between([x0, x0 + total_w],
                        y_cursor - row_height, y_cursor,
                        color=bg, edgecolor='none')
        cx = x0
        for j, (cell, cw) in enumerate(zip(row, col_widths)):
            ax.text(cx + pad_x, y_cursor - row_height / 2, cell,
                    ha='left', va='center', fontsize=body_size,
                    family='sans-serif')
            cx += cw
        y_cursor -= row_height

    # Outer border
    y_bot = y0 - total_h
    rect = plt.Rectangle((x0, y_bot), total_w, total_h,
                          fill=False, edgecolor='black', linewidth=1.0)
    ax.add_patch(rect)
    # Horizontal lines
    y_line = y0
    if title:
        y_line -= row_height * 0.8
    for i in range(n_rows + 1):
        ax.plot([x0, x0 + total_w], [y_line, y_line], 'k-', linewidth=0.5)
        y_line -= row_height

    return y_bot


# ── Table 1: Material Properties ─────────────────────────────────────────
mat_headers = ['Property', 'Symbol', 'Value']
mat_rows = [
    ['Material',              '',   'Doped poly-Si (LPCVD)'],
    ["Young's modulus",       'E',  '160 GPa'],
    ["Poisson's ratio",       'ν',  '0.22'],
    ['Density',               'ρ',  '2330 kg/m\u00B3'],
    ['Structural thickness',  't',  '0.5 \u00B5m'],
    ['Lamé parameter',        'λ',  '51,522 MPa'],
    ['Lamé parameter',        'μ',  '65,574 MPa'],
]
mat_cols = [0.30, 0.12, 0.30]

draw_table(ax, 0.14, 0.90, mat_cols, 0.050, mat_headers, mat_rows,
           title='Material Properties')

# ── Table 2: Boundary Conditions ─────────────────────────────────────────
bc_headers = ['', 'Notebook 3a  (half-beam)', 'Notebook 4a  (full spring)']
bc_rows = [
    ['Anchor (left)',
     'x = 0 :  clamped,  u\u2093 = u\u1D67 = 0',
     'x = 0 :  clamped,  u\u2093 = u\u1D67 = 0'],
    ['Anchor (right)',
     '\u2014',
     'x = 80 \u00B5m :  clamped,  u\u2093 = u\u1D67 = 0'],
    ['Shuttle',
     'x = L :  u\u1D67 prescribed,  u\u2093 free',
     'Center :  u\u1D67 prescribed,  u\u2093 free'],
    ['Formulation',
     'Geom. nonlinear (NLGEOM)',
     'Total Lagrangian,  St. Venant\u2013Kirchhoff'],
    ['Element type',
     'CPE3  (plane-strain triangle)',
     'P1  (plane-strain triangle)'],
    ['Analysis type',
     '2D plane strain',
     '2D plane strain'],
]
bc_cols = [0.17, 0.36, 0.36]

draw_table(ax, 0.055, 0.47, bc_cols, 0.050, bc_headers, bc_rows,
           title='Boundary Conditions & Constraints')

# ── Shared note ──────────────────────────────────────────────────────────
ax.text(0.055, 0.08,
        'Both analyses assume plane-strain conditions with thickness t = 0.5 \u00B5m '
        'and geometrically nonlinear (large-deformation) kinematics.',
        ha='left', va='center', fontsize=9, family='sans-serif', color='0.35',
        style='italic')

# ── Save ─────────────────────────────────────────────────────────────────
fig.savefig('src/verification/plots/simulation_summary.pdf',
            bbox_inches='tight', facecolor='white', dpi=300)
fig.savefig('src/verification/plots/simulation_summary.png',
            bbox_inches='tight', facecolor='white', dpi=200)
print("Saved: src/verification/plots/simulation_summary.pdf")
print("Saved: src/verification/plots/simulation_summary.png")
