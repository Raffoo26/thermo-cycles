"""
Closed feedwater heaters and multiple extractions.
Reference: Moran & Shapiro, "Fundamentals of Engineering Thermodynamics", Example 8.6:
reheat–regenerative cycle, 8 MPa / 480 °C, reheat at 0.7 MPa to 440 °C, condenser 8 kPa,
closed heater at 2 MPa (feedwater leaves at 205 °C, drains throttled to the open heater),
open heater at 0.3 MPa, isentropic turbines and pumps, 100 MW net.
"""

import sys
from pathlib import Path

import pytest
from CoolProp.CoolProp import PropsSI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import FeedwaterHeater, exergy_analysis, rankine_reheat_regen_cycle  # noqa: E402

TTD_86 = PropsSI("T", "P", 20e5, "Q", 0, "Water") - 273.15 - 205   # feedwater leaves at 205 °C
BASE = dict(p_high_bar=80, p_low_bar=0.08, T_max_C=480)


def example_86():
    return rankine_reheat_regen_cycle(**BASE, p_reheat_bar=7, T_reheat_C=440,
                                      heaters=[FeedwaterHeater(20, "closed", TTD_86),
                                               FeedwaterHeater(3, "open")])


def test_closed_and_open_heater_textbook():
    r = example_86()
    assert r.efficiency == pytest.approx(0.431, abs=0.003)
    assert r.mass_flow_for_power(100e6) * 3600 == pytest.approx(2.8e5, rel=0.01)
    assert r.extractions[20] == pytest.approx(0.1522, abs=0.005)
    assert r.extractions[3] == pytest.approx(0.0941, abs=0.003)


@pytest.mark.parametrize("heaters", [
    [FeedwaterHeater(5, "closed")],                                       # drains to condenser
    [FeedwaterHeater(30, "closed", 3), FeedwaterHeater(10, "closed", 3)],  # cascaded drains
    [FeedwaterHeater(40, "closed", 2), FeedwaterHeater(8, "open"),
     FeedwaterHeater(2, "closed", 2), FeedwaterHeater(0.5, "closed", 2)],  # mixed, 4 extractions
    [(20, "closed", 5), 3, {"p_bar": 1, "kind": "closed"}],               # tuple / number / dict
])
def test_energy_and_exergy_balance(heaters):
    r = rankine_reheat_regen_cycle(120, 0.08, 540, p_reheat_bar=20, eta_turbine=0.88,
                                   eta_pump=0.8, heaters=heaters)
    assert r.q_in - r.q_out == pytest.approx(r.w_net, rel=1e-9)
    ex = exergy_analysis(r, T0_C=20, T_source_C=1200)
    assert ex.balance_error == pytest.approx(0, abs=1e-6 * ex.fuel)
    assert all(x > -1e-6 * ex.fuel for x in ex.destruction.values())


def test_more_extractions_raise_efficiency():
    one = rankine_reheat_regen_cycle(**BASE, heaters=[FeedwaterHeater(10, "closed")])
    three = rankine_reheat_regen_cycle(**BASE, heaters=[FeedwaterHeater(30, "closed"),
                                                        FeedwaterHeater(10, "closed"),
                                                        FeedwaterHeater(2, "closed")])
    assert three.efficiency > one.efficiency


def test_ttd_lowers_efficiency():
    ideal = rankine_reheat_regen_cycle(**BASE, heaters=[FeedwaterHeater(10, "closed", 0)])
    real = rankine_reheat_regen_cycle(**BASE, heaters=[FeedwaterHeater(10, "closed", 8)])
    assert real.efficiency < ideal.efficiency


def test_open_heater_shortcut_is_unchanged():
    a = rankine_reheat_regen_cycle(**BASE, p_fwh_bar=7, eta_turbine=0.85)
    b = rankine_reheat_regen_cycle(**BASE, heaters=[7], eta_turbine=0.85)
    assert a.efficiency == pytest.approx(b.efficiency, rel=1e-12)
    assert a.efficiency == pytest.approx(0.369, abs=0.003)          # Moran Example 8.5


def test_invalid_heaters():
    with pytest.raises(ValueError):
        rankine_reheat_regen_cycle(**BASE, heaters=[5, (5, "closed")])     # same pressure
    with pytest.raises(ValueError):
        rankine_reheat_regen_cycle(**BASE, heaters=[(5, "mixed")])         # unknown kind
    with pytest.raises(ValueError):
        rankine_reheat_regen_cycle(**BASE, heaters=[(0.1, "closed", 30)])  # cannot heat
    with pytest.raises(ValueError):
        rankine_reheat_regen_cycle(**BASE, heaters=[100])                  # above boiler pressure
