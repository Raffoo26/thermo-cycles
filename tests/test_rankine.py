"""
Validation against worked textbook examples.
Reference: Moran & Shapiro, "Fundamentals of Engineering Thermodynamics",
Examples 8.1 (ideal cycle) and 8.2 (isentropic efficiencies of 0.85).
Cycle: saturated vapour at 8 MPa (80 bar), condenser at 8 kPa (0.08 bar).
Small deviations come from the property data (CoolProp vs printed steam tables).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import rankine_cycle  # noqa: E402


def test_ideal_rankine_textbook():
    r = rankine_cycle(p_high_bar=80, p_low_bar=0.08)
    assert r.efficiency == pytest.approx(0.371, abs=0.003)
    assert r.states["4"].x == pytest.approx(0.6745, abs=0.003)
    assert r.w_turbine / 1e3 == pytest.approx(963.2, rel=0.005)
    assert r.w_pump / 1e3 == pytest.approx(8.06, rel=0.02)
    assert r.q_in / 1e3 == pytest.approx(2576.1, rel=0.005)


def test_real_rankine_textbook():
    r = rankine_cycle(p_high_bar=80, p_low_bar=0.08, eta_turbine=0.85, eta_pump=0.85)
    assert r.efficiency == pytest.approx(0.314, abs=0.003)


def test_energy_balance():
    r = rankine_cycle(p_high_bar=100, p_low_bar=0.1, T_max_C=500, eta_turbine=0.9, eta_pump=0.8)
    # First law over the cycle: q_in - q_out = w_turbine - w_pump
    assert r.q_in - r.q_out == pytest.approx(r.w_net, rel=1e-6)


def test_superheat_increases_efficiency():
    base = rankine_cycle(80, 0.08)
    sh = rankine_cycle(80, 0.08, T_max_C=480)
    assert sh.efficiency > base.efficiency
    assert sh.states["4"].x > base.states["4"].x


def test_invalid_inputs():
    with pytest.raises(ValueError):
        rankine_cycle(p_high_bar=0.05, p_low_bar=0.08)
    with pytest.raises(ValueError):
        rankine_cycle(p_high_bar=80, p_low_bar=0.08, T_max_C=200)  # below T_sat (~295 °C)
