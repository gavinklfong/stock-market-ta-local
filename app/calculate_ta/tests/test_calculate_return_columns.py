"""Unit tests for calculate_return.py — verifies forward-looking return computations."""

import os
import math

import numpy as np
import pandas as pd
import pytest

from calculate_return import (
    compute_alpha_beta,
    compute_future_returns,
    compute_past_performance,
    compute_return_columns,
    process_csv,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sample(n=50, base_price=100.0, base_range=2.0):
    """Generate aligned OHLC data for testing."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 1.0)
        closes.append(max(closes[-1] + change, 10.0))

    highs = [c + abs(np.random.normal(0, base_range / 2)) for c in closes]
    lows = [max(c - abs(np.random.normal(0, base_range / 2)), 1.0) for c in closes]

    return highs, lows, closes


def _make_dates(n):
    """Generate n consecutive dates starting from 2024-01-01."""
    return [pd.Timestamp("2024-01-01") + pd.Timedelta(days=i) for i in range(n)]


# ---------------------------------------------------------------------------
# TestComputeFutureReturns
# ---------------------------------------------------------------------------


class TestComputeReturnColumns:
    def test_expected_keys(self):
        highs, lows, closes = _make_sample(50)
        cols = compute_return_columns(highs, lows, closes, [1000] * 50, 50, _make_dates(50))
        expected = {
            "ta_return_5d",
            "ta_return_10d",
            "ta_return_20d",
            "ta_performance_1m",
            "ta_performance_3m",
            "ta_performance_6m",
            "ta_performance_1y",
        }
        assert set(cols.keys()) == expected

    def test_all_same_length(self):
        highs, lows, closes = _make_sample(50)
        cols = compute_return_columns(highs, lows, closes, [1000] * 50, 50, _make_dates(50))
        for col in cols.values():
            assert len(col) == 50

    def test_short_data(self):
        n = 5
        cols = compute_return_columns(
            [100.0] * n, [90.0] * n, [95.0] * n, [1000] * n, n, _make_dates(n)
        )
        for col in cols.values():
            assert all(v is None for v in col)

    def test_with_realistic_data(self):
        np.random.seed(42)
        n = 200
        base = 150.0
        closes = [base]
        for _ in range(n - 1):
            change = np.random.normal(0, 1.5)
            closes.append(max(closes[-1] + change, 50.0))

        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]
        volumes = [int(1e6 * np.random.uniform(0.8, 1.2)) for _ in closes]

        cols = compute_return_columns(highs, lows, closes, volumes, n, _make_dates(n))

        # 5d return should have some non-None values
        valid_5d = [v for v in cols["ta_return_5d"] if v is not None]
        assert len(valid_5d) > 0

        # 20d return should have fewer non-None values
        valid_20d = [v for v in cols["ta_return_20d"] if v is not None]
        assert len(valid_20d) > 0
        assert len(valid_5d) > len(valid_20d)

    def test_positive_returns_in_uptrend(self):
        """Strong uptrend should produce positive returns across horizons."""
        n = 50
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [1000] * n

        cols = compute_return_columns(highs, lows, closes, volumes, n, _make_dates(n))
        for h in (5, 10, 20):
            col_name = f"ta_return_{h}d"
            valid = [v for v in cols[col_name] if v is not None]
            assert all(v > 0 for v in valid)


# ---------------------------------------------------------------------------
# TestProcessCSV
# ---------------------------------------------------------------------------


