"""
Usage example: regeneration with open and closed feedwater heaters (multiple extractions).
Reproduces the layout of Moran & Shapiro Example 8.6 and shows how the efficiency grows
with the number of heaters.

Run from the project root:
    python examples/feedwater_heaters_example.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import FeedwaterHeater as FWH            # noqa: E402
from thermocycles import rankine_reheat_regen_cycle        # noqa: E402
from thermocycles.plots import plot_ph, plot_Ts            # noqa: E402

IMAGES = Path(__file__).resolve().parents[1] / "images"
IMAGES.mkdir(exist_ok=True)

# --- 1. Moran & Shapiro Example 8.6 ------------------------------------------
ttd = PropsSI("T", "P", 20e5, "Q", 0, "Water") - 273.15 - 205     # feedwater leaves at 205 °C
r = rankine_reheat_regen_cycle(80, 0.08, 480, p_reheat_bar=7, T_reheat_C=440,
                               heaters=[FWH(20, "closed", ttd), FWH(3, "open")])
r.summary()
print(f"Steam for 100 MW: {r.mass_flow_for_power(100e6) * 3600:.3g} kg/h")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
plot_Ts(r, ax=ax1, title=f"Reheat + closed heater (20 bar) + open heater (3 bar) — η = {r.efficiency * 100:.1f} %")
plot_ph(r, ax=ax2)
fig.tight_layout()
fig.savefig(IMAGES / "rankine_feedwater_heaters_Ts_ph.png", dpi=150)

# --- 2. Efficiency vs number of heaters --------------------------------------
# 165 bar / 540 °C, reheat at 35 bar to 540 °C, condenser 0.07 bar, η_t = 0.88, η_p = 0.80,
# closed heaters with TTD = 3 K and a deaerator (open heater) in the middle.
BASE = dict(p_high_bar=165, p_low_bar=0.07, T_max_C=540, p_reheat_bar=35, T_reheat_C=540,
            eta_turbine=0.88, eta_pump=0.80)
layouts = {
    "No heaters": [],
    "1 open (deaerator 7 bar)": [FWH(7, "open")],
    "1 open + 1 closed HP": [FWH(50, "closed", 3), FWH(7, "open")],
    "1 open + 2 closed HP": [FWH(50, "closed", 3), FWH(20, "closed", 3), FWH(7, "open")],
    "1 open + 2 HP + 2 LP closed": [FWH(50, "closed", 3), FWH(20, "closed", 3), FWH(7, "open"),
                                    FWH(2, "closed", 3), FWH(0.5, "closed", 3)],
    "1 open + 3 HP + 3 LP closed": [FWH(60, "closed", 3), FWH(35, "closed", 3), FWH(16, "closed", 3),
                                    FWH(7, "open"), FWH(2.5, "closed", 3), FWH(0.9, "closed", 3),
                                    FWH(0.3, "closed", 3)],
}
print(f"\n{'Layout':>30} | {'η [%]':>6} | {'feedwater T [°C]':>16} | {'total extraction':>16}")
print("-" * 78)
names, eta = [], []
for name, heaters in layouts.items():
    res = rankine_reheat_regen_cycle(**BASE, heaters=heaters)
    boiler = next(c for c in res.components if c.name == "Boiler")
    T_fw = boiler.inlets[0][0].T - 273.15
    names.append(name.replace(" + ", "\n+ "))
    eta.append(res.efficiency * 100)
    print(f"{name:>30} | {res.efficiency * 100:6.2f} | {T_fw:16.1f} | {res.extraction_fraction:16.3f}")

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(range(len(eta)), eta, color="C0")
for b, e in zip(bars, eta):
    ax.annotate(f"{e:.1f} %", (b.get_x() + b.get_width() / 2, e), xytext=(0, 3),
                textcoords="offset points", ha="center")
ax.set_xticks(range(len(eta)), names, fontsize=8)
ax.set_ylim(min(eta) - 3, max(eta) + 2)
ax.set_ylabel("Cycle efficiency [%]")
ax.set_title("Regeneration: efficiency vs number of feedwater heaters (165 bar / 540 °C, reheat)")
ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(IMAGES / "rankine_heaters_comparison.png", dpi=150)
print(f"\nPlots saved in: {IMAGES}")
plt.show()
