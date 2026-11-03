"""
Rankine cycle: simple, with reheat, with regeneration (open feedwater heater), or both.

Simple cycle states:
    1 - condenser outlet  (saturated liquid, p_low)
    2 - pump outlet       (compressed liquid, p_high)
    3 - boiler outlet     (saturated or superheated vapour, p_high)
    4 - turbine outlet    (wet mixture or vapour, p_low)

With reheat and/or an open feedwater heater the states are numbered in flow order,
starting from the condenser outlet (see rankine_reheat_regen_cycle).

Fluid properties come from CoolProp (real-fluid equations of state, not tables).
Inputs use "engineering" units (bar, °C); everything is SI internally.
"""

from dataclasses import dataclass

from CoolProp.CoolProp import PropsSI

from .core import (BAR, KELVIN, Component, CycleResults, State,  # noqa: F401 (re-exported)
                   isentropic_process, state_from)


@dataclass
class RankineResults(CycleResults):
    w_turbine: float = 0.0          # J/kg of steam through the boiler
    w_pump: float = 0.0             # J/kg
    q_in: float = 0.0               # J/kg (boiler + reheater)
    q_out: float = 0.0              # J/kg (condenser)
    extraction_fraction: float = 0.0  # y: fraction of steam bled to the feedwater heater

    name = "Rankine cycle"

    @property
    def w_net(self) -> float:
        return self.w_turbine - self.w_pump

    @property
    def efficiency(self) -> float:
        return self.w_net / self.q_in

    @property
    def bwr(self) -> float:
        """Back Work Ratio: fraction of the turbine work used by the pumps."""
        return self.w_pump / self.w_turbine

    @property
    def headline(self) -> str:
        return f"η = {self.efficiency * 100:.1f} %"

    def mass_flow_for_power(self, power_W: float) -> float:
        """Steam mass flow through the boiler [kg/s] for a given net power output [W]."""
        return power_W / self.w_net

    def summary(self) -> None:
        self._print_states()
        if self.extraction_fraction:
            print(f"Extraction fraction y : {self.extraction_fraction:8.4f}")
        print(f"Turbine work      : {self.w_turbine / 1e3:8.2f} kJ/kg")
        print(f"Pump work         : {self.w_pump / 1e3:8.2f} kJ/kg")
        print(f"Net work          : {self.w_net / 1e3:8.2f} kJ/kg")
        print(f"Heat input        : {self.q_in / 1e3:8.2f} kJ/kg")
        print(f"Heat rejected     : {self.q_out / 1e3:8.2f} kJ/kg")
        print(f"Thermal efficiency: {self.efficiency * 100:8.2f} %")
        print(f"Back Work Ratio   : {self.bwr * 100:8.2f} %")
        self._print_warnings()


def rankine_cycle(p_high_bar: float, p_low_bar: float, T_max_C: float | None = None,
                  eta_turbine: float = 1.0, eta_pump: float = 1.0,
                  fluid: str = "Water") -> RankineResults:
    """
    Solve a simple Rankine cycle.

    p_high_bar  : boiler pressure [bar]
    p_low_bar   : condenser pressure [bar]
    T_max_C     : turbine inlet temperature [°C]; None = saturated vapour
    eta_turbine : turbine isentropic efficiency (1 = ideal)
    eta_pump    : pump isentropic efficiency (1 = ideal)
    fluid       : CoolProp fluid name ("Water", "R245fa", "Toluene", ...)
    """
    return rankine_reheat_regen_cycle(p_high_bar, p_low_bar, T_max_C,
                                      eta_turbine=eta_turbine, eta_pump=eta_pump, fluid=fluid)


def _superheated(name, fluid, p, T_C, label):
    T_sat = PropsSI("T", "P", p, "Q", 1, fluid)
    if T_C + KELVIN <= T_sat:
        raise ValueError(
            f"{label} ({T_C:.1f} °C) is not above the saturation temperature "
            f"at {p / BAR:g} bar ({T_sat - KELVIN:.1f} °C): no superheating possible.")
    return state_from(name, fluid, "P", p, "T", T_C + KELVIN)


