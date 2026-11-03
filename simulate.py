"""
Interactive simulator: enter your own values and get results and diagrams,
without writing any code.

Run from the project root:
    python simulate.py

For every value the default is shown in square brackets: press Enter to keep it.
Efficiencies can be typed as fractions (0.85) or percentages (85).
"""

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "results"

RANKINE_FLUIDS = "Water, R245fa, Toluene, Cyclopentane, R1233zd(E), ..."
REFRIGERANTS = "R134a, R1234yf, R290 (propane), R600a (isobutane), R32, R410A, Ammonia, ..."


# --- Input helpers (no CoolProp needed, tested in tests/test_simulate.py) ---

def parse_number(text: str) -> float:
    """Parse a number, accepting a decimal comma ("0,85") as well as a point."""
    return float(text.strip().replace(",", "."))


def parse_efficiency(text: str) -> float:
    """Parse an efficiency typed as a fraction (0.85) or a percentage (85 or 85%)."""
    value = parse_number(text.replace("%", ""))
    if value > 1:
        value /= 100
    if not 0 < value <= 1:
        raise ValueError("an efficiency must be between 0 and 1 (or 0 and 100 %)")
    return value


def parse_fraction(text: str) -> float:
    """Parse a value between 0 and 1 typed as a fraction (0.8) or a percentage (80 or 80%)."""
    value = parse_number(text.replace("%", ""))
    if value > 1:
        value /= 100
    if not 0 <= value <= 1:
        raise ValueError("the value must be between 0 and 1 (or 0 and 100 %)")
    return value


def ask(prompt: str, default=None, parser=parse_number, optional: bool = False):
    """Ask for a value until a valid one is entered.

    Empty input returns the default (or None if the value is optional)."""
    if default is not None:
        suffix = f" [{default}]"
    elif optional:
        suffix = " [optional]"
    else:
        suffix = ""
    while True:
        text = input(f"  {prompt}{suffix}: ").strip()
        if not text:
            if default is not None:
                return default
            if optional:
                return None
            print("    Please enter a value.")
            continue
        try:
            return parser(text)
        except ValueError as e:
            print(f"    Invalid value ({e}). Try again.")


def ask_choice(prompt: str, options: dict[str, str], default: str) -> str:
    for key, label in options.items():
        print(f"    {key}) {label}")
    while True:
        text = input(f"  {prompt} [{default}]: ").strip() or default
        if text in options:
            return text
        print(f"    Please choose one of: {', '.join(options)}")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    text = input(f"  {prompt} [{hint}]: ").strip().lower()
    if not text:
        return default
    return text in ("y", "yes", "s", "si", "sì")


def check_fluid(name: str) -> str:
    from CoolProp.CoolProp import PropsSI
    try:
        PropsSI("Tcrit", name)
    except ValueError:
        raise ValueError(f"'{name}' is not a CoolProp fluid name") from None
    return name


# --- Cycles -----------------------------------------------------------------

def run_rankine():
    from thermocycles import rankine_reheat_regen_cycle

    print("\nRANKINE CYCLE (steam power plant or ORC)")
    print(f"  Fluid examples: {RANKINE_FLUIDS}")
    fluid = ask("Working fluid", "Water", check_fluid)
    p_high = ask("Boiler pressure [bar]", 80.0)
    p_low = ask("Condenser pressure [bar]", 0.08)
    T_max = ask("Turbine inlet temperature [°C], empty = saturated vapour", None, optional=True)
    p_rh = T_rh = p_fwh = None
    if ask_yes_no("Add reheat?", default=False):
        p_rh = ask("Reheat pressure [bar]", 7.0)
        T_rh = ask("Temperature after reheat [°C]", T_max if T_max is not None else 440.0)
    if ask_yes_no("Add an open feedwater heater (regeneration)?", default=False):
        p_fwh = ask("Feedwater heater (extraction) pressure [bar]", 7.0)
    eta_t = ask("Turbine isentropic efficiency [0-1 or %]", 1.0, parse_efficiency)
    eta_p = ask("Pump isentropic efficiency [0-1 or %]", 1.0, parse_efficiency)
    power = ask("Net power output [MW]", None, optional=True)

    r = rankine_reheat_regen_cycle(p_high, p_low, T_max, p_rh, T_rh, p_fwh, eta_t, eta_p, fluid)
    r.summary()
    if power is not None:
        m = r.mass_flow_for_power(power * 1e6)
        print(f"\nFor {power:g} MW net:")
        print(f"  Steam mass flow    : {m:10.2f} kg/s")
        print(f"  Turbine power      : {m * r.w_turbine / 1e6:10.2f} MW")
        print(f"  Pump power         : {m * r.w_pump / 1e6:10.3f} MW")
        print(f"  Boiler heat input  : {m * r.q_in / 1e6:10.2f} MW")
        print(f"  Condenser heat out : {m * r.q_out / 1e6:10.2f} MW")
    return r


