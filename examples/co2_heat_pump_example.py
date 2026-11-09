"""
Usage example: transcritical CO₂ heat pump — the optimal gas cooler pressure.

Run from the project root:
    python examples/co2_heat_pump_example.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import exergy_analysis, optimal_high_pressure, transcritical_heat_pump  # noqa: E402
from thermocycles.plots import plot_ph, plot_Ts                                           # noqa: E402

IMAGES = Path(__file__).resolve().parents[1] / "images"
IMAGES.mkdir(exist_ok=True)

T_EVAP, SUPERHEAT, ETA = 0, 5, 0.70


def liao(t_e, t_gc):
    """Optimal pressure correlation of Liao, Zhao & Jakobsen (2000) [bar]."""
    return (2.778 - 0.0157 * t_e) * t_gc + (0.381 * t_e - 9.34)


# --- 1. Domestic hot water heat pump at the optimal pressure ----------------
p_opt, r = optimal_high_pressure(T_EVAP, 35, SUPERHEAT, ETA)
print(f"Optimal gas cooler pressure: {p_opt:.1f} bar (Liao correlation: {liao(T_EVAP, 35):.1f} bar)")
r.summary()
ex = exergy_analysis(r, T0_C=7, T_user_C=35)
ex.summary()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
plot_Ts(r, ax=ax1)
plot_ph(r, ax=ax2)
fig.tight_layout()
fig.savefig(IMAGES / "co2_heat_pump_Ts_ph.png", dpi=150)

# --- 2. COP vs gas cooler pressure: the optimum ------------------------------
fig, ax = plt.subplots(figsize=(9, 5.5))
print(f"\n{'T_gc,out [°C]':>13} | {'p_opt [bar]':>11} | {'Liao [bar]':>10} | {'COP heating':>11}")
for k, T_gc in enumerate((35, 40, 45, 50)):   # above 31 °C (critical point): truly transcritical
    p = np.linspace(75, 150, 120)
    cop = []
    for pp in p:
        try:
            cop.append(transcritical_heat_pump(T_EVAP, pp, T_gc, SUPERHEAT, ETA).cop_heating)
        except ValueError:
            cop.append(np.nan)
    p_o, best = optimal_high_pressure(T_EVAP, T_gc, SUPERHEAT, ETA)
    ax.plot(p, cop, color=f"C{k}", label=f"gas cooler outlet {T_gc} °C")
    ax.plot(p_o, best.cop_heating, "o", color=f"C{k}")
    ax.axvline(liao(T_EVAP, T_gc), color=f"C{k}", ls=":", lw=1)
    print(f"{T_gc:13d} | {p_o:11.1f} | {liao(T_EVAP, T_gc):10.1f} | {best.cop_heating:11.2f}")
ax.set_xlabel("Gas cooler pressure [bar]")
ax.set_ylabel("COP heating")
ax.set_title("Transcritical CO₂: COP vs high pressure (dots = optimum, dotted = Liao correlation)")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(IMAGES / "co2_cop_vs_pressure.png", dpi=150)
print(f"\nPlots saved in: {IMAGES}")
plt.show()
