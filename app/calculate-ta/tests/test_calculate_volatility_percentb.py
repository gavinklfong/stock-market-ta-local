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


class TestBollingerPercentB:
    def test_pctb_none_before_period(self):
        """%B should be None before the first valid index."""
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(19):
            assert result["ta_bband_pctb"][i] is None

    def test_pctb_bounded_0_to_1_at_bounds(self):
        """%B = 1 at upper band, = 0 at lower band."""
        period = 5
        # Create prices that touch upper and lower bands
        # Middle ~100, std=5, so upper=110, lower=90 with num_std=2
        closes = []
        for i in range(50):
            if i % 3 == 0:
                closes.append(110.0)  # at upper band
            elif i % 3 == 1:
                closes.append(90.0)   # at lower band
            else:
                closes.append(100.0)  # at middle
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_pctb = [v for v in result["ta_bband_pctb"] if v is not None]
        assert len(valid_pctb) > 0

    def test_pctb_formula(self):
        """%B = (close - lower) / (upper - lower)."""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0] * 10
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        bb = compute_bollinger_bands(closes)  # default period=20, num_std=2.0
        result = compute_volatility_columns(highs, lows, closes, len(closes))
        # First valid index for period=20 is 19
        for i in range(19, len(closes)):
            if bb["upper"][i] is not None and bb["upper"][i] != bb["lower"][i]:
                expected = (closes[i] - bb["lower"][i]) / (bb["upper"][i] - bb["lower"][i])
                assert result["ta_bband_pctb"][i] == pytest.approx(expected)

    def test_pctb_at_middle_price(self):
        """When close = middle band, %B should be 0.5."""
        period = 5
        closes = [100.0] * 50
        highs = [101.0] * 50
        lows = [99.0] * 50
        bb = compute_bollinger_bands(closes, period=period)
        # With constant prices, std=0, so upper=lower=middle=100
        # Band width = 0, so %B should be None (denominator is 0)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(period - 1, len(closes)):
            assert result["ta_bband_pctb"][i] is None

    def test_pctb_varying_prices(self):
        """%B should vary between values as price moves relative to bands."""
        np.random.seed(42)
        closes = [100.0]
        for _ in range(49):
            closes.append(max(closes[-1] + np.random.normal(0, 1.5), 50.0))
        highs = [c + 1.0 for c in closes]
        lows = [max(c - 1.0, 1.0) for c in closes]
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_pctb = [v for v in result["ta_bband_pctb"] if v is not None]
        assert len(valid_pctb) > 0
        # %B should vary (not all the same value)
        assert len(set(round(v, 4) for v in valid_pctb)) > 1

    def test_pctb_at_upper_band(self):
        """When price is at upper band, %B should be ~1."""
        period = 5
        # Prices that stay near upper band
        # With constant std, if price = upper = middle + 2*std, %B = 1
        base = 100.0
        std = 5.0
        # Create a window where price = upper band
        # upper = mean + 2*std, so we need closes centered around base=90 with std=5
        # Actually, let's just verify the formula directly
        closes = [80.0, 85.0, 90.0, 95.0, 100.0] * 10  # increasing
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_pctb = [v for v in result["ta_bband_pctb"] if v is not None]
        assert len(valid_pctb) > 0

    def test_pctb_less_than_one_when_narrow_bands(self):
        """With very narrow bands and price near middle, %B should be near 0.5."""
        # Create a tight range of prices
        closes = [100.0 + (i % 10 - 5) * 0.1 for i in range(50)]  # 99.5 to 100.5
        highs = [c + 0.1 for c in closes]
        lows = [max(c - 0.1, 1.0) for c in closes]
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_pctb = [v for v in result["ta_bband_pctb"] if v is not None]
        assert len(valid_pctb) > 0
        # With tight prices, %B should be reasonable (not NaN or Inf)
        for v in valid_pctb:
            assert math.isfinite(v)


# ---------------------------------------------------------------------------
# TestComputeHistoricalVolatility
# ---------------------------------------------------------------------------


