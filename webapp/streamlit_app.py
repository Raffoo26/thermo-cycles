"""
Thermo Cycles — web app.

Run locally from the project root:
    pip install -r webapp/requirements.txt
    streamlit run webapp/streamlit_app.py
"""

import base64
import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import (brayton_cycle, critical_point, exergy_analysis,  # noqa: E402
                          rankine_reheat_regen_cycle, refrigeration_cycle,
                          saturation_pressure_bar)
from thermocycles.plots import plot_exergy, plot_ph, plot_Ts  # noqa: E402

REPO = "https://github.com/Raffoo26/thermo-cycles"

st.set_page_config(page_title="Thermo Cycles", page_icon="🔥", layout="wide")


# --- Cached computations ------------------------------------------------------
# The free hosting has a small CPU: every combination of inputs is computed and
# drawn only once, so the server stays responsive.
SOLVERS = {"rankine": rankine_reheat_regen_cycle, "refrigeration": refrigeration_cycle,
           "brayton": brayton_cycle}


@st.cache_data(show_spinner=False, max_entries=300)
def solve(kind, args):
    return SOLVERS[kind](*args)


@st.cache_data(show_spinner=False, max_entries=300)
def exergy(kind, args, T0, T_res):
    r = solve(kind, args)
    if kind == "refrigeration":
        return exergy_analysis(r, T0_C=T0, T_cold_C=T_res)
    return exergy_analysis(r, T0_C=T0, T_source_C=T_res)


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=90)
    plt.close(fig)
    return buf.getvalue()


@st.cache_data(show_spinner=False, max_entries=300)
def diagrams_png(kind, args) -> bytes:
    r = solve(kind, args)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    plot_Ts(r, ax=ax1)
    plot_ph(r, ax=ax2)
    fig.tight_layout()
    return _png(fig)


@st.cache_data(show_spinner=False, max_entries=300)
def exergy_png(kind, args, T0, T_res) -> bytes:
    fig, ax = plt.subplots(figsize=(9, 4))
    plot_exergy(exergy(kind, args, T0, T_res), ax=ax)
    fig.tight_layout()
    return _png(fig)


def show_png(png: bytes, alt: str) -> None:
    """Embed the image in the page itself (no separate download request)."""
    b64 = base64.b64encode(png).decode()
    st.markdown(f'<img src="data:image/png;base64,{b64}" alt="{alt}" style="width:100%">',
                unsafe_allow_html=True)


def fluid_picker(label, options, default, key):
    choice = st.sidebar.selectbox(label, options + ["Other (type a CoolProp name)"],
                                  index=options.index(default), key=key)
    if choice.startswith("Other"):
        return st.sidebar.text_input("CoolProp fluid name", "R1234ze(E)", key=key + "_other").strip()
    return choice


@st.cache_data(show_spinner=False)
def rankine_defaults(fluid):
    """Sensible starting values for each fluid (steam plant for water, ORC otherwise)."""
    if fluid == "Water":
        return 80.0, 0.08, 480.0
    T_crit, _ = critical_point(fluid)
    T_evap = min(120.0, T_crit - 25)
    p_high = round(saturation_pressure_bar(fluid, T_evap), 2)
    p_low = round(saturation_pressure_bar(fluid, 35.0), 3)
    return p_high, p_low, T_evap + 10


def pct(box, label, default, key, lo=40, hi=100):
    return box.slider(label, lo, hi, default, step=1, format="%d %%", key=key) / 100


# --- Sidebar: inputs ----------------------------------------------------------
# Choices that show or hide fields stay outside the form (they update at once);
# all the numbers live in a form, so the cycle is computed only when the user
# presses "Calculate" instead of at every single click.
st.sidebar.title("🔥 Thermo Cycles")
cycle = st.sidebar.radio("Cycle", ["Rankine (steam / ORC power plant)",
                                   "Refrigeration / heat pump",
                                   "Brayton (gas turbine)"])
