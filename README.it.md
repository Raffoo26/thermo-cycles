# Thermo Cycles

🇬🇧 [English version](README.md)

Simulatore in Python di cicli termodinamici diretti e inversi con **proprietà reali dei fluidi** ([CoolProp](http://www.coolprop.org/)). Nato per mettere in pratica i corsi di Fisica Tecnica e Macchine a Fluido.

## Cosa fa

- Risolve il **ciclo Rankine** (vapore saturo o surriscaldato, rendimenti isentropici di pompa e turbina): rendimento, Back Work Ratio, portata per una data potenza.
- Risolve il **ciclo frigorifero / pompa di calore a compressione di vapore** (surriscaldamento, sottoraffreddamento, rendimento isentropico del compressore): COP in raffreddamento e riscaldamento, COP di Carnot, rendimento di secondo principio, rapporto di compressione, temperatura di mandata, capacità frigorifera volumetrica.
- Confronta i **refrigeranti** a parità di condizioni (R134a, R1234yf, R290, R600a, R32, ...).
- Disegna i diagrammi **T-s** e **p-h** con la curva limite e le trasformazioni reali.
- Esegue **studi parametrici** (es. rendimento al variare di pressione in caldaia e temperatura di ingresso turbina).
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

## Uso

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

Esempi completi con grafici:

```bash
python examples/rankine_example.py
python examples/refrigeration_example.py
```

Test:

```bash
pytest
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
