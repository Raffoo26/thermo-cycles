"""
Usage example: solves a Rankine cycle, saves the T-s and p-h diagrams
and runs a parametric study of efficiency versus boiler pressure.

Run from the project root:
    python examples/rankine_example.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import rankine_cycle            # noqa: E402
from thermocycles.plots import plot_ph, plot_Ts  # noqa: E402

IMAGES = Path(__file__).resolve().parents[1] / "images"
IMAGES.mkdir(exist_ok=True)

# --- 1. Single cycle --------------------------------------------------------
r = rankine_cycle(p_high_bar=80, p_low_bar=0.08, T_max_C=480,
                  eta_turbine=0.85, eta_pump=0.85)
r.summary()
print(f"Mass flow for 100 MW net: {r.mass_flow_for_power(100e6):.1f} kg/s")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
plot_Ts(r, ax=ax1)
plot_ph(r, ax=ax2)
fig.tight_layout()
fig.savefig(IMAGES / "rankine_Ts_ph.png", dpi=150)

# --- 2. Parametric study: efficiency vs boiler pressure ---------------------
pressures = np.linspace(20, 160, 30)  # bar
fig, ax = plt.subplots(figsize=(8, 5))
for T_max in (400, 480, 560):
    eta = [rankine_cycle(p, 0.08, T_max, 0.85, 0.85).efficiency * 100 for p in pressures]
    ax.plot(pressures, eta, label=f"Turbine inlet T = {T_max} °C")
ax.set_xlabel("Boiler pressure [bar]")
ax.set_ylabel("Cycle efficiency [%]")
ax.set_title("Rankine: effect of pressure and superheat (p_cond = 0.08 bar, η_is = 0.85)")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(IMAGES / "rankine_parametric_study.png", dpi=150)

print(f"\nPlots saved in: {IMAGES}")
plt.show()
