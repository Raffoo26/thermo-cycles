"""
Usage example: Organic Rankine Cycle (ORC) working-fluid comparison
for low-temperature heat recovery (e.g. hot water / exhaust at about 150 °C).

Run from the project root:
    python examples/orc_example.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import (critical_point, exergy_analysis, rankine_cycle,  # noqa: E402
                          saturation_pressure_bar)
from thermocycles.plots import plot_Ts                                    # noqa: E402

IMAGES = Path(__file__).resolve().parents[1] / "images"
IMAGES.mkdir(exist_ok=True)

T_SOURCE = 150      # °C, heat source
T_EVAP = 120        # °C, evaporating temperature (30 K below the source)
T_COND = 35         # °C, condensing temperature (air- or water-cooled)
SUPERHEAT = 5       # K
ETA_T, ETA_P = 0.80, 0.70

fluids = ["R245fa", "R1233zd(E)", "Isopentane", "n-Pentane", "Toluene", "R134a", "Water"]

print(f"ORC comparison — evaporating {T_EVAP} °C, condensing {T_COND} °C, "
      f"superheat {SUPERHEAT} K, η_t = {ETA_T}, η_p = {ETA_P}\n")
print(f"{'Fluid':>11} | {'T_crit':>6} | {'p_evap':>6} | {'p_cond':>6} | {'η [%]':>5} | "
      f"{'η_II [%]':>8} | {'exhaust':>12} | {'vol. ratio':>10} | {'m³/s per MW':>11}")
print("-" * 99)
results = {}
for f in fluids:
    T_crit, _ = critical_point(f)
    if T_EVAP >= T_crit:
        print(f"{f:>11} | {T_crit:6.1f} | skipped: evaporating above the critical temperature")
        continue
    p_ev, p_co = saturation_pressure_bar(f, T_EVAP), saturation_pressure_bar(f, T_COND)
    r = rankine_cycle(p_ev, p_co, T_EVAP + SUPERHEAT, ETA_T, ETA_P, f)
    ex = exergy_analysis(r, T0_C=20, T_source_C=T_SOURCE)
    s3, s4 = r.states["3"], r.states["4"]
    rho3 = PropsSI("D", "P", s3.p, "H", s3.h, f)
    rho4 = PropsSI("D", "P", s4.p, "H", s4.h, f)
    vol_ratio = rho3 / rho4                       # turbine outlet / inlet volume flow
    vol_flow_MW = r.mass_flow_for_power(1e6) / rho4   # exhaust volume flow for 1 MW net
    exhaust = f"x = {s4.x:.3f}" if s4.x is not None else f"{s4.T - 273.15:.0f} °C sup."
    results[f] = r
    print(f"{f:>11} | {T_crit:6.1f} | {p_ev:6.2f} | {p_co:6.3f} | {r.efficiency * 100:5.1f} | "
          f"{ex.efficiency * 100:8.1f} | {exhaust:>12} | {vol_ratio:10.1f} | {vol_flow_MW:11.2f}")

print("\nReading the table:")
print("- With the same temperatures, water has the highest efficiency on paper, but it condenses")
print("  under deep vacuum and its exhaust volume flow per MW is many times larger: a big,")
print("  multi-stage, expensive turbine. Organic fluids allow small, cheap single-stage turbines,")
print("  which is why ORC plants are used for heat sources below ~300 °C.")
print("- 'Dry' fluids (R245fa, R1233zd(E), pentanes, toluene) leave the turbine superheated:")
print("  no droplets, but that heat should be recovered with a recuperator.")
print("- R134a cannot evaporate at 120 °C: it is above its critical temperature.")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for ax, f in zip(axes, ["R245fa", "Isopentane"]):
    plot_Ts(results[f], ax=ax)
fig.tight_layout()
fig.savefig(IMAGES / "orc_Ts.png", dpi=150)
print(f"\nPlot saved in: {IMAGES}")
plt.show()
