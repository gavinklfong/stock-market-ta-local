"""Tests for today's-date recalculation behavior.

These tests verify that when the last row of input data matches today's date,
process_csv always forces a full recomputation -- replacing any existing entry
for that date even when the row count hasn't changed.

This ensures today's indicators are always up to date as new intraday data
arrives (or when the OHLCV CSV is updated).
"""

import os
import tempfile
from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

# All 7 modules
from calculate_trend import process_csv as trend_process_csv
from calculate_momentum import process_csv as momentum_process_csv
from calculate_volume import process_csv as volume_process_csv
from calculate_volatility import process_csv as volatility_process_csv
from calculate_regime import process_csv as regime_process_csv
from calculate_structure import process_csv as structure_process_csv
from calculate_return import process_csv as return_process_csv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(n=100, base_price=100.0, noise_range=0.01, end_date=None):
    """Generate OHLCV data as a DataFrame.

    Parameters
    ----------
    n : int
        Number of trading days.
    base_price : float
        Starting price.
    noise_range : float
        Max percentage change per bar.
    end_date : str or None
        If given, the last date is set to this value (useful for testing
        "today's date" scenarios).  The date range is generated backwards
        from end_date.
    """
    np.random.seed(42)
    if end_date is not None:
        start_date = pd.Timestamp(end_date) - timedelta(days=n)
        dates = pd.date_range(start=start_date, periods=n, freq="B")
        dates = dates[:n]  # safety
    else:
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, noise_range) * closes[-1]
        closes.append(max(closes[-1] + change, 10.0))

    opens = [c * (1 + np.random.uniform(-0.005, 0.005)) for c in closes]
    highs = [o * (1 + abs(np.random.normal(0, 0.005))) for o in opens]
    lows = [o * (1 - abs(np.random.normal(0, 0.005))) for o in opens]
    volumes = [int(1e6 * abs(np.random.normal(1, 0.1))) for _ in range(n)]

    return pd.DataFrame({
        "Date": dates, "Open": opens, "High": highs,
        "Low": lows, "Close": closes, "Volume": volumes,
    })


def _make_ohlcv_with_today(n=100):
    """Generate OHLCV where the LAST row has *today's* date."""
    df = _make_ohlcv(n=n)
    today_str = pd.Timestamp(pd.Timestamp.now().date()).strftime("%Y-%m-%d")
    df.loc[df.index[-1], "Date"] = pd.Timestamp(today_str)
    df = df.sort_values("Date").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Shared helper used by all test classes
# ---------------------------------------------------------------------------

def _test_today_recalculation(process_fn, module_name):
    """Run all three today-recalculation tests for a given module."""
    results = []

    # Test 1: recomputes when last date is today
    df = _make_ohlcv_with_today(n=100)
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.csv")
        df.to_csv(input_path, index=False)

        rows = process_fn(input_path, output_path, 1, 1)
        assert rows == 100

        out = pd.read_csv(output_path)
        last_row_before = out.iloc[-1].to_dict()

        # Modify last row's closing price
        df2 = _make_ohlcv_with_today(n=100)
        df2.loc[df2.index[-1], "Close"] *= 1.01

        df2.to_csv(input_path, index=False)
        process_fn(input_path, output_path, 1, 1)

        out2 = pd.read_csv(output_path)
        last_row_after = out2.iloc[-1].to_dict()

        changed_cols = []
        for col in out2.columns:
            v1 = last_row_before.get(col)
            v2 = last_row_after.get(col)
            if v1 is not None and v2 is not None:
                try:
                    if abs(float(v1) - float(v2)) > 1e-6:
                        changed_cols.append(col)
                except (ValueError, TypeError):
                    if str(v1) != str(v2):
                        changed_cols.append(col)

        assert len(changed_cols) > 0, (
            f"{module_name}: no indicators changed despite input "
            f"modification when last date is today"
        )
        results.append(("test_recomputes_when_last_date_is_today", True))

        # Test 2: recomputes with existing state and today
        process_fn(input_path, output_path, 1, 1)
        out = pd.read_csv(output_path)
        assert len(out) == 100
        ta_cols = [c for c in out.columns if c.startswith("ta_")]
        assert len(ta_cols) > 0, f"{module_name}: no ta_ columns in output"
        results.append(("test_recomputes_with_existing_state_and_today", True))

        # Test 3: no recomputation bypass when last date NOT today
        df3 = _make_ohlcv(n=100)
        with tempfile.TemporaryDirectory() as tmpdir2:
            input_path2 = os.path.join(tmpdir2, "input.csv")
            output_path2 = os.path.join(tmpdir2, "output.csv")
            df3.to_csv(input_path2, index=False)
            process_fn(input_path2, output_path2, 1, 1)
            process_fn(input_path2, output_path2, 1, 1)
            out3 = pd.read_csv(output_path2)
            assert len(out3) == 100
            results.append(("test_no_recompute_when_last_date_not_today", True))

    return results


