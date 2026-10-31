# Thermo Cycles

🇬🇧 [English version](README.md)

Simulatore in Python di cicli termodinamici diretti e inversi con **proprietà reali dei fluidi** ([CoolProp](http://www.coolprop.org/)). Nato per mettere in pratica i corsi di Fisica Tecnica e Macchine a Fluido.

## Cosa fa

- Risolve il **ciclo Rankine** (vapore saturo o surriscaldato, rendimenti isentropici di pompa e turbina).
- Calcola stati termodinamici, lavori, calori, rendimento, Back Work Ratio e portata necessaria per una data potenza.
- Disegna i diagrammi **T-s** e **p-h** con la curva limite e le trasformazioni reali.
- Esegue **studi parametrici** (es. rendimento al variare di pressione in caldaia e temperatura di ingresso turbina).
- Funziona con qualsiasi fluido di CoolProp: acqua, ma anche fluidi organici per cicli ORC (`R245fa`, `Toluene`, ...).

![Diagrammi T-s e p-h](images/rankine_Ts_ph.png)

## Validazione

I risultati sono confrontati con esempi svolti di letteratura (Moran & Shapiro, es. 8.1 e 8.2) nei test automatici:

| Caso (80 bar → 0.08 bar, vapore saturo) | Libro | Questo codice |
|---|---|---|
| Ciclo ideale — rendimento | 37.1 % | 37.1 % |
| Ciclo ideale — titolo uscita turbina | 0.6745 | 0.6749 |
| η<sub>is</sub> = 0.85 — rendimento | 31.4 % | 31.4 % |

Le piccole differenze sul quarto decimale dipendono dalle proprietà del fluido: CoolProp usa la formulazione IAPWS-95, il libro tabelle stampate.

## Esempio di risultato

Ciclo a 80 bar / 480 °C, condensatore a 0.08 bar, rendimenti isentropici 0.85:
rendimento **33.7 %**, lavoro netto **1067 kJ/kg**, portata per 100 MW netti **93.7 kg/s**.
Il titolo allo scarico turbina (x = 0.874) è sotto la soglia pratica di 0.88–0.90: è il motivo per cui negli impianti reali si adotta il risurriscaldamento (prossimo modulo).

![Studio parametrico](images/rankine_parametric_study.png)

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

Esempio completo con grafici e studio parametrico:

```bash
python examples/rankine_example.py
```

Test:

```bash
pytest
```

## Roadmap

- [x] Ciclo Rankine semplice
- [ ] Rankine con risurriscaldamento e rigenerazione
- [ ] Ciclo frigorifero / pompa di calore a compressione di vapore (COP)
- [ ] Ciclo Brayton (turbina a gas) con recupero
- [ ] Confronto fluidi per cicli ORC
- [ ] Web app interattiva

## Autore

Studente di Ingegneria Meccanica.

## Licenza

[MIT](LICENSE)
