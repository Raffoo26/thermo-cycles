"""Thermodynamic cycle simulator with real-fluid properties (CoolProp)."""

from .brayton import BraytonResults, brayton_cycle
from .core import State, critical_point, saturation_pressure_bar, saturation_temperature_C
from .exergy import ExergyResults, exergy_analysis
from .rankine import RankineResults, rankine_cycle, rankine_reheat_regen_cycle
from .refrigeration import RefrigerationResults, refrigeration_cycle

__all__ = [
    "rankine_cycle", "rankine_reheat_regen_cycle", "RankineResults",
    "refrigeration_cycle", "RefrigerationResults",
    "brayton_cycle", "BraytonResults",
    "exergy_analysis", "ExergyResults",
    "State", "saturation_pressure_bar", "saturation_temperature_C", "critical_point",
]