st.sidebar.divider()

if cycle.startswith("Rankine"):
    fluid = fluid_picker("Working fluid", ["Water", "R245fa", "R1233zd(E)", "Isopentane",
                                           "n-Pentane", "Toluene", "R134a"], "Water", "rk_fluid")
    superheat = st.sidebar.checkbox("Superheated vapour at turbine inlet", True)
    reheat = st.sidebar.checkbox("Reheat", False)
    fwh = st.sidebar.checkbox("Regeneration (open feedwater heater)", False)
elif cycle.startswith("Refrigeration"):
    fluid = fluid_picker("Refrigerant", ["R134a", "R1234yf", "R290", "R600a", "R32", "R410A",
                                         "Ammonia"], "R134a", "rf_fluid")
else:
    fluid = fluid_picker("Working gas", ["Air", "Nitrogen", "Helium", "CO2"], "Air", "br_fluid")

form = st.sidebar.form("inputs")
input_error = None
try:
    if cycle.startswith("Rankine"):
        d_high, d_low, d_T = rankine_defaults(fluid)
        p_high = form.number_input("Boiler pressure [bar]", 0.01, 1000.0, d_high, 1.0, key=f"ph_{fluid}")
        p_low = form.number_input("Condenser pressure [bar]", 0.001, 100.0, d_low, 0.01,
                                  format="%.3f", key=f"pl_{fluid}")
        T_max = form.number_input("Turbine inlet temperature [°C]", -50.0, 1000.0, d_T, 5.0,
                                  key=f"tm_{fluid}") if superheat else None
        p_rh = T_rh = p_fwh = None
        if reheat:
            p_rh = form.number_input("Reheat pressure [bar]", 0.01, 1000.0, 7.0, 0.5)
            T_rh = form.number_input("Temperature after reheat [°C]", -50.0, 1000.0,
                                     T_max if T_max is not None else 440.0, 5.0)
        if fwh:
            p_fwh = form.number_input("Feedwater heater pressure [bar]", 0.01, 1000.0, 7.0, 0.5)
        eta_t = pct(form, "Turbine isentropic efficiency", 85, "rk_eta_t")
        eta_p = pct(form, "Pump isentropic efficiency", 85, "rk_eta_p")
        power = form.number_input("Net power output [MW] (for sizing)", 0.0, 5000.0, 100.0, 10.0)
        kind, args = "rankine", (p_high, p_low, T_max, p_rh, T_rh, p_fwh, eta_t, eta_p, fluid)
        default_T0, default_res = 20.0, (1200.0 if fluid == "Water" else 150.0)

    elif cycle.startswith("Refrigeration"):
        T_evap = form.number_input("Evaporating temperature [°C]", -100.0, 100.0, -10.0, 1.0)
        T_cond = form.number_input("Condensing temperature [°C]", -50.0, 150.0, 40.0, 1.0)
        sh = form.number_input("Superheat at compressor inlet [K]", 0.0, 50.0, 5.0, 1.0)
        sc = form.number_input("Subcooling at condenser outlet [K]", 0.0, 50.0, 3.0, 1.0)
        eta_c = pct(form, "Compressor isentropic efficiency", 75, "rf_eta_c")
        capacity = form.number_input("Cooling capacity [kW] (for sizing)", 0.0, 100000.0, 3.5, 0.5)
        kind, args = "refrigeration", (T_evap, T_cond, sh, sc, eta_c, fluid)
        default_T0, default_res = 25.0, float(round(T_evap + sh + 5))

    else:
        pr = form.number_input("Compressor pressure ratio [-]", 1.1, 100.0, 10.0, 0.5)
        TIT = form.number_input("Turbine inlet temperature [°C]", 100.0, 2000.0, 1200.0, 10.0)
        T_in = form.number_input("Compressor inlet temperature [°C]", -50.0, 100.0, 15.0, 1.0)
        p_in = form.number_input("Compressor inlet pressure [bar]", 0.1, 50.0, 1.013, 0.01, format="%.3f")
        eta_c = pct(form, "Compressor isentropic efficiency", 86, "br_eta_c")
        eta_tb = pct(form, "Turbine isentropic efficiency", 89, "br_eta_t")
        eps = form.slider("Regenerator effectiveness (0 = none)", 0, 100, 0, 5, format="%d %%") / 100
        power = form.number_input("Net power output [MW] (for sizing)", 0.0, 2000.0, 50.0, 5.0)
        kind, args = "brayton", (pr, TIT, T_in, p_in, eta_c, eta_tb, eps, fluid)
        default_T0, default_res = float(T_in), 1800.0   # open gas turbine: ambient = intake air

    with form.expander("Exergy analysis settings"):
        T0 = st.number_input("Ambient (dead state) temperature [°C]", -30.0, 50.0, default_T0, 1.0,
                             key=f"T0_{cycle}")
        res_label = ("Refrigerated space temperature [°C]" if kind == "refrigeration"
                     else "Hot source temperature [°C] (flame, flue gas…)")
        T_res = st.number_input(res_label, -100.0, 3000.0, default_res, 1.0,
                                key=f"res_{cycle}_{fluid}")
