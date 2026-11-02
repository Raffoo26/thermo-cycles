"""
Validation against worked textbook examples.
Reference: Moran & Shapiro, "Fundamentals of Engineering Thermodynamics",
Examples 10.1 (ideal cycle) and 10.2 (compressor isentropic efficiency of 0.80).
Cycle: R-134a, saturated vapour at -10 °C entering the compressor,
saturated liquid leaving the condenser at 9 bar, mass flow 0.08 kg/s.
Small deviations come from the property data (CoolProp vs printed tables).
"""

import sys
from pathlib import Path

import pytest
from CoolProp.CoolProp import PropsSI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import refrigeration_cycle  # noqa: E402

# Saturation temperature of R-134a at 9 bar (≈ 35.5 °C)
T_COND_9BAR = PropsSI("T", "P", 9e5, "Q", 0, "R134a") - 273.15
M_DOT = 0.08  # kg/s


def test_ideal_cycle_textbook():
    r = refrigeration_cycle(T_evap_C=-10, T_cond_C=T_COND_9BAR, fluid="R134a")
    assert r.cop_cooling == pytest.approx(4.57, rel=0.02)
    assert r.w_comp / 1e3 == pytest.approx(31.04, rel=0.02)
    assert r.q_evap / 1e3 == pytest.approx(141.79, rel=0.01)
    assert M_DOT * r.w_comp / 1e3 == pytest.approx(2.48, rel=0.02)    # compressor power [kW]
    assert M_DOT * r.q_evap / 1e3 == pytest.approx(11.34, rel=0.01)   # cooling capacity [kW]


def test_real_compressor_textbook():
    r = refrigeration_cycle(T_evap_C=-10, T_cond_C=T_COND_9BAR, eta_comp=0.80, fluid="R134a")
    assert r.cop_cooling == pytest.approx(3.66, rel=0.02)


def test_energy_balance_and_heat_pump_cop():
    r = refrigeration_cycle(-5, 45, superheat_K=5, subcooling_K=5, eta_comp=0.7, fluid="R290")
    # First law over the cycle: heat to condenser = heat from evaporator + compressor work
    assert r.q_cond == pytest.approx(r.q_evap + r.w_comp, rel=1e-6)
    # For the same cycle, COP_heating = COP_cooling + 1
    assert r.cop_heating == pytest.approx(r.cop_cooling + 1, rel=1e-6)


def test_below_carnot():
    for fluid in ("R134a", "R1234yf", "R290", "R600a", "R32"):
        r = refrigeration_cycle(-10, 40, fluid=fluid)
        assert r.cop_cooling < r.cop_carnot_cooling


def test_subcooling_increases_cop():
    base = refrigeration_cycle(-10, 40)
    sub = refrigeration_cycle(-10, 40, subcooling_K=5)
    assert sub.cop_cooling > base.cop_cooling


def test_invalid_inputs():
    with pytest.raises(ValueError):
        refrigeration_cycle(T_evap_C=40, T_cond_C=-10)
    with pytest.raises(ValueError):
        refrigeration_cycle(-10, 40, eta_comp=1.5)
    with pytest.raises(ValueError):
        refrigeration_cycle(-10, 40, fluid="CO2")  # 40 °C is above the critical point of CO2 (31 °C)
