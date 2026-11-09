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
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import (FeedwaterHeater, brayton_cycle, combined_cycle,  # noqa: E402
                          critical_point, exergy_analysis, optimal_high_pressure,
                          rankine_reheat_regen_cycle, refrigeration_cycle,
                          saturation_pressure_bar, transcritical_heat_pump)
from thermocycles.plots import plot_exergy, plot_hrsg, plot_ph, plot_Ts  # noqa: E402

REPO = "https://github.com/Raffoo26/thermo-cycles"
CYCLES = {
    "Rankine (steam / ORC power plant)": "rankine",
    "Brayton (gas turbine)": "brayton",
    "Combined cycle (gas + steam)": "combined",
    "Refrigeration / heat pump": "refrigeration",
    "Transcritical CO₂ heat pump": "co2",
}

st.set_page_config(page_title="Thermo Cycles", page_icon="🔥", layout="wide")


# --- Cached computations ------------------------------------------------------
# The free hosting has a small CPU: every combination of inputs is computed and
# drawn only once, so the server stays responsive.

def _rankine(p_high, p_low, T_max, p_rh, T_rh, heaters, eta_t, eta_p, fluid):
    return rankine_reheat_regen_cycle(p_high, p_low, T_max, p_rh, T_rh, None, eta_t, eta_p, fluid,
                                      heaters=[FeedwaterHeater(*h) for h in heaters])


def _combined(gas_args, steam_args, T_stack):
    return combined_cycle(brayton_cycle(*gas_args), _rankine(*steam_args), T_stack)


def _co2(T_e, p_high, T_gc, sh, eta):
    if p_high is None:
        return optimal_high_pressure(T_e, T_gc, sh, eta)[1]
    return transcritical_heat_pump(T_e, p_high, T_gc, sh, eta)


SOLVERS = {"rankine": _rankine, "refrigeration": refrigeration_cycle, "brayton": brayton_cycle,
           "combined": _combined, "co2": _co2}


@st.cache_data(show_spinner=False, max_entries=300)
def solve(kind, args):
    return SOLVERS[kind](*args)


@st.cache_data(show_spinner=False, max_entries=300)
def exergy(kind, args, T0, T_res):
    r = solve(kind, args)
    if kind == "refrigeration":
        return exergy_analysis(r, T0_C=T0, T_cold_C=T_res)
    if kind == "co2":
        return exergy_analysis(r, T0_C=T0, T_user_C=T_res)
    return exergy_analysis(r, T0_C=T0, T_source_C=T_res)


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=90)
    plt.close(fig)
    return buf.getvalue()


@st.cache_data(show_spinner=False, max_entries=300)
def diagrams_png(kind, args) -> bytes:
    r = solve(kind, args)
    if kind == "combined":
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5.5))
        plot_Ts(r.gas, ax=ax1, title=f"Gas turbine — η = {r.gas.efficiency * 100:.1f} %")
        plot_Ts(r.steam, ax=ax2, title=f"Steam cycle — η = {r.steam.efficiency * 100:.1f} %")
        plot_hrsg(r, ax=ax3)
    else:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
        plot_Ts(r, ax=ax1)
        plot_ph(r, ax=ax2)
    fig.tight_layout()
    return _png(fig)


@st.cache_data(show_spinner=False, max_entries=100)
def co2_pressure_png(T_e, T_gc, sh, eta, p_current) -> bytes:
    p = np.linspace(75, 150, 60)
    cop = []
    for pp in p:
        try:
            cop.append(transcritical_heat_pump(T_e, pp, T_gc, sh, eta).cop_heating)
        except ValueError:
            cop.append(np.nan)
    p_opt, best = optimal_high_pressure(T_e, T_gc, sh, eta)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(p, cop, "C0-", lw=2)
    ax.plot(p_opt, best.cop_heating, "o", color="C2", label=f"optimum {p_opt:.1f} bar")
    ax.axvline(p_current, color="C3", ls="--", lw=1, label=f"this design {p_current:.1f} bar")
    ax.set_xlabel("Gas cooler pressure [bar]")
    ax.set_ylabel("COP heating")
    ax.set_title("COP vs gas cooler pressure")
    ax.grid(alpha=0.3)
    ax.legend()
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
cycle = st.sidebar.radio("Cycle", list(CYCLES))
kind = CYCLES[cycle]
st.sidebar.divider()

