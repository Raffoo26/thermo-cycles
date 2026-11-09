# Thermo Cycles

🇮🇹 [Versione italiana](README.it.md)

[![Web app](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://thermo-cycles.streamlit.app)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Raffoo26/thermo-cycles/blob/main/notebooks/thermo_cycles_demo.ipynb)

**▶ Try it online: [thermo-cycles.streamlit.app](https://thermo-cycles.streamlit.app)**

A Python simulator of thermodynamic power, combined, refrigeration and heat pump cycles using **real-fluid properties** ([CoolProp](http://www.coolprop.org/)), with **exergy analysis**, an **interactive simulator**, a **web app** and a browser notebook. Built to put into practice what I study in Engineering Thermodynamics and Fluid Machinery courses. Every solver is **validated against worked textbook examples**.

## Try it without installing anything

- **Google Colab**: click the *Open in Colab* badge above, run the *Setup* cell, then change the values in the forms. Needs only a Google account.
- **Web app**: open [thermo-cycles.streamlit.app](https://thermo-cycles.streamlit.app) from any computer or phone. If the app has been idle it may need a minute to wake up; if some fields do not load, reload the page or try another browser.
- **On your computer**: see [Installation](#installation), then `python simulate.py`.

## Features

| Module | What it does |
|---|---|
| **Rankine cycle** | Simple, with **reheat**, with **regeneration** through any number of **open and closed feedwater heaters** (multiple extractions, drains cascaded backward, terminal temperature difference). Steam plants and **ORC** with organic fluids. Efficiency, Back Work Ratio, extraction fractions, mass flow for a given power. |
| **Refrigeration / heat pump** | Vapour compression with superheat, subcooling and compressor efficiency. COP (cooling and heating), Carnot COP, pressure ratio, discharge temperature, volumetric capacity. |
| **Brayton cycle** | Gas turbine with real-gas air, compressor/turbine efficiencies and **regenerator**. |
| **Combined cycle** | Gas turbine + steam cycle coupled by a heat recovery steam generator (HRSG): stack temperature, **pinch point**, steam-to-air ratio, power split, T-Q diagram. |
| **Transcritical CO₂ heat pump** | Gas cooler above the critical point, Lorenz COP, **optimal high pressure** search. |
| **Exergy analysis** | Exergy destroyed in every component (Gouy–Stodola) and second-law efficiency, for every cycle. |
| **Diagrams** | **T-s** and **p-h** diagrams with saturation dome and real process paths, HRSG **T-Q** diagram, exergy bar charts, parametric studies. |
| **Interfaces** | Interactive terminal simulator, Streamlit web app, Colab notebook, Python API. |

Works with any CoolProp fluid: water, refrigerants (R134a, R1234yf, R290, R600a, R32, R410A, ammonia…), organic fluids (R245fa, R1233zd(E), pentanes, toluene…) and gases (air, nitrogen, helium, CO₂).

![Rankine cycle with reheat, a closed and an open feedwater heater](images/rankine_feedwater_heaters_Ts_ph.png)

## Validation

Every solver is checked by automated tests (72 tests) against worked examples of Moran & Shapiro, *Fundamentals of Engineering Thermodynamics*. Deviations stay below 1–2 % and come from the property data (CoolProp uses reference equations of state, the textbook uses printed tables).

**Rankine cycle** (8 MPa / 480 °C or saturated vapour, condenser 8 kPa)

| Example | Quantity | Textbook | This code |
|---|---|---|---|
| 8.1 ideal, saturated vapour | thermal efficiency | 37.1 % | 37.1 % |
| 8.1 ideal, saturated vapour | turbine exhaust quality | 0.6745 | 0.6749 |
| 8.2 η<sub>is</sub> = 0.85 | thermal efficiency | 31.4 % | 31.4 % |
| 8.3 reheat (7 bar → 440 °C) | thermal efficiency | 40.3 % | 40.3 % |
| 8.4 reheat, η<sub>t</sub> = 0.85 | thermal efficiency | 35.1 % | 35.1 % |
| 8.5 open feedwater heater (7 bar), η<sub>t</sub> = 0.85 | thermal efficiency | 36.9 % | 36.9 % |
| 8.5 open feedwater heater, 100 MW net | steam mass flow | 3.69·10⁵ kg/h | 3.69·10⁵ kg/h |
| 8.6 reheat + closed heater (20 bar) + open heater (3 bar) | thermal efficiency | 43.1 % | 43.1 % |
| 8.6 same, 100 MW net | steam mass flow | 2.8·10⁵ kg/h | 2.79·10⁵ kg/h |
| 8.6 same | extraction fractions | 0.1522 / 0.0941 | 0.1496 / 0.0948 |

**Refrigeration cycle** (R-134a, −10 °C evaporator, 9 bar condenser, 0.08 kg/s)

| Example | Quantity | Textbook | This code |
|---|---|---|---|
| 10.1 ideal | COP | 4.57 | 4.58 |
| 10.1 ideal | compressor power | 2.48 kW | 2.50 kW |
| 10.1 ideal | cooling capacity | 11.34 kW | 11.43 kW |
| 10.2 η<sub>comp</sub> = 0.80 | COP | 3.66 | 3.66 |

**Brayton cycle** (air, 100 kPa / 300 K, pressure ratio 10, turbine inlet 1400 K)

| Example | Quantity | Textbook | This code |
|---|---|---|---|
| 9.4 ideal | thermal efficiency | 45.7 % | 45.7 % |
| 9.4 ideal | Back Work Ratio | 39.6 % | 39.6 % |
| 9.5 η<sub>c</sub> = η<sub>t</sub> = 0.80 | thermal efficiency | 24.8 % | 24.9 % |
| 9.5 η<sub>c</sub> = η<sub>t</sub> = 0.80 | Back Work Ratio | 61.9 % | 61.9 % |
| 9.6 regenerator ε = 0.80 | thermal efficiency | 56.8 % | 56.8 % |

**Combined cycle** (Example 9.12 — 45 MW; gas: pressure ratio 12, 1400 K, η<sub>c</sub> = 0.84, η<sub>t</sub> = 0.88, exhaust leaves the HRSG at 400 K; steam: 8 MPa / 400 °C, 8 kPa, η<sub>t</sub> = 0.90, η<sub>p</sub> = 0.80)

| Quantity | Textbook | This code |
|---|---|---|
| air mass flow | 100.87 kg/s | 100.8 kg/s |
| steam mass flow | 15.6 kg/s | 15.6 kg/s |

The resulting combined efficiency is 52.7 %. The code also finds a pinch point of only 2.4 K: the textbook design is at the limit of feasibility (a real HRSG needs about 8–15 K), and the program warns about it.

**Transcritical CO₂ heat pump** — there is no worked textbook example, so the optimal gas cooler pressure is compared with the correlation of Liao, Zhao & Jakobsen, *Applied Thermal Engineering* 20 (2000): p<sub>opt</sub> = (2.778 − 0.0157 t<sub>e</sub>) t<sub>gc</sub> + (0.381 t<sub>e</sub> − 9.34) [bar, °C].

| Evaporating / gas cooler outlet | Liao correlation | This code |
|---|---|---|
| 0 °C / 35 °C | 87.9 bar | 87.4 bar |
| 0 °C / 40 °C | 101.8 bar | 101.3 bar |
| 0 °C / 45 °C | 115.7 bar | 115.9 bar |
| 0 °C / 50 °C | 129.6 bar | 131.5 bar |

The exergy analysis is checked by closing the exergy balance (fuel = product + destruction) on every cycle.

## Example results

### Steam power plant: reheat and regeneration

80 bar / 480 °C, condenser at 0.08 bar, isentropic efficiencies 0.85:

| Layout | Efficiency | Net work [kJ/kg] | Exhaust quality | Steam for 100 MW [kg/s] |
|---|---|---|---|---|
| Simple | 33.7 % | 1067 | 0.874 | 93.7 |
| Reheat (7 bar → 440 °C) | 35.1 % | 1293 | 0.996 | 77.4 |
| Open feedwater heater (7 bar) | 36.9 % | 975 | 0.864 | 102.6 |
| Reheat + open feedwater heater | 37.2 % | 1138 | 0.996 | 87.9 |

- The simple cycle ends with too much liquid at the turbine exhaust (x = 0.874, below the practical limit of 0.88–0.90): **reheat** fixes it and raises the net work per kg.
- **Regeneration** raises the efficiency most, because the water enters the boiler hotter; the best extraction pressure here is about 9 bar.

![Parametric study](images/rankine_parametric_study.png)
![Best feedwater heater pressure](images/rankine_fwh_pressure_study.png)

### Multiple feedwater heaters (open and closed)

Large steam plants bleed steam from the turbine at several pressures to preheat the feedwater. Closed heaters are shell-and-tube exchangers (the feedwater leaves a few kelvin, the *TTD*, below the saturation temperature of the bled steam, and the condensed steam is throttled to the next heater); the open heater (deaerator) mixes the streams.

165 bar / 540 °C, reheat at 35 bar to 540 °C, condenser 0.07 bar, η<sub>t</sub> = 0.88, η<sub>p</sub> = 0.80, TTD = 3 K:

| Layout | Efficiency | Feedwater to boiler | Total extraction |
|---|---|---|---|
| No heaters | 39.9 % | 40 °C | 0 |
| 1 open (deaerator, 7 bar) | 43.2 % | 168 °C | 0.18 |
| 1 open + 1 closed HP | 43.9 % | 261 °C | 0.32 |
| 1 open + 2 closed HP | 44.5 % | 261 °C | 0.32 |
| 1 open + 2 HP + 2 LP closed | 45.7 % | 261 °C | 0.34 |
| 1 open + 3 HP + 3 LP closed | 46.2 % | 273 °C | 0.36 |

Each heater adds a little less than the previous one: real plants stop at 6–8 heaters, where the extra efficiency no longer pays for the extra equipment.

![Efficiency vs number of feedwater heaters](images/rankine_heaters_comparison.png)

### Refrigeration cycle and refrigerant comparison

Domestic refrigerator / small air conditioner: evaporator at −10 °C, condenser at 40 °C, 5 K superheat, 3 K subcooling, compressor efficiency 0.75.

![Refrigeration T-s and p-h diagrams](images/refrigeration_Ts_ph.png)

| Refrigerant | COP | Vol. capacity [kJ/m³] | p<sub>evap</sub> [bar] | p<sub>cond</sub> [bar] | Discharge T [°C] |
|---|---|---|---|---|---|
| R134a | 3.13 | 1421 | 2.01 | 10.17 | 61.9 |
| R1234yf | 2.98 | 1354 | 2.22 | 10.18 | 49.7 |
| R290 (propane) | 3.09 | 2035 | 3.45 | 13.69 | 61.1 |
| R600a (isobutane) | 3.20 | 766 | 1.08 | 5.31 | 51.5 |
| R32 | 3.01 | 3837 | 5.83 | 24.78 | 103.7 |

- **R600a** has the best COP but the lowest volumetric capacity: it needs a large compressor, which is why it is used in small domestic refrigerators.
- **R32** has about 2.7× the volumetric capacity of R134a (much smaller compressor) but a discharge temperature above 100 °C and condensing pressures near 25 bar.
- **R290** is a good compromise: COP close to R134a with about 40 % more volumetric capacity, and a natural refrigerant with very low GWP — a key option under the EU F-gas phase-down.
- **R1234yf** behaves almost like R134a (it was designed as a drop-in replacement) with a slightly lower COP.

![Refrigerant comparison](images/refrigerant_comparison.png)
![COP vs evaporating temperature](images/refrigeration_cop_vs_tevap.png)

### Gas turbine (Brayton)

Pressure ratio 10, turbine inlet 1200 °C, intake at 15 °C, η<sub>c</sub> = 0.86, η<sub>t</sub> = 0.89: efficiency **35.0 %** without regenerator, **48.0 %** with a regenerator of effectiveness 0.8 (exhaust cooled from 633 °C to 385 °C). 50 MW need about 142 kg/s of air.

![Brayton T-s diagrams](images/brayton_Ts.png)

Without regeneration the efficiency keeps growing with the pressure ratio; **with regeneration it peaks at low pressure ratios**, because the hot turbine exhaust has more heat to give back to the compressed air.

![Brayton efficiency vs pressure ratio](images/brayton_pressure_ratio_study.png)

### Combined cycle (gas turbine + steam)

Gas turbine with pressure ratio 18, turbine inlet 1350 °C, intake 15 °C (η<sub>c</sub> = 0.88, η<sub>t</sub> = 0.90); single-pressure HRSG at 40 bar / 520 °C with a deaerator at 1.5 bar; stack at 170 °C:

| | Efficiency |
|---|---|
| Gas turbine alone | 41.9 % |
| Steam cycle alone | 36.9 % |
| **Combined cycle** | **58.0 %** |

The gas turbine exhaust (610 °C) would be wasted in a simple-cycle plant; here it produces 0.155 kg of steam per kg of air and 28 % of the total power. For 400 MW the plant needs 640 kg/s of air and 99 kg/s of steam (289 MW gas turbine + 111 MW steam turbine). The pinch point is 12.7 K.

![Combined cycle: gas turbine, steam cycle and HRSG T-Q diagram](images/combined_cycle.png)

With a single-pressure HRSG, cooling the stack further recovers more heat, until the pinch point closes; higher steam pressures close it sooner. This is why modern plants use HRSGs with two or three pressure levels.

![Stack temperature and pinch point](images/combined_stack_study.png)

### Organic Rankine Cycle (ORC) for low-temperature heat

Heat source at about 150 °C, evaporating at 120 °C (+5 K superheat), condensing at 35 °C, η<sub>t</sub> = 0.80, η<sub>p</sub> = 0.70:

| Fluid | p<sub>evap</sub> [bar] | p<sub>cond</sub> [bar] | Efficiency | Turbine exhaust | Volume ratio | Exhaust volume flow [m³/s per MW] |
|---|---|---|---|---|---|---|
| R245fa | 19.30 | 2.120 | 13.0 % | superheated (64 °C) | 10.6 | 3.0 |
| R1233zd(E) | 15.79 | 1.837 | 13.4 % | superheated (62 °C) | 9.5 | 3.4 |
| Isopentane | 10.86 | 1.290 | 13.1 % | superheated (78 °C) | 9.2 | 4.8 |
| n-Pentane | 9.07 | 0.977 | 13.3 % | superheated (77 °C) | 9.9 | 6.0 |
| Toluene | 1.31 | 0.062 | 14.9 % | superheated (66 °C) | 18.7 | 62.9 |
| Water | 1.99 | 0.056 | 16.2 % | wet (x = 0.891) | 24.8 | 54.0 |

Water has the highest efficiency on paper, but it condenses under deep vacuum and needs **about 18 times the exhaust volume flow** of R245fa: a large, multi-stage, expensive turbine. Organic fluids allow small single-stage turbines, which is why ORC plants are used for heat sources below about 300 °C. "Dry" fluids leave the turbine superheated (no droplets), and that heat is normally recovered with a recuperator. R134a cannot be used here: 120 °C is above its critical temperature.

![ORC T-s diagrams](images/orc_Ts.png)

### Transcritical CO₂ heat pump

CO₂ (R744) is a natural refrigerant with a critical point at only 31 °C, so heat pumps that heat water reject heat **above the critical pressure**, in a gas cooler without condensation. The high pressure is then a free design choice, and the COP has a maximum:

| Gas cooler outlet | Optimal pressure | COP heating |
|---|---|---|
| 35 °C | 87.4 bar | 3.47 |
| 40 °C | 101.3 bar | 2.97 |
| 45 °C | 115.9 bar | 2.62 |
| 50 °C | 131.5 bar | 2.37 |

(evaporating at 0 °C, 5 K superheat, compressor efficiency 0.70). The colder the water entering the gas cooler, the higher the COP: this is why CO₂ heat pumps are excellent for domestic hot water, heated from 10–15 °C.

![COP vs gas cooler pressure](images/co2_cop_vs_pressure.png)
![Transcritical CO₂ cycle](images/co2_heat_pump_Ts_ph.png)

### Exergy analysis: where is the useful work lost?

![Exergy destruction](images/exergy_destruction.png)

- In the steam plant (flame at 1200 °C, ambient 20 °C) the **boiler** destroys about a third of the fuel exergy: heat goes from a very hot flame to water boiling at ~295 °C. This is why combined cycles put a gas turbine on top of the steam cycle. The turbines lose much less, and the pumps almost nothing.
- In the refrigerator (cabinet 4 °C, kitchen 25 °C) the losses are spread over all components: compressor, the two heat exchangers (finite temperature differences) and the **expansion valve**, which is a purely irreversible process.
- In the combined cycle the second-law efficiency rises to 67 %: the combustor is still the largest loss (14 % of the fuel exergy), but the hot exhaust is no longer thrown away.
- In the CO₂ heat pump the **expansion valve** is the largest loss (24 % of the compressor work), because it throttles a supercritical fluid across a very large pressure drop. This is why advanced CO₂ systems replace it with an ejector or an expander.

![Combined cycle exergy destruction](images/combined_exergy.png)

## Installation

```bash
git clone https://github.com/Raffoo26/thermo-cycles.git
cd thermo-cycles
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Every time you open a new terminal, enter the folder and activate the environment again (`cd thermo-cycles` and `source .venv/bin/activate`).

## Run it with your own values (no coding needed)

```bash
python simulate.py
```

The simulator asks which cycle you want (Rankine with any feedwater heaters, refrigeration / heat pump, Brayton, combined cycle, transcritical CO₂ heat pump), then every value with its **unit of measurement** and a **default** in square brackets. Press Enter to keep the default, or type your own value. Example session:

```text
Which cycle do you want to simulate?
    1) Rankine cycle (steam power plant / ORC)
    2) Refrigeration / heat pump cycle
    3) Brayton cycle (gas turbine)
    4) Combined cycle (gas turbine + steam)
    5) Transcritical CO2 heat pump
  Choice [1]: 2

VAPOUR-COMPRESSION CYCLE (refrigerator / air conditioner / heat pump)
  Refrigerant [R134a]: R32
  Evaporating temperature [°C] [-10.0]: 7
  Condensing temperature [°C] [40.0]: 45
  Superheat at compressor inlet [K] [0.0]: 5
  Subcooling at condenser outlet [K] [0.0]: 3
  Compressor isentropic efficiency [0-1 or %] [1.0]: 70
  Cooling capacity [kW] [optional]: 3.5
```

It prints the state table and all results, sizes the system if you gave a power or capacity, optionally runs the exergy analysis, and saves the T-s, p-h and exergy diagrams as PNG files in the `results/` folder.

Input tips:
- Decimals with a point or a comma (`0.08` or `0,08`); efficiencies as a fraction or a percentage (`0.85` or `85`).
- Fluid names follow [CoolProp](http://www.coolprop.org/fluid_properties/PurePseudoPure.html#list-of-fluids).
- Physically impossible inputs (e.g. condenser pressure above boiler pressure, or a boiler above the critical pressure) are rejected with an explanation.

## Web app

A [Streamlit](https://streamlit.io/) app with fields for all five cycles (Rankine with up to 4 feedwater heaters, Brayton, combined cycle, refrigeration, transcritical CO₂): change the values, press **Calculate**, and get diagrams, state tables, plant sizing, exergy analysis and downloads (PNG, CSV).

Run it locally:

```bash
pip install -r webapp/requirements.txt
streamlit run webapp/streamlit_app.py
```

Publish it online for free on Streamlit Community Cloud:
1. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
2. **Create app** → *Deploy a public app from GitHub* → repository `Raffoo26/thermo-cycles`, branch `main`, main file `webapp/streamlit_app.py`.
3. In **Advanced settings** choose Python 3.12, then **Deploy**. You get a public link to share.

## Use it from Python

```python
from thermocycles import (FeedwaterHeater, rankine_reheat_regen_cycle, refrigeration_cycle,
                          brayton_cycle, combined_cycle, transcritical_heat_pump,
                          optimal_high_pressure, exergy_analysis)
from thermocycles.plots import plot_Ts, plot_ph, plot_exergy, plot_hrsg

plant = rankine_reheat_regen_cycle(p_high_bar=80, p_low_bar=0.08, T_max_C=480,
                                   p_reheat_bar=7, T_reheat_C=440,
                                   heaters=[FeedwaterHeater(20, "closed", ttd_K=3),
                                            FeedwaterHeater(3, "open")],
                                   eta_turbine=0.85, eta_pump=0.85)
plant.summary()                          # state table and results
print(plant.extractions)                 # {20: y1, 3: y2}
plot_Ts(plant)

ex = exergy_analysis(plant, T0_C=20, T_source_C=1200)
ex.summary()
plot_exergy(ex)

hp = refrigeration_cycle(T_evap_C=-5, T_cond_C=45, superheat_K=5,
                         subcooling_K=3, eta_comp=0.75, fluid="R290")
print(hp.cop_heating)                    # COP as a heat pump

gt = brayton_cycle(pressure_ratio=10, T_turbine_in_C=1200, T_in_C=15,
                   eta_comp=0.86, eta_turb=0.89, regen_effectiveness=0.8)
print(gt.efficiency)

cc = combined_cycle(brayton_cycle(18, 1350, T_in_C=15, eta_comp=0.88, eta_turb=0.90),
                    rankine_reheat_regen_cycle(40, 0.05, 520, eta_turbine=0.88, heaters=[1.5]),
                    T_stack_C=170)
print(cc.efficiency, cc.pinch_K)         # ≈ 0.58, ≈ 12.7 K
plot_hrsg(cc)

p_opt, co2 = optimal_high_pressure(T_evap_C=0, T_gc_out_C=35, superheat_K=5, eta_comp=0.7)
print(p_opt, co2.cop_heating)            # ≈ 87 bar, ≈ 3.5
```

Inputs use practical units (bar, °C); all results are in SI units (Pa, K, J/kg). Divide by 1000 for kJ/kg, by 10<sup>5</sup> for bar, subtract 273.15 for °C.

### Rankine — `rankine_cycle(...)` and `rankine_reheat_regen_cycle(...)`

| Parameter | Unit | Default | Meaning |
|---|---|---|---|
| `p_high_bar` | bar | required | Boiler pressure (must be below the critical pressure) |
| `p_low_bar` | bar | required | Condenser pressure |
| `T_max_C` | °C | `None` | Turbine inlet temperature; `None` = saturated vapour |
| `p_reheat_bar` | bar | `None` | Reheat pressure; `None` = no reheat *(advanced function only)* |
| `T_reheat_C` | °C | = `T_max_C` | Temperature after reheat *(advanced function only)* |
| `p_fwh_bar` | bar | `None` | Shortcut for one open feedwater heater at this pressure *(advanced function only)* |
| `heaters` | – | `None` | List of feedwater heaters *(advanced function only)*: `FeedwaterHeater(p_bar, kind, ttd_K)`, a tuple `(p_bar, kind, ttd_K)`, a dict, or a pressure (= open heater). `kind` is `"open"` or `"closed"`; `ttd_K` [K] is the terminal temperature difference of closed heaters (feedwater leaves at T<sub>sat</sub> − TTD). |
| `eta_turbine` | – | `1.0` | Isentropic efficiency of every turbine section |
| `eta_pump` | – | `1.0` | Isentropic efficiency of every pump |
| `fluid` | – | `"Water"` | CoolProp fluid name |

`rankine_cycle` is the simple cycle (states 1–4). In `rankine_reheat_regen_cycle` states are numbered along the feedwater line from the condenser outlet, then the boiler outlet, the turbine expansion and finally the drains of the closed heaters; `exhaust` names the turbine exhaust state. Drains of closed heaters are throttled to the next lower-pressure heater (or the condenser). If an extraction and the reheat have the same pressure, steam is bled before the reheater. Specific quantities are per kg of steam through the boiler.

| Result | Unit | Meaning |
|---|---|---|
| `efficiency` | – | Thermal efficiency w<sub>net</sub> / q<sub>in</sub> |
| `w_turbine`, `w_pump`, `w_net` | J/kg | Turbine, pump and net work |
| `q_in`, `q_out` | J/kg | Heat in boiler + reheater / heat rejected in the condenser |
| `bwr` | – | Back Work Ratio w<sub>pump</sub> / w<sub>turbine</sub> |
| `extractions` | – | Dict {extraction pressure [bar]: fraction of boiler steam bled} |
| `extraction_fraction` | – | Total fraction of steam bled to the heaters |
| `mass_flow_for_power(P)` | kg/s | Steam mass flow for a net power `P` in **W** |

### Refrigeration / heat pump — `refrigeration_cycle(...)`

| Parameter | Unit | Default | Meaning |
|---|---|---|---|
| `T_evap_C` | °C | required | Evaporating (saturation) temperature |
| `T_cond_C` | °C | required | Condensing (saturation) temperature, below the critical one |
| `superheat_K` | K | `0` | Vapour superheat at the compressor inlet |
| `subcooling_K` | K | `0` | Liquid subcooling at the condenser outlet |
| `eta_comp` | – | `1.0` | Compressor isentropic efficiency |
| `fluid` | – | `"R134a"` | CoolProp refrigerant name |

| Result | Unit | Meaning |
|---|---|---|
| `cop_cooling`, `cop_heating` | – | COP as refrigerator / as heat pump |
| `cop_carnot_cooling` | – | Reverse Carnot COP between evaporating and condensing temperatures |
| `w_comp`, `q_evap`, `q_cond` | J/kg | Compressor work, refrigerating effect, heat to condenser |
| `pressure_ratio` | – | p<sub>cond</sub> / p<sub>evap</sub> |
| `discharge_temperature_C` | °C | Compressor discharge temperature |
| `volumetric_capacity` | J/m³ | Cooling per m³ of vapour drawn in by the compressor |
| `mass_flow_for_cooling(Q)` | kg/s | Refrigerant mass flow for a cooling capacity `Q` in **W** |

### Brayton — `brayton_cycle(...)`

| Parameter | Unit | Default | Meaning |
|---|---|---|---|
| `pressure_ratio` | – | required | Compressor pressure ratio p<sub>2</sub>/p<sub>1</sub> |
| `T_turbine_in_C` | °C | required | Turbine inlet temperature |
| `T_in_C` | °C | `27` | Compressor inlet temperature |
| `p_in_bar` | bar | `1.0` | Compressor inlet pressure |
| `eta_comp`, `eta_turb` | – | `1.0` | Compressor / turbine isentropic efficiency |
| `regen_effectiveness` | – | `0` | Regenerator effectiveness (0 = none, 1 = ideal) |
| `fluid` | – | `"Air"` | CoolProp gas name |

Results: `efficiency`, `w_comp`, `w_turb`, `w_net`, `q_in`, `q_out` [J/kg], `bwr`, `exhaust_temperature_C`, `mass_flow_for_power(P)`. States: 1 compressor inlet, 2 compressor outlet, x regenerator outlet, 3 turbine inlet, 4 turbine outlet, y exhaust.

### Combined cycle — `combined_cycle(gas, steam, T_stack_C)`

| Parameter | Unit | Default | Meaning |
|---|---|---|---|
| `gas` | – | required | Result of `brayton_cycle(...)` (the topping cycle) |
| `steam` | – | required | Result of `rankine_cycle(...)` or `rankine_reheat_regen_cycle(...)`; all its boiler and reheat heat comes from the gas turbine exhaust |
| `T_stack_C` | °C | `100` | Temperature of the gas leaving the HRSG |

| Result | Unit | Meaning |
|---|---|---|
| `efficiency` | – | Combined efficiency (net work of both cycles / combustor heat) |
| `w_net`, `q_in`, `q_hrsg` | J/kg air | Net work, combustor heat, heat recovered in the HRSG |
| `steam_per_air` | kg/kg | Steam mass flow per kg of air |
| `gas_share` | – | Fraction of the net power from the gas turbine |
| `pinch_K` | K | Minimum gas–water temperature difference (where the water starts boiling) |
| `stack`, `gas`, `steam` | – | Stack state and the two cycle results |
| `mass_flows_for_power(P)` | kg/s | (air, steam) mass flows for a total net power `P` in **W** |

The pinch point must be positive (otherwise a `ValueError` explains how to fix the design); below 8 K a warning is added.

### Transcritical CO₂ heat pump — `transcritical_heat_pump(...)` and `optimal_high_pressure(...)`

| Parameter | Unit | Default | Meaning |
|---|---|---|---|
| `T_evap_C` | °C | required | Evaporating temperature (below the critical temperature) |
| `p_high_bar` | bar | required | Gas cooler pressure (above the critical pressure); not used by `optimal_high_pressure` |
| `T_gc_out_C` | °C | required | Gas cooler outlet temperature |
| `superheat_K` | K | `0` | Vapour superheat at the compressor inlet |
| `eta_comp` | – | `1.0` | Compressor isentropic efficiency |
| `fluid` | – | `"CO2"` | CoolProp fluid name |

`optimal_high_pressure(T_evap_C, T_gc_out_C, superheat_K, eta_comp)` returns `(p_opt_bar, result)`. Results have the same attributes as `refrigeration_cycle` (with `q_cond` = heat to the gas cooler) plus `cop_lorenz_heating` and `gas_cooler_mean_temperature`. States: 1 compressor inlet, 2 compressor outlet, 3 gas cooler outlet, 4 evaporator inlet.

### Exergy — `exergy_analysis(result, ...)`

| Parameter | Unit | Default | Meaning |
|---|---|---|---|
| `result` | – | required | Any cycle result above |
| `T0_C` | °C | `25` | Ambient (dead state) temperature; heat to the ambient crosses the boundary here |
| `T_source_C` | °C | `None` | Hot source (flame, flue gas, hot water); `None` = highest fluid temperature of each heater |
| `T_cold_C` | °C | `None` | Refrigerated space; `None` = highest fluid temperature in the evaporator |
| `T_user_C` | °C | `None` | Heat pumps: temperature at which heat is delivered (e.g. hot water); `None` = lowest fluid temperature in the gas cooler |

Results: `destruction` (dict, J/kg per component), `fuel`, `product`, `efficiency` (second-law), `table()`, `summary()`. Power and combined cycles: fuel = exergy of the heat from the source, product = net work. Refrigeration: fuel = compressor work, product = exergy of the cold produced. Heat pumps: fuel = compressor work, product = exergy of the heat delivered (the evaporator takes heat from the ambient at T0).

Helpers: `saturation_pressure_bar(fluid, T_C)`, `saturation_temperature_C(fluid, p_bar)`, `critical_point(fluid)`. Every result also has `states`, `summary()`, `state_table()` and `warnings`.

## Examples and tests

```bash
python examples/rankine_example.py           # simple Rankine + parametric study
python examples/rankine_advanced_example.py  # reheat, regeneration, best extraction pressure
python examples/refrigeration_example.py     # refrigeration + refrigerant comparison
python examples/brayton_example.py           # gas turbine with/without regenerator
python examples/orc_example.py               # ORC working-fluid comparison
python examples/exergy_example.py            # exergy destruction per component
python examples/feedwater_heaters_example.py # open/closed heaters, Moran 8.6, number of heaters
python examples/combined_cycle_example.py    # combined cycle, HRSG T-Q diagram, stack/pinch study
python examples/co2_heat_pump_example.py     # transcritical CO₂, optimal pressure
pytest                                       # validation and unit tests
```

## Project structure

```text
thermocycles/      the package: core.py, rankine.py, refrigeration.py, brayton.py, combined.py,
                   transcritical.py, exergy.py, plots.py
simulate.py        interactive terminal simulator
webapp/            Streamlit web app
notebooks/         Google Colab notebook
examples/          example scripts that produce the images in images/
tests/             validation and unit tests (pytest)
```

## Limits of the models

Steady state, no pressure drops in heat exchangers and piping, no heat losses to the environment, closed air-standard Brayton cycle (no combustion chemistry), single-pressure HRSG, drains of closed feedwater heaters cascaded backward (not pumped forward), single-stage vapour compression (no internal heat exchanger or ejector). These are the standard assumptions of an engineering thermodynamics course.

## Roadmap

- [x] Simple Rankine cycle
- [x] Rankine with reheat and regeneration
- [x] Vapour-compression refrigeration / heat pump cycle with refrigerant comparison
- [x] Brayton cycle (gas turbine) with regeneration
- [x] Working fluid comparison for ORC cycles
- [x] Exergy analysis
- [x] Interactive simulator, web app and Colab notebook
- [x] Combined gas–steam cycle
- [x] Closed feedwater heaters and multiple extractions
- [x] Transcritical CO₂ heat pump

Ideas for the future: multi-pressure HRSG, supercritical steam cycles, CO₂ heat pump with internal heat exchanger or ejector.

## Author

Mechanical Engineering student.

## License

[MIT](LICENSE)