def run_brayton():
    from thermocycles import brayton_cycle

    print("\nBRAYTON CYCLE (gas turbine)")
    fluid = ask("Working gas (Air, Nitrogen, Helium, CO2, ...)", "Air", check_fluid)
    pr = ask("Compressor pressure ratio [-]", 10.0)
    TIT = ask("Turbine inlet temperature [°C]", 1200.0)
    T_in = ask("Compressor inlet temperature [°C]", 15.0)
    p_in = ask("Compressor inlet pressure [bar]", 1.013)
    eta_c = ask("Compressor isentropic efficiency [0-1 or %]", 1.0, parse_efficiency)
    eta_t = ask("Turbine isentropic efficiency [0-1 or %]", 1.0, parse_efficiency)
    eps = ask("Regenerator effectiveness [0-1 or %, 0 = none]", 0.0, parse_fraction)
    power = ask("Net power output [MW]", None, optional=True)

    r = brayton_cycle(pr, TIT, T_in, p_in, eta_c, eta_t, eps, fluid)
    r.summary()
    if power is not None:
        m = r.mass_flow_for_power(power * 1e6)
        print(f"\nFor {power:g} MW net:")
        print(f"  Gas mass flow      : {m:10.2f} kg/s")
        print(f"  Compressor power   : {m * r.w_comp / 1e6:10.2f} MW")
        print(f"  Turbine power      : {m * r.w_turb / 1e6:10.2f} MW")
        print(f"  Heat input         : {m * r.q_in / 1e6:10.2f} MW")
    return r


def run_exergy(r):
    from thermocycles import exergy_analysis

    print("\nEXERGY ANALYSIS")
    if r.name.startswith("Brayton"):
        default_T0 = round(r.states["1"].T - 273.15, 2)   # open gas turbine: ambient = intake air
    elif hasattr(r, "cop_cooling"):
        default_T0 = 25.0
    else:
        default_T0 = 20.0
    T0 = ask("Ambient (dead state) temperature [°C]", default_T0)
    if hasattr(r, "cop_cooling"):
        default = round(r.states["1"].T - 273.15 + 5)
        T_cold = ask("Refrigerated space temperature [°C]", float(default))
        ex = exergy_analysis(r, T0_C=T0, T_cold_C=T_cold)
    else:
        default_src = 1800.0 if r.name.startswith("Brayton") else (1200.0 if r.fluid == "Water" else 150.0)
        T_src = ask("Hot source temperature [°C] (flame, flue gas, hot water, ...)", default_src)
        ex = exergy_analysis(r, T0_C=T0, T_source_C=T_src)
    ex.summary()
    return ex


def run_refrigeration():
    from thermocycles import refrigeration_cycle

    print("\nVAPOUR-COMPRESSION CYCLE (refrigerator / air conditioner / heat pump)")
    print(f"  Refrigerant examples: {REFRIGERANTS}")
    fluid = ask("Refrigerant", "R134a", check_fluid)
    T_evap = ask("Evaporating temperature [°C]", -10.0)
    T_cond = ask("Condensing temperature [°C]", 40.0)
    superheat = ask("Superheat at compressor inlet [K]", 0.0)
    subcool = ask("Subcooling at condenser outlet [K]", 0.0)
    eta_c = ask("Compressor isentropic efficiency [0-1 or %]", 1.0, parse_efficiency)
    capacity = ask("Cooling capacity [kW]", None, optional=True)

    r = refrigeration_cycle(T_evap, T_cond, superheat, subcool, eta_c, fluid)
    r.summary()
    print(f"Volumetric capacity    : {r.volumetric_capacity / 1e3:8.0f} kJ/m³")
    if capacity is not None:
        m = r.mass_flow_for_cooling(capacity * 1e3)
        print(f"\nFor {capacity:g} kW of cooling:")
        print(f"  Refrigerant mass flow : {m * 1e3:10.2f} g/s")
        print(f"  Compressor power      : {m * r.w_comp / 1e3:10.2f} kW")
        print(f"  Heat to condenser     : {m * r.q_cond / 1e3:10.2f} kW  (heating capacity as a heat pump)")
    return r


def save_plots(r, ex=None) -> Path:
    import matplotlib.pyplot as plt

    from thermocycles import plots

    n = 3 if ex is not None else 2
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 6))
    plots.plot_Ts(r, ax=axes[0])
    plots.plot_ph(r, ax=axes[1])
    if ex is not None:
        plots.plot_exergy(ex, ax=axes[2])
    fig.tight_layout()
    RESULTS.mkdir(exist_ok=True)
    kind = r.name.split()[0].lower()
    path = RESULTS / f"{kind}_{r.fluid}_{datetime.now():%Y%m%d_%H%M%S}.png"
    fig.savefig(path, dpi=150)
    return path


def main():
    print("=" * 62)
    print(" THERMO CYCLES — interactive simulator")
    print(" Press Enter to accept the default value shown in [brackets].")
    print("=" * 62)
    while True:
        print("\nWhich cycle do you want to simulate?")
        choice = ask_choice("Choice", {"1": "Rankine cycle (steam power plant / ORC)",
                                       "2": "Refrigeration / heat pump cycle",
                                       "3": "Brayton cycle (gas turbine)"}, "1")
        runner = {"1": run_rankine, "2": run_refrigeration, "3": run_brayton}[choice]
        try:
            r = runner()
        except ValueError as e:
            print(f"\nERROR: {e}")
        else:
            ex = None
            if ask_yes_no("\nRun the exergy analysis?"):
                try:
                    ex = run_exergy(r)
                except ValueError as e:
                    print(f"\nExergy analysis not possible: {e}")
            if ask_yes_no("\nSave and show the diagrams?"):
                import matplotlib.pyplot as plt
                path = save_plots(r, ex)
                print(f"  Diagrams saved in: {path}")
                print("  Close the plot window to continue.")
                plt.show()
        if not ask_yes_no("\nRun another simulation?", default=False):
            print("Bye!")
            break


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nBye!")
