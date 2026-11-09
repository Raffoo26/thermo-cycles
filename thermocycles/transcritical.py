"""
Transcritical CO₂ (R744) heat pump.

CO₂ has its critical point at only 31 °C / 73.8 bar, so a heat pump that heats water
or air above that temperature rejects heat ABOVE the critical pressure: there is no
condensation, the supercritical gas is simply cooled in a "gas cooler" with a
continuously falling temperature. This suits domestic hot water very well, because
the water also warms up continuously (e.g. 10 → 60 °C).

Cycle states:
    1 - compressor inlet    (saturated or superheated vapour, p_evap)
    2 - compressor outlet   (supercritical, p_high)
    3 - gas cooler outlet   (supercritical, p_high, T_gc_out)
    4 - evaporator inlet    (two-phase after throttling, h4 = h3)

Unlike a condensing cycle, the high pressure is NOT fixed by a temperature: it is a
free design variable, and the COP has a maximum at an optimal high pressure
(see optimal_high_pressure).
"""

from dataclasses import dataclass

import numpy as np
from CoolProp.CoolProp import PropsSI

from .core import BAR, KELVIN, Component, isentropic_process, state_from
from .refrigeration import RefrigerationResults


@dataclass
class TranscriticalResults(RefrigerationResults):
    name = "Transcritical CO₂ heat pump"
    is_heat_pump = True

    @property
    def headline(self) -> str:
        return f"COP heating = {self.cop_heating:.2f}"

    @property
    def gas_cooler_mean_temperature(self) -> float:
        """Thermodynamic mean temperature of heat rejection, q / Δs [K]."""
        s2, s3 = self.states["2"], self.states["3"]
        return (s2.h - s3.h) / (s2.s - s3.s)

    @property
    def cop_carnot_cooling(self) -> float:
        """Lorenz (reversible) COP between the evaporating temperature and the mean
        gas cooler temperature."""
        T_e = PropsSI("T", "P", self.states["1"].p, "Q", 1, self.fluid)
        T_m = self.gas_cooler_mean_temperature
        return T_e / (T_m - T_e)

    @property
    def cop_lorenz_heating(self) -> float:
        return self.cop_carnot_cooling + 1

    def summary(self) -> None:
        self._print_states()
        print(f"Compressor work          : {self.w_comp / 1e3:8.2f} kJ/kg")
        print(f"Heat from evaporator     : {self.q_evap / 1e3:8.2f} kJ/kg")
        print(f"Heat to gas cooler       : {self.q_cond / 1e3:8.2f} kJ/kg")
        print(f"COP heating              : {self.cop_heating:8.2f}")
        print(f"COP cooling              : {self.cop_cooling:8.2f}")
        print(f"Lorenz COP (heating)     : {self.cop_lorenz_heating:8.2f}")
        print(f"Gas cooler mean temp.    : {self.gas_cooler_mean_temperature - KELVIN:8.1f} °C")
        print(f"Pressure ratio           : {self.pressure_ratio:8.2f}")
        print(f"Discharge temperature    : {self.discharge_temperature_C:8.1f} °C")
        self._print_warnings()