def rankine_reheat_regen_cycle(p_high_bar: float, p_low_bar: float,
                               T_max_C: float | None = None,
                               p_reheat_bar: float | None = None,
                               T_reheat_C: float | None = None,
                               p_fwh_bar: float | None = None,
                               eta_turbine: float = 1.0, eta_pump: float = 1.0,
                               fluid: str = "Water") -> RankineResults:
    """
    Solve a Rankine cycle with optional reheat and an optional open feedwater heater.

    p_high_bar   : boiler pressure [bar]
    p_low_bar    : condenser pressure [bar]
    T_max_C      : turbine inlet temperature [°C]; None = saturated vapour
    p_reheat_bar : reheat pressure [bar]; None = no reheat
    T_reheat_C   : temperature after reheat [°C]; None = same as T_max_C
    p_fwh_bar    : pressure of the open feedwater heater (steam extraction) [bar];
                   None = no regeneration
    eta_turbine  : isentropic efficiency of every turbine section (1 = ideal)
    eta_pump     : isentropic efficiency of every pump (1 = ideal)
    fluid        : CoolProp fluid name

    The feedwater heater outlet is saturated liquid at p_fwh_bar. If the extraction
    pressure equals the reheat pressure, steam is bled before the reheater.
    All specific quantities are per kg of steam through the boiler.
    """
    if p_low_bar <= 0 or p_high_bar <= 0:
        raise ValueError("Pressures must be positive.")
    if p_low_bar >= p_high_bar:
        raise ValueError("Boiler pressure must be higher than condenser pressure.")
    if not (0 < eta_turbine <= 1 and 0 < eta_pump <= 1):
        raise ValueError("Isentropic efficiencies must be between 0 and 1.")
    for label, p in (("Reheat pressure", p_reheat_bar), ("Feedwater heater pressure", p_fwh_bar)):
        if p is not None and not p_low_bar < p < p_high_bar:
            raise ValueError(f"{label} must be between the condenser and the boiler pressure.")
    if p_reheat_bar is not None and T_reheat_C is None:
        if T_max_C is None:
            raise ValueError("With reheat, give the reheat temperature (T_reheat_C).")
        T_reheat_C = T_max_C

    p_crit = PropsSI("pcrit", fluid)
    if p_high_bar * BAR >= p_crit:
        raise ValueError(f"Boiler pressure ({p_high_bar:g} bar) is not below the critical pressure of "
                         f"{fluid} ({p_crit / BAR:.1f} bar): supercritical cycles are not supported.")

    p_high, p_low = p_high_bar * BAR, p_low_bar * BAR
    p_rh = p_reheat_bar * BAR if p_reheat_bar is not None else None
    p_fwh = p_fwh_bar * BAR if p_fwh_bar is not None else None

    states: dict[str, State] = {}

    def add(st: State) -> State:
        st.name = str(len(states) + 1)
        states[st.name] = st
        return st

    def pump(inlet, p_out):
        return add(isentropic_process("", inlet, p_out, eta_pump, fluid, expansion=False))

    def expand(inlet, p_out):
        return add(isentropic_process("", inlet, p_out, eta_turbine, fluid, expansion=True))

    paths: list[tuple[str, str, str]] = []

    # Feedwater line
    s_cond = add(state_from("", fluid, "P", p_low, "Q", 0))
    if p_fwh is not None:
        s_p1 = pump(s_cond, p_fwh)
        s_fwh = add(state_from("", fluid, "P", p_fwh, "Q", 0))
        s_p2 = pump(s_fwh, p_high)
        paths += [(s_cond.name, s_p1.name, "line"), (s_p1.name, s_fwh.name, "isobar"),
                  (s_fwh.name, s_p2.name, "line")]
    else:
        s_p1 = s_fwh = None
        s_p2 = pump(s_cond, p_high)
        paths.append((s_cond.name, s_p2.name, "line"))

    # Boiler
    if T_max_C is None:
        s_boil = add(state_from("", fluid, "P", p_high, "Q", 1))
    else:
        s_boil = add(_superheated("", fluid, p_high, T_max_C, "T_max"))
    paths.append((s_p2.name, s_boil.name, "isobar"))

    # Turbine expansion, stopping at reheat / extraction pressures
    stops = sorted({p for p in (p_rh, p_fwh) if p is not None} | {p_low}, reverse=True)
    sections = []                 # (inlet, outlet)
    s_ext = s_hp_out = s_rh = None
    current = s_boil
    for p in stops:
        out = expand(current, p)
        sections.append((current, out))
        paths.append((current.name, out.name, "line"))
        if p_fwh is not None and p == p_fwh:
            s_ext = out
        if p_rh is not None and p == p_rh:
            s_hp_out = out
            s_rh = add(_superheated("", fluid, p_rh, T_reheat_C, "T_reheat"))
            paths.append((out.name, s_rh.name, "isobar"))
            current = s_rh
        else:
            current = out
    s_exh = current
    paths.append((s_exh.name, s_cond.name, "isobar"))
    if s_ext is not None:
        paths.append((s_ext.name, s_fwh.name, "isobar"))

    # Mass balance of the open feedwater heater
    y = 0.0
    if p_fwh is not None:
        y = (s_fwh.h - s_p1.h) / (s_ext.h - s_p1.h)
        if not 0 < y < 1:
            raise ValueError("Feedwater heater balance not possible with these inputs "
                             f"(extraction fraction y = {y:.3f}).")

    def section_flow(out: State) -> float:
        return 1.0 if p_fwh is None or out.p >= p_fwh * (1 - 1e-9) else 1 - y

    m_rh = 1.0 if p_fwh is None or (p_rh is not None and p_rh > p_fwh) else 1 - y

    w_turbine = sum(section_flow(o) * (i.h - o.h) for i, o in sections)
    if p_fwh is not None:
        w_pump = (1 - y) * (s_p1.h - s_cond.h) + (s_p2.h - s_fwh.h)
    else:
        w_pump = s_p2.h - s_cond.h
    q_boiler = s_boil.h - s_p2.h
    q_reheat = m_rh * (s_rh.h - s_hp_out.h) if s_rh is not None else 0.0
    q_in = q_boiler + q_reheat
    q_out = (1 - y) * (s_exh.h - s_cond.h)

    # Components (for the exergy analysis)
    comps = []
    if p_fwh is not None:
        comps += [Component("Pump 1", [(s_cond, 1 - y)], [(s_p1, 1 - y)]),
                  Component("Feedwater heater", [(s_p1, 1 - y), (s_ext, y)], [(s_fwh, 1.0)]),
                  Component("Pump 2", [(s_fwh, 1.0)], [(s_p2, 1.0)])]
    else:
        comps.append(Component("Pump", [(s_cond, 1.0)], [(s_p2, 1.0)]))
    comps.append(Component("Boiler", [(s_p2, 1.0)], [(s_boil, 1.0)], q_boiler, "source"))
    for k, (i, o) in enumerate(sections):
        label = "Turbine" if len(sections) == 1 else f"Turbine {i.p / BAR:g}→{o.p / BAR:g} bar"
        m = section_flow(o)
        comps.append(Component(label, [(i, m)], [(o, m)]))
        if s_rh is not None and o is s_hp_out:
            comps.append(Component("Reheater", [(s_hp_out, m_rh)], [(s_rh, m_rh)], q_reheat, "source"))
    comps.append(Component("Condenser", [(s_exh, 1 - y)], [(s_cond, 1 - y)], -q_out, "sink"))

    warnings = []
    for i, o in sections:
        if o.x is not None and o.x < 0.88:
            warnings.append(f"low vapour quality at turbine outlet, state {o.name} (x = {o.x:.3f}): "
                            "risk of blade erosion (in practice x > 0.88-0.90 is required).")
    if s_exh.x is None and s_exh.T > s_cond.T + 5:
        warnings.append(f"turbine exhaust is superheated ({s_exh.T - KELVIN:.1f} °C, "
                        f"condensing at {s_cond.T - KELVIN:.1f} °C): the condenser must first "
                        "desuperheat the vapour; with 'dry' organic fluids (ORC) a recuperator "
                        "is normally used to recover this heat.")

    return RankineResults(states=states, fluid=fluid, paths=paths, components=comps,
                          warnings=warnings, w_turbine=w_turbine, w_pump=w_pump,
                          q_in=q_in, q_out=q_out, extraction_fraction=y)
