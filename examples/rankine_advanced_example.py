"""
Usage example: reheat and regeneration in a steam power plant.
Compares the simple cycle with reheat, an open feedwater heater and both,
then studies the best extraction pressure for the feedwater heater.

Run from the project root:
    python examples/rankine_advanced_example.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import rankine_reheat_regen_cycle  # noqa: E402
from thermocycles.plots import plot_ph, plot_Ts      # noqa: E402

IMAGES = Path(__file__).resolve().parents[1] / "images"
IMAGES.mkdir(exist_ok=True)

BASE = dict(p_high_bar=80, p_low_bar=0.08, T_max_C=480, eta_turbine=0.85, eta_pump=0.85)

# --- 1. Four layouts of the same plant --------------------------------------
layouts = {
    "Simple": {},
    "Reheat (7 bar → 440 °C)": dict(p_reheat_bar=7, T_reheat_C=440),
    "Open FWH (7 bar)": dict(p_fwh_bar=7),
    "Reheat + open FWH": dict(p_reheat_bar=7, T_reheat_C=440, p_fwh_bar=7),
}
results = {name: rankine_reheat_regen_cycle(**BASE, **opts) for name, opts in layouts.items()}

print(f"{'Layout':>24} | {'η [%]':>6} | {'w_net [kJ/kg]':>13} | {'x exhaust':>9} | {'kg/s for 100 MW':>15}")
print("-" * 80)
for name, r in results.items():
    exhaust = list(r.states.values())[-1]
    x = f"{exhaust.x:.3f}" if exhaust.x is not None else "superh."
    print(f"{name:>24} | {r.efficiency * 100:6.2f} | {r.w_net / 1e3:13.1f} | {x:>9} | "
          f"{r.mass_flow_for_power(100e6):15.1f}")

r = results["Reheat + open FWH"]
r.summary()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
plot_Ts(r, ax=ax1)
plot_ph(r, ax=ax2)
fig.tight_layout()
fig.savefig(IMAGES / "rankine_reheat_regen_Ts_ph.png", dpi=150)

# --- 2. Best extraction pressure for the open feedwater heater -------------
p_fwh = np.geomspace(0.3, 60, 40)
eta = [rankine_reheat_regen_cycle(**BASE, p_fwh_bar=p).efficiency * 100 for p in p_fwh]
best = p_fwh[int(np.argmax(eta))]
fig, ax = plt.subplots(figsize=(8, 5))
ax.semilogx(p_fwh, eta, label="With open feedwater heater")
ax.axhline(results["Simple"].efficiency * 100, color="k", ls="--", lw=1, label="Simple cycle")
ax.axvline(best, color="C3", ls=":", lw=1, label=f"Best extraction ≈ {best:.1f} bar")
ax.set_xlabel("Feedwater heater (extraction) pressure [bar]")
ax.set_ylabel("Cycle efficiency [%]")
ax.set_title("Regeneration: effect of the extraction pressure (80 bar / 480 °C, η_is = 0.85)")
ax.grid(alpha=0.3, which="both")
ax.legend()
fig.tight_layout()
fig.savefig(IMAGES / "rankine_fwh_pressure_study.png", dpi=150)

print(f"\nBest extraction pressure: {best:.1f} bar  (η = {max(eta):.2f} %)")
print(f"Plots saved in: {IMAGES}")
plt.show()
