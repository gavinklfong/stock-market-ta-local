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


class TestComputeFutureReturns:
    def test_length(self):
        _, _, closes = _make_sample(50)
        result = compute_future_returns(closes)
        for h in result:
            assert len(result[h]) == 50

    def test_short_data(self):
        closes = [100.0 + i for i in range(5)]
        result = compute_future_returns(closes, horizons=(5,))
        assert result[5] == [None] * 5

    def test_first_element_has_return(self):
        closes = [100.0, 102.0, 104.0, 106.0, 108.0, 110.0]
        result = compute_future_returns(closes, horizons=(5,))
        assert result[5][0] is not None

    def test_last_rows_none(self):
        closes = [100.0 + i for i in range(20)]
        result = compute_future_returns(closes, horizons=(5, 10))
        # Last 5 rows should be None for 5d horizon
        for i in range(15, 20):
            assert result[5][i] is None
        # Last 10 rows should be None for 10d horizon
        for i in range(10, 20):
            assert result[10][i] is None
        # Earlier rows should have values
        assert result[5][0] is not None
        assert result[10][0] is not None

    def test_positive_return_uptrend(self):
        """Uptrend should produce positive returns."""
        closes = [100.0 + i for i in range(30)]
        result = compute_future_returns(closes, horizons=(5, 10))
        for h in result:
            for i in range(len(closes) - h):
                assert result[h][i] > 0

    def test_negative_return_downtrend(self):
        """Downtrend should produce negative returns."""
        closes = [100.0 - i for i in range(30)]
        result = compute_future_returns(closes, horizons=(5, 10))
        for h in result:
            for i in range(len(closes) - h):
                assert result[h][i] < 0

    def test_constant_prices_zero_return(self):
        """Constant prices should produce zero returns."""
        closes = [100.0] * 20
        result = compute_future_returns(closes, horizons=(5,))
        for i in range(len(closes) - 5):
            assert result[5][i] == 0.0

    def test_multiple_horizons(self):
        """Multiple horizons should all be present."""
        closes = [100.0 + i * 0.5 for i in range(50)]
        horizons = (5, 10, 20)
        result = compute_future_returns(closes, horizons=horizons)
        for h in horizons:
            assert h in result
            assert len(result[h]) == 50

    def test_return_formula(self):
        """Return should match (future_close - close) / close."""
        closes = [100.0, 105.0, 110.0, 115.0, 120.0, 125.0]
        result = compute_future_returns(closes, horizons=(1,))
        # 1-day return at index 0: (105 - 100) / 100 = 0.05
        assert result[1][0] == pytest.approx(0.05, abs=1e-10)
        # 1-day return at index 1: (110 - 105) / 105 ≈ 0.0476
        assert result[1][1] == pytest.approx(5.0 / 105, abs=1e-10)

    def test_horizon_5_returns_larger_than_1(self):
        """In a strong trend, 5d return should exceed 1d return."""
        closes = [100.0 + i for i in range(30)]
        result = compute_future_returns(closes, horizons=(1, 5))
        # At index 0, 5d return should be 5x the 1d return
        assert result[5][0] == pytest.approx(result[1][0] * 5, abs=1e-10)