# ---------------------------------------------------------------------------
# Individual test classes -- one per module
# ---------------------------------------------------------------------------

class TestTrendTodayRecalculation:
    def test_recomputes_when_last_date_is_today(self):
        """Trend: last date today forces full recomputation."""
        _test_today_recalculation(trend_process_csv, "trend")[0]

    def test_recomputes_with_existing_state_and_today(self):
        """Trend: existing state + today date forces full recomputation."""
        _test_today_recalculation(trend_process_csv, "trend")[1]

    def test_no_recompute_when_last_date_not_today(self):
        """Trend: last date not today uses normal incremental logic."""
        _test_today_recalculation(trend_process_csv, "trend")[2]


class TestMomentumTodayRecalculation:
    def test_recomputes_when_last_date_is_today(self):
        """Momentum: last date today forces full recomputation."""
        _test_today_recalculation(momentum_process_csv, "momentum")[0]

    def test_recomputes_with_existing_state_and_today(self):
        """Momentum: existing state + today date forces full recomputation."""
        _test_today_recalculation(momentum_process_csv, "momentum")[1]

    def test_no_recompute_when_last_date_not_today(self):
        """Momentum: last date not today uses normal incremental logic."""
        _test_today_recalculation(momentum_process_csv, "momentum")[2]


class TestVolumeTodayRecalculation:
    def test_recomputes_when_last_date_is_today(self):
        """Volume: last date today forces full recomputation."""
        _test_today_recalculation(volume_process_csv, "volume")[0]

    def test_recomputes_with_existing_state_and_today(self):
        """Volume: existing state + today date forces full recomputation."""
        _test_today_recalculation(volume_process_csv, "volume")[1]

    def test_no_recompute_when_last_date_not_today(self):
        """Volume: last date not today uses normal incremental logic."""
        _test_today_recalculation(volume_process_csv, "volume")[2]


class TestVolatilityTodayRecalculation:
    def test_recomputes_when_last_date_is_today(self):
        """Volatility: last date today forces full recomputation."""
        _test_today_recalculation(volatility_process_csv, "volatility")[0]

    def test_recomputes_with_existing_state_and_today(self):
        """Volatility: existing state + today date forces full recomputation."""
        _test_today_recalculation(volatility_process_csv, "volatility")[1]

    def test_no_recompute_when_last_date_not_today(self):
        """Volatility: last date not today uses normal incremental logic."""
        _test_today_recalculation(volatility_process_csv, "volatility")[2]


class TestRegimeTodayRecalculation:
    def test_recomputes_when_last_date_is_today(self):
        """Regime: last date today forces full recomputation."""
        _test_today_recalculation(regime_process_csv, "regime")[0]

    def test_recomputes_with_existing_state_and_today(self):
        """Regime: existing state + today date forces full recomputation."""
        _test_today_recalculation(regime_process_csv, "regime")[1]

    def test_no_recompute_when_last_date_not_today(self):
        """Regime: last date not today uses normal incremental logic."""
        _test_today_recalculation(regime_process_csv, "regime")[2]


class TestStructureTodayRecalculation:
    def test_recomputes_when_last_date_is_today(self):
        """Structure: last date today forces full recomputation."""
        _test_today_recalculation(structure_process_csv, "structure")[0]

    def test_recomputes_with_existing_state_and_today(self):
        """Structure: existing state + today date forces full recomputation."""
        _test_today_recalculation(structure_process_csv, "structure")[1]

    def test_no_recompute_when_last_date_not_today(self):
        """Structure: last date not today uses normal incremental logic."""
        _test_today_recalculation(structure_process_csv, "structure")[2]


class TestReturnTodayRecalculation:
    def test_recomputes_when_last_date_is_today(self):
        """Return: last date today forces full recomputation."""
        _test_today_recalculation(return_process_csv, "return")[0]

    def test_recomputes_with_existing_state_and_today(self):
        """Return: existing state + today date forces full recomputation."""
        _test_today_recalculation(return_process_csv, "return")[1]

    def test_no_recompute_when_last_date_not_today(self):
        """Return: last date not today uses normal incremental logic."""
        _test_today_recalculation(return_process_csv, "return")[2]
