"""
Rankine cycle: simple, with reheat, with any number of open and closed feedwater
heaters (multiple extractions), or all of these.

Simple cycle states:
    1 - condenser outlet  (saturated liquid, p_low)
    2 - pump outlet       (compressed liquid, p_high)
    3 - boiler outlet     (saturated or superheated vapour, p_high)
    4 - turbine outlet    (wet mixture or vapour, p_low)

With reheat and/or feedwater heaters the states are numbered in this order:
feedwater line (from the condenser outlet up to the boiler inlet), boiler outlet,
turbine expansion (extractions and reheat in order), then the drains of the
closed heaters. results.exhaust names the turbine exhaust state.

Feedwater heaters:
  - open (deaerator type): extracted steam mixes with the feedwater; the outlet is
    saturated liquid at the heater pressure and a pump follows it.
  - closed (shell-and-tube): the feedwater is heated without mixing. It leaves at
    T_sat(heater pressure) − TTD (terminal temperature difference). The condensed
    steam (drain) leaves as saturated liquid and is throttled backward into the
    next lower-pressure heater, or into the condenser.

Fluid properties come from CoolProp (real-fluid equations of state, not tables).
Inputs use "engineering" units (bar, °C); everything is SI internally.
"""

from dataclasses import dataclass, field

from CoolProp.CoolProp import PropsSI

from .core import (BAR, KELVIN, Component, CycleResults, State,  # noqa: F401 (re-exported)
                   isentropic_process, state_from)


@dataclass
class FeedwaterHeater:
    """A feedwater heater fed by a turbine extraction.

    p_bar : extraction (heater shell) pressure [bar]
    kind  : "open" or "closed"
    ttd_K : terminal temperature difference of a closed heater [K]:
            feedwater outlet = T_sat(p_bar) − ttd_K (ignored for open heaters)
    """
    p_bar: float
    kind: str = "open"
    ttd_K: float = 0.0

    def __post_init__(self):
        if self.kind not in ("open", "closed"):
            raise ValueError("A feedwater heater must be 'open' or 'closed'.")
        if self.ttd_K < 0:
            raise ValueError("The terminal temperature difference cannot be negative.")


@dataclass
class RankineResults(CycleResults):
    w_turbine: float = 0.0            # J/kg of steam through the boiler
    w_pump: float = 0.0               # J/kg
    q_in: float = 0.0                 # J/kg (boiler + reheater)
    q_out: float = 0.0                # J/kg (condenser)
    extraction_fraction: float = 0.0  # total fraction of steam bled to the heaters
    extractions: dict[float, float] = field(default_factory=dict)  # {pressure [bar]: fraction}
    exhaust: str = "4"                # name of the turbine exhaust state

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

    @property
    def exhaust_state(self) -> State:
        return self.states[self.exhaust]

    def mass_flow_for_power(self, power_W: float) -> float:
        """Steam mass flow through the boiler [kg/s] for a given net power output [W]."""
        return power_W / self.w_net

    def summary(self) -> None:
        self._print_states()
        for p, y in self.extractions.items():
            print(f"Extraction at {p:g} bar : y = {y:.4f}")
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


def _as_heater(h) -> FeedwaterHeater:
    if isinstance(h, FeedwaterHeater):
        return h
    if isinstance(h, (int, float)):
        return FeedwaterHeater(float(h))
    if isinstance(h, dict):
        return FeedwaterHeater(**h)
    return FeedwaterHeater(*h)


