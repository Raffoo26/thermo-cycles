"""
Validation against worked textbook examples (air-standard Brayton cycle).
Reference: Moran & Shapiro, "Fundamentals of Engineering Thermodynamics".
  Example 9.4: air at 100 kPa / 300 K, pressure ratio 10, turbine inlet 1400 K (ideal).
  Example 9.5: same cycle, compressor and turbine isentropic efficiencies of 0.80.
  Example 9.6: Example 9.4 with a regenerator of effectiveness 0.80.
The textbook uses ideal-gas air tables; here real-gas air properties (CoolProp) are used.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import brayton_cycle  # noqa: E402

BASE = dict(pressure_ratio=10, T_turbine_in_C=1400 - 273.15, T_in_C=300 - 273.15, p_in_bar=1.0)


def test_ideal_brayton_textbook():
    r = brayton_cycle(**BASE)
    assert r.efficiency == pytest.approx(0.457, abs=0.006)
    assert r.bwr == pytest.approx(0.396, abs=0.006)


def test_real_brayton_textbook():
    r = brayton_cycle(**BASE, eta_comp=0.8, eta_turb=0.8)
    assert r.efficiency == pytest.approx(0.248, abs=0.006)
    assert r.bwr == pytest.approx(0.619, abs=0.008)


def test_regenerative_brayton_textbook():
    r = brayton_cycle(**BASE, regen_effectiveness=0.8)
    assert r.efficiency == pytest.approx(0.568, abs=0.008)


def test_energy_balance_and_regenerator():
    r = brayton_cycle(8, 1100, eta_comp=0.85, eta_turb=0.9, regen_effectiveness=0.7)
    assert r.q_in - r.q_out == pytest.approx(r.w_net, rel=1e-6)
    no_regen = brayton_cycle(8, 1100, eta_comp=0.85, eta_turb=0.9)
    assert r.efficiency > no_regen.efficiency
    assert r.exhaust_temperature_C < no_regen.exhaust_temperature_C


def test_regenerator_ignored_when_useless():
    r = brayton_cycle(40, 900, regen_effectiveness=0.8)   # exhaust colder than compressor outlet
    assert r.regen_effectiveness == 0 and r.warnings


def test_invalid_inputs():
    with pytest.raises(ValueError):
        brayton_cycle(0.5, 1000)
    with pytest.raises(ValueError):
        brayton_cycle(10, 20, T_in_C=25)
    with pytest.raises(ValueError):
        brayton_cycle(10, 1000, regen_effectiveness=1.5)
