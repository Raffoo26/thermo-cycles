"""
Combined gas–steam cycle.

A Brayton (gas turbine) topping cycle and a Rankine (steam) bottoming cycle are
coupled by a heat recovery steam generator (HRSG): the hot turbine exhaust heats
the feedwater, boils it and superheats (and reheats) the steam, then leaves
through the stack at T_stack.

Energy balance of the HRSG, per kg of air:
    h_exhaust − h_stack = (m_steam / m_air) · q_in,steam

The pinch point is the smallest temperature difference between the gas and the
water, which occurs where the water starts boiling. It must be positive (and in
practice at least about 8–15 K).
"""

from dataclasses import dataclass, field

from CoolProp.CoolProp import PropsSI

from .brayton import BraytonResults
from .core import BAR, KELVIN, Component, State, state_from
from .rankine import RankineResults


def _scaled(c: Component, k: float) -> Component:
    return Component(c.name, [(s, m * k) for s, m in c.inlets], [(s, m * k) for s, m in c.outlets],
                     c.heat * k, c.reservoir)


@dataclass
class CombinedCycleResults:
    gas: BraytonResults
    steam: RankineResults
    steam_per_air: float          # kg of steam per kg of air
    stack: State                  # gas leaving the HRSG
    pinch_K: float                # minimum gas–water temperature difference [K]
    T_gas_pinch: float            # gas temperature at the pinch point [K]
    components: list[Component] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    name = "Combined cycle"

    @property
    def fluid(self) -> str:
        return f"{self.gas.fluid} / {self.steam.fluid}"

    @property
    def w_net(self) -> float:
        """Net work per kg of air (gas turbine + steam turbine)."""
        return self.gas.w_net + self.steam_per_air * self.steam.w_net

    @property
    def q_in(self) -> float:
        """Heat input per kg of air (combustor only)."""
        return self.gas.q_in

    @property
    def efficiency(self) -> float:
        return self.w_net / self.q_in

    @property
    def gas_share(self) -> float:
        """Fraction of the net power produced by the gas turbine."""
        return self.gas.w_net / self.w_net

    @property
    def q_hrsg(self) -> float:
        """Heat recovered in the HRSG per kg of air."""
        return self.steam_per_air * self.steam.q_in

    @property
    def headline(self) -> str:
        return f"η = {self.efficiency * 100:.1f} %"

    def mass_flows_for_power(self, power_W: float) -> tuple[float, float]:
        """Air and steam mass flows [kg/s] for a given total net power [W]."""
        m_air = power_W / self.w_net
        return m_air, m_air * self.steam_per_air

    def summary(self) -> None:
        print(f"\nCombined cycle — gas: {self.gas.fluid}, steam: {self.steam.fluid}")
        print(f"Gas turbine efficiency (alone) : {self.gas.efficiency * 100:7.2f} %")
        print(f"Steam cycle efficiency (alone) : {self.steam.efficiency * 100:7.2f} %")
        print(f"Steam per kg of air            : {self.steam_per_air:7.4f} kg/kg")
        print(f"Net work per kg of air         : {self.w_net / 1e3:7.1f} kJ/kg")
        print(f"   gas turbine / steam cycle   : {self.gas_share * 100:5.1f} % / {(1 - self.gas_share) * 100:5.1f} %")
        print(f"Heat recovered in the HRSG     : {self.q_hrsg / 1e3:7.1f} kJ/kg air")
        print(f"Stack temperature              : {self.stack.T - KELVIN:7.1f} °C")
        print(f"Pinch point                    : {self.pinch_K:7.1f} K")
        print(f"COMBINED EFFICIENCY            : {self.efficiency * 100:7.2f} %")
        for w in self.warnings:
            print(f"WARNING: {w}")