def rankine_reheat_regen_cycle(p_high_bar: float, p_low_bar: float,
                               T_max_C: float | None = None,
                               p_reheat_bar: float | None = None,
                               T_reheat_C: float | None = None,
                               p_fwh_bar: float | None = None,
                               eta_turbine: float = 1.0, eta_pump: float = 1.0,
                               fluid: str = "Water",
                               heaters: list | None = None) -> RankineResults:
    """
    Solve a Rankine cycle with optional reheat and feedwater heaters.

    p_high_bar   : boiler pressure [bar]
    p_low_bar    : condenser pressure [bar]
    T_max_C      : turbine inlet temperature [°C]; None = saturated vapour
    p_reheat_bar : reheat pressure [bar]; None = no reheat
    T_reheat_C   : temperature after reheat [°C]; None = same as T_max_C
    p_fwh_bar    : shortcut for ONE open feedwater heater at this pressure [bar]
    eta_turbine  : isentropic efficiency of every turbine section (1 = ideal)
    eta_pump     : isentropic efficiency of every pump (1 = ideal)
    fluid        : CoolProp fluid name
    heaters      : list of feedwater heaters, each a FeedwaterHeater(p_bar, kind, ttd_K),
                   a (p_bar, kind, ttd_K) tuple, a dict, or just a pressure (= open heater).
                   Any number and order; pressures must be different.

    If an extraction pressure equals the reheat pressure, steam is bled before the
    reheater. All specific quantities are per kg of steam through the boiler.
    """
    if p_low_bar <= 0 or p_high_bar <= 0:
        raise ValueError("Pressures must be positive.")
    if p_low_bar >= p_high_bar:
        raise ValueError("Boiler pressure must be higher than condenser pressure.")
    if not (0 < eta_turbine <= 1 and 0 < eta_pump <= 1):
        raise ValueError("Isentropic efficiencies must be between 0 and 1.")

    heater_list = [_as_heater(h) for h in (heaters or [])]
    if p_fwh_bar is not None:
        heater_list.append(FeedwaterHeater(p_fwh_bar, "open"))
    pressures = [h.p_bar for h in heater_list]
    if len(set(pressures)) != len(pressures):
        raise ValueError("Two feedwater heaters cannot have the same extraction pressure.")
    for label, p in [("Reheat pressure", p_reheat_bar)] + \
                    [("Feedwater heater pressure", h.p_bar) for h in heater_list]:
        if p is not None and not p_low_bar < p < p_high_bar:
            raise ValueError(f"{label} ({p:g} bar) must be between the condenser and the boiler pressure.")
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
    asc = sorted(heater_list, key=lambda h: h.p_bar)          # feedwater flow order

    states: dict[str, State] = {}

    def add(st: State) -> State:
        st.name = str(len(states) + 1)
        states[st.name] = st
        return st

    def pump(inlet, p_out):
        return add(isentropic_process("", inlet, p_out, eta_pump, fluid, expansion=False))

    def expand(inlet, p_out):
        return add(isentropic_process("", inlet, p_out, eta_turbine, fluid, expansion=True))

    def segment_pressure(i):
        """Feedwater pressure after heater index i-1: next open heater above, or the boiler."""
        for h in asc[i:]:
            if h.kind == "open":
                return h.p_bar * BAR
        return p_high

    paths: list[tuple[str, str, str]] = []

    # --- Feedwater line (condenser → boiler) ---------------------------------
    s_cond = add(state_from("", fluid, "P", p_low, "Q", 0))
    pumps = []                       # (inlet, outlet, key of the flow through it)
    fw = {}                          # heater index -> (feedwater inlet, feedwater outlet)
    s = pump(s_cond, segment_pressure(0))
    pumps.append((s_cond, s, "bottom"))
    paths.append((s_cond.name, s.name, "line"))
    for i, h in enumerate(asc):
        if h.kind == "closed":
            T_out = PropsSI("T", "P", h.p_bar * BAR, "Q", 0, fluid) - h.ttd_K
            if T_out <= s.T + 1e-6:
                raise ValueError(f"Closed heater at {h.p_bar:g} bar cannot heat the feedwater: its outlet "
                                 f"({T_out - KELVIN:.1f} °C) would not be hotter than its inlet "
                                 f"({s.T - KELVIN:.1f} °C). Reduce the TTD or raise the pressure.")
            if T_out >= PropsSI("T", "P", s.p, "Q", 0, fluid):
                raise ValueError(f"Closed heater at {h.p_bar:g} bar would boil the feedwater at "
                                 f"{s.p / BAR:g} bar: place an open heater or a pump before it.")
            out = add(state_from("", fluid, "P", s.p, "T", T_out))
            fw[i] = (s, out)
            paths.append((s.name, out.name, "isobar"))
            s = out
        else:
            out = add(state_from("", fluid, "P", h.p_bar * BAR, "Q", 0))
            fw[i] = (s, out)
            paths.append((s.name, out.name, "isobar"))
            s = pump(out, segment_pressure(i + 1))
            pumps.append((out, s, i))
            paths.append((out.name, s.name, "line"))
    s_fw = s                          # boiler inlet

    # --- Boiler -----------------------------------------------------------------
    if T_max_C is None:
        s_boil = add(state_from("", fluid, "P", p_high, "Q", 1))
    else:
        s_boil = add(_superheated("", fluid, p_high, T_max_C, "T_max"))
    paths.append((s_fw.name, s_boil.name, "isobar"))

    # --- Turbine expansion, stopping at reheat / extraction pressures ------------
    stops = sorted({h.p_bar * BAR for h in asc} | ({p_rh} if p_rh else set()) | {p_low}, reverse=True)
    sections = []                     # (inlet, outlet)
    ext = {}                          # extraction pressure [Pa] -> extracted state
    s_hp_out = s_rh = None
    current = s_boil
    for p in stops:
        out = expand(current, p)
        sections.append((current, out))
        paths.append((current.name, out.name, "line"))
        if p != p_low:
            ext[p] = out
        if p_rh is not None and p == p_rh:
            s_hp_out = out
            s_rh = add(_superheated("", fluid, p_rh, T_reheat_C, "T_reheat"))
            paths.append((out.name, s_rh.name, "isobar"))
            current = s_rh
        else:
            current = out
    s_exh = current
    paths.append((s_exh.name, s_cond.name, "isobar"))

    # --- Heater mass and energy balances, from the highest pressure down --------
    y = {}                            # heater index -> extraction fraction
    drain_state = {}                  # closed heater index -> drain state
    drain_in = {}                     # heater index -> (flow, state) of drains arriving
    seg_flow = {}                     # key -> feedwater flow (open heater outlet / bottom)
    fw_flow = {}                      # heater index -> (feedwater flow in, feedwater flow out)
    m_seg = 1.0                       # feedwater flow in the current segment
    d_flow, d_state = 0.0, None       # drains cascading down
    for i in reversed(range(len(asc))):
        h = asc[i]
        s_ext = ext[h.p_bar * BAR]
        fw_in, fw_out = fw[i]
        drain_in[i] = (d_flow, d_state)
        if h.kind == "closed":
            s_dr = add(state_from("", fluid, "P", h.p_bar * BAR, "Q", 0))
            drain_state[i] = s_dr
            heat_from_drains = d_flow * (d_state.h - s_dr.h) if d_flow else 0.0
            yi = (m_seg * (fw_out.h - fw_in.h) - heat_from_drains) / (s_ext.h - s_dr.h)
            fw_flow[i] = (m_seg, m_seg)
            paths.append((s_ext.name, s_dr.name, "isobar"))
            d_flow, d_state = d_flow + yi, s_dr
        else:
            seg_flow[i] = m_seg
            drains_term = d_flow * (d_state.h - fw_in.h) if d_flow else 0.0
            yi = (m_seg * (fw_out.h - fw_in.h) - drains_term) / (s_ext.h - fw_in.h)
            paths.append((s_ext.name, fw_out.name, "isobar"))
            fw_flow[i] = (m_seg - yi - d_flow, m_seg)
            m_seg = m_seg - yi - d_flow
            d_flow, d_state = 0.0, None
        if not 0 < yi < 1 or m_seg <= 0:
            raise ValueError(f"Heat balance of the feedwater heater at {h.p_bar:g} bar is not possible "
                             f"with these inputs (extraction fraction {yi:.3f}).")
        y[i] = yi
    seg_flow["bottom"] = m_seg
    drains_to_condenser = (d_flow, d_state)

    # Drain throttling lines (to the next lower-pressure heater, or the condenser)
    for i, s_dr in drain_state.items():
        target = (drain_state.get(i - 1) or fw[i - 1][1]) if i > 0 else s_cond
        paths.append((s_dr.name, target.name, "throttle"))

    y_total = sum(y.values())
    p_of = {i: asc[i].p_bar * BAR for i in y}

    def section_flow(inlet: State) -> float:
        """Steam flow in a turbine section = 1 − extractions taken at or above its inlet."""
        return 1.0 - sum(y[i] for i in y if p_of[i] >= inlet.p * (1 - 1e-9))

    m_rh = 1.0 - sum(y[i] for i in y if p_rh is not None and p_of[i] >= p_rh * (1 - 1e-9))
    m_exh = 1.0 - y_total

    w_turbine = sum(section_flow(i) * (i.h - o.h) for i, o in sections)
    w_pump = sum(seg_flow[k] * (o.h - i.h) for i, o, k in pumps)
    q_boiler = s_boil.h - s_fw.h
    q_reheat = m_rh * (s_rh.h - s_hp_out.h) if s_rh is not None else 0.0
    q_in = q_boiler + q_reheat
    d_c, d_c_state = drains_to_condenser
    q_out = m_exh * s_exh.h + (d_c * d_c_state.h if d_c else 0.0) - seg_flow["bottom"] * s_cond.h

    # --- Components (for the exergy analysis) -------------------------------------
    comps = []
    multi = len(pumps) > 1
    for k, (i_st, o_st, key) in enumerate(pumps):
        name = f"Pump {k + 1}" if multi else "Pump"
        comps.append(Component(name, [(i_st, seg_flow[key])], [(o_st, seg_flow[key])]))
    for i, h in enumerate(asc):
        fw_in, fw_out = fw[i]
        dflow, dstate = drain_in[i]
        extra = [(dstate, dflow)] if dflow else []
        label = f"{h.kind.capitalize()} heater {h.p_bar:g} bar"
        s_ext = ext[h.p_bar * BAR]
        m_in, m_out = fw_flow[i]
        if h.kind == "closed":
            comps.append(Component(label, [(fw_in, m_in), (s_ext, y[i])] + extra,
                                   [(fw_out, m_out), (drain_state[i], y[i] + dflow)]))
        else:
            comps.append(Component(label, [(fw_in, m_in), (s_ext, y[i])] + extra, [(fw_out, m_out)]))
    comps.append(Component("Boiler", [(s_fw, 1.0)], [(s_boil, 1.0)], q_boiler, "source"))
    for i_st, o_st in sections:
        label = "Turbine" if len(sections) == 1 else f"Turbine {i_st.p / BAR:g}→{o_st.p / BAR:g} bar"
        m = section_flow(i_st)
        comps.append(Component(label, [(i_st, m)], [(o_st, m)]))
        if s_rh is not None and o_st is s_hp_out:
            comps.append(Component("Reheater", [(s_hp_out, m_rh)], [(s_rh, m_rh)], q_reheat, "source"))
    cond_in = [(s_exh, m_exh)] + ([(d_c_state, d_c)] if d_c else [])
    comps.append(Component("Condenser", cond_in, [(s_cond, seg_flow["bottom"])], -q_out, "sink"))

    warnings = []
    for i_st, o_st in sections:
        if o_st.x is not None and o_st.x < 0.88:
            warnings.append(f"low vapour quality at turbine outlet, state {o_st.name} (x = {o_st.x:.3f}): "
                            "risk of blade erosion (in practice x > 0.88-0.90 is required).")
    if s_exh.x is None and s_exh.T > s_cond.T + 5:
        warnings.append(f"turbine exhaust is superheated ({s_exh.T - KELVIN:.1f} °C, "
                        f"condensing at {s_cond.T - KELVIN:.1f} °C): the condenser must first "
                        "desuperheat the vapour; with 'dry' organic fluids (ORC) a recuperator "
                        "is normally used to recover this heat.")

    return RankineResults(states=states, fluid=fluid, paths=paths, components=comps,
                          warnings=warnings, w_turbine=w_turbine, w_pump=w_pump,
                          q_in=q_in, q_out=q_out, extraction_fraction=y_total,
                          extractions={asc[i].p_bar: y[i] for i in sorted(y, key=lambda j: -p_of[j])},
                          exhaust=s_exh.name)
