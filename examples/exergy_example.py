"""
Usage example: exergy (second-law) analysis — where is the useful work lost?

Run from the project root:
    python examples/exergy_example.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import exergy_analysis, rankine_reheat_regen_cycle, refrigeration_cycle  # noqa: E402
from thermocycles.plots import plot_exergy                                                # noqa: E402

IMAGES = Path(__file__).resolve().parents[1] / "images"
IMAGES.mkdir(exist_ok=True)

# Steam plant with reheat and an open feedwater heater; flame / flue gas at 1200 °C
plant = rankine_reheat_regen_cycle(80, 0.08, 480, p_reheat_bar=7, T_reheat_C=440, p_fwh_bar=7,
                                   eta_turbine=0.85, eta_pump=0.85)
ex_plant = exergy_analysis(plant, T0_C=20, T_source_C=1200)
print(f"First-law efficiency: {plant.efficiency * 100:.1f} %")
ex_plant.summary()

# Domestic refrigerator: cabinet at 4 °C, kitchen at 25 °C
fridge = refrigeration_cycle(-10, 40, 5, 3, 0.75, "R600a")
ex_fridge = exergy_analysis(fridge, T0_C=25, T_cold_C=4)
print(f"\nCOP: {fridge.cop_cooling:.2f}")
ex_fridge.summary()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
plot_exergy(ex_plant, ax=ax1, title=f"Steam plant — η_II = {ex_plant.efficiency * 100:.1f} % "
                                    "(source at 1200 °C, T0 = 20 °C)")
plot_exergy(ex_fridge, ax=ax2, title=f"Refrigerator R600a — η_II = {ex_fridge.efficiency * 100:.1f} % "
                                     "(cabinet 4 °C, kitchen 25 °C)")
fig.tight_layout()
fig.savefig(IMAGES / "exergy_destruction.png", dpi=150)
print(f"\nPlot saved in: {IMAGES}")
plt.show()
