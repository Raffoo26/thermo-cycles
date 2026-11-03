"""
Usage example: gas turbine (Brayton) cycle with and without regenerator.
Shows the classic result: without regeneration the efficiency grows with the
pressure ratio; with regeneration it is highest at LOW pressure ratios.

Run from the project root:
    python examples/brayton_example.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import brayton_cycle  # noqa: E402
from thermocycles.plots import plot_Ts  # noqa: E402

IMAGES = Path(__file__).resolve().parents[1] / "images"
IMAGES.mkdir(exist_ok=True)

# --- 1. Single cycle --------------------------------------------------------
r = brayton_cycle(pressure_ratio=10, T_turbine_in_C=1200, T_in_C=15,
                  eta_comp=0.86, eta_turb=0.89, regen_effectiveness=0.8)
r.summary()
print(f"Air mass flow for 50 MW: {r.mass_flow_for_power(50e6):.1f} kg/s")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
plot_Ts(r, ax=ax1, title=f"With regenerator (ε = 0.8) — η = {r.efficiency * 100:.1f} %")
r0 = brayton_cycle(10, 1200, 15, eta_comp=0.86, eta_turb=0.89)
plot_Ts(r0, ax=ax2, title=f"Without regenerator — η = {r0.efficiency * 100:.1f} %")
fig.tight_layout()
fig.savefig(IMAGES / "brayton_Ts.png", dpi=150)

# --- 2. Efficiency vs pressure ratio ----------------------------------------
ratios = np.linspace(2, 30, 60)
fig, ax = plt.subplots(figsize=(8, 5))
for eps, style in ((0.0, "-"), (0.6, "--"), (0.8, "-.")):
    eta = []
    for pr in ratios:
        res = brayton_cycle(pr, 1200, 15, eta_comp=0.86, eta_turb=0.89, regen_effectiveness=eps)
        eta.append(res.efficiency * 100 if res.regen_effectiveness == eps else np.nan)
    label = "No regenerator" if eps == 0 else f"Regenerator ε = {eps}"
    ax.plot(ratios, eta, style, label=label)
ax.set_xlabel("Compressor pressure ratio [-]")
ax.set_ylabel("Cycle efficiency [%]")
ax.set_title("Brayton: efficiency vs pressure ratio (TIT = 1200 °C, η_c = 0.86, η_t = 0.89)")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(IMAGES / "brayton_pressure_ratio_study.png", dpi=150)

print(f"\nPlots saved in: {IMAGES}")
plt.show()