except ValueError as e:          # e.g. an unknown fluid name
    input_error = str(e)
finally:
    form.form_submit_button("Calculate ▶", type="primary", use_container_width=True)

try:
    if input_error:
        raise ValueError(input_error)
    r = solve(kind, args)
except ValueError as e:
    st.title("Thermo Cycles")
    st.error(f"These inputs are not physically possible: {e}")
    st.stop()

# Exergy analysis (an error here does not hide the other results)
ex, ex_error = None, None
try:
    ex = exergy(kind, args, T0, T_res)
except ValueError as e:
    ex_error = str(e)

# --- Main page: results -------------------------------------------------------
st.title(f"{r.name} — {r.fluid}")
st.caption(f"Real-fluid properties from CoolProp · validated against textbook examples · [source code]({REPO})")

for w in r.warnings:
    st.warning(w)

if cycle.startswith("Refrigeration"):
    m = r.mass_flow_for_cooling(capacity * 1e3) if capacity > 0 else None
    cols = st.columns(5)
    cols[0].metric("COP cooling", f"{r.cop_cooling:.2f}")
    cols[1].metric("COP heating (heat pump)", f"{r.cop_heating:.2f}")
    cols[2].metric("Carnot COP", f"{r.cop_carnot_cooling:.2f}")
    cols[3].metric("Discharge temperature", f"{r.discharge_temperature_C:.1f} °C")
    cols[4].metric("Pressure ratio", f"{r.pressure_ratio:.2f}")
    sizing = {
        "Refrigerating effect [kJ/kg]": r.q_evap / 1e3,
        "Compressor work [kJ/kg]": r.w_comp / 1e3,
        "Heat to condenser [kJ/kg]": r.q_cond / 1e3,
        "Volumetric cooling capacity [kJ/m³]": r.volumetric_capacity / 1e3,
    }
    if m:
        sizing.update({"Refrigerant mass flow [g/s]": m * 1e3,
                       "Compressor power [kW]": m * r.w_comp / 1e3,
                       "Heating capacity as heat pump [kW]": m * r.q_cond / 1e3})