if kind == "rankine":
    fluid = fluid_picker("Working fluid", ["Water", "R245fa", "R1233zd(E)", "Isopentane",
                                           "n-Pentane", "Toluene", "R134a"], "Water", "rk_fluid")
    superheat = st.sidebar.checkbox("Superheated vapour at turbine inlet", True)
    reheat = st.sidebar.checkbox("Reheat", False)
    n_heaters = st.sidebar.selectbox("Feedwater heaters (regeneration)", [0, 1, 2, 3, 4], index=0,
                                     key="n_heaters")
elif kind == "refrigeration":
    fluid = fluid_picker("Refrigerant", ["R134a", "R1234yf", "R290", "R600a", "R32", "R410A",
                                         "Ammonia"], "R134a", "rf_fluid")
elif kind == "brayton":
    fluid = fluid_picker("Working gas", ["Air", "Nitrogen", "Helium", "CO2"], "Air", "br_fluid")
elif kind == "combined":
    fluid = "Air / Water"
    cc_reheat = st.sidebar.checkbox("Steam reheat", False)
    cc_deaerator = st.sidebar.checkbox("Deaerator (open feedwater heater)", True)
else:
    fluid = "CO2"
    use_optimum = st.sidebar.checkbox("Use the optimal gas cooler pressure", True)

