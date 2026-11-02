# Thermo Cycles

🇬🇧 [English version](README.md)

Simulatore in Python di cicli termodinamici diretti e inversi con **proprietà reali dei fluidi** ([CoolProp](http://www.coolprop.org/)). Nato per mettere in pratica i corsi di Fisica Tecnica e Macchine a Fluido.

## Cosa fa

- Risolve il **ciclo Rankine** (vapore saturo o surriscaldato, rendimenti isentropici di pompa e turbina): rendimento, Back Work Ratio, portata per una data potenza.
- Risolve il **ciclo frigorifero / pompa di calore a compressione di vapore** (surriscaldamento, sottoraffreddamento, rendimento isentropico del compressore): COP in raffreddamento e riscaldamento, COP di Carnot, rendimento di secondo principio, rapporto di compressione, temperatura di mandata, capacità frigorifera volumetrica.
- Confronta i **refrigeranti** a parità di condizioni (R134a, R1234yf, R290, R600a, R32, ...).
- Disegna i diagrammi **T-s** e **p-h** con la curva limite e le trasformazioni reali.
- Esegue **studi parametrici** (es. rendimento al variare di pressione in caldaia e temperatura di ingresso turbina).
- **Simulatore interattivo** (`simulate.py`): inserisci i tuoi valori con le unità di misura e ottieni risultati e diagrammi, senza scrivere codice.
- Funziona con qualsiasi fluido di CoolProp: acqua, ma anche fluidi organici per cicli ORC (`R245fa`, `Toluene`, ...).

![Diagrammi T-s e p-h](images/rankine_Ts_ph.png)

## Validazione

I risultati sono confrontati con esempi svolti di letteratura (Moran & Shapiro) nei test automatici:

**Ciclo Rankine** (es. 8.1 e 8.2 — 80 bar → 0.08 bar, vapore saturo)

| Grandezza | Libro | Questo codice |
|---|---|---|
| Ciclo ideale — rendimento | 37.1 % | 37.1 % |
| Ciclo ideale — titolo uscita turbina | 0.6745 | 0.6749 |
| η<sub>is</sub> = 0.85 — rendimento | 31.4 % | 31.4 % |

**Ciclo frigorifero** (es. 10.1 e 10.2 — R-134a, evaporatore a −10 °C, condensatore a 9 bar, 0.08 kg/s)

| Grandezza | Libro | Questo codice |
|---|---|---|
| Ciclo ideale — COP | 4.57 | 4.58 |
| Ciclo ideale — potenza compressore | 2.48 kW | 2.50 kW |
| Ciclo ideale — potenza frigorifera | 11.34 kW | 11.43 kW |
| η<sub>comp</sub> = 0.80 — COP | 3.66 | 3.66 |

Le piccole differenze (sotto l'1 %) dipendono dalle proprietà dei fluidi: CoolProp usa equazioni di stato di riferimento (IAPWS-95 per l'acqua), il libro tabelle stampate.

## Risultati di esempio

### Ciclo Rankine

Ciclo a 80 bar / 480 °C, condensatore a 0.08 bar, rendimenti isentropici 0.85:
rendimento **33.7 %**, lavoro netto **1067 kJ/kg**, portata per 100 MW netti **93.7 kg/s**.
Il titolo allo scarico turbina (x = 0.874) è sotto la soglia pratica di 0.88–0.90: è il motivo per cui negli impianti reali si adotta il risurriscaldamento (prossimo modulo).

![Studio parametrico](images/rankine_parametric_study.png)

### Ciclo frigorifero e confronto tra refrigeranti

Condizioni da frigorifero domestico / piccolo condizionatore: evaporatore a −10 °C, condensatore a 40 °C, surriscaldamento 5 K, sottoraffreddamento 3 K, rendimento isentropico del compressore 0.75.

![Diagrammi T-s e p-h del ciclo frigorifero](images/refrigeration_Ts_ph.png)

| Refrigerante | COP | Capacità vol. [kJ/m³] | p<sub>evap</sub> [bar] | p<sub>cond</sub> [bar] | T mandata [°C] |
|---|---|---|---|---|---|
| R134a | 3.13 | 1421 | 2.01 | 10.17 | 61.9 |
| R1234yf | 2.98 | 1354 | 2.22 | 10.18 | 49.7 |
| R290 (propano) | 3.09 | 2035 | 3.45 | 13.69 | 61.1 |
| R600a (isobutano) | 3.20 | 766 | 1.08 | 5.31 | 51.5 |
| R32 | 3.01 | 3837 | 5.83 | 24.78 | 103.7 |

Cosa dicono i numeri:
- **R600a** ha il COP migliore ma la capacità volumetrica più bassa: serve un compressore grande, ed è per questo che si usa nei piccoli frigoriferi domestici.
- **R32** ha circa 2,7 volte la capacità volumetrica dell'R134a (compressore molto più piccolo), ma temperatura di mandata oltre 100 °C e pressioni di condensazione vicine a 25 bar.
- **R290** è un buon compromesso: COP simile all'R134a con circa il 40 % di capacità volumetrica in più, ed è un refrigerante naturale con GWP bassissimo, un'opzione chiave con la riduzione dei gas fluorurati nell'UE.
- **R1234yf** si comporta quasi come l'R134a (è nato come suo sostituto diretto) con un COP leggermente più basso.

![Confronto tra refrigeranti](images/refrigerant_comparison.png)

![COP in funzione della temperatura di evaporazione](images/refrigeration_cop_vs_tevap.png)

## Installazione

```bash
git clone https://github.com/Raffoo26/thermo-cycles.git
cd thermo-cycles
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usalo con i tuoi valori (senza scrivere codice)

Dalla cartella del progetto, con l'ambiente virtuale attivo:

```bash
python simulate.py
```

Il simulatore chiede quale ciclo vuoi, poi chiede ogni valore con la sua **unità di misura** e un **valore predefinito** tra parentesi quadre. Premi Invio per tenere il predefinito, oppure scrivi il tuo valore. Esempio di sessione (il programma è in inglese):

```text
Which cycle do you want to simulate?
    1) Rankine cycle (power plant)
    2) Refrigeration / heat pump cycle
  Choice [1]: 2