def combined_cycle(gas: BraytonResults, steam: RankineResults,
                   T_stack_C: float = 100.0) -> CombinedCycleResults:
    """
    Couple a gas turbine cycle and a steam cycle through a heat recovery steam generator.

    gas       : result of brayton_cycle(...) — the topping cycle
    steam     : result of rankine_cycle(...) or rankine_reheat_regen_cycle(...) — the bottoming
                cycle; all its boiler and reheater heat is supplied by the gas turbine exhaust
    T_stack_C : temperature of the gas leaving the HRSG (stack) [°C]
    """
    exhaust = gas.states["y"] if "y" in gas.states else gas.states["4"]
    p_gas = exhaust.p
    if T_stack_C + KELVIN >= exhaust.T:
        raise ValueError(f"The stack temperature ({T_stack_C:.0f} °C) must be lower than the gas "
                         f"turbine exhaust ({exhaust.T - KELVIN:.0f} °C).")
    boiler = next(c for c in steam.components if c.name == "Boiler")
    s_fw, s_steam = boiler.inlets[0][0], boiler.outlets[0][0]
    T_steam_max = max(T for c in steam.components if c.reservoir == "source" for T in c.fluid_temperatures)
    if T_steam_max >= exhaust.T:
        raise ValueError(f"The steam ({T_steam_max - KELVIN:.0f} °C) cannot be hotter than the gas turbine "
                         f"exhaust ({exhaust.T - KELVIN:.0f} °C): lower the steam temperature.")
    if T_stack_C + KELVIN <= s_fw.T:
        raise ValueError(f"The stack ({T_stack_C:.0f} °C) must be hotter than the feedwater entering "
                         f"the HRSG ({s_fw.T - KELVIN:.0f} °C).")

    stack = state_from("stack", gas.fluid, "P", p_gas, "T", T_stack_C + KELVIN)
    ratio = (exhaust.h - stack.h) / steam.q_in

    # Pinch point: where the water starts to boil (economizer outlet)
    h_f = PropsSI("H", "P", s_fw.p, "Q", 0, steam.fluid)
    T_sat = PropsSI("T", "P", s_fw.p, "Q", 0, steam.fluid)
    h_gas_pinch = stack.h + ratio * (h_f - s_fw.h)
    T_gas_pinch = PropsSI("T", "P", p_gas, "H", h_gas_pinch, gas.fluid)
    pinch = T_gas_pinch - T_sat
    if pinch <= 0:
        raise ValueError(f"Pinch point violated: at the start of boiling the gas would be at "
                         f"{T_gas_pinch - KELVIN:.0f} °C, below the boiling water ({T_sat - KELVIN:.0f} °C). "
                         "Raise the stack temperature or lower the steam pressure.")
    warnings = list(gas.warnings) + list(steam.warnings)
    if pinch < 8:
        warnings.append(f"very small pinch point ({pinch:.1f} K): a real HRSG needs about 8–15 K, "
                        "otherwise its surface becomes huge.")

    # Components for the exergy analysis (per kg of air)
    comps = []
    for c in gas.components:
        if c.reservoir != "sink":                   # gas exhaust now goes to the HRSG
            gc = _scaled(c, 1.0)
            gc.name = f"Gas: {c.name}"
            comps.append(gc)
    hrsg_in, hrsg_out = [(exhaust, 1.0)], [(stack, 1.0)]
    for c in steam.components:
        if c.reservoir == "source":                 # boiler and reheater → HRSG
            hrsg_in += [(s, m * ratio) for s, m in c.inlets]
            hrsg_out += [(s, m * ratio) for s, m in c.outlets]
        else:
            sc = _scaled(c, ratio)
            sc.name = f"Steam: {c.name}"
            comps.append(sc)
    comps.append(Component("HRSG", hrsg_in, hrsg_out))
    s1 = gas.states["1"]
    comps.append(Component("Stack (exhaust to ambient)", [(stack, 1.0)], [(s1, 1.0)], -(stack.h - s1.h), "sink"))

    return CombinedCycleResults(gas=gas, steam=steam, steam_per_air=ratio, stack=stack,
                                pinch_K=pinch, T_gas_pinch=T_gas_pinch, components=comps,
                                warnings=warnings)
