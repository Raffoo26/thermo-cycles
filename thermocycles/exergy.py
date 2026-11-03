"""
Exergy (second-law) analysis of any cycle in this package.

For every component the entropy generation is computed from the flows and the
heat exchanged with the external reservoirs:

    s_gen = Σ m_out s_out − Σ m_in s_in − Σ q / T_boundary
    exergy destroyed = T0 · s_gen                    (Gouy–Stodola theorem)

Power cycles (Rankine, Brayton): fuel = exergy of the heat from the hot source,
product = net work.  Refrigeration cycles: fuel = compressor work, product =
exergy of the cold produced, q_evap (T0 / T_cold − 1).

Reservoir temperatures:
    T0_C     : ambient (dead state) temperature; heat rejected to the ambient
               (condenser, exhaust) crosses the boundary at T0.
    T_source_C : temperature of the hot source (flame, flue gas, ...). If omitted,
               each heater uses the highest fluid temperature it reaches: the
               heat-transfer loss in the boiler is then not counted.
    T_cold_C : temperature of the refrigerated space. If omitted, the highest
               fluid temperature in the evaporator is used.
"""

from dataclasses import dataclass, field

from .core import KELVIN


@dataclass
class ExergyResults:
    T0: float                                   # K
    destruction: dict[str, float]               # J/kg per component
    fuel: float                                 # J/kg
    product: float                              # J/kg
    fuel_label: str
    product_label: str
    notes: list[str] = field(default_factory=list)

    @property
    def total_destruction(self) -> float:
        return sum(self.destruction.values())

    @property
    def efficiency(self) -> float:
        """Second-law (exergetic) efficiency = product / fuel."""
        return self.product / self.fuel

    @property
    def balance_error(self) -> float:
        """fuel − product − destruction: should be ~0 (numerical check)."""
        return self.fuel - self.product - self.total_destruction

    def table(self) -> list[dict]:
        rows = [{"Component": name, "Exergy destroyed [kJ/kg]": x / 1e3,
                 "Share of fuel [%]": x / self.fuel * 100}
                for name, x in sorted(self.destruction.items(), key=lambda kv: -kv[1])]
        return rows

    def summary(self) -> None:
        print(f"\nExergy analysis (T0 = {self.T0 - KELVIN:.1f} °C)")
        print(f"{'Component':>30} | {'Destroyed [kJ/kg]':>17} | {'% of fuel':>9}")
        print("-" * 64)
        for row in self.table():
            print(f"{row['Component']:>30} | {row['Exergy destroyed [kJ/kg]']:17.2f} | "
                  f"{row['Share of fuel [%]']:9.1f}")
        print("-" * 64)
        print(f"{'Total destroyed':>30} | {self.total_destruction / 1e3:17.2f} | "
              f"{self.total_destruction / self.fuel * 100:9.1f}")
        print(f"Fuel exergy ({self.fuel_label}): {self.fuel / 1e3:.2f} kJ/kg")
        print(f"Product exergy ({self.product_label}): {self.product / 1e3:.2f} kJ/kg")
        print(f"Second-law efficiency: {self.efficiency * 100:.1f} %")
        for n in self.notes:
            print(f"NOTE: {n}")


def exergy_analysis(r, T0_C: float = 25.0, T_source_C: float | None = None,
                    T_cold_C: float | None = None) -> ExergyResults:
    """Exergy destruction per component and second-law efficiency of a cycle result."""
    T0 = T0_C + KELVIN
    T_source = T_source_C + KELVIN if T_source_C is not None else None
    T_cold = T_cold_C + KELVIN if T_cold_C is not None else None
    notes = []

    destruction: dict[str, float] = {}
    fuel_heat = 0.0      # exergy of heat from the hot source
    cold_product = 0.0   # exergy of the cold produced
    for c in r.components:
        T_fluid = c.fluid_temperatures
        T_b = None
        if c.reservoir == "source":
            T_b = T_source if T_source is not None else max(T_fluid)
            if T_b < max(T_fluid) - 1e-6:
                raise ValueError(f"The hot source ({T_b - KELVIN:.1f} °C) must be at least as hot as "
                                 f"the fluid leaving the {c.name.lower()} ({max(T_fluid) - KELVIN:.1f} °C).")
            fuel_heat += c.heat * (1 - T0 / T_b)
        elif c.reservoir == "sink":
            T_b = T0
            if T0 > min(T_fluid) + 1e-6:
                raise ValueError(f"The ambient ({T0_C:.1f} °C) must be colder than the fluid in the "
                                 f"{c.name.lower()} (down to {min(T_fluid) - KELVIN:.1f} °C).")
        elif c.reservoir == "cold":
            T_b = T_cold if T_cold is not None else max(T_fluid)
            if T_b < max(T_fluid) - 1e-6:
                raise ValueError(f"The refrigerated space ({T_b - KELVIN:.1f} °C) must be warmer than "
                                 f"the refrigerant in the evaporator (up to {max(T_fluid) - KELVIN:.1f} °C).")
            if T_b > T0:
                raise ValueError("The refrigerated space must be colder than the ambient.")
            cold_product += c.heat * (T0 / T_b - 1)
        s_gen = c.entropy_change - (c.heat / T_b if T_b else 0.0)
        destruction[c.name] = destruction.get(c.name, 0.0) + T0 * s_gen

    if cold_product > 0:
        fuel, fuel_label = r.w_comp, "compressor work"
        product, product_label = cold_product, "cold produced"
        if T_cold is None:
            notes.append("refrigerated space taken at the evaporator's highest fluid temperature: "
                         "heat-transfer losses in the evaporator are not counted.")
    else:
        fuel, fuel_label = fuel_heat, "heat from the hot source"
        product, product_label = r.w_net, "net work"
        if T_source is None:
            notes.append("hot source taken at the highest fluid temperature of each heater: "
                         "heat-transfer losses in the boiler/combustor are not counted.")

    return ExergyResults(T0=T0, destruction=destruction, fuel=fuel, product=product,
                         fuel_label=fuel_label, product_label=product_label, notes=notes)