VAPOUR-COMPRESSION CYCLE (refrigerator / air conditioner / heat pump)
  Refrigerant [R134a]: R290
  Evaporating temperature [°C] [-10.0]: -5
  Condensing temperature [°C] [40.0]: 45
  Superheat at compressor inlet [K] [0.0]: 5
  Subcooling at condenser outlet [K] [0.0]: 3
  Compressor isentropic efficiency [0-1 or %] [1.0]: 75
  Cooling capacity [kW] [optional]: 3.5
```

Poi stampa la tabella degli stati e tutti i risultati, dimensiona l'impianto se hai indicato una potenza (portata, potenza di compressore o turbina, calori scambiati) e salva i diagrammi T-s e p-h come immagini PNG nella cartella `results/`.

Consigli per l'inserimento:
- I decimali si possono scrivere con il punto o con la virgola (`0.08` oppure `0,08`).
- I rendimenti si possono scrivere come frazione o in percentuale (`0.85` oppure `85`).
- I nomi dei fluidi sono quelli di [CoolProp](http://www.coolprop.org/fluid_properties/PurePseudoPure.html#list-of-fluids): ad esempio `Water`, `R134a`, `R1234yf`, `R290`, `R600a`, `R32`, `R410A`, `Ammonia`, `R245fa`, `Toluene`.
- I valori non validi (es. pressione al condensatore maggiore di quella in caldaia, o condensazione sopra la temperatura critica) vengono rifiutati con una spiegazione.

## Usalo da Python

```python
from thermocycles import rankine_cycle, refrigeration_cycle
from thermocycles.plots import plot_Ts, plot_refrigeration_ph

r = rankine_cycle(p_high_bar=80, p_low_bar=0.08, T_max_C=480,
                  eta_turbine=0.85, eta_pump=0.85)
r.summary()                      # stampa tabella degli stati e risultati
print(r.efficiency)              # ≈ 0.337
plot_Ts(r)

hp = refrigeration_cycle(T_evap_C=-10, T_cond_C=40, superheat_K=5,
                         subcooling_K=3, eta_comp=0.75, fluid="R290")