form = st.sidebar.form("inputs")
input_error = None
try:
    if kind == "rankine":
        d_high, d_low, d_T = rankine_defaults(fluid)
        p_high = form.number_input("Boiler pressure [bar]", 0.01, 1000.0, d_high, 1.0, key=f"ph_{fluid}")
        p_low = form.number_input("Condenser pressure [bar]", 0.001, 100.0, d_low, 0.01,
                                  format="%.3f", key=f"pl_{fluid}")
        T_max = form.number_input("Turbine inlet temperature [°C]", -50.0, 1000.0, d_T, 5.0,
                                  key=f"tm_{fluid}") if superheat else None
        p_rh = T_rh = None
        if reheat:
            p_rh = form.number_input("Reheat pressure [bar]", 0.01, 1000.0, round(d_high / 10, 2), 0.5,
                                     key=f"prh_{fluid}")
            T_rh = form.number_input("Temperature after reheat [°C]", -50.0, 1000.0,
                                     T_max if T_max is not None else d_T, 5.0, key=f"trh_{fluid}")
        heaters = []
        for i in range(n_heaters):
            # default pressures spread geometrically between condenser and boiler
            p_def = d_low * (d_high / d_low) ** ((n_heaters - i) / (n_heaters + 1))
            kind_def = "open" if i == n_heaters // 2 else "closed"
            form.markdown(f"**Feedwater heater {i + 1}**")
            h_kind = form.selectbox("Type", ["closed", "open"], index=["closed", "open"].index(kind_def),
                                    key=f"hk_{n_heaters}_{i}")
            h_p = form.number_input("Extraction pressure [bar]", 0.001, 1000.0, float(f"{p_def:.3g}"),
                                    0.5, key=f"hp_{fluid}_{n_heaters}_{i}")
            h_ttd = form.number_input("TTD, closed heaters only [K]", 0.0, 30.0, 3.0, 0.5,
                                      key=f"ht_{n_heaters}_{i}")
            heaters.append((h_p, h_kind, h_ttd))
        eta_t = pct(form, "Turbine isentropic efficiency", 85, "rk_eta_t")
        eta_p = pct(form, "Pump isentropic efficiency", 85, "rk_eta_p")
        power = form.number_input("Net power output [MW] (for sizing)", 0.0, 5000.0, 100.0, 10.0)
        args = (p_high, p_low, T_max, p_rh, T_rh, tuple(heaters), eta_t, eta_p, fluid)
        default_T0, default_res = 20.0, (1200.0 if fluid == "Water" else 150.0)

    elif kind == "refrigeration":
        T_evap = form.number_input("Evaporating temperature [°C]", -100.0, 100.0, -10.0, 1.0)
        T_cond = form.number_input("Condensing temperature [°C]", -50.0, 150.0, 40.0, 1.0)
        sh = form.number_input("Superheat at compressor inlet [K]", 0.0, 50.0, 5.0, 1.0)
        sc = form.number_input("Subcooling at condenser outlet [K]", 0.0, 50.0, 3.0, 1.0)
        eta_c = pct(form, "Compressor isentropic efficiency", 75, "rf_eta_c")
        capacity = form.number_input("Cooling capacity [kW] (for sizing)", 0.0, 100000.0, 3.5, 0.5)
        args = (T_evap, T_cond, sh, sc, eta_c, fluid)
        default_T0, default_res = 25.0, float(round(T_evap + sh + 5))

    elif kind == "brayton":
        pr = form.number_input("Compressor pressure ratio [-]", 1.1, 100.0, 10.0, 0.5)
        TIT = form.number_input("Turbine inlet temperature [°C]", 100.0, 2000.0, 1200.0, 10.0)
        T_in = form.number_input("Compressor inlet temperature [°C]", -50.0, 100.0, 15.0, 1.0)
        p_in = form.number_input("Compressor inlet pressure [bar]", 0.1, 50.0, 1.013, 0.01, format="%.3f")
        eta_c = pct(form, "Compressor isentropic efficiency", 86, "br_eta_c")
        eta_tb = pct(form, "Turbine isentropic efficiency", 89, "br_eta_t")
        eps = form.slider("Regenerator effectiveness (0 = none)", 0, 100, 0, 5, format="%d %%") / 100
        power = form.number_input("Net power output [MW] (for sizing)", 0.0, 2000.0, 50.0, 5.0)
        args = (pr, TIT, T_in, p_in, eta_c, eta_tb, eps, fluid)
        default_T0, default_res = float(T_in), 1800.0   # open gas turbine: ambient = intake air

    elif kind == "combined":
        form.markdown("**Gas turbine**")
        pr = form.number_input("Compressor pressure ratio [-]", 1.1, 100.0, 18.0, 0.5, key="cc_pr")
        TIT = form.number_input("Turbine inlet temperature [°C]", 100.0, 2000.0, 1350.0, 10.0, key="cc_tit")
        T_in = form.number_input("Air intake temperature [°C]", -50.0, 60.0, 15.0, 1.0, key="cc_tin")
        eta_c = pct(form, "Compressor isentropic efficiency", 88, "cc_eta_c")
        eta_tb = pct(form, "Gas turbine isentropic efficiency", 90, "cc_eta_t")
        form.markdown("**Steam cycle**")
        s_p = form.number_input("HRSG steam pressure [bar]", 1.0, 200.0, 40.0, 1.0, key="cc_sp")
        s_T = form.number_input("Steam temperature [°C]", 100.0, 650.0, 520.0, 5.0, key="cc_sT")
        s_pc = form.number_input("Condenser pressure [bar]", 0.01, 1.0, 0.05, 0.01, format="%.3f", key="cc_pc")
        s_rh = s_Trh = None
        if cc_reheat:
            s_rh = form.number_input("Reheat pressure [bar]", 0.5, 200.0, 8.0, 0.5, key="cc_prh")
            s_Trh = form.number_input("Reheat temperature [°C]", 100.0, 650.0, 520.0, 5.0, key="cc_trh")
        s_heaters = ((form.number_input("Deaerator pressure [bar]", 0.1, 20.0, 1.5, 0.1, key="cc_da"),
                      "open", 0.0),) if cc_deaerator else ()
        s_eta_t = pct(form, "Steam turbine isentropic efficiency", 88, "cc_seta_t")
        s_eta_p = pct(form, "Pump isentropic efficiency", 80, "cc_seta_p")
        T_stack = form.number_input("Stack temperature [°C]", 50.0, 400.0, 170.0, 5.0, key="cc_stack")
        power = form.number_input("Net power output [MW] (for sizing)", 0.0, 5000.0, 400.0, 10.0, key="cc_pw")
        args = ((pr, TIT, T_in, 1.013, eta_c, eta_tb, 0.0, "Air"),
                (s_p, s_pc, s_T, s_rh, s_Trh, s_heaters, s_eta_t, s_eta_p, "Water"), T_stack)
        default_T0, default_res = float(T_in), 1800.0

    else:
        T_e = form.number_input("Evaporating temperature [°C]", -50.0, 25.0, 0.0, 1.0, key="co2_te")
        T_gc = form.number_input("Gas cooler outlet temperature [°C]", -20.0, 80.0, 35.0, 1.0, key="co2_tgc")
        p_gc = None if use_optimum else form.number_input("Gas cooler pressure [bar]", 74.0, 200.0, 95.0, 1.0,
                                                          key="co2_p")
        sh = form.number_input("Superheat at compressor inlet [K]", 0.0, 30.0, 5.0, 1.0, key="co2_sh")
        eta_c = pct(form, "Compressor isentropic efficiency", 70, "co2_eta")
        capacity = form.number_input("Heating capacity [kW] (for sizing)", 0.0, 10000.0, 8.0, 0.5, key="co2_cap")
        args = (T_e, p_gc, T_gc, sh, eta_c)
        default_T0, default_res = float(round(T_e + sh + 5)), float(T_gc)

    with form.expander("Exergy analysis settings"):
        T0 = st.number_input("Ambient (dead state) temperature [°C]", -40.0, 50.0, default_T0, 1.0,
                             key=f"T0_{cycle}_{default_T0}")
        res_label = {"refrigeration": "Refrigerated space temperature [°C]",
                     "co2": "Temperature of the heated water / air [°C]"}.get(
            kind, "Hot source temperature [°C] (flame, flue gas…)")
        T_res = st.number_input(res_label, -100.0, 3000.0, default_res, 1.0,
                                key=f"res_{cycle}_{fluid}_{default_res}")
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
eta_II = f"{ex.efficiency * 100:.1f} %" if ex else "–"

