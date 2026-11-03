"""Shared building blocks: thermodynamic states, cycle components and property helpers."""

from dataclasses import dataclass, field

from CoolProp.CoolProp import PropsSI

BAR = 1e5        # Pa
KELVIN = 273.15  # °C -> K offset


@dataclass
class State:
    """Thermodynamic state of a cycle point (SI units)."""
    name: str
    p: float          # Pa
    T: float          # K
    h: float          # J/kg
    s: float          # J/(kg K)
    x: float | None   # vapour quality (None outside the two-phase region)

    def row(self) -> str:
        quality = f"{self.x:6.4f}" if self.x is not None else "   -  "
        return (f"{self.name:>3} | {self.p / BAR:9.4f} | {self.T - KELVIN:8.2f} | "
                f"{self.h / 1e3:9.2f} | {self.s / 1e3:10.4f} | {quality}")


def state_from(name: str, fluid: str, prop1: str, val1: float,
               prop2: str, val2: float) -> State:
    """Build a full state from two known properties (CoolProp syntax)."""
    def get(prop):
        return PropsSI(prop, prop1, val1, prop2, val2, fluid)

    p, T, h, s = get("P"), get("T"), get("H"), get("S")
    try:
        x = get("Q")
    except ValueError:
        x = -1.0
    # CoolProp returns -1 (or values outside [0, 1]) for single-phase states
    x = x if 0.0 <= x <= 1.0 else None
    return State(name, p, T, h, s, x)


def isentropic_process(name: str, inlet: State, p_out: float, eta: float,
                       fluid: str, expansion: bool) -> State:
    """Outlet of a compressor/pump (expansion=False) or turbine (expansion=True)
    with isentropic efficiency eta."""
    h_s = PropsSI("H", "P", p_out, "S", inlet.s, fluid)
    if expansion:
        h = inlet.h - eta * (inlet.h - h_s)
    else:
        h = inlet.h + (h_s - inlet.h) / eta
    return state_from(name, fluid, "P", p_out, "H", h)


@dataclass
class Component:
    """A cycle component, described for the exergy analysis.

    Flows are (state, mass fraction) pairs, with mass fractions referred to the
    cycle's reference mass flow (1 kg through the boiler / evaporator / compressor).
    heat is the heat entering the fluid in J per kg of reference flow (negative if
    it leaves). reservoir says where that heat comes from or goes to:
    "source" (hot source), "sink" (ambient) or "cold" (refrigerated space)."""
    name: str
    inlets: list[tuple[State, float]]
    outlets: list[tuple[State, float]]
    heat: float = 0.0
    reservoir: str | None = None

    @property
    def fluid_temperatures(self) -> list[float]:
        return [st.T for st, _ in self.inlets + self.outlets]

    @property
    def entropy_change(self) -> float:
        """Entropy carried out minus entropy carried in by the flows [J/(K kg)]."""
        return (sum(m * st.s for st, m in self.outlets)
                - sum(m * st.s for st, m in self.inlets))


@dataclass
class CycleResults:
    """Common part of all cycle results."""
    states: dict[str, State]
    fluid: str
    paths: list[tuple[str, str, str]] = field(default_factory=list)
    components: list[Component] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    name = "Cycle"
    show_dome = True

    @property
    def headline(self) -> str:
        return ""

    def _print_states(self) -> None:
        print(f"\n{self.name} — fluid: {self.fluid}")
        print("  # |   p [bar] |   T [°C] | h [kJ/kg] | s [kJ/kgK] |   x")
        print("-" * 62)
        for st in self.states.values():
            print(st.row())
        print("-" * 62)

    def _print_warnings(self) -> None:
        for w in self.warnings:
            print(f"WARNING: {w}")

    def state_table(self) -> list[dict]:
        """States as a list of rows in practical units (for tables and CSV export)."""
        return [{"State": st.name, "p [bar]": st.p / BAR, "T [°C]": st.T - KELVIN,
                 "h [kJ/kg]": st.h / 1e3, "s [kJ/(kg·K)]": st.s / 1e3,
                 "x [-]": st.x} for st in self.states.values()]


# --- Property helpers --------------------------------------------------------

def saturation_pressure_bar(fluid: str, T_C: float) -> float:
    """Saturation pressure [bar] of a fluid at temperature T_C [°C]."""
    return PropsSI("P", "T", T_C + KELVIN, "Q", 0, fluid) / BAR


def saturation_temperature_C(fluid: str, p_bar: float) -> float:
    """Saturation temperature [°C] of a fluid at pressure p_bar [bar]."""
    return PropsSI("T", "P", p_bar * BAR, "Q", 0, fluid) - KELVIN


def critical_point(fluid: str) -> tuple[float, float]:
    """Critical temperature [°C] and pressure [bar] of a fluid."""
    return PropsSI("Tcrit", fluid) - KELVIN, PropsSI("pcrit", fluid) / BAR