print(hp.cop_heating)            # COP come pompa di calore
plot_refrigeration_ph(hp)
```

### `rankine_cycle(...)` — parametri di ingresso

| Parametro | Unità | Predefinito | Significato |
|---|---|---|---|
| `p_high_bar` | bar | obbligatorio | Pressione in caldaia (massima) |
| `p_low_bar` | bar | obbligatorio | Pressione al condensatore (minima) |
| `T_max_C` | °C | `None` | Temperatura di ingresso turbina; `None` = vapore saturo secco (niente surriscaldamento) |
| `eta_turbine` | – | `1.0` | Rendimento isentropico della turbina (1 = ideale) |
| `eta_pump` | – | `1.0` | Rendimento isentropico della pompa (1 = ideale) |
| `fluid` | – | `"Water"` | Nome del fluido in CoolProp |

### `rankine_cycle(...)` — risultati

| Attributo / metodo | Unità | Significato |
|---|---|---|
| `efficiency` | – | Rendimento del ciclo l<sub>netto</sub> / q<sub>in</sub> |
| `w_turbine`, `w_pump`, `w_net` | J/kg | Lavoro specifico di turbina, pompa e netto |
| `q_in`, `q_out` | J/kg | Calore fornito in caldaia / ceduto al condensatore |
| `bwr` | – | Back Work Ratio l<sub>pompa</sub> / l<sub>turbina</sub> |
| `mass_flow_for_power(P)` | kg/s | Portata per una potenza netta `P` in **W** |
| `states["1"]` … `states["4"]` | SI | Punti del ciclo: `.p` [Pa], `.T` [K], `.h` [J/kg], `.s` [J/(kg·K)], `.x` titolo [–] |
| `warnings` | – | Elenco degli avvisi (es. titolo basso allo scarico turbina) |

### `refrigeration_cycle(...)` — parametri di ingresso

| Parametro | Unità | Predefinito | Significato |
|---|---|---|---|
| `T_evap_C` | °C | obbligatorio | Temperatura di evaporazione (saturazione) |
| `T_cond_C` | °C | obbligatorio | Temperatura di condensazione (saturazione) |
| `superheat_K` | K | `0` | Surriscaldamento del vapore all'ingresso del compressore |
| `subcooling_K` | K | `0` | Sottoraffreddamento del liquido all'uscita del condensatore |
| `eta_comp` | – | `1.0` | Rendimento isentropico del compressore (1 = ideale) |
| `fluid` | – | `"R134a"` | Nome del refrigerante in CoolProp |

### `refrigeration_cycle(...)` — risultati

| Attributo / metodo | Unità | Significato |
|---|---|---|
| `cop_cooling` | – | COP come frigorifero / condizionatore q<sub>evap</sub> / l<sub>comp</sub> |
| `cop_heating` | – | COP come pompa di calore q<sub>cond</sub> / l<sub>comp</sub> |
| `cop_carnot_cooling` | – | COP di Carnot inverso tra temperatura di evaporazione e di condensazione |
| `w_comp`, `q_evap`, `q_cond` | J/kg | Lavoro del compressore, effetto frigorifero, calore al condensatore |
| `pressure_ratio` | – | Rapporto di compressione p<sub>cond</sub> / p<sub>evap</sub> |
| `discharge_temperature_C` | °C | Temperatura di mandata del compressore |
| `volumetric_capacity` | J/m³ | Effetto frigorifero per m³ di vapore aspirato dal compressore |
| `mass_flow_for_cooling(Q)` | kg/s | Portata di refrigerante per una potenza frigorifera `Q` in **W** |
| `states["1"]` … `states["4"]` | SI | Punti del ciclo (stessi attributi di sopra) |
| `warnings` | – | Elenco degli avvisi (es. temperatura di mandata elevata) |

Gli ingressi usano unità pratiche (bar, °C); tutti i risultati sono in unità SI (Pa, K, J/kg). Dividi per 1000 per avere kJ/kg, per 10<sup>5</sup> per avere bar, sottrai 273.15 per avere °C.

## Esempi e test

```bash
python examples/rankine_example.py         # diagrammi Rankine + studio parametrico
python examples/refrigeration_example.py   # diagrammi frigorifero + confronto refrigeranti
pytest                                     # test di validazione e unitari
```

## Roadmap

- [x] Ciclo Rankine semplice
- [ ] Rankine con risurriscaldamento e rigenerazione
- [x] Ciclo frigorifero / pompa di calore a compressione di vapore con confronto tra refrigeranti
- [ ] Ciclo Brayton (turbina a gas) con recupero
- [ ] Confronto fluidi per cicli ORC
- [ ] Web app interattiva

## Autore

Studente di Ingegneria Meccanica.

## Licenza

[MIT](LICENSE)
