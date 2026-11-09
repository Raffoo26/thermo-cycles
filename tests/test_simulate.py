"""Tests for the input parsing of the interactive simulator (simulate.py)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulate import ask, parse_efficiency, parse_number  # noqa: E402


def test_parse_number_accepts_decimal_comma():
    assert parse_number("0,08") == pytest.approx(0.08)
    assert parse_number(" 80 ") == 80
    assert parse_number("-10.5") == -10.5


def test_parse_efficiency_fraction_or_percent():
    assert parse_efficiency("0.85") == pytest.approx(0.85)
    assert parse_efficiency("85") == pytest.approx(0.85)
    assert parse_efficiency("85%") == pytest.approx(0.85)
    assert parse_efficiency("1") == 1


@pytest.mark.parametrize("bad", ["0", "-5", "150", "abc"])
def test_parse_efficiency_rejects_invalid(bad):
    with pytest.raises(ValueError):
        parse_efficiency(bad)


def test_ask_uses_default_on_empty_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert ask("Boiler pressure [bar]", 80.0) == 80.0
    assert ask("Optional value", None, optional=True) is None


def test_ask_retries_until_valid(monkeypatch):
    answers = iter(["abc", "", "12,5"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert ask("Required value") == 12.5


def test_parse_fraction_allows_zero():
    from simulate import parse_fraction
    assert parse_fraction("0") == 0
    assert parse_fraction("80") == pytest.approx(0.8)
    assert parse_fraction("0,6") == pytest.approx(0.6)
    with pytest.raises(ValueError):
        parse_fraction("-1")


def test_parse_count_and_heater_kind():
    from simulate import parse_count, parse_heater_kind
    assert parse_count("3") == 3
    with pytest.raises(ValueError):
        parse_count("2.5")
    with pytest.raises(ValueError):
        parse_count("9")
    assert parse_heater_kind("Closed") == "closed"
    assert parse_heater_kind("aperto") == "open"
    with pytest.raises(ValueError):
        parse_heater_kind("mixed")
