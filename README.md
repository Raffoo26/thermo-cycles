# Thermo Cycles

🇮🇹 [Versione italiana](README.it.md)

A Python simulator of thermodynamic power and refrigeration cycles using **real-fluid properties** ([CoolProp](http://www.coolprop.org/)). Built to put into practice what I study in Engineering Thermodynamics and Fluid Machinery courses.

## Features

- Solves the **Rankine cycle** (saturated or superheated steam, pump and turbine isentropic efficiencies).
- Computes thermodynamic states, work, heat, thermal efficiency, Back Work Ratio and the mass flow rate required for a given power output.
- Plots **T-s** and **p-h** diagrams with the saturation dome and the real process paths.
- Runs **parametric studies** (e.g. efficiency versus boiler pressure and turbine inlet temperature).
- Works with any CoolProp fluid: water, but also organic fluids for ORC cycles (`R245fa`, `Toluene`, ...).

![T-s and p-h diagrams](images/rankine_Ts_ph.png)

## Validation

Results are checked against worked textbook examples (Moran & Shapiro, Examples 8.1 and 8.2) by automated tests:

| Case (80 bar → 0.08 bar, saturated vapour) | Textbook | This code |
|---|---|---|
| Ideal cycle — thermal efficiency | 37.1 % | 37.1 % |
| Ideal cycle — turbine exhaust quality | 0.6745 | 0.6749 |
| η<sub>is</sub> = 0.85 — thermal efficiency | 31.4 % | 31.4 % |

The small difference in the fourth decimal place comes from the property data: CoolProp uses the IAPWS-95 formulation, the textbook uses printed steam tables.

## Example result

Cycle at 80 bar / 480 °C, condenser at 0.08 bar, isentropic efficiencies of 0.85:
thermal efficiency **33.7 %**, net work **1067 kJ/kg**, mass flow for 100 MW net **93.7 kg/s**.
The turbine exhaust quality (x = 0.874) falls below the practical limit of 0.88–0.90: this is why real plants use reheat (next module).

![Parametric study](images/rankine_parametric_study.png)

## Installation

```bash
git clone https://github.com/Raffoo26/thermo-cycles.git
cd thermo-cycles
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```python
from thermocycles import rankine_cycle
from thermocycles.plots import plot_Ts

r = rankine_cycle(p_high_bar=80, p_low_bar=0.08, T_max_C=480,
                  eta_turbine=0.85, eta_pump=0.85)
r.summary()
plot_Ts(r)
```

Full example with plots and parametric study:

```bash
python examples/rankine_example.py
```

Tests:

```bash
pytest
```

## Roadmap

- [x] Simple Rankine cycle
- [ ] Rankine with reheat and regeneration
- [ ] Vapour-compression refrigeration / heat pump cycle (COP)
- [ ] Brayton cycle (gas turbine) with recuperation
- [ ] Working fluid comparison for ORC cycles
- [ ] Interactive web app

## Author

Mechanical Engineering student.

## License

[MIT](LICENSE)
