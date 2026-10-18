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


class TestComputeBollingerBands:
    def test_length(self):
        closes = _make_sample(n=50)[2]
        result = compute_bollinger_bands(closes, period=20)
        assert len(result["upper"]) == 50
        assert len(result["middle"]) == 50
        assert len(result["lower"]) == 50

    def test_first_values_are_none(self):
        closes = _make_sample(n=50)[2]
        result = compute_bollinger_bands(closes, period=20)
        for i in range(19):  # 0-indexed, first valid at index 19 (20th element)
            assert result["middle"][i] is None
            assert result["upper"][i] is None
            assert result["lower"][i] is None

    def test_first_valid_value_equals_sma(self):
        """At first valid index, middle band equals SMA of window."""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0] * 5
        period = 5
        result = compute_bollinger_bands(closes, period=period)
        first_valid = result["middle"][period - 1]
        expected_sma = sum(closes[:period]) / period
        assert first_valid == pytest.approx(expected_sma)

    def test_upper_and_lower_are_symmetric(self):
        """Upper band should be middle + k*std, lower should be middle - k*std."""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0] * 10
        period = 5
        num_std = 2.0
        result = compute_bollinger_bands(closes, period=period, num_std=num_std)
        for i in range(period - 1, len(closes)):
            if result["middle"][i] is not None:
                assert result["upper"][i] == pytest.approx(result["middle"][i] + num_std * self._std(closes, i, period))
                assert result["lower"][i] == pytest.approx(result["middle"][i] - num_std * self._std(closes, i, period))

    def test_upper_below_lower(self):
        """Upper band should always be >= lower band."""
        closes = _make_sample(n=100)[2]
        result = compute_bollinger_bands(closes, period=20)
        for i in range(len(closes)):
            if result["upper"][i] is not None and result["lower"][i] is not None:
                assert result["upper"][i] >= result["lower"][i]

    def test_short_series_returns_all_none(self):
        """When series is shorter than period, all values are None."""
        closes = [100.0, 101.0, 102.0]
        result = compute_bollinger_bands(closes, period=20)
        assert all(v is None for v in result["middle"])

    def _std(self, closes, end_idx, period):
        """Compute population std of the window ending at end_idx."""
        window = [float(closes[j]) for j in range(end_idx - period + 1, end_idx + 1)]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        return math.sqrt(variance)

    def test_constant_prices(self):
        """With constant prices, std=0 so upper=lower=middle."""
        closes = [50.0] * 30
        result = compute_bollinger_bands(closes, period=10)
        for i in range(9, len(closes)):
            assert result["middle"][i] == pytest.approx(50.0)
            assert result["upper"][i] == pytest.approx(50.0)
            assert result["lower"][i] == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# TestComputeVolatilityColumns
# ---------------------------------------------------------------------------


