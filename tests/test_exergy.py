"""Exergy analysis: balance checks (fuel = product + destruction) and physical sanity."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from thermocycles import (brayton_cycle, exergy_analysis, rankine_cycle,  # noqa: E402
                          rankine_reheat_regen_cycle, refrigeration_cycle)

CYCLES = [
    rankine_cycle(80, 0.08, 480, 0.85, 0.85),
    rankine_reheat_regen_cycle(120, 0.08, 520, p_reheat_bar=15, p_fwh_bar=5, eta_turbine=0.88),
    brayton_cycle(10, 1100, eta_comp=0.85, eta_turb=0.88, regen_effectiveness=0.7),
    refrigeration_cycle(-10, 40, 5, 3, 0.75, "R290"),
]


@pytest.mark.parametrize("cycle", CYCLES, ids=lambda r: r.name)
def test_exergy_balance_closes(cycle):
    ex = exergy_analysis(cycle, T0_C=20)
    assert ex.balance_error == pytest.approx(0, abs=1e-6 * ex.fuel)
    assert all(x > -1e-6 * ex.fuel for x in ex.destruction.values())
    assert 0 < ex.efficiency < 1


def test_ideal_rankine_destroys_exergy_only_in_heat_exchange():
    ex = exergy_analysis(rankine_cycle(80, 0.08, 480), T0_C=20)
    assert ex.destruction["Turbine"] == pytest.approx(0, abs=1)
    assert ex.destruction["Pump"] == pytest.approx(0, abs=1)


def test_hotter_source_lowers_second_law_efficiency():
    r = rankine_cycle(80, 0.08, 480, 0.85, 0.85)
    assert exergy_analysis(r, T_source_C=1200).efficiency < exergy_analysis(r).efficiency


def test_refrigeration_product_is_cold_exergy():
    r = refrigeration_cycle(-10, 40, eta_comp=0.8)
    ex = exergy_analysis(r, T0_C=25, T_cold_C=0)
    assert ex.product == pytest.approx(r.q_evap * (298.15 / 273.15 - 1), rel=1e-9)
    assert 0 < ex.efficiency < 1


def test_invalid_reservoirs():
    r = rankine_cycle(80, 0.08, 480)
    with pytest.raises(ValueError):
        exergy_analysis(r, T_source_C=300)       # source colder than the steam
    with pytest.raises(ValueError):
        exergy_analysis(r, T0_C=60)              # ambient hotter than the condenser