# --- Main page: results -------------------------------------------------------
st.title(f"{r.name} — {r.fluid}")
st.caption(f"Real-fluid properties from CoolProp · validated against textbook examples · [source code]({REPO})")

for w in r.warnings:
    st.warning(w)

if kind == "refrigeration":
    m = r.mass_flow_for_cooling(capacity * 1e3) if capacity > 0 else None
    cols = st.columns(5)
    cols[0].metric("COP cooling", f"{r.cop_cooling:.2f}")
    cols[1].metric("COP heating (heat pump)", f"{r.cop_heating:.2f}")
    cols[2].metric("Carnot COP", f"{r.cop_carnot_cooling:.2f}")
    cols[3].metric("Discharge temperature", f"{r.discharge_temperature_C:.1f} °C")
    cols[4].metric("Second-law efficiency", eta_II)
    sizing = {"Refrigerating effect [kJ/kg]": r.q_evap / 1e3, "Compressor work [kJ/kg]": r.w_comp / 1e3,
              "Heat to condenser [kJ/kg]": r.q_cond / 1e3, "Pressure ratio [-]": r.pressure_ratio,
              "Volumetric cooling capacity [kJ/m³]": r.volumetric_capacity / 1e3}
    if m:
        sizing.update({"Refrigerant mass flow [g/s]": m * 1e3, "Compressor power [kW]": m * r.w_comp / 1e3,
                       "Heating capacity as heat pump [kW]": m * r.q_cond / 1e3})
elif kind == "co2":
    p_used = r.states["2"].p / 1e5
    m = capacity * 1e3 / r.q_cond if capacity > 0 else None
    cols = st.columns(5)
    cols[0].metric("COP heating", f"{r.cop_heating:.2f}")
    cols[1].metric("Lorenz COP (ideal)", f"{r.cop_lorenz_heating:.2f}")
    cols[2].metric("Gas cooler pressure", f"{p_used:.1f} bar" + (" (optimum)" if use_optimum else ""))
    cols[3].metric("Discharge temperature", f"{r.discharge_temperature_C:.1f} °C")
    cols[4].metric("Second-law efficiency", eta_II)
    sizing = {"Heat to gas cooler [kJ/kg]": r.q_cond / 1e3, "Heat from evaporator [kJ/kg]": r.q_evap / 1e3,
              "Compressor work [kJ/kg]": r.w_comp / 1e3, "COP cooling [-]": r.cop_cooling,
              "Gas cooler mean temperature [°C]": r.gas_cooler_mean_temperature - 273.15,
              "Pressure ratio [-]": r.pressure_ratio}
    if m:
        sizing.update({"CO₂ mass flow [g/s]": m * 1e3, "Compressor power [kW]": m * r.w_comp / 1e3,
                       "Heat taken from the ambient [kW]": m * r.q_evap / 1e3})
