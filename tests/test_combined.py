"""
Combined gas–steam cycle.
Reference: Moran & Shapiro, "Fundamentals of Engineering Thermodynamics", Example 9.12:
45 MW net; air 100 kPa / 300 K, pressure ratio 12, η_c = 0.84, turbine inlet 1400 K,
η_t = 0.88, exhaust leaves the heat exchanger at 400 K; steam 8 MPa / 400 °C, condenser
8 kPa, η_turbine = 0.90, η_pump = 0.80. Textbook mass flows: 100.87 kg/s air, 15.6 kg/s steam.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import (FeedwaterHeater, brayton_cycle, combined_cycle,  # noqa: E402
                          exergy_analysis, rankine_cycle, rankine_reheat_regen_cycle)


def example_912():
    gas = brayton_cycle(12, 1400 - 273.15, T_in_C=300 - 273.15, p_in_bar=1.0, eta_comp=0.84, eta_turb=0.88)
    steam = rankine_cycle(80, 0.08, 400, 0.90, 0.80)
    return combined_cycle(gas, steam, T_stack_C=400 - 273.15)


def test_mass_flows_textbook():
    m_air, m_steam = example_912().mass_flows_for_power(45e6)
    assert m_air == pytest.approx(100.87, rel=0.01)
    assert m_steam == pytest.approx(15.6, rel=0.015)


def test_combined_beats_both_cycles():
    c = example_912()
    assert c.efficiency > c.gas.efficiency and c.efficiency > c.steam.efficiency
    assert c.efficiency == pytest.approx(0.527, abs=0.01)


def test_energy_balance_per_kg_air():
    c = example_912()
    s1 = c.gas.states["1"]
    q_stack = c.stack.h - s1.h
    q_condenser = c.steam_per_air * c.steam.q_out
    assert c.q_in == pytest.approx(c.w_net + q_stack + q_condenser, rel=1e-9)
    assert c.q_hrsg == pytest.approx(c.gas.states["4"].h - c.stack.h, rel=1e-9)


def test_exergy_balance_and_small_pinch_warning():
    c = example_912()
    ex = exergy_analysis(c, T0_C=25, T_source_C=1600)
    assert ex.balance_error == pytest.approx(0, abs=1e-6 * ex.fuel)
    assert 0 < c.pinch_K < 8 and any("pinch" in w for w in c.warnings)


def test_modern_plant_with_reheat_and_heaters():
    gas = brayton_cycle(18, 1350, T_in_C=15, p_in_bar=1.013, eta_comp=0.88, eta_turb=0.90)
    # single-pressure HRSG at 40 bar with a deaerator at 1.5 bar (feedwater at ~111 °C)
    steam = rankine_reheat_regen_cycle(40, 0.05, 520, eta_turbine=0.88, eta_pump=0.8,
                                       heaters=[FeedwaterHeater(1.5, "open")])
    c = combined_cycle(gas, steam, T_stack_C=170)
    assert 0.55 < c.efficiency < 0.62
    assert 8 < c.pinch_K < 20
    with pytest.raises(ValueError):       # a lower stack temperature violates the pinch
        combined_cycle(gas, steam, T_stack_C=130)


def test_invalid_combinations():
    gas = brayton_cycle(12, 1100, T_in_C=15)
    with pytest.raises(ValueError):
        combined_cycle(gas, rankine_cycle(80, 0.08, 700), T_stack_C=120)     # steam hotter than exhaust
    with pytest.raises(ValueError):
        combined_cycle(gas, rankine_cycle(80, 0.08, 450), T_stack_C=30)      # stack below feedwater
    with pytest.raises(ValueError):
        combined_cycle(gas, rankine_cycle(80, 0.08, 450), T_stack_C=60)      # pinch violated
