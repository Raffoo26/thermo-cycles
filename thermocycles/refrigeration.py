"""
Vapour-compression refrigeration / heat pump cycle.

Cycle states:
    1 - compressor inlet    (saturated or superheated vapour, p_evap)
    2 - compressor outlet   (superheated vapour, p_cond)
    3 - condenser outlet    (saturated or subcooled liquid, p_cond)
    4 - evaporator inlet    (two-phase mixture after throttling, p_evap; h4 = h3)

The same cycle works as a refrigerator (useful effect: heat absorbed in the
evaporator) or as a heat pump (useful effect: heat released in the condenser).
Inputs use evaporating/condensing temperatures in °C, as in practice.
"""

from dataclasses import dataclass, field

from CoolProp.CoolProp import PropsSI

from .rankine import BAR, KELVIN, State, state_from


@dataclass
class RefrigerationResults:
    states: dict[str, State]
    fluid: str
    w_comp: float      # J/kg, compressor work
    q_evap: float      # J/kg, heat absorbed in the evaporator (refrigerating effect)
    q_cond: float      # J/kg, heat released in the condenser
    warnings: list[str] = field(default_factory=list)

    @property
    def cop_cooling(self) -> float:
        """COP as a refrigerator / air conditioner."""
        return self.q_evap / self.w_comp

    @property
    def cop_heating(self) -> float:
        """COP as a heat pump."""
        return self.q_cond / self.w_comp

    @property
    def cop_carnot_cooling(self) -> float:
        """Reverse Carnot COP between evaporating and condensing temperatures."""
        T_e = PropsSI("T", "P", self.states["1"].p, "Q", 1, self.fluid)
        T_c = PropsSI("T", "P", self.states["3"].p, "Q", 0, self.fluid)
        return T_e / (T_c - T_e)

    @property
    def pressure_ratio(self) -> float:
        return self.states["2"].p / self.states["1"].p

    @property
    def discharge_temperature_C(self) -> float:
        return self.states["2"].T - KELVIN

    @property
    def volumetric_capacity(self) -> float:
        """Volumetric cooling capacity [J/m³]: cooling per m³ of vapour drawn in by the
        compressor. Higher value = smaller compressor for the same capacity."""
        rho1 = PropsSI("D", "P", self.states["1"].p, "H", self.states["1"].h, self.fluid)
        return self.q_evap * rho1

    def mass_flow_for_cooling(self, capacity_W: float) -> float:
        """Refrigerant mass flow [kg/s] for a given cooling capacity [W]."""
        return capacity_W / self.q_evap

    def summary(self) -> None:
        print(f"\nVapour-compression cycle — fluid: {self.fluid}")
        print("  # |   p [bar] |   T [°C] | h [kJ/kg] | s [kJ/kgK] |   x")
        print("-" * 62)
        for st in self.states.values():
            print(st.row())
        print("-" * 62)
        print(f"Compressor work        : {self.w_comp / 1e3:8.2f} kJ/kg")
        print(f"Refrigerating effect   : {self.q_evap / 1e3:8.2f} kJ/kg")
        print(f"Heat to condenser      : {self.q_cond / 1e3:8.2f} kJ/kg")
        print(f"COP cooling            : {self.cop_cooling:8.2f}")
        print(f"COP heating            : {self.cop_heating:8.2f}")
        print(f"COP Carnot (cooling)   : {self.cop_carnot_cooling:8.2f}")
        print(f"Second-law efficiency  : {self.cop_cooling / self.cop_carnot_cooling * 100:8.1f} %")
        print(f"Pressure ratio         : {self.pressure_ratio:8.2f}")
        print(f"Discharge temperature  : {self.discharge_temperature_C:8.1f} °C")
        for w in self.warnings:
            print(f"WARNING: {w}")


def refrigeration_cycle(T_evap_C: float, T_cond_C: float, superheat_K: float = 0.0,
                        subcooling_K: float = 0.0, eta_comp: float = 1.0,
                        fluid: str = "R134a") -> RefrigerationResults:
    """
    Solve a single-stage vapour-compression cycle.

    T_evap_C     : evaporating (saturation) temperature [°C]
    T_cond_C     : condensing (saturation) temperature [°C]
    superheat_K  : vapour superheat at compressor inlet [K]
    subcooling_K : liquid subcooling at condenser outlet [K]
    eta_comp     : compressor isentropic efficiency (1 = ideal)
    fluid        : CoolProp fluid name ("R134a", "R1234yf", "R290", "R600a", "R32", ...)
    """
    if T_evap_C >= T_cond_C:
        raise ValueError("Evaporating temperature must be lower than condensing temperature.")
    if not 0 < eta_comp <= 1:
        raise ValueError("Compressor isentropic efficiency must be between 0 and 1.")
    if superheat_K < 0 or subcooling_K < 0:
        raise ValueError("Superheat and subcooling cannot be negative.")
    T_crit = PropsSI("Tcrit", fluid)
    if T_cond_C + KELVIN >= T_crit:
        raise ValueError(
            f"Condensing temperature ({T_cond_C:.1f} °C) is above the critical temperature of "
            f"{fluid} ({T_crit - KELVIN:.1f} °C): a subcritical cycle is not possible.")

    T_e, T_c = T_evap_C + KELVIN, T_cond_C + KELVIN
    p_evap = PropsSI("P", "T", T_e, "Q", 1, fluid)
    p_cond = PropsSI("P", "T", T_c, "Q", 0, fluid)
    warnings = []

    # 1: compressor inlet
    if superheat_K == 0:
        s1 = state_from("1", fluid, "P", p_evap, "Q", 1)
    else:
        s1 = state_from("1", fluid, "P", p_evap, "T", T_e + superheat_K)

    # 2: compression (isentropic, then corrected with the efficiency)
    h2s = PropsSI("H", "P", p_cond, "S", s1.s, fluid)
    h2 = s1.h + (h2s - s1.h) / eta_comp
    s2 = state_from("2", fluid, "P", p_cond, "H", h2)

    # 3: condenser outlet
    if subcooling_K == 0:
        s3 = state_from("3", fluid, "P", p_cond, "Q", 0)
    else:
        s3 = state_from("3", fluid, "P", p_cond, "T", T_c - subcooling_K)

    # 4: throttling valve (isenthalpic)
    s4 = state_from("4", fluid, "P", p_evap, "H", s3.h)

    if s2.T - KELVIN > 130:
        warnings.append(f"high discharge temperature ({s2.T - KELVIN:.0f} °C): "
                        "risk of lubricant degradation.")
    if p_evap < 1 * BAR:
        warnings.append(f"evaporating pressure below atmospheric ({p_evap / BAR:.2f} bar): "
                        "air and moisture could leak into the circuit.")

    return RefrigerationResults(
        states={"1": s1, "2": s2, "3": s3, "4": s4},
        fluid=fluid,
        w_comp=s2.h - s1.h,
        q_evap=s1.h - s4.h,
        q_cond=s2.h - s3.h,
        warnings=warnings,
    )
