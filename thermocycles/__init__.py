"""Thermodynamic cycle simulator with real-fluid properties (CoolProp)."""

from .brayton import BraytonResults, brayton_cycle
from .combined import CombinedCycleResults, combined_cycle
from .core import State, critical_point, saturation_pressure_bar, saturation_temperature_C
from .exergy import ExergyResults, exergy_analysis
from .rankine import FeedwaterHeater, RankineResults, rankine_cycle, rankine_reheat_regen_cycle
from .refrigeration import RefrigerationResults, refrigeration_cycle
from .transcritical import TranscriticalResults, optimal_high_pressure, transcritical_heat_pump

__all__ = [
    "rankine_cycle", "rankine_reheat_regen_cycle", "RankineResults", "FeedwaterHeater",
    "refrigeration_cycle", "RefrigerationResults",
    "transcritical_heat_pump", "optimal_high_pressure", "TranscriticalResults",
    "brayton_cycle", "BraytonResults",
    "combined_cycle", "CombinedCycleResults",
    "exergy_analysis", "ExergyResults",
    "State", "saturation_pressure_bar", "saturation_temperature_C", "critical_point",
]
