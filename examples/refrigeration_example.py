"""
Usage example: solves a vapour-compression cycle, saves the T-s and p-h diagrams
and compares common refrigerants under the same operating conditions.

Run from the project root:
    python examples/refrigeration_example.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import refrigeration_cycle                                # noqa: E402
from thermocycles.plots import plot_refrigeration_ph, plot_refrigeration_Ts  # noqa: E402

IMAGES = Path(__file__).resolve().parents[1] / "images"
IMAGES.mkdir(exist_ok=True)

# Typical conditions for a domestic refrigerator / small air conditioner
COND = dict(T_evap_C=-10, T_cond_C=40, superheat_K=5, subcooling_K=3, eta_comp=0.75)

# --- 1. Single cycle --------------------------------------------------------
r = refrigeration_cycle(**COND, fluid="R134a")
r.summary()
print(f"Mass flow for 1 kW of cooling: {r.mass_flow_for_cooling(1e3) * 1e3:.2f} g/s")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
plot_refrigeration_Ts(r, ax=ax1)
plot_refrigeration_ph(r, ax=ax2)
fig.tight_layout()
fig.savefig(IMAGES / "refrigeration_Ts_ph.png", dpi=150)

# --- 2. Refrigerant comparison ----------------------------------------------
# R134a: traditional HFC (high GWP, being phased down in the EU)
# R1234yf: HFO replacement used in car air conditioning
# R290 (propane) and R600a (isobutane): natural refrigerants, very low GWP
# R32: HFC used in modern residential air conditioners and heat pumps
fluids = ["R134a", "R1234yf", "R290", "R600a", "R32"]
results = {f: refrigeration_cycle(**COND, fluid=f) for f in fluids}

print("\nRefrigerant comparison  (T_evap = -10 °C, T_cond = 40 °C, η_comp = 0.75)")
print(f"{'Fluid':>8} | {'COP':>5} | {'Vol. cap. [kJ/m³]':>17} | {'p_evap [bar]':>12} | "
      f"{'p_cond [bar]':>12} | {'T_disch [°C]':>12}")
print("-" * 82)
for f, res in results.items():
    print(f"{f:>8} | {res.cop_cooling:5.2f} | {res.volumetric_capacity / 1e3:17.0f} | "
          f"{res.states['1'].p / 1e5:12.2f} | {res.states['2'].p / 1e5:12.2f} | "
          f"{res.discharge_temperature_C:12.1f}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
ax1.bar(fluids, [res.cop_cooling for res in results.values()], color="C0")
ax1.set_ylabel("COP (cooling)")
ax1.set_title("Efficiency")
ax2.bar(fluids, [res.volumetric_capacity / 1e3 for res in results.values()], color="C1")
ax2.set_ylabel("Volumetric cooling capacity [kJ/m³]")
ax2.set_title("Compressor size (higher = smaller compressor)")
for ax in (ax1, ax2):
    ax.grid(alpha=0.3, axis="y")
fig.suptitle("Refrigerant comparison — T_evap = -10 °C, T_cond = 40 °C, η_comp = 0.75")
fig.tight_layout()
fig.savefig(IMAGES / "refrigerant_comparison.png", dpi=150)

# --- 3. COP vs evaporating temperature --------------------------------------
T_evap = np.linspace(-30, 10, 30)
fig, ax = plt.subplots(figsize=(8, 5))
for f in fluids:
    cop = [refrigeration_cycle(Te, 40, 5, 3, 0.75, f).cop_cooling for Te in T_evap]
    ax.plot(T_evap, cop, label=f)
ax.set_xlabel("Evaporating temperature [°C]")
ax.set_ylabel("COP (cooling)")
ax.set_title("COP vs evaporating temperature (T_cond = 40 °C, η_comp = 0.75)")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(IMAGES / "refrigeration_cop_vs_tevap.png", dpi=150)

print(f"\nPlots saved in: {IMAGES}")
plt.show()
