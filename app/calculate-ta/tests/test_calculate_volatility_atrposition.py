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


class TestComputeATRPositionSize:
    def test_length(self):
        highs, lows, closes = _make_sample(n=50)
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=3.0)
        assert len(result) == 50

    def test_first_values_are_none(self):
        """Position size should be None where ATR is None."""
        highs, lows, closes = _make_sample(n=50)
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=3.0)
        for i in range(14):
            assert result[i] is None

    def test_positive_with_varying_prices(self):
        """Position size should be positive when prices vary."""
        highs, lows, closes = _make_sample(n=100)
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=3.0)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v > 0

    def test_formula(self):
        """Verify position_size_pct = risk_pct / stop_distance_pct * 100."""
        # Deterministic case: flat close=100, constant ATR=5
        closes = [100.0] * 30
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 5.0
        # stop_distance = 3 * 5 / 100 * 100 = 15%
        # position_size = 2.0 / 15 * 100 = 13.33...%
        result = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=3.0)
        expected = 2.0 / 15.0 * 100  # ≈ 13.33%
        for i in range(14, 30):
            assert result[i] == pytest.approx(expected, rel=1e-5)

    def test_custom_risk_pct(self):
        """Position size scales linearly with risk_pct."""
        closes = [100.0] * 30
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 5.0
        result_1 = compute_atr_position_size(closes, atr, risk_pct=1.0, multiplier=3.0)
        result_4 = compute_atr_position_size(closes, atr, risk_pct=4.0, multiplier=3.0)
        valid_1 = [v for v in result_1 if v is not None]
        valid_4 = [v for v in result_4 if v is not None]
        assert len(valid_1) > 0
        for v1, v4 in zip(valid_1, valid_4):
            assert v4 == pytest.approx(v1 * 4.0)

    def test_custom_multiplier(self):
        """Position size is inversely proportional to multiplier."""
        closes = [100.0] * 30
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 5.0
        result_2 = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=2.0)
        result_4 = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=4.0)
        valid_2 = [v for v in result_2 if v is not None]
        valid_4 = [v for v in result_4 if v is not None]
        assert len(valid_2) > 0
        # With 2×ATR, stop_distance is half → position is double
        for v2, v4 in zip(valid_2, valid_4):
            assert v2 == pytest.approx(v4 * 2.0)

    def test_short_series_returns_all_none(self):
        """When no ATR values are available, all results are None."""
        closes = [100.0, 101.0, 102.0]
        atr = [None, None, None]
        result = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=3.0)
        assert all(v is None for v in result)

    def test_none_close_returns_none(self):
        """When close is None, position size should be None."""
        closes = [100.0, None, 102.0]
        atr = [5.0, 5.0, 5.0]
        result = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=3.0)
        expected = 2.0 / (3.0 * 5.0 / 100.0 * 100) * 100  # ≈ 13.33%
        assert result[0] == pytest.approx(expected)
        assert result[1] is None
        assert result[2] == pytest.approx(2.0 / (3.0 * 5.0 / 102.0 * 100) * 100)

    def test_higher_price_allows_larger_position(self):
        """When price is higher (same ATR%), position size should be larger."""
        # Price=100, ATR=5 → ATR% = 5%
        # Price=200, ATR=10 → ATR% = 5% → same position size
        closes = [100.0] * 30 + [200.0] * 30
        atr = [None] * 60
        for i in range(14, 30):
            atr[i] = 5.0
        for i in range(30 + 14, 60):
            atr[i] = 10.0
        result = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=3.0)
        valid_100 = [v for v in result[14:30] if v is not None]
        valid_200 = [v for v in result[44:60] if v is not None]
        assert len(valid_100) > 0
        assert len(valid_200) > 0
        # Both have same ATR% so position sizes should be equal
        assert valid_100[0] == pytest.approx(valid_200[0])

    def test_increasing_atr_decreases_position_size(self):
        """When ATR increases, position size should decrease (wider stop)."""
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
        result = compute_atr_position_size(closes, atr, risk_pct=2.0, multiplier=3.0)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Position size should decrease as ATR widens
        assert valid[-1] < valid[0]


# ---------------------------------------------------------------------------
# TestComputeRRRatio
# ---------------------------------------------------------------------------


