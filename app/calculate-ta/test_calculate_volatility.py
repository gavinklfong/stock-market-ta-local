"""Unit tests for calculate_volatility.py — verifies ATR and Bollinger Bands calculations."""

import math
import os
import sys

import numpy as np
import pandas as pd
import pytest

from calculate_volatility import (
    compute_atr,
    compute_bollinger_bands,
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
        # Need n >= period + 1 = 3 for period=2
        # TR for i=0: 100-90 = 10
        # TR for i=1: max(100-90, |100-95|, |90-95|) = max(10,5,5) = 10
        # Initial ATR at i=2: avg(TR[0], TR[1]) = (10+10)/2 = 10
        highs = [100, 100, 90]
        lows = [90, 90, 80]
        closes = [95, 95, 85]
        result = compute_atr(highs, lows, closes, period=2)
        assert result[2] == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# TestComputeBollingerBands
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


class TestComputeVolatilityColumns:
    def test_returns_expected_keys(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        assert "ta_atr14" in result
        assert "ta_bband_upper" in result
        assert "ta_bband_middle" in result
        assert "ta_bband_lower" in result

    def test_column_lengths_match(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for key, values in result.items():
            assert len(values) == 50

    def test_atr_none_before_period(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(14):
            assert result["ta_atr14"][i] is None

    def test_bbands_none_before_period(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(19):
            assert result["ta_bband_upper"][i] is None
            assert result["ta_bband_lower"][i] is None

    def test_short_series(self):
        """When n < 20, Bollinger Bands should all be None; ATR depends on n."""
        highs, lows, closes = _make_sample(n=10)
        result = compute_volatility_columns(highs, lows, closes, 10)
        assert all(v is None for v in result["ta_bband_upper"])
        # ATR also needs >= period + 1
        assert all(v is None for v in result["ta_atr14"])
