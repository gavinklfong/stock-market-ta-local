"""Backtesting framework — reusable, ticker-agnostic."""

from .engine import BacktestEngine
from .metrics import calculate_metrics
from .extensions import register_custom, load_custom_strategies
from .signal import SignalBase
from .report import generate_report

__all__ = [
    "BacktestEngine",
    "calculate_metrics",
    "register_custom",
    "load_custom_strategies",
    "SignalBase",
    "generate_report",
]
