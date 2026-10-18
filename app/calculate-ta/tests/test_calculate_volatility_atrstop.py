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


class TestComputeATRStopDistance:
    def test_length(self):
        highs, lows, closes = _make_sample(n=50)
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_atr_stop_distance(closes, atr, multiplier=3.0)
        assert len(result) == 50

    def test_first_values_are_none(self):
        """ATR Stop Distance should be None where ATR is None."""
        highs, lows, closes = _make_sample(n=50)
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_atr_stop_distance(closes, atr, multiplier=3.0)
        for i in range(14):
            assert result[i] is None

    def test_positive_with_varying_prices(self):
        """ATR Stop Distance should be positive when prices vary."""
        highs, lows, closes = _make_sample(n=100)
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_atr_stop_distance(closes, atr, multiplier=3.0)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v > 0

    def test_zero_with_constant_prices(self):
        """With constant prices, ATR is constant and stop dist is a fixed percentage."""
        closes = [100.0] * 50
        highs = [105.0] * 50
        lows = [95.0] * 50
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_atr_stop_distance(closes, atr, multiplier=3.0)
        # ATR should be 10 (high - low) for all bars
        # Stop dist = 3 * 10 / 100 * 100 = 30%
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(30.0)

    def test_custom_multiplier(self):
        """Stop distance scales linearly with multiplier."""
        closes = [100.0] * 50
        highs = [105.0] * 50
        lows = [95.0] * 50
        atr = compute_atr(highs, lows, closes, 14)
        result_2 = compute_atr_stop_distance(closes, atr, multiplier=2.0)
        result_4 = compute_atr_stop_distance(closes, atr, multiplier=4.0)
        valid_2 = [v for v in result_2 if v is not None]
        valid_4 = [v for v in result_4 if v is not None]
        assert len(valid_2) > 0
        for v2, v4 in zip(valid_2, valid_4):
            assert v4 == pytest.approx(v2 * 2.0)

    def test_formula(self):
        """Verify stop distance = (multiplier * ATR / close) * 100."""
        # Deterministic case: flat close=100, constant ATR=5
        closes = [100.0] * 30
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 5.0
        result = compute_atr_stop_distance(closes, atr, multiplier=2.0)
        # stop_dist = 2 * 5 / 100 * 100 = 10%
        for i in range(14, 30):
            assert result[i] == pytest.approx(10.0)

    def test_short_series_returns_all_none(self):
        """When no ATR values are available, all results are None."""
        closes = [100.0, 101.0, 102.0]
        atr = [None, None, None]
        result = compute_atr_stop_distance(closes, atr, multiplier=3.0)
        assert all(v is None for v in result)

    def test_none_close_returns_none(self):
        """When close is None, stop distance should be None."""
        closes = [100.0, None, 102.0]
        atr = [5.0, 5.0, 5.0]
        result = compute_atr_stop_distance(closes, atr, multiplier=3.0)
        assert result[0] == pytest.approx((3.0 * 5.0 / 100.0) * 100)
        assert result[1] is None
        assert result[2] == pytest.approx((3.0 * 5.0 / 102.0) * 100)

    def test_increasing_atr_increases_stop_distance(self):
        """When ATR increases, stop distance should increase."""
        np.random.seed(99)
        n = 100
        closes = [100.0]
        highs = [101.0]
        lows = [99.0]
        for i in range(1, n):
            widening = i * 0.3  # range widens over time
            change = np.random.normal(0, 0.5)
            close = max(closes[-1] + change, 50.0)
            closes.append(close)
            highs.append(max(highs[-1], close) + widening)
            lows.append(max(min(lows[-1], close) - widening, 1.0))
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_atr_stop_distance(closes, atr, multiplier=3.0)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Last value should be higher than first (ATR widening)
        assert valid[-1] > valid[0]


# ---------------------------------------------------------------------------
# TestComputeATRPositionSize
# ---------------------------------------------------------------------------


