"""
Transcritical CO₂ heat pump.
There is no worked textbook example; the optimal gas cooler pressure is checked against
the correlation of Liao, Zhao & Jakobsen, "A correlation of optimal heat rejection
pressures in transcritical carbon dioxide cycles", Applied Thermal Engineering 20 (2000):
    p_opt [bar] = (2.778 − 0.0157 t_e) t_gc + (0.381 t_e − 9.34)    (t in °C)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import (exergy_analysis, optimal_high_pressure,  # noqa: E402
                          refrigeration_cycle, transcritical_heat_pump)


def liao(t_e, t_gc):
    return (2.778 - 0.0157 * t_e) * t_gc + (0.381 * t_e - 9.34)


@pytest.mark.parametrize("t_e, t_gc", [(0, 35), (0, 40), (-10, 40), (5, 45), (10, 35)])
def test_optimal_pressure_matches_liao_correlation(t_e, t_gc):
    p_opt, _ = optimal_high_pressure(t_e, t_gc, eta_comp=0.7)
    assert p_opt == pytest.approx(liao(t_e, t_gc), rel=0.03)


def test_optimum_is_a_maximum():
    p_opt, best = optimal_high_pressure(0, 40, eta_comp=0.7)
    for dp in (-8, +8):
        other = transcritical_heat_pump(0, p_opt + dp, 40, eta_comp=0.7)
        assert other.cop_heating < best.cop_heating


def test_energy_balance_and_lorenz_limit():
    r = transcritical_heat_pump(0, 95, 35, superheat_K=5, eta_comp=0.7)
    assert r.q_cond == pytest.approx(r.q_evap + r.w_comp, rel=1e-9)
    assert r.cop_heating == pytest.approx(r.cop_cooling + 1, rel=1e-9)
    assert r.cop_heating < r.cop_lorenz_heating
    assert r.states["3"].x is None and r.states["4"].x is not None   # supercritical out, two-phase in


def test_colder_gas_cooler_outlet_raises_cop():
    # the key advantage for hot water: cold water entering the gas cooler → high COP
    warm = optimal_high_pressure(0, 45, eta_comp=0.7)[1]
    cold = optimal_high_pressure(0, 20, eta_comp=0.7)[1]
    assert cold.cop_heating > warm.cop_heating + 1


def test_heat_pump_exergy_balance():
    r = transcritical_heat_pump(0, 90, 35, superheat_K=5, eta_comp=0.7)
    ex = exergy_analysis(r, T0_C=7, T_user_C=35)
    assert ex.product_label == "heat delivered"
    assert ex.balance_error == pytest.approx(0, abs=1e-6 * ex.fuel)
    assert 0 < ex.efficiency < 1


def test_refrigeration_cycle_still_rejects_co2_above_critical():
    with pytest.raises(ValueError):
        refrigeration_cycle(0, 40, fluid="CO2")


def test_invalid_inputs():
    with pytest.raises(ValueError):
        transcritical_heat_pump(0, 60, 35)          # below the critical pressure
    with pytest.raises(ValueError):
        transcritical_heat_pump(35, 90, 40)         # evaporating above the critical temperature
    with pytest.raises(ValueError):
        transcritical_heat_pump(0, 80, 120)         # gas cooler outlet hotter than discharge
    with pytest.raises(ValueError):
        exergy_analysis(transcritical_heat_pump(0, 90, 35), T0_C=-5)   # ambient colder than evaporator
