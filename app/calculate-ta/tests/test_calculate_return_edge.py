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


class TestEdgeCases:
    def test_single_value(self):
        cols = compute_return_columns([100.0], [90.0], [95.0], [1000], 1, _make_dates(1))
        assert cols["ta_return_5d"] == [None]
        assert cols["ta_return_10d"] == [None]
        assert cols["ta_return_20d"] == [None]

    def test_two_values(self):
        cols = compute_return_columns([100.0, 105.0], [90.0, 95.0], [95.0, 100.0], [1000, 1100], 2, _make_dates(2))
        assert len(cols["ta_return_5d"]) == 2
        assert all(v is None for v in cols["ta_return_5d"])

    def test_constant_prices(self):
        """Constant prices should produce zero returns where horizon fits."""
        n = 25
        cols = compute_return_columns(
            [100.0] * n, [90.0] * n, [95.0] * n, [1000] * n, n, _make_dates(n)
        )
        # 5d return should be 0 where available
        for i in range(n - 5):
            assert cols["ta_return_5d"][i] == 0.0
        # Last 5 should be None
        for i in range(n - 5, n):
            assert cols["ta_return_5d"][i] is None

    def test_large_price_range(self):
        """Very large price swings should produce valid returns."""
        n = 30
        closes = [10.0]
        for _ in range(n - 1):
            closes.append(closes[-1] * (1 + np.random.uniform(-0.1, 0.2)))

        highs = [c * 1.02 for c in closes]
        lows = [c * 0.98 for c in closes]
        volumes = [1000] * n

        cols = compute_return_columns(highs, lows, closes, volumes, n, _make_dates(n))

        valid_5d = [v for v in cols["ta_return_5d"] if v is not None]
        assert len(valid_5d) > 0
        for v in valid_5d:
            assert math.isfinite(v)

    def test_very_small_returns(self):
        """Tiny price changes should produce small returns."""
        n = 30
        closes = [100.0 + i * 0.001 for i in range(n)]
        highs = [c + 0.001 for c in closes]
        lows = [c - 0.001 for c in closes]
        volumes = [1000] * n

        cols = compute_return_columns(highs, lows, closes, volumes, n, _make_dates(n))

        valid_5d = [v for v in cols["ta_return_5d"] if v is not None]
        assert len(valid_5d) > 0
        # 5d return for tiny increments should be small positive
        assert all(v > 0 for v in valid_5d)
