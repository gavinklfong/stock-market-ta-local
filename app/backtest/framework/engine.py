"""Core backtest engine — vectorbt-based with optional custom fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal

import numpy as np
import pandas as pd
import vectorbt as vbt
from vectorbt.portfolio.enums import SizeType

from .metrics import calculate_metrics

# Standard constants
INITIAL_CAPITAL = 100_000
COMMISSION = 0.001
SLIPPAGE = 0.001
DEFAULT_CUTOFF = pd.Timestamp("2016-10-15")  # ~10 years


class BacktestEngine:
    """Run backtests via vectorbt and collect metrics.

    Parameters
    ----------
    data_path : str | Path
        Path to the analysis-data CSV for a ticker.
    cutoff_date : pd.Timestamp | None
        Only analyse data on or after this date.  Pass None to use the
        full history.
    initial_capital : float
        Starting cash.
    commission : float
        Round-trip commission / slippage.
    trailing_pct : float | None
        If set, use TrailingStopPortfolio instead of regular Portfolio.
    """

    def __init__(
        self,
        data_path: str | Path,
        cutoff_date: pd.Timestamp | None = DEFAULT_CUTOFF,
        initial_capital: float = INITIAL_CAPITAL,
        commission: float = COMMISSION,
        slippage: float = SLIPPAGE,
        trailing_pct: float | None = None,
    ):
        self.data_path = Path(data_path)
        self.cutoff_date = cutoff_date
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.trailing_pct = trailing_pct
        self._df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def load_data(self) -> pd.DataFrame:
        """Load and clean the analysis-data CSV."""
        df = pd.read_csv(self.data_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        df = df.dropna(subset=["Close", "High", "Low"])
        df.index = df["Date"]

        if self.cutoff_date is not None:
            df = df[df["Date"] >= self.cutoff_date].reset_index(drop=True)
            df.index = df["Date"]

        self._df = df
        return df

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            self.load_data()
        return self._df

    # ------------------------------------------------------------------
    # Signal resolution
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_signal(signals) -> tuple[pd.Series, pd.Series]:
        """Accept either (entries, exits) or callables."""
        entries, exits = signals
        if callable(entries):
            entries = entries(df)  # type: ignore[name-defined]
        if callable(exits):
            exits = exits(df)
        return entries.astype(int), exits.astype(int)

    def get_signals(
        self,
        signal_fn: Callable,
        df: pd.DataFrame | None = None,
    ) -> tuple[pd.Series, pd.Series]:
        """Call a signal function and return (entries, exits) as int Series."""
        data = df or self.df
        signals = signal_fn(data)
        return self._resolve_signal(signals)

    # ------------------------------------------------------------------
    # Backtest execution
    # ------------------------------------------------------------------
    def run(
        self,
        signal_fn: Callable,
        df: pd.DataFrame | None = None,
    ) -> vbt.Portfolio:
        """Run a single backtest and return the vectorbt Portfolio."""
        entries, exits = self.get_signals(signal_fn, df)
        close = (df or self.df)["Close"]
        return self._run_from_signals(close, entries, exits)

    def _run_from_signals(
        self,
        close: pd.Series,
        entries: pd.Series,
        exits: pd.Series,
    ) -> vbt.Portfolio:
        """Execute the backtest engine given aligned series."""
        if self.trailing_pct is not None:
            return vbt.TrailingStopPortfolio.from_signals(
                close=close,
                entries=entries,
                exits=exits,
                init_cash=self.initial_capital,
                freq="1D",
                slippage=self.slippage,
                size=1.0,
                size_type=SizeType.Percent,
                fees=self.commission,
                trailing_pct=self.trailing_pct,
            )
        return vbt.Portfolio.from_signals(
            close=close,
            entries=entries,
            exits=exits,
            init_cash=self.initial_capital,
            freq="1D",
            slippage=self.slippage,
            size=1.0,
            size_type=SizeType.Percent,
            fees=self.commission,
        )

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def run_and_metrics(
        self,
        signal_fn: Callable,
        df: pd.DataFrame | None = None,
    ) -> tuple[vbt.Portfolio, dict]:
        """Run a backtest and return (portfolio, metrics_dict)."""
        pf = self.run(signal_fn, df)
        return pf, calculate_metrics(pf)

    def run_batch(
        self,
        signal_fns: dict[str, Callable],
    ) -> list[dict]:
        """Run multiple signals and return a list of result dicts."""
        results = []
        for name, sfn in signal_fns.items():
            pf, metrics = self.run_and_metrics(sfn)
            metrics["Strategy"] = name
            metrics["Portfolio"] = pf  # keep for report generation
            results.append(metrics)
        return results

    # ------------------------------------------------------------------
    # Returns extraction (for quantstats / benchmarking)
    # ------------------------------------------------------------------
    def get_benchmark_returns(self) -> pd.Series:
        """Buy-and-hold daily returns of the ticker."""
        return self.df["Close"].pct_change().dropna()

    def get_strategy_returns(
        self,
        signal_fn: Callable,
    ) -> pd.Series:
        """Daily returns from running a single strategy."""
        pf = self.run(signal_fn)
        return pf.daily_returns().dropna()

    def aligned_returns(
        self,
        strategy_ret: pd.Series,
    ) -> tuple[pd.Series, pd.Series]:
        """Return (strategy_ret, benchmark_ret) aligned to common index."""
        bench = self.get_benchmark_returns()
        idx = strategy_ret.index.intersection(bench.index)
        return strategy_ret.loc[idx], bench.loc[idx]
