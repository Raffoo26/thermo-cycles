# Thermo Cycles

🇮🇹 [Versione italiana](README.it.md)

A Python simulator of thermodynamic power and refrigeration cycles using **real-fluid properties** ([CoolProp](http://www.coolprop.org/)). Built to put into practice what I study in Engineering Thermodynamics and Fluid Machinery courses.

## Features

- Solves the **Rankine cycle** (saturated or superheated steam, pump and turbine isentropic efficiencies): thermal efficiency, Back Work Ratio, mass flow for a given power output.
- Solves the **vapour-compression refrigeration / heat pump cycle** (superheat, subcooling, compressor isentropic efficiency): COP for cooling and heating, Carnot COP, second-law efficiency, pressure ratio, discharge temperature, volumetric cooling capacity.
- Compares **refrigerants** under the same operating conditions (R134a, R1234yf, R290, R600a, R32, ...).
- Plots **T-s** and **p-h** diagrams with the saturation dome and the real process paths.
- Runs **parametric studies** (e.g. efficiency versus boiler pressure and turbine inlet temperature).
- Works with any CoolProp fluid: water, but also organic fluids for ORC cycles (`R245fa`, `Toluene`, ...).

![T-s and p-h diagrams](images/rankine_Ts_ph.png)

## Validation

Results are checked against worked textbook examples (Moran & Shapiro) by automated tests:

**Rankine cycle** (Examples 8.1 and 8.2 — 80 bar → 0.08 bar, saturated vapour)

| Quantity | Textbook | This code |
|---|---|---|
| Ideal cycle — thermal efficiency | 37.1 % | 37.1 % |
| Ideal cycle — turbine exhaust quality | 0.6745 | 0.6749 |
| η<sub>is</sub> = 0.85 — thermal efficiency | 31.4 % | 31.4 % |

**Refrigeration cycle** (Examples 10.1 and 10.2 — R-134a, −10 °C evaporator, 9 bar condenser, 0.08 kg/s)

| Quantity | Textbook | This code |
|---|---|---|
| Ideal cycle — COP | 4.57 | 4.58 |
| Ideal cycle — compressor power | 2.48 kW | 2.50 kW |
| Ideal cycle — cooling capacity | 11.34 kW | 11.43 kW |
| η<sub>comp</sub> = 0.80 — COP | 3.66 | 3.66 |

Small deviations (below 1 %) come from the property data: CoolProp uses reference equations of state (IAPWS-95 for water), the textbook uses printed tables.

## Example results

### Rankine cycle

Cycle at 80 bar / 480 °C, condenser at 0.08 bar, isentropic efficiencies of 0.85:
thermal efficiency **33.7 %**, net work **1067 kJ/kg**, mass flow for 100 MW net **93.7 kg/s**.
The turbine exhaust quality (x = 0.874) falls below the practical limit of 0.88–0.90: this is why real plants use reheat (next module).

![Parametric study](images/rankine_parametric_study.png)

### Refrigeration cycle and refrigerant comparison

Domestic refrigerator / small air conditioner conditions: evaporator at −10 °C, condenser at 40 °C, 5 K superheat, 3 K subcooling, compressor isentropic efficiency 0.75.

![Refrigeration T-s and p-h diagrams](images/refrigeration_Ts_ph.png)

| Refrigerant | COP | Vol. capacity [kJ/m³] | p<sub>evap</sub> [bar] | p<sub>cond</sub> [bar] | Discharge T [°C] |
|---|---|---|---|---|---|
| R134a | 3.13 | 1421 | 2.01 | 10.17 | 61.9 |
| R1234yf | 2.98 | 1354 | 2.22 | 10.18 | 49.7 |
| R290 (propane) | 3.09 | 2035 | 3.45 | 13.69 | 61.1 |
| R600a (isobutane) | 3.20 | 766 | 1.08 | 5.31 | 51.5 |
| R32 | 3.01 | 3837 | 5.83 | 24.78 | 103.7 |

What the numbers show:
- **R600a** has the best COP but the lowest volumetric capacity: it needs a large compressor, which is why it is used in small domestic refrigerators.
- **R32** has about 2.7× the volumetric capacity of R134a (much smaller compressor) but a discharge temperature above 100 °C and condensing pressures near 25 bar.
- **R290** is a good compromise: COP close to R134a with about 40 % more volumetric capacity, and a natural refrigerant with very low GWP — a key option under the EU F-gas phase-down.
- **R1234yf** behaves almost like R134a (it was designed as a drop-in replacement) with a slightly lower COP.

![Refrigerant comparison](images/refrigerant_comparison.png)

![COP vs evaporating temperature](images/refrigeration_cop_vs_tevap.png)

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

```python
from thermocycles import refrigeration_cycle
from thermocycles.plots import plot_refrigeration_ph

r = refrigeration_cycle(T_evap_C=-10, T_cond_C=40, superheat_K=5,
                        subcooling_K=3, eta_comp=0.75, fluid="R290")
r.summary()
plot_refrigeration_ph(r)
```

Full examples with plots:

```bash
python examples/rankine_example.py
python examples/refrigeration_example.py
```

Tests:

```bash
pytest
```

## Roadmap

- [x] Simple Rankine cycle
- [ ] Rankine with reheat and regeneration
- [x] Vapour-compression refrigeration / heat pump cycle with refrigerant comparison
- [ ] Brayton cycle (gas turbine) with recuperation
- [ ] Working fluid comparison for ORC cycles
- [ ] Interactive web app

## Author

Mechanical Engineering student.

## License

[MIT](LICENSE)
