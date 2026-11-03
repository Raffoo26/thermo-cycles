"""
Validation of reheat and regeneration against worked textbook examples.
Reference: Moran & Shapiro, "Fundamentals of Engineering Thermodynamics".
  Example 8.3: reheat — 8 MPa / 480 °C, expansion to 0.7 MPa, reheat to 440 °C, condenser 8 kPa.
  Example 8.4: same cycle with turbine isentropic efficiency of 0.85.
  Example 8.5: regeneration — 8 MPa / 480 °C, open feedwater heater at 0.7 MPa,
               condenser 8 kPa, turbine stages 85 %, 100 MW net.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import rankine_cycle, rankine_reheat_regen_cycle  # noqa: E402


def test_reheat_ideal_textbook():
    r = rankine_reheat_regen_cycle(80, 0.08, 480, p_reheat_bar=7, T_reheat_C=440)
    assert r.efficiency == pytest.approx(0.403, abs=0.004)


def test_reheat_real_turbine_textbook():
    r = rankine_reheat_regen_cycle(80, 0.08, 480, p_reheat_bar=7, T_reheat_C=440, eta_turbine=0.85)
    assert r.efficiency == pytest.approx(0.351, abs=0.004)


def test_open_feedwater_heater_textbook():
    r = rankine_reheat_regen_cycle(80, 0.08, 480, p_fwh_bar=7, eta_turbine=0.85)
    assert r.efficiency == pytest.approx(0.369, abs=0.004)
    # steam mass flow for 100 MW net: 3.69e5 kg/h
    assert r.mass_flow_for_power(100e6) * 3600 == pytest.approx(3.69e5, rel=0.01)


def test_without_options_equals_simple_cycle():
    a = rankine_cycle(100, 0.1, 500, 0.9, 0.8)
    b = rankine_reheat_regen_cycle(100, 0.1, 500, eta_turbine=0.9, eta_pump=0.8)
    assert a.efficiency == pytest.approx(b.efficiency, rel=1e-12)
    assert list(b.states) == ["1", "2", "3", "4"]


@pytest.mark.parametrize("kwargs", [
    dict(p_reheat_bar=10, T_reheat_C=500),
    dict(p_fwh_bar=5),
    dict(p_reheat_bar=20, T_reheat_C=500, p_fwh_bar=5),     # extraction after reheat
    dict(p_reheat_bar=10, T_reheat_C=500, p_fwh_bar=30),    # extraction before reheat
    dict(p_reheat_bar=10, T_reheat_C=500, p_fwh_bar=10),    # extraction at reheat pressure
])
def test_energy_balance(kwargs):
    r = rankine_reheat_regen_cycle(120, 0.08, 520, eta_turbine=0.88, eta_pump=0.8, **kwargs)
    assert r.q_in - r.q_out == pytest.approx(r.w_net, rel=1e-6)


def test_reheat_and_regeneration_improve_the_cycle():
    base = rankine_cycle(80, 0.08, 480, 0.85, 0.85)
    reheat = rankine_reheat_regen_cycle(80, 0.08, 480, p_reheat_bar=7, eta_turbine=0.85, eta_pump=0.85)
    regen = rankine_reheat_regen_cycle(80, 0.08, 480, p_fwh_bar=7, eta_turbine=0.85, eta_pump=0.85)
    reheat_exhaust = reheat.states[str(len(reheat.states))]   # last state = turbine exhaust
    # drier exhaust: higher quality, or no liquid at all (superheated)
    assert reheat_exhaust.x is None or reheat_exhaust.x > base.states["4"].x
    assert regen.efficiency > base.efficiency                   # higher efficiency


def test_invalid_inputs():
    with pytest.raises(ValueError):
        rankine_reheat_regen_cycle(80, 0.08, 480, p_reheat_bar=100)      # above boiler pressure
    with pytest.raises(ValueError):
        rankine_reheat_regen_cycle(80, 0.08, None, p_reheat_bar=7)       # reheat T missing
    with pytest.raises(ValueError):
        rankine_reheat_regen_cycle(80, 0.08, 480, p_fwh_bar=0.01)        # below condenser pressure
