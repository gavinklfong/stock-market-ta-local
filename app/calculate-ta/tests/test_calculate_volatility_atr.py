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


class TestComputeATR:
    def test_length(self):
        highs, lows, closes = _make_sample(n=30, base_price=100.0, base_range=5.0)
        result = compute_atr(highs, lows, closes, period=14)
        assert len(result) == 30

    def test_first_values_are_none(self):
        highs, lows, closes = _make_sample(n=30, base_price=100.0, base_range=5.0)
        result = compute_atr(highs, lows, closes, period=14)
        # ATR needs at least `period` true range values; first valid at index `period`
        for i in range(14):
            assert result[i] is None

    def test_first_valid_atr_value(self):
        # Use a simple deterministic case: flat high/low with constant range
        highs = [105.0] * 30
        lows = [95.0] * 30
        closes = [100.0] * 30
        result = compute_atr(highs, lows, closes, period=14)
        # First valid ATR at index 14
        assert result[14] is not None
        # With flat highs/lows, True Range = high - low = 10 for all rows
        # Initial ATR = average of first 14 TRs = 10
        assert result[14] == pytest.approx(10.0)

    def test_increasing_atr(self):
        """With widening range, ATR should increase over time."""
        np.random.seed(99)
        n = 50
        base = 100.0
        closes = [base]
        highs = [base + 1.0]
        lows = [base - 1.0]
        for i in range(1, n):
            widening = i * 0.2  # range grows over time
            close = closes[-1] + np.random.normal(0, 1.0)
            closes.append(close)
            highs.append(max(highs[-1], close) + widening)
            lows.append(min(lows[-1], close) - widening)

        result = compute_atr(highs, lows, closes, period=14)
        # ATR should generally be increasing
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] > valid[0]

    def test_short_series_returns_all_none(self):
        """When series is shorter than period + 1, all values are None."""
        highs = [100.0, 101.0, 102.0]
        lows = [98.0, 99.0, 100.0]
        closes = [99.0, 100.0, 101.0]
        result = compute_atr(highs, lows, closes, period=14)
        assert all(v is None for v in result)

    def test_atr_with_gap_down(self):
        """ATR should capture large true range from price gap."""
        highs = [100, 100, 90]
        lows = [90, 90, 80]
        closes = [95, 95, 85]
        result = compute_atr(highs, lows, closes, period=2)
        assert result[2] == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# TestComputeBollingerBands
# ---------------------------------------------------------------------------