def transcritical_heat_pump(T_evap_C: float, p_high_bar: float, T_gc_out_C: float,
                            superheat_K: float = 0.0, eta_comp: float = 1.0,
                            fluid: str = "CO2") -> TranscriticalResults:
    """
    Solve a transcritical vapour-compression heat pump (normally with CO₂).

    T_evap_C    : evaporating temperature [°C] (below the critical temperature)
    p_high_bar  : gas cooler pressure [bar] (above the critical pressure)
    T_gc_out_C  : gas cooler outlet temperature [°C]
    superheat_K : vapour superheat at the compressor inlet [K]
    eta_comp    : compressor isentropic efficiency (1 = ideal)
    fluid       : CoolProp fluid name (default "CO2")
    """
    T_crit, p_crit = PropsSI("Tcrit", fluid), PropsSI("pcrit", fluid)
    if T_evap_C + KELVIN >= T_crit:
        raise ValueError(f"The evaporating temperature must be below the critical temperature of "
                         f"{fluid} ({T_crit - KELVIN:.1f} °C).")
    if p_high_bar * BAR <= p_crit:
        raise ValueError(f"The gas cooler pressure ({p_high_bar:g} bar) must be above the critical "
                         f"pressure of {fluid} ({p_crit / BAR:.1f} bar); below it, use refrigeration_cycle.")
    if T_gc_out_C <= T_evap_C:
        raise ValueError("The gas cooler outlet must be warmer than the evaporating temperature.")
    if not 0 < eta_comp <= 1:
        raise ValueError("Compressor isentropic efficiency must be between 0 and 1.")
    if superheat_K < 0:
        raise ValueError("Superheat cannot be negative.")

    T_e = T_evap_C + KELVIN
    p_evap = PropsSI("P", "T", T_e, "Q", 1, fluid)
    p_high = p_high_bar * BAR

    s1 = (state_from("1", fluid, "P", p_evap, "Q", 1) if superheat_K == 0
          else state_from("1", fluid, "P", p_evap, "T", T_e + superheat_K))
    s2 = isentropic_process("2", s1, p_high, eta_comp, fluid, expansion=False)
    s3 = state_from("3", fluid, "P", p_high, "T", T_gc_out_C + KELVIN)
    if s3.T >= s2.T:
        raise ValueError(f"The gas cooler outlet ({T_gc_out_C:.0f} °C) must be colder than the "
                         f"compressor discharge ({s2.T - KELVIN:.0f} °C): raise the pressure.")
    s4 = state_from("4", fluid, "P", p_evap, "H", s3.h)

    warnings = []
    if s2.T - KELVIN > 140:
        warnings.append(f"high discharge temperature ({s2.T - KELVIN:.0f} °C): risk of lubricant degradation.")
    if p_high_bar > 140:
        warnings.append(f"very high gas cooler pressure ({p_high_bar:g} bar): above typical component ratings.")

    w_comp, q_evap, q_gc = s2.h - s1.h, s1.h - s4.h, s2.h - s3.h
    components = [
        Component("Compressor", [(s1, 1.0)], [(s2, 1.0)]),
        Component("Gas cooler", [(s2, 1.0)], [(s3, 1.0)], -q_gc, "user"),
        Component("Expansion valve", [(s3, 1.0)], [(s4, 1.0)]),
        Component("Evaporator", [(s4, 1.0)], [(s1, 1.0)], q_evap, "ambient"),
    ]
    return TranscriticalResults(
        states={"1": s1, "2": s2, "3": s3, "4": s4}, fluid=fluid,
        paths=[("1", "2", "line"), ("2", "3", "isobar"), ("3", "4", "throttle"), ("4", "1", "isobar")],
        components=components, warnings=warnings, w_comp=w_comp, q_evap=q_evap, q_cond=q_gc)


def optimal_high_pressure(T_evap_C: float, T_gc_out_C: float, superheat_K: float = 0.0,
                          eta_comp: float = 1.0, fluid: str = "CO2",
                          p_min_bar: float | None = None, p_max_bar: float = 160.0):
    """
    Gas cooler pressure that maximises the heating COP.

    Returns (p_opt_bar, result_at_optimum). Coarse scan followed by a golden-section
    refinement; the COP curve has a single, rather flat maximum. If the gas cooler
    outlet is below the critical temperature (31 °C for CO₂) the "optimum" falls at the
    lowest pressure: a subcritical cycle (refrigeration_cycle) is then the better choice.
    """
    p_crit_bar = PropsSI("pcrit", fluid) / BAR
    lo = p_min_bar if p_min_bar is not None else p_crit_bar + 0.5

    def cop(p):
        try:
            return transcritical_heat_pump(T_evap_C, p, T_gc_out_C, superheat_K, eta_comp, fluid).cop_heating
        except ValueError:
            return -np.inf

    grid = np.linspace(lo, p_max_bar, 60)
    values = [cop(p) for p in grid]
    k = int(np.argmax(values))
    if not np.isfinite(values[k]):
        raise ValueError("No feasible gas cooler pressure in the range: check the temperatures.")
    a, b = grid[max(k - 1, 0)], grid[min(k + 1, len(grid) - 1)]
    g = (np.sqrt(5) - 1) / 2
    c, d = b - g * (b - a), a + g * (b - a)
    for _ in range(40):
        if cop(c) > cop(d):
            b, d = d, c
            c = b - g * (b - a)
        else:
            a, c = c, d
            d = a + g * (b - a)
    p_opt = (a + b) / 2
    return p_opt, transcritical_heat_pump(T_evap_C, p_opt, T_gc_out_C, superheat_K, eta_comp, fluid)
