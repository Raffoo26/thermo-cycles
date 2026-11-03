"""
Brayton cycle (gas turbine), closed-cycle air-standard model with real-gas properties,
with an optional regenerator (recuperator).

Cycle states (Moran & Shapiro notation):
    1 - compressor inlet
    2 - compressor outlet
    x - regenerator cold-side outlet = combustor inlet   (only with regeneration)
    3 - turbine inlet
    4 - turbine outlet
    y - regenerator hot-side outlet = exhaust            (only with regeneration)

Heat addition (combustor) and heat rejection (exhaust to ambient) are modelled as
constant-pressure processes, as in the air-standard analysis.
"""

from dataclasses import dataclass

from .core import BAR, KELVIN, Component, CycleResults, isentropic_process, state_from


@dataclass
class BraytonResults(CycleResults):
    w_comp: float = 0.0     # J/kg
    w_turb: float = 0.0     # J/kg
    q_in: float = 0.0       # J/kg, combustor
    q_out: float = 0.0      # J/kg, exhaust to ambient
    regen_effectiveness: float = 0.0

    name = "Brayton cycle"
    show_dome = False

    @property
    def w_net(self) -> float:
        return self.w_turb - self.w_comp

    @property
    def efficiency(self) -> float:
        return self.w_net / self.q_in

    @property
    def bwr(self) -> float:
        """Back Work Ratio: fraction of the turbine work used by the compressor."""
        return self.w_comp / self.w_turb

    @property
    def headline(self) -> str:
        return f"η = {self.efficiency * 100:.1f} %"

    @property
    def exhaust_temperature_C(self) -> float:
        last = self.states["y"] if "y" in self.states else self.states["4"]
        return last.T - KELVIN

    def mass_flow_for_power(self, power_W: float) -> float:
        """Air mass flow [kg/s] for a given net power output [W]."""
        return power_W / self.w_net

    def summary(self) -> None:
        self._print_states()
        print(f"Compressor work   : {self.w_comp / 1e3:8.2f} kJ/kg")
        print(f"Turbine work      : {self.w_turb / 1e3:8.2f} kJ/kg")
        print(f"Net work          : {self.w_net / 1e3:8.2f} kJ/kg")
        print(f"Heat input        : {self.q_in / 1e3:8.2f} kJ/kg")
        print(f"Heat rejected     : {self.q_out / 1e3:8.2f} kJ/kg")
        print(f"Thermal efficiency: {self.efficiency * 100:8.2f} %")
        print(f"Back Work Ratio   : {self.bwr * 100:8.2f} %")
        print(f"Exhaust temperature: {self.exhaust_temperature_C:7.1f} °C")
        self._print_warnings()


def brayton_cycle(pressure_ratio: float, T_turbine_in_C: float,
                  T_in_C: float = 27.0, p_in_bar: float = 1.0,
                  eta_comp: float = 1.0, eta_turb: float = 1.0,
                  regen_effectiveness: float = 0.0, fluid: str = "Air") -> BraytonResults:
    """
    Solve a Brayton cycle.

    pressure_ratio      : compressor pressure ratio p2/p1 [-]
    T_turbine_in_C      : turbine inlet temperature [°C]
    T_in_C              : compressor inlet temperature [°C]
    p_in_bar            : compressor inlet pressure [bar]
    eta_comp            : compressor isentropic efficiency (1 = ideal)
    eta_turb            : turbine isentropic efficiency (1 = ideal)
    regen_effectiveness : regenerator effectiveness, 0 = no regenerator, 1 = ideal
    fluid               : CoolProp fluid name ("Air", "Nitrogen", "Helium", "CO2", ...)
    """
    if pressure_ratio <= 1:
        raise ValueError("The pressure ratio must be greater than 1.")
    if T_turbine_in_C <= T_in_C:
        raise ValueError("Turbine inlet temperature must be higher than compressor inlet temperature.")
    if not (0 < eta_comp <= 1 and 0 < eta_turb <= 1):
        raise ValueError("Isentropic efficiencies must be between 0 and 1.")
    if not 0 <= regen_effectiveness <= 1:
        raise ValueError("Regenerator effectiveness must be between 0 and 1.")

    p1 = p_in_bar * BAR
    p2 = p1 * pressure_ratio
    warnings = []

    s1 = state_from("1", fluid, "P", p1, "T", T_in_C + KELVIN)
    s2 = isentropic_process("2", s1, p2, eta_comp, fluid, expansion=False)
    s3 = state_from("3", fluid, "P", p2, "T", T_turbine_in_C + KELVIN)
    if s2.T >= s3.T:
        raise ValueError(f"Compressor outlet ({s2.T - KELVIN:.0f} °C) is already hotter than the "
                         "turbine inlet: reduce the pressure ratio or raise the turbine inlet temperature.")
    s4 = isentropic_process("4", s3, p1, eta_turb, fluid, expansion=True)

    eps = regen_effectiveness
    if eps > 0 and s4.T <= s2.T:
        warnings.append(f"turbine exhaust ({s4.T - KELVIN:.0f} °C) is colder than the compressor "
                        f"outlet ({s2.T - KELVIN:.0f} °C): a regenerator cannot help, so it was ignored.")
        eps = 0.0

    states = {"1": s1, "2": s2}
    if eps > 0:
        # Effectiveness defined on enthalpy: h_x = h2 + eps (h4 - h2); energy balance on the hot side
        hx = s2.h + eps * (s4.h - s2.h)
        sx = state_from("x", fluid, "P", p2, "H", hx)
        sy = state_from("y", fluid, "P", p1, "H", s4.h - (hx - s2.h))
        states.update({"x": sx, "3": s3, "4": s4, "y": sy})
        heater_in, exhaust = sx, sy
        paths = [("1", "2", "line"), ("2", "x", "isobar"), ("x", "3", "isobar"),
                 ("3", "4", "line"), ("4", "y", "isobar"), ("y", "1", "isobar")]
    else:
        states.update({"3": s3, "4": s4})
        heater_in, exhaust = s2, s4
        paths = [("1", "2", "line"), ("2", "3", "isobar"), ("3", "4", "line"), ("4", "1", "isobar")]

    w_comp, w_turb = s2.h - s1.h, s3.h - s4.h
    q_in, q_out = s3.h - heater_in.h, exhaust.h - s1.h

    components = [Component("Compressor", [(s1, 1.0)], [(s2, 1.0)])]
    if eps > 0:
        components.append(Component("Regenerator", [(s2, 1.0), (s4, 1.0)], [(sx, 1.0), (sy, 1.0)]))
    components += [
        Component("Combustor (heat addition)", [(heater_in, 1.0)], [(s3, 1.0)], q_in, "source"),
        Component("Turbine", [(s3, 1.0)], [(s4, 1.0)]),
        Component("Exhaust (heat rejection)", [(exhaust, 1.0)], [(s1, 1.0)], -q_out, "sink"),
    ]

    return BraytonResults(states=states, fluid=fluid, paths=paths, components=components,
                          warnings=warnings, w_comp=w_comp, w_turb=w_turb, q_in=q_in,
                          q_out=q_out, regen_effectiveness=eps)