elif kind == "combined":
    cols = st.columns(5)
    cols[0].metric("Combined efficiency", f"{r.efficiency * 100:.1f} %")
    cols[1].metric("Gas turbine alone", f"{r.gas.efficiency * 100:.1f} %")
    cols[2].metric("Steam cycle alone", f"{r.steam.efficiency * 100:.1f} %")
    cols[3].metric("Pinch point", f"{r.pinch_K:.1f} K")
    cols[4].metric("Second-law efficiency", eta_II)
    sizing = {"Net work [kJ/kg air]": r.w_net / 1e3, "Steam per kg of air [kg/kg]": r.steam_per_air,
              "Power from gas turbine [%]": r.gas_share * 100,
              "Gas turbine exhaust [°C]": r.gas.states["4"].T - 273.15,
              "Heat recovered in HRSG [kJ/kg air]": r.q_hrsg / 1e3}
    if power > 0:
        m_air, m_steam = r.mass_flows_for_power(power * 1e6)
        sizing.update({"Air mass flow [kg/s]": m_air, "Steam mass flow [kg/s]": m_steam,
                       "Gas turbine net power [MW]": m_air * r.gas.w_net / 1e6,
                       "Steam turbine net power [MW]": m_steam * r.steam.w_net / 1e6,
                       "Fuel heat input [MW]": m_air * r.q_in / 1e6})
else:
    m = r.mass_flow_for_power(power * 1e6) if power > 0 else None
    cols = st.columns(4)
    cols[0].metric("Thermal efficiency", f"{r.efficiency * 100:.1f} %")
    cols[1].metric("Net work", f"{r.w_net / 1e3:.0f} kJ/kg")
    cols[2].metric("Back Work Ratio", f"{r.bwr * 100:.1f} %")
    cols[3].metric("Second-law efficiency", eta_II)
    if kind == "rankine":
        sizing = {"Turbine work [kJ/kg]": r.w_turbine / 1e3, "Pump work [kJ/kg]": r.w_pump / 1e3,
                  "Heat input [kJ/kg]": r.q_in / 1e3, "Heat rejected [kJ/kg]": r.q_out / 1e3}
        for p_x, y_x in r.extractions.items():
            sizing[f"Extraction at {p_x:g} bar [-]"] = y_x
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
    show_png(png, "Cycle diagrams")
    st.download_button("Download diagrams (PNG)", png, "thermo_cycle_diagrams.png", "image/png")
    if kind == "co2":
        show_png(co2_pressure_png(T_e, T_gc, sh, eta_c, r.states["2"].p / 1e5), "COP vs pressure")

with tab_states:
    left, right = st.columns([3, 2])
    if kind == "combined":
        tables = {"Gas turbine (Air)": r.gas.state_table(), "Steam cycle (Water)": r.steam.state_table()}
    else:
        tables = {"Thermodynamic states": r.state_table()}
    csv = []
    for title, rows in tables.items():
        df = pd.DataFrame(rows).set_index("State")
        left.subheader(title)
        left.dataframe(df.style.format(precision=4, na_rep="–"))
        csv.append(f"# {title}\n" + df.to_csv())
    left.download_button("Download states (CSV)", "\n".join(csv).encode(), "states.csv", "text/csv")
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
    st.markdown(f"""
This app solves thermodynamic cycles with real-fluid properties from
[CoolProp](http://www.coolprop.org/). The solvers are validated against worked examples of
Moran & Shapiro, *Fundamentals of Engineering Thermodynamics* (deviation below 1 %), and the
CO₂ optimal pressure against the correlation of Liao et al. (2000).

- **Rankine**: simple, with reheat and up to 4 open or closed feedwater heaters; water or organic fluids (ORC).
- **Brayton**: air-standard gas turbine with real-gas properties and optional regenerator.
- **Combined cycle**: gas turbine + steam cycle through a single-pressure heat recovery steam
  generator, with stack temperature and pinch point.
- **Refrigeration / heat pump**: single-stage subcritical vapour compression.
- **Transcritical CO₂ heat pump**: gas cooler above the critical point, optimal high pressure.
- **Exergy analysis**: exergy destroyed in every component (Gouy–Stodola) and second-law efficiency.

Inputs: pressures in bar, temperatures in °C, efficiencies in %. Results per kg of working fluid,
plus plant sizing for the power or capacity you enter.

Source code, documentation and tests: [{REPO}]({REPO})
""")