else:
    m = r.mass_flow_for_power(power * 1e6) if power > 0 else None
    cols = st.columns(4)
    cols[0].metric("Thermal efficiency", f"{r.efficiency * 100:.1f} %")
    cols[1].metric("Net work", f"{r.w_net / 1e3:.0f} kJ/kg")
    cols[2].metric("Back Work Ratio", f"{r.bwr * 100:.1f} %")
    cols[3].metric("Second-law efficiency", f"{ex.efficiency * 100:.1f} %" if ex else "–")
    if cycle.startswith("Rankine"):
        sizing = {"Turbine work [kJ/kg]": r.w_turbine / 1e3, "Pump work [kJ/kg]": r.w_pump / 1e3,
                  "Heat input [kJ/kg]": r.q_in / 1e3, "Heat rejected [kJ/kg]": r.q_out / 1e3}
        if r.extraction_fraction:
            sizing["Extraction fraction y [-]"] = r.extraction_fraction
        if m:
            sizing.update({"Steam mass flow [kg/s]": m, "Boiler + reheat duty [MW]": m * r.q_in / 1e6,
                           "Condenser duty [MW]": m * r.q_out / 1e6})
    else:
        sizing = {"Compressor work [kJ/kg]": r.w_comp / 1e3, "Turbine work [kJ/kg]": r.w_turb / 1e3,
                  "Heat input [kJ/kg]": r.q_in / 1e3, "Exhaust temperature [°C]": r.exhaust_temperature_C}
        if m:
            sizing.update({"Air mass flow [kg/s]": m, "Fuel heat input [MW]": m * r.q_in / 1e6,
                           "Compressor power [MW]": m * r.w_comp / 1e6})

tab_diag, tab_states, tab_exergy, tab_about = st.tabs(
    ["📈 Diagrams", "📋 States & results", "♻️ Exergy analysis", "ℹ️ About"])

with tab_diag:
    png = diagrams_png(kind, args)
    show_png(png, "T-s and p-h diagrams")
    st.download_button("Download diagrams (PNG)", png, "thermo_cycle_diagrams.png", "image/png")

with tab_states:
    left, right = st.columns([3, 2])
    states_df = pd.DataFrame(r.state_table()).set_index("State")
    left.subheader("Thermodynamic states")
    left.dataframe(states_df.style.format(precision=4, na_rep="–"))
    left.download_button("Download states (CSV)", states_df.to_csv().encode(), "states.csv", "text/csv")
    right.subheader("Energy balance and sizing")
    right.dataframe(pd.DataFrame({"Value": sizing}).style.format(precision=3))

with tab_exergy:
    if ex is None:
        st.error(f"Exergy analysis not possible with these reservoir temperatures: {ex_error}")
        st.info("Change them in *Exergy analysis settings* in the sidebar.")
    else:
        st.markdown(f"**Second-law efficiency: {ex.efficiency * 100:.1f} %** — fuel: {ex.fuel_label} "
                    f"({ex.fuel / 1e3:.1f} kJ/kg), product: {ex.product_label} ({ex.product / 1e3:.1f} kJ/kg). "
                    "Change the reservoir temperatures in *Exergy analysis settings* in the sidebar.")
        show_png(exergy_png(kind, args, T0, T_res), "Exergy destruction")
        st.dataframe(pd.DataFrame(ex.table()).set_index("Component").style.format(precision=2))
        for n in ex.notes:
            st.info(n)

with tab_about:
    T_crit, p_crit = critical_point(r.fluid)
    st.markdown(f"""
**{r.fluid}** — critical point: {T_crit:.1f} °C, {p_crit:.2f} bar.

This app solves thermodynamic cycles with real-fluid properties from
[CoolProp](http://www.coolprop.org/). The solvers are validated against worked examples of
Moran & Shapiro, *Fundamentals of Engineering Thermodynamics* (deviation below 1 %).

- **Rankine**: simple, with reheat, with an open feedwater heater, or both. Works with water and
  organic fluids (ORC).
- **Refrigeration / heat pump**: single-stage subcritical vapour compression with superheat,
  subcooling and compressor efficiency (transcritical CO₂ cycles are not supported).
- **Brayton**: air-standard gas turbine with real-gas properties and optional regenerator.
- **Exergy analysis**: exergy destroyed in every component (Gouy–Stodola) and second-law efficiency.

Inputs: pressures in bar, temperatures in °C, efficiencies in %. Results per kg of working fluid,
plus plant sizing for the power or capacity you enter.

Source code, documentation and tests: [{REPO}]({REPO})
""")
