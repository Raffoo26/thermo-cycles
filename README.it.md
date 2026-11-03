# Thermo Cycles

🇬🇧 [English version](README.md)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Raffoo26/thermo-cycles/blob/main/notebooks/thermo_cycles_demo.ipynb)

Simulatore in Python di cicli termodinamici diretti e inversi con **proprietà reali dei fluidi** ([CoolProp](http://www.coolprop.org/)), con **analisi exergetica**, **simulatore interattivo**, **web app** e notebook da usare nel browser. Nato per mettere in pratica i corsi di Fisica Tecnica e Macchine a Fluido. Ogni modulo è **validato su esempi svolti di letteratura**.

## Provalo senza installare niente

- **Google Colab**: clicca il pulsante *Open in Colab* qui sopra, esegui la cella *Setup* e cambia i valori nei moduli. Basta un account Google.
- **Web app**: vedi [Web app](#web-app) per avviarla sul tuo computer o pubblicarla online.
- **Sul tuo computer**: vedi [Installazione](#installazione), poi `python simulate.py`.

## Cosa fa

| Modulo | Cosa calcola |
|---|---|
| **Ciclo Rankine** | Semplice, con **risurriscaldamento**, con **rigenerazione** (rigeneratore aperto) o entrambi. Impianti a vapore e **ORC** con fluidi organici. Rendimento, Back Work Ratio, frazione spillata, portata per una data potenza. |
| **Frigorifero / pompa di calore** | Compressione di vapore con surriscaldamento, sottoraffreddamento e rendimento del compressore. COP (raffreddamento e riscaldamento), COP di Carnot, rapporto di compressione, temperatura di mandata, capacità volumetrica. |
| **Ciclo Brayton** | Turbina a gas con aria a proprietà reali, rendimenti di compressore e turbina e **rigeneratore**. |
| **Analisi exergetica** | Exergia distrutta in ogni componente (Gouy–Stodola) e rendimento di secondo principio, per ogni ciclo. |
| **Diagrammi** | Diagrammi **T-s** e **p-h** con curva limite e trasformazioni reali, grafici dell'exergia distrutta, studi parametrici. |
| **Interfacce** | Simulatore interattivo da terminale, web app Streamlit, notebook Colab, uso da Python. |

Funziona con qualsiasi fluido di CoolProp: acqua, refrigeranti (R134a, R1234yf, R290, R600a, R32, R410A, ammoniaca…), fluidi organici (R245fa, R1233zd(E), pentani, toluene…) e gas (aria, azoto, elio, CO₂).

![Ciclo Rankine con risurriscaldamento e rigenerazione](images/rankine_reheat_regen_Ts_ph.png)

## Validazione

Ogni modulo è verificato da test automatici sugli esempi svolti del Moran & Shapiro, *Fundamentals of Engineering Thermodynamics*. Gli scarti restano sotto l'1 % e dipendono dalle proprietà dei fluidi (CoolProp usa equazioni di stato di riferimento, il libro tabelle stampate).

**Ciclo Rankine** (8 MPa / 480 °C o vapore saturo, condensatore a 8 kPa)

| Esempio | Grandezza | Libro | Questo codice |
|---|---|---|---|
| 8.1 ideale, vapore saturo | rendimento | 37.1 % | 37.1 % |
| 8.1 ideale, vapore saturo | titolo uscita turbina | 0.6745 | 0.6749 |
| 8.2 η<sub>is</sub> = 0.85 | rendimento | 31.4 % | 31.4 % |
| 8.3 risurriscaldamento (7 bar → 440 °C) | rendimento | 40.3 % | 40.3 % |
| 8.4 risurriscaldamento, η<sub>t</sub> = 0.85 | rendimento | 35.1 % | 35.1 % |
| 8.5 rigeneratore aperto (7 bar), η<sub>t</sub> = 0.85 | rendimento | 36.9 % | 36.9 % |
| 8.5 rigeneratore aperto, 100 MW netti | portata di vapore | 3.69·10⁵ kg/h | 3.69·10⁵ kg/h |

**Ciclo frigorifero** (R-134a, evaporatore a −10 °C, condensatore a 9 bar, 0.08 kg/s)

| Esempio | Grandezza | Libro | Questo codice |
|---|---|---|---|
| 10.1 ideale | COP | 4.57 | 4.58 |
| 10.1 ideale | potenza compressore | 2.48 kW | 2.50 kW |
| 10.1 ideale | potenza frigorifera | 11.34 kW | 11.43 kW |
| 10.2 η<sub>comp</sub> = 0.80 | COP | 3.66 | 3.66 |

**Ciclo Brayton** (aria, 100 kPa / 300 K, rapporto di compressione 10, ingresso turbina 1400 K)

| Esempio | Grandezza | Libro | Questo codice |
|---|---|---|---|
| 9.4 ideale | rendimento | 45.7 % | 45.7 % |
| 9.4 ideale | Back Work Ratio | 39.6 % | 39.6 % |
| 9.5 η<sub>c</sub> = η<sub>t</sub> = 0.80 | rendimento | 24.8 % | 24.9 % |
| 9.5 η<sub>c</sub> = η<sub>t</sub> = 0.80 | Back Work Ratio | 61.9 % | 61.9 % |
| 9.6 rigeneratore ε = 0.80 | rendimento | 56.8 % | 56.8 % |

L'analisi exergetica è verificata controllando che il bilancio exergetico si chiuda (exergia spesa = prodotto + distrutta) su ogni ciclo.

## Risultati di esempio

### Impianto a vapore: risurriscaldamento e rigenerazione

80 bar / 480 °C, condensatore a 0.08 bar, rendimenti isentropici 0.85:

| Configurazione | Rendimento | Lavoro netto [kJ/kg] | Titolo allo scarico | Vapore per 100 MW [kg/s] |
|---|---|---|---|---|
| Semplice | 33.7 % | 1067 | 0.874 | 93.7 |
| Risurriscaldamento (7 bar → 440 °C) | 35.1 % | 1293 | 0.996 | 77.4 |
| Rigeneratore aperto (7 bar) | 36.9 % | 975 | 0.864 | 102.6 |
| Risurriscaldamento + rigeneratore | 37.2 % | 1138 | 0.996 | 87.9 |

- Il ciclo semplice finisce con troppo liquido allo scarico della turbina (x = 0.874, sotto il limite pratico di 0.88–0.90): il **risurriscaldamento** risolve il problema e aumenta il lavoro per kg.
- La **rigenerazione** aumenta di più il rendimento, perché l'acqua entra in caldaia più calda; qui la pressione di spillamento migliore è circa 9 bar.

![Studio parametrico](images/rankine_parametric_study.png)
![Pressione ottimale del rigeneratore](images/rankine_fwh_pressure_study.png)

### Ciclo frigorifero e confronto tra refrigeranti

Frigorifero domestico / piccolo condizionatore: evaporatore a −10 °C, condensatore a 40 °C, surriscaldamento 5 K, sottoraffreddamento 3 K, rendimento del compressore 0.75.

![Diagrammi T-s e p-h del ciclo frigorifero](images/refrigeration_Ts_ph.png)

| Refrigerante | COP | Capacità vol. [kJ/m³] | p<sub>evap</sub> [bar] | p<sub>cond</sub> [bar] | T mandata [°C] |
|---|---|---|---|---|---|
| R134a | 3.13 | 1421 | 2.01 | 10.17 | 61.9 |
| R1234yf | 2.98 | 1354 | 2.22 | 10.18 | 49.7 |
| R290 (propano) | 3.09 | 2035 | 3.45 | 13.69 | 61.1 |
| R600a (isobutano) | 3.20 | 766 | 1.08 | 5.31 | 51.5 |
| R32 | 3.01 | 3837 | 5.83 | 24.78 | 103.7 |

- **R600a** ha il COP migliore ma la capacità volumetrica più bassa: serve un compressore grande, ed è per questo che si usa nei piccoli frigoriferi domestici.
- **R32** ha circa 2,7 volte la capacità volumetrica dell'R134a (compressore molto più piccolo), ma temperatura di mandata oltre 100 °C e pressioni di condensazione vicine a 25 bar.
- **R290** è un buon compromesso: COP simile all'R134a con circa il 40 % di capacità volumetrica in più, ed è un refrigerante naturale con GWP bassissimo, un'opzione chiave con la riduzione dei gas fluorurati nell'UE.
- **R1234yf** si comporta quasi come l'R134a (è nato come suo sostituto diretto) con un COP leggermente più basso.

![Confronto tra refrigeranti](images/refrigerant_comparison.png)
![COP in funzione della temperatura di evaporazione](images/refrigeration_cop_vs_tevap.png)

### Turbina a gas (Brayton)

Rapporto di compressione 10, ingresso turbina 1200 °C, aspirazione a 15 °C, η<sub>c</sub> = 0.86, η<sub>t</sub> = 0.89: rendimento **35.0 %** senza rigeneratore, **48.0 %** con un rigeneratore di efficacia 0.8 (scarico raffreddato da 633 °C a 385 °C). Per 50 MW servono circa 142 kg/s di aria.

![Diagrammi T-s del ciclo Brayton](images/brayton_Ts.png)

Senza rigenerazione il rendimento cresce sempre con il rapporto di compressione; **con la rigenerazione il massimo si ha a rapporti di compressione bassi**, perché lo scarico della turbina è più caldo e ha più calore da restituire all'aria compressa.

![Rendimento del Brayton in funzione del rapporto di compressione](images/brayton_pressure_ratio_study.png)

### Ciclo Rankine organico (ORC) per calore a bassa temperatura

Sorgente di calore a circa 150 °C, evaporazione a 120 °C (+5 K di surriscaldamento), condensazione a 35 °C, η<sub>t</sub> = 0.80, η<sub>p</sub> = 0.70:

| Fluido | p<sub>evap</sub> [bar] | p<sub>cond</sub> [bar] | Rendimento | Scarico turbina | Rapporto volumetrico | Portata volumetrica allo scarico [m³/s per MW] |
|---|---|---|---|---|---|---|
| R245fa | 19.30 | 2.120 | 13.0 % | surriscaldato (64 °C) | 10.6 | 3.0 |
| R1233zd(E) | 15.79 | 1.837 | 13.4 % | surriscaldato (62 °C) | 9.5 | 3.4 |
| Isopentano | 10.86 | 1.290 | 13.1 % | surriscaldato (78 °C) | 9.2 | 4.8 |
| n-Pentano | 9.07 | 0.977 | 13.3 % | surriscaldato (77 °C) | 9.9 | 6.0 |
| Toluene | 1.31 | 0.062 | 14.9 % | surriscaldato (66 °C) | 18.7 | 62.9 |
| Acqua | 1.99 | 0.056 | 16.2 % | umido (x = 0.891) | 24.8 | 54.0 |

Sulla carta l'acqua ha il rendimento più alto, ma condensa in vuoto spinto e richiede una **portata volumetrica allo scarico circa 18 volte quella dell'R245fa**: una turbina grande, multistadio e costosa. I fluidi organici permettono turbine piccole a un solo stadio, ed è per questo che gli impianti ORC si usano per sorgenti sotto i 300 °C circa. I fluidi "secchi" escono dalla turbina surriscaldati (niente gocce), e quel calore si recupera di solito con un recuperatore. L'R134a qui non si può usare: 120 °C sono oltre la sua temperatura critica.

![Diagrammi T-s degli ORC](images/orc_Ts.png)

### Analisi exergetica: dove si perde il lavoro utile?

![Exergia distrutta](images/exergy_destruction.png)

- Nell'impianto a vapore (fiamma a 1200 °C, ambiente a 20 °C) la **caldaia** distrugge circa un terzo dell'exergia del combustibile: il calore passa da una fiamma caldissima ad acqua che bolle a ~295 °C. È il motivo per cui i cicli combinati mettono una turbina a gas "sopra" il ciclo a vapore. Le turbine perdono molto meno, le pompe quasi niente.
- Nel frigorifero (cella a 4 °C, cucina a 25 °C) le perdite sono distribuite su tutti i componenti: compressore, i due scambiatori (differenze di temperatura finite) e la **valvola di laminazione**, che è una trasformazione puramente irreversibile.

## Installazione

```bash
git clone https://github.com/Raffoo26/thermo-cycles.git
cd thermo-cycles
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Ogni volta che apri un nuovo Terminale, entra nella cartella e riattiva l'ambiente (`cd thermo-cycles` e `source .venv/bin/activate`).

## Usalo con i tuoi valori (senza scrivere codice)

```bash
python simulate.py
```

Il simulatore chiede quale ciclo vuoi (Rankine, frigorifero / pompa di calore, Brayton), poi ogni valore con la sua **unità di misura** e un **valore predefinito** tra parentesi quadre. Premi Invio per tenere il predefinito, oppure scrivi il tuo valore. Esempio di sessione (il programma è in inglese):

```text
Which cycle do you want to simulate?
    1) Rankine cycle (steam power plant / ORC)
    2) Refrigeration / heat pump cycle
    3) Brayton cycle (gas turbine)
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

Stampa la tabella degli stati e tutti i risultati, dimensiona l'impianto se hai indicato una potenza, se vuoi esegue l'analisi exergetica e salva i diagrammi T-s, p-h ed exergetico come immagini PNG nella cartella `results/`.

Consigli per l'inserimento:
- Decimali con il punto o con la virgola (`0.08` oppure `0,08`); rendimenti come frazione o in percentuale (`0.85` oppure `85`).
- I nomi dei fluidi sono quelli di [CoolProp](http://www.coolprop.org/fluid_properties/PurePseudoPure.html#list-of-fluids).
- I valori fisicamente impossibili (es. pressione al condensatore maggiore di quella in caldaia, o caldaia oltre la pressione critica) vengono rifiutati con una spiegazione.

## Web app

Un'app [Streamlit](https://streamlit.io/) con cursori e campi per ogni ciclo, diagrammi che si aggiornano subito, tabelle degli stati, analisi exergetica e download (PNG, CSV).

Per avviarla sul tuo computer:

```bash
pip install -r webapp/requirements.txt
streamlit run webapp/streamlit_app.py
```

Per pubblicarla online gratis su Streamlit Community Cloud:
1. Accedi a [share.streamlit.io](https://share.streamlit.io) con il tuo account GitHub.
2. **Create app** → *Deploy a public app from GitHub* → repository `Raffoo26/thermo-cycles`, branch `main`, file principale `webapp/streamlit_app.py`.
3. In **Advanced settings** scegli Python 3.12, poi **Deploy**. Ottieni un link pubblico da condividere.

## Usalo da Python

```python
from thermocycles import (rankine_reheat_regen_cycle, refrigeration_cycle,
                          brayton_cycle, exergy_analysis)
from thermocycles.plots import plot_Ts, plot_ph, plot_exergy

plant = rankine_reheat_regen_cycle(p_high_bar=80, p_low_bar=0.08, T_max_C=480,
                                   p_reheat_bar=7, T_reheat_C=440, p_fwh_bar=7,
                                   eta_turbine=0.85, eta_pump=0.85)
plant.summary()                          # tabella degli stati e risultati
print(plant.efficiency)                  # ≈ 0.372
plot_Ts(plant)

ex = exergy_analysis(plant, T0_C=20, T_source_C=1200)
ex.summary()
plot_exergy(ex)

hp = refrigeration_cycle(T_evap_C=-5, T_cond_C=45, superheat_K=5,
                         subcooling_K=3, eta_comp=0.75, fluid="R290")
print(hp.cop_heating)                    # COP come pompa di calore

gt = brayton_cycle(pressure_ratio=10, T_turbine_in_C=1200, T_in_C=15,
                   eta_comp=0.86, eta_turb=0.89, regen_effectiveness=0.8)
print(gt.efficiency)
```

Gli ingressi usano unità pratiche (bar, °C); tutti i risultati sono in unità SI (Pa, K, J/kg). Dividi per 1000 per avere kJ/kg, per 10<sup>5</sup> per avere bar, sottrai 273.15 per avere °C.

### Rankine — `rankine_cycle(...)` e `rankine_reheat_regen_cycle(...)`

| Parametro | Unità | Predefinito | Significato |
|---|---|---|---|
| `p_high_bar` | bar | obbligatorio | Pressione in caldaia (sotto la pressione critica) |
| `p_low_bar` | bar | obbligatorio | Pressione al condensatore |
| `T_max_C` | °C | `None` | Temperatura di ingresso turbina; `None` = vapore saturo secco |
| `p_reheat_bar` | bar | `None` | Pressione di risurriscaldamento; `None` = niente risurriscaldamento *(solo funzione avanzata)* |
| `T_reheat_C` | °C | = `T_max_C` | Temperatura dopo il risurriscaldamento *(solo funzione avanzata)* |
| `p_fwh_bar` | bar | `None` | Pressione del rigeneratore aperto (spillamento); `None` = niente rigenerazione *(solo funzione avanzata)* |
| `eta_turbine` | – | `1.0` | Rendimento isentropico di ogni tratto di turbina |
| `eta_pump` | – | `1.0` | Rendimento isentropico di ogni pompa |
| `fluid` | – | `"Water"` | Nome del fluido in CoolProp |

`rankine_cycle` è il ciclo semplice (stati 1–4). In `rankine_reheat_regen_cycle` gli stati sono numerati nell'ordine del flusso a partire dall'uscita del condensatore; se spillamento e risurriscaldamento sono alla stessa pressione, il vapore viene spillato prima del risurriscaldatore. Le grandezze specifiche sono per kg di vapore che attraversa la caldaia.

| Risultato | Unità | Significato |
|---|---|---|
| `efficiency` | – | Rendimento l<sub>netto</sub> / q<sub>in</sub> |
| `w_turbine`, `w_pump`, `w_net` | J/kg | Lavoro di turbina, pompe e netto |
| `q_in`, `q_out` | J/kg | Calore in caldaia + risurriscaldatore / calore ceduto al condensatore |
| `bwr` | – | Back Work Ratio l<sub>pompe</sub> / l<sub>turbina</sub> |
| `extraction_fraction` | – | Frazione di vapore spillata verso il rigeneratore |
| `mass_flow_for_power(P)` | kg/s | Portata di vapore per una potenza netta `P` in **W** |

### Frigorifero / pompa di calore — `refrigeration_cycle(...)`

| Parametro | Unità | Predefinito | Significato |
|---|---|---|---|
| `T_evap_C` | °C | obbligatorio | Temperatura di evaporazione (saturazione) |
| `T_cond_C` | °C | obbligatorio | Temperatura di condensazione (saturazione), sotto quella critica |
| `superheat_K` | K | `0` | Surriscaldamento del vapore all'ingresso del compressore |
| `subcooling_K` | K | `0` | Sottoraffreddamento del liquido all'uscita del condensatore |
| `eta_comp` | – | `1.0` | Rendimento isentropico del compressore |
| `fluid` | – | `"R134a"` | Nome del refrigerante in CoolProp |

| Risultato | Unità | Significato |
|---|---|---|
| `cop_cooling`, `cop_heating` | – | COP come frigorifero / come pompa di calore |
| `cop_carnot_cooling` | – | COP di Carnot inverso tra temperatura di evaporazione e di condensazione |
| `w_comp`, `q_evap`, `q_cond` | J/kg | Lavoro del compressore, effetto frigorifero, calore al condensatore |
| `pressure_ratio` | – | Rapporto di compressione p<sub>cond</sub> / p<sub>evap</sub> |
| `discharge_temperature_C` | °C | Temperatura di mandata del compressore |
| `volumetric_capacity` | J/m³ | Effetto frigorifero per m³ di vapore aspirato dal compressore |
| `mass_flow_for_cooling(Q)` | kg/s | Portata di refrigerante per una potenza frigorifera `Q` in **W** |

### Brayton — `brayton_cycle(...)`

| Parametro | Unità | Predefinito | Significato |
|---|---|---|---|
| `pressure_ratio` | – | obbligatorio | Rapporto di compressione p<sub>2</sub>/p<sub>1</sub> |
| `T_turbine_in_C` | °C | obbligatorio | Temperatura di ingresso turbina |
| `T_in_C` | °C | `27` | Temperatura di aspirazione del compressore |
| `p_in_bar` | bar | `1.0` | Pressione di aspirazione del compressore |
| `eta_comp`, `eta_turb` | – | `1.0` | Rendimento isentropico di compressore / turbina |
| `regen_effectiveness` | – | `0` | Efficacia del rigeneratore (0 = assente, 1 = ideale) |
| `fluid` | – | `"Air"` | Nome del gas in CoolProp |

Risultati: `efficiency`, `w_comp`, `w_turb`, `w_net`, `q_in`, `q_out` [J/kg], `bwr`, `exhaust_temperature_C`, `mass_flow_for_power(P)`. Stati: 1 aspirazione compressore, 2 mandata compressore, x uscita rigeneratore, 3 ingresso turbina, 4 uscita turbina, y scarico.

### Exergia — `exergy_analysis(risultato, ...)`

| Parametro | Unità | Predefinito | Significato |
|---|---|---|---|
| `result` | – | obbligatorio | Il risultato di uno qualsiasi dei cicli |
| `T0_C` | °C | `25` | Temperatura ambiente (stato morto); il calore ceduto all'ambiente attraversa qui il confine |
| `T_source_C` | °C | `None` | Sorgente calda (fiamma, fumi, acqua calda); `None` = temperatura massima del fluido in ogni riscaldatore |
| `T_cold_C` | °C | `None` | Cella frigorifera; `None` = temperatura massima del fluido nell'evaporatore |

Risultati: `destruction` (dizionario, J/kg per componente), `fuel`, `product`, `efficiency` (secondo principio), `table()`, `summary()`. Cicli motori: exergia spesa = exergia del calore della sorgente, prodotto = lavoro netto. Frigorifero: exergia spesa = lavoro del compressore, prodotto = exergia del freddo prodotto.

Funzioni di supporto: `saturation_pressure_bar(fluid, T_C)`, `saturation_temperature_C(fluid, p_bar)`, `critical_point(fluid)`. Ogni risultato ha anche `states`, `summary()`, `state_table()` e `warnings`.

## Esempi e test

```bash
python examples/rankine_example.py           # Rankine semplice + studio parametrico
python examples/rankine_advanced_example.py  # risurriscaldamento, rigenerazione, spillamento ottimale
python examples/refrigeration_example.py     # frigorifero + confronto refrigeranti
python examples/brayton_example.py           # turbina a gas con/senza rigeneratore
python examples/orc_example.py               # confronto fluidi per ORC
python examples/exergy_example.py            # exergia distrutta per componente
pytest                                       # test di validazione e unitari
```

## Struttura del progetto

```text
thermocycles/      il pacchetto: core.py, rankine.py, refrigeration.py, brayton.py, exergy.py, plots.py
simulate.py        simulatore interattivo da terminale
webapp/            web app Streamlit
notebooks/         notebook per Google Colab
examples/          script di esempio che generano le immagini in images/
tests/             test di validazione e unitari (pytest)
```

## Limiti dei modelli

Regime stazionario, nessuna perdita di carico negli scambiatori e nelle tubazioni, nessuna dispersione di calore verso l'ambiente, compressione di vapore monostadio subcritica (niente CO₂ transcritica), ciclo Brayton chiuso ad aria standard (niente chimica della combustione). Sono le ipotesi standard di un corso di Fisica Tecnica.

## Roadmap

- [x] Ciclo Rankine semplice
- [x] Rankine con risurriscaldamento e rigenerazione
- [x] Ciclo frigorifero / pompa di calore a compressione di vapore con confronto tra refrigeranti
- [x] Ciclo Brayton (turbina a gas) con rigenerazione
- [x] Confronto fluidi per cicli ORC
- [x] Analisi exergetica
- [x] Simulatore interattivo, web app e notebook Colab
- [ ] Ciclo combinato gas–vapore
- [ ] Rigeneratori chiusi e spillamenti multipli
- [ ] Pompa di calore a CO₂ transcritica

## Autore

Studente di Ingegneria Meccanica.

## Licenza

[MIT](LICENSE)
