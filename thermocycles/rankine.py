"""
Simple Rankine cycle (saturated or superheated steam).

Cycle states:
    1 - condenser outlet  (saturated liquid, p_low)
    2 - pump outlet       (compressed liquid, p_high)
    3 - boiler outlet     (saturated or superheated vapour, p_high)
    4 - turbine outlet    (wet mixture or vapour, p_low)

Fluid properties come from CoolProp (real-fluid equations of state, not tables).
Inputs use "engineering" units (bar, °C); everything is SI internally.
"""

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
    x = get("Q")
    # CoolProp returns -1 (or values outside [0, 1]) for single-phase states
    x = x if 0.0 <= x <= 1.0 else None
    return State(name, p, T, h, s, x)


@dataclass
class RankineResults:
    states: dict[str, State]
    fluid: str
    w_turbine: float   # J/kg
    w_pump: float      # J/kg
    q_in: float        # J/kg
    q_out: float       # J/kg
    warnings: list[str] = field(default_factory=list)

    @property
    def w_net(self) -> float:
        return self.w_turbine - self.w_pump

    @property
    def efficiency(self) -> float:
        return self.w_net / self.q_in

    @property
    def bwr(self) -> float:
        """Back Work Ratio: fraction of the turbine work used by the pump."""
        return self.w_pump / self.w_turbine

    def mass_flow_for_power(self, power_W: float) -> float:
        """Mass flow rate [kg/s] required for a given net power output [W]."""
        return power_W / self.w_net

    def summary(self) -> None:
        print(f"\nRankine cycle — fluid: {self.fluid}")
        print("  # |   p [bar] |   T [°C] | h [kJ/kg] | s [kJ/kgK] |   x")
        print("-" * 62)
        for st in self.states.values():
            print(st.row())
        print("-" * 62)
        print(f"Turbine work      : {self.w_turbine / 1e3:8.2f} kJ/kg")
        print(f"Pump work         : {self.w_pump / 1e3:8.2f} kJ/kg")
        print(f"Net work          : {self.w_net / 1e3:8.2f} kJ/kg")
        print(f"Heat input        : {self.q_in / 1e3:8.2f} kJ/kg")
        print(f"Heat rejected     : {self.q_out / 1e3:8.2f} kJ/kg")
        print(f"Thermal efficiency: {self.efficiency * 100:8.2f} %")
        print(f"Back Work Ratio   : {self.bwr * 100:8.2f} %")
        for w in self.warnings:
            print(f"WARNING: {w}")


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
    if p_low_bar >= p_high_bar:
        raise ValueError("Boiler pressure must be higher than condenser pressure.")
    if not (0 < eta_turbine <= 1 and 0 < eta_pump <= 1):
        raise ValueError("Isentropic efficiencies must be between 0 and 1.")

    p_high, p_low = p_high_bar * BAR, p_low_bar * BAR
    warnings = []

    # 1: saturated liquid at the condenser outlet
    s1 = state_from("1", fluid, "P", p_low, "Q", 0)

    # 2: pump (ideal isentropic compression, then corrected with the efficiency)
    h2s = PropsSI("H", "P", p_high, "S", s1.s, fluid)
    h2 = s1.h + (h2s - s1.h) / eta_pump
    s2 = state_from("2", fluid, "P", p_high, "H", h2)

    # 3: boiler outlet
    if T_max_C is None:
        s3 = state_from("3", fluid, "P", p_high, "Q", 1)
    else:
        T_sat = PropsSI("T", "P", p_high, "Q", 1, fluid)
        if T_max_C + KELVIN <= T_sat:
            raise ValueError(
                f"T_max ({T_max_C:.1f} °C) is not above the saturation temperature "
                f"at {p_high_bar} bar ({T_sat - KELVIN:.1f} °C): no superheating possible.")
        s3 = state_from("3", fluid, "P", p_high, "T", T_max_C + KELVIN)

    # 4: turbine expansion
    h4s = PropsSI("H", "P", p_low, "S", s3.s, fluid)
    h4 = s3.h - eta_turbine * (s3.h - h4s)
    s4 = state_from("4", fluid, "P", p_low, "H", h4)

    if s4.x is not None and s4.x < 0.88:
        warnings.append(f"low vapour quality at turbine exhaust (x4 = {s4.x:.3f}): "
                        "risk of blade erosion (in practice x > 0.88-0.90 is required).")

    return RankineResults(
        states={"1": s1, "2": s2, "3": s3, "4": s4},
        fluid=fluid,
        w_turbine=s3.h - s4.h,
        w_pump=s2.h - s1.h,
        q_in=s3.h - s2.h,
        q_out=s4.h - s1.h,
        warnings=warnings,
    )
