"""Base class for signal strategies — optional OOP wrapper around function-style signals."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class SignalBase(ABC):
    """Abstract base class for backtest signal strategies.

    Concrete subclasses implement ``signal()`` which receives a DataFrame
    and returns ``(entries, exits)`` — both pandas Series of int with
    1 for entry, -1 for exit, 0 otherwise.
    """

    name: str = "base"
    display_name: str = "Base Strategy"
    category: str = "custom"

    @abstractmethod
    def signal(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """Return (entries, exits) signal series."""
        ...

    def __call__(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """Allow the instance to be called directly as a signal function."""
        return self.signal(df)


# ---------------------------------------------------------------------------
# Convenience helpers that many strategies share
# ---------------------------------------------------------------------------

def _rising(series: pd.Series, periods: int = 1) -> pd.Series:
    """Return True where *series* is rising compared *periods* bars ago."""
    return series > series.shift(periods)


def _falling(series: pd.Series, periods: int = 1) -> pd.Series:
    """Return True where *series* is falling compared *periods* bars ago."""
    return series < series.shift(periods)


def _bullish_cross(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """True on the bar where *fast* crosses above *slow*."""
    return (fast > slow) & (fast.shift(1) <= slow.shift(1))


def _bearish_cross(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """True on the bar where *fast* crosses below *slow*."""
    return (fast < slow) & (fast.shift(1) >= slow.shift(1))


def _near(series_a: pd.Series, series_b: pd.Series, pct: float = 0.03) -> pd.Series:
    """True where *series_a* is within *pct* of *series_b*."""
    return (series_a - series_b).abs() / series_a < pct


def _rolling_quantile(series: pd.Series, window: int, q: float = 0.75) -> pd.Series:
    """Rolling *q*-quantile of *series* over *window* bars."""
    return series.rolling(window).quantile(q)
