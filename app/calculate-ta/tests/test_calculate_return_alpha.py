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


class TestComputeAlphaBeta:
    def test_length(self):
        closes = [100.0 + i * 0.5 for i in range(100)]
        bench = [50.0 + i * 0.3 for i in range(100)]
        result = compute_alpha_beta(closes, bench, window=20)
        assert len(result["alpha"]) == 100
        assert len(result["beta"]) == 100

    def test_first_rows_none(self):
        """First window rows should be None (returns start at index 1, need 20 returns)."""
        closes = [100.0 + i for i in range(50)]
        bench = [50.0 + i for i in range(50)]
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20):
            assert result["alpha"][i] is None
            assert result["beta"][i] is None

    def test_first_valid_at_window(self):
        """First non-None value should be at index=window."""
        closes = [100.0 + i for i in range(50)]
        bench = [50.0 + i for i in range(50)]
        result = compute_alpha_beta(closes, bench, window=20)
        assert result["alpha"][20] is not None
        assert result["beta"][20] is not None

    def test_perfect_correlation_beta_1(self):
        """If stock and benchmark have identical % changes, beta should be ~1.0."""
        np.random.seed(42)
        closes = [100.0]
        bench = [50.0]
        for _ in range(99):
            noise = np.random.normal(0, 0.005)
            closes.append(closes[-1] * (1.01 + noise))
            bench.append(bench[-1] * (1.01 + noise))
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["beta"][i] == pytest.approx(1.0, abs=0.01)

    def test_perfect_correlation_alpha_zero(self):
        """Identical % changes → alpha should be ~0."""
        np.random.seed(42)
        closes = [100.0]
        bench = [50.0]
        for _ in range(99):
            noise = np.random.normal(0, 0.005)
            closes.append(closes[-1] * (1.01 + noise))
            bench.append(bench[-1] * (1.01 + noise))
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["alpha"][i] == pytest.approx(0.0, abs=0.05)

    def test_outperformance_positive_alpha(self):
        """Stock with higher % return than benchmark → positive alpha."""
        np.random.seed(42)
        closes = [100.0]
        bench = [100.0]
        for _ in range(99):
            noise = np.random.normal(0, 0.005)
            closes.append(closes[-1] * (1.02 + noise))  # 2% daily
            bench.append(bench[-1] * (1.01 + noise))     # 1% daily
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["alpha"][i] > 0

    def test_underperformance_negative_alpha(self):
        """Stock with lower % return than benchmark → negative alpha."""
        np.random.seed(42)
        closes = [100.0]
        bench = [100.0]
        for _ in range(99):
            noise = np.random.normal(0, 0.005)
            closes.append(closes[-1] * (1.01 + noise))  # 1% daily
            bench.append(bench[-1] * (1.02 + noise))    # 2% daily
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["alpha"][i] < 0

    def test_high_beta(self):
        """Stock with 2x volatility of benchmark → beta ~2."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        bench = [100.0]
        for _ in range(n - 1):
            noise = np.random.normal(0, 0.015)  # shared noise
            s_ret = 0.01 + noise * 2             # 2x noise → 2x vol
            b_ret = 0.005 + noise                # baseline
            closes.append(closes[-1] * (1 + s_ret))
            bench.append(bench[-1] * (1 + b_ret))
        result = compute_alpha_beta(closes, bench, window=20)
        assert result["beta"][20] > 1.0

    def test_negative_beta(self):
        """Inverted return pattern → negative beta."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        bench = [100.0]
        for i in range(n - 1):
            base_ret = 0.01
            noise = np.random.normal(0, 0.015)
            s_ret = base_ret + noise          # positive correlation with noise
            b_ret = base_ret - noise          # opposite sign on noise
            closes.append(closes[-1] * (1 + s_ret))
            bench.append(bench[-1] * (1 + b_ret))
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["beta"][i] < 0

    def test_constant_benchmark(self):
        """Constant benchmark (zero variance) should give beta=0."""
        closes = [100.0 + i for i in range(100)]
        bench = [50.0] * 100
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["beta"][i] == 0.0

    def test_short_data_all_none(self):
        """Data shorter than window should produce all None."""
        closes = [100.0 + i for i in range(10)]
        bench = [50.0 + i for i in range(10)]
        result = compute_alpha_beta(closes, bench, window=20)
        assert all(v is None for v in result["alpha"])
        assert all(v is None for v in result["beta"])

    def test_multiple_windows(self):
        """Different window sizes should produce different results."""
        closes = [100.0 + i * 0.5 for i in range(100)]
        bench = [50.0 + i * 0.3 for i in range(100)]
        r20 = compute_alpha_beta(closes, bench, window=20)
        r50 = compute_alpha_beta(closes, bench, window=50)
        # 50-window should have more None values at the start
        none_count_20 = sum(1 for v in r20["alpha"] if v is None)
        none_count_50 = sum(1 for v in r50["alpha"] if v is None)
        assert none_count_50 > none_count_20

    def test_default_window(self):
        """Default window should be 20."""
        closes = [100.0 + i for i in range(50)]
        bench = [50.0 + i for i in range(50)]
        result = compute_alpha_beta(closes, bench)
        # First 20 should be None (default window=20, returns start at index 1)
        assert result["alpha"][20] is not None


# ---------------------------------------------------------------------------
# TestComputeReturnColumns
# ---------------------------------------------------------------------------


