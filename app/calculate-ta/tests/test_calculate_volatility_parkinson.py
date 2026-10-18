"""Unit tests for calculate_volatility.py — ATR, Bollinger Bands, Band Width, %B, Historical Volatility, Parkinson Volatility."""

import math
import os
import sys

import numpy as np
import pandas as pd
import pytest

from calculate_volatility import (
    compute_atr,
    compute_atr_position_size,
    compute_atr_stop_distance,
    compute_bollinger_bands,
    compute_historical_volatility,
    compute_parkinson_volatility,
    compute_rr_ratio,
    compute_volatility_columns,
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


# ---------------------------------------------------------------------------
# TestComputeATR
# ---------------------------------------------------------------------------


class TestComputeParkinsonVolatility:
    def test_length(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_parkinson_volatility(highs, lows, period=20)
        assert len(result) == 50

    def test_first_values_are_none(self):
        """Parkinson Vol needs at least `period` bars; first valid at index `period-1`."""
        highs, lows, closes = _make_sample(n=50)
        result = compute_parkinson_volatility(highs, lows, period=20)
        for i in range(19):
            assert result[i] is None

    def test_returns_positive_for_varying_prices(self):
        """Parkinson Vol should be positive when prices vary."""
        highs, lows, closes = _make_sample(n=100)
        result = compute_parkinson_volatility(highs, lows, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v > 0

    def test_short_series_returns_all_none(self):
        """When series is shorter than period, all values are None."""
        highs = [100.0, 101.0, 102.0]
        lows = [98.0, 99.0, 100.0]
        result = compute_parkinson_volatility(highs, lows, period=20)
        assert all(v is None for v in result)

    def test_annualization(self):
        """Annualized Parkinson Vol should be non_annualized * sqrt(252)."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(closes[-1] * (1 + np.random.normal(0, 0.01)))
        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]
        result_ann = compute_parkinson_volatility(highs, lows, period=20, annualize=True)
        result_raw = compute_parkinson_volatility(highs, lows, period=20, annualize=False)
        valid_ann = [v for v in result_ann if v is not None]
        valid_raw = [v for v in result_raw if v is not None]
        assert len(valid_ann) > 0
        assert len(valid_raw) > 0
        for a, r in zip(valid_ann, valid_raw):
            assert a == pytest.approx(r * math.sqrt(252))

    def test_increasing_with_widening_range(self):
        """Parkinson Vol should increase when high-low ranges widen."""
        np.random.seed(99)
        n = 100
        base = 100.0
        closes = [base]
        highs = [base + 1.0]
        lows = [base - 1.0]
        for i in range(1, n):
            widening = 0.3 * i  # range grows over time
            change = np.random.normal(0, 0.5)
            close = closes[-1] + change
            close = max(min(close, base + 10), base - 10)  # keep close near base
            closes.append(close)
            highs.append(max(highs[-1], close) + widening)
            lows.append(min(lows[-1], close) - widening)
            # Ensure lows stay positive
            lows[-1] = max(lows[-1], 1.0)
        result = compute_parkinson_volatility(highs, lows, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Average of last 5 should be higher than average of first 5
        assert sum(valid[-5:]) / 5 > sum(valid[:5]) / 5

    def test_formula_constant_range(self):
        """With constant high/low ratio, verify formula manually."""
        # Constant range ratio: high = 105, low = 95 for all bars
        n = 30
        highs = [105.0] * n
        lows = [95.0] * n
        period = 20
        result = compute_parkinson_volatility(highs, lows, period=period, annualize=False)
        # Manual: ln(105/95) = ln(1.10526...)
        hl_ratio = math.log(105.0 / 95.0)
        expected = math.sqrt((period * hl_ratio ** 2) / (4 * math.log(2) * period))
        # First valid at index 19
        assert result[period - 1] == pytest.approx(expected)

    def test_zero_when_low_equals_high(self):
        """When high == low for all bars, Parkinson Vol should be 0."""
        n = 30
        highs = [100.0] * n
        lows = [100.0] * n
        result = compute_parkinson_volatility(highs, lows, period=20, annualize=False)
        for i in range(19, n):
            assert result[i] == pytest.approx(0.0)

    def test_non_annualized_value(self):
        """Non-annualized Parkinson Vol should be a reasonable small positive number."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(closes[-1] * (1 + np.random.normal(0, 0.01)))
        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]
        result = compute_parkinson_volatility(highs, lows, period=20, annualize=False)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Daily vol is typically 0.5-5% for most stocks
        assert all(0 < v < 0.5 for v in valid)


# ---------------------------------------------------------------------------
# TestComputeATRStopDistance
# ---------------------------------------------------------------------------


