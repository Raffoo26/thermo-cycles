"""
Usage example: combined gas–steam cycle with a heat recovery steam generator (HRSG).

Run from the project root:
    python examples/combined_cycle_example.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import (FeedwaterHeater, brayton_cycle, combined_cycle,      # noqa: E402
                          exergy_analysis, rankine_reheat_regen_cycle)
from thermocycles.plots import plot_exergy, plot_hrsg, plot_Ts                 # noqa: E402

IMAGES = Path(__file__).resolve().parents[1] / "images"
IMAGES.mkdir(exist_ok=True)

# Gas turbine: pressure ratio 18, turbine inlet 1350 °C, intake 15 °C
gas = brayton_cycle(18, 1350, T_in_C=15, p_in_bar=1.013, eta_comp=0.88, eta_turb=0.90)
# Steam cycle: single-pressure HRSG at 40 bar, 520 °C, deaerator at 1.5 bar
steam = rankine_reheat_regen_cycle(40, 0.05, 520, eta_turbine=0.88, eta_pump=0.80,
                                   heaters=[FeedwaterHeater(1.5, "open")])
cc = combined_cycle(gas, steam, T_stack_C=170)
cc.summary()
m_air, m_steam = cc.mass_flows_for_power(400e6)
print(f"For 400 MW: air {m_air:.0f} kg/s, steam {m_steam:.1f} kg/s, "
      f"gas turbine {m_air * gas.w_net / 1e6:.0f} MW + steam turbine {m_steam * steam.w_net / 1e6:.0f} MW")

ex = exergy_analysis(cc, T0_C=15, T_source_C=1800)
ex.summary()

fig, axes = plt.subplots(1, 3, figsize=(21, 6))
plot_Ts(gas, ax=axes[0], title=f"Gas turbine — η = {gas.efficiency * 100:.1f} %")
plot_Ts(steam, ax=axes[1], title=f"Steam cycle — η = {steam.efficiency * 100:.1f} %")
plot_hrsg(cc, ax=axes[2])
fig.suptitle(f"Combined cycle — η = {cc.efficiency * 100:.1f} %", fontsize=15)
fig.tight_layout()
fig.savefig(IMAGES / "combined_cycle.png", dpi=150)

# --- Efficiency and pinch point vs stack temperature and steam pressure ------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
for p in (20, 40, 60, 80):
    st = rankine_reheat_regen_cycle(p, 0.05, 520, eta_turbine=0.88, eta_pump=0.80,
                                    heaters=[FeedwaterHeater(1.5, "open")])
    T_stack = np.linspace(120, 260, 50)
    eta, pinch = [], []
    for Ts in T_stack:
        try:
            c = combined_cycle(gas, st, Ts)
            eta.append(c.efficiency * 100)
            pinch.append(c.pinch_K)
        except ValueError:                 # pinch violated: not a feasible design
            eta.append(np.nan)
            pinch.append(np.nan)
    ax1.plot(T_stack, eta, label=f"{p} bar")
    ax2.plot(T_stack, pinch, label=f"{p} bar")
ax2.axhspan(0, 8, color="C3", alpha=0.1, label="pinch < 8 K (impractical)")
ax1.set_ylabel("Combined efficiency [%]")
ax2.set_ylabel("Pinch point [K]")
for ax in (ax1, ax2):
    ax.set_xlabel("Stack temperature [°C]")
    ax.grid(alpha=0.3)
    ax.legend(title="HRSG pressure")
fig.suptitle("Single-pressure HRSG: lower stack temperature = more heat recovered, until the pinch closes")
fig.tight_layout()
fig.savefig(IMAGES / "combined_stack_study.png", dpi=150)

fig, ax = plt.subplots(figsize=(9, 4.5))
plot_exergy(ex, ax=ax, title=f"Combined cycle exergy destruction — η_II = {ex.efficiency * 100:.1f} %")
fig.tight_layout()
fig.savefig(IMAGES / "combined_exergy.png", dpi=150)
print(f"\nPlots saved in: {IMAGES}")
plt.show()
