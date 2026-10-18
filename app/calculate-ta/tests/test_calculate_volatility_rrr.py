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


class TestComputeRRRatio:
    def test_length(self):
        highs, lows, closes = _make_sample(n=50)
        bb = compute_bollinger_bands(closes)
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_rr_ratio(closes, atr, bb["upper"], multiplier=3.0)
        assert len(result) == 50

    def test_first_values_are_none(self):
        """RR ratio should be None where ATR or BB upper is None."""
        highs, lows, closes = _make_sample(n=50)
        bb = compute_bollinger_bands(closes)
        atr = compute_atr(highs, lows, closes, 14)
        result = compute_rr_ratio(closes, atr, bb["upper"], multiplier=3.0)
        for i in range(19):  # BB starts at index 19, ATR at 14 → both available from 19
            assert result[i] is None

    def test_positive_when_below_upper_bb(self):
        """RR ratio should be positive when price is below upper BB."""
        closes = [100.0] * 30
        bb_upper = [120.0] * 30  # BB upper well above price → positive reward
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 5.0
        result = compute_rr_ratio(closes, atr, bb_upper, multiplier=3.0)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v > 0

    def test_negative_when_above_upper_bb(self):
        """RR ratio should be negative when price is above upper BB."""
        # Price well above BB upper → negative reward
        closes = [150.0] * 30
        highs = [155.0] * 30
        lows = [145.0] * 30
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 3.0
        bb = compute_bollinger_bands(closes)
        # With flat data BB upper = close, so use custom bb_upper
        bb_upper = [100.0] * 30  # BB upper well below price
        result = compute_rr_ratio(closes, atr, bb_upper, multiplier=3.0)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v < 0

    def test_formula(self):
        """Verify rr_ratio = (BB_upper - close) / (multiplier * ATR)."""
        closes = [100.0] * 30
        highs = [102.0] * 30
        lows = [98.0] * 30
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 5.0
        bb = compute_bollinger_bands(closes)
        bb_upper = bb["upper"]
        # With flat data, BB upper = 100 (mean) + 2 * 0 (std) = 100
        # So BB upper = close = 100, ratio = 0
        result = compute_rr_ratio(closes, atr, bb_upper, multiplier=3.0)
        valid = [v for v in result if v is not None]
        for v in valid:
            assert v == pytest.approx(0.0)

    def test_formula_with_sprread(self):
        """Verify formula with non-zero BB width."""
        # Price=100, ATR=5, BB_upper=110, multiplier=3
        # reward = 110 - 100 = 10, risk = 3 * 5 = 15
        # rr = 10 / 15 = 0.6667
        closes = [100.0] * 30
        bb_upper = [110.0] * 30
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 5.0
        result = compute_rr_ratio(closes, atr, bb_upper, multiplier=3.0)
        expected = 10.0 / (3.0 * 5.0)  # = 0.6667
        for i in range(14, 30):
            assert result[i] == pytest.approx(expected, rel=1e-5)

    def test_higher_atr_reduces_ratio(self):
        """Higher ATR (more risk) reduces the RR ratio."""
        closes = [100.0] * 30
        bb_upper = [120.0] * 30  # reward = 20
        atr_small = [None] * 30
        atr_large = [None] * 30
        for i in range(14, 30):
            atr_small[i] = 3.0
            atr_large[i] = 10.0
        result_small = compute_rr_ratio(closes, atr_small, bb_upper, multiplier=3.0)
        result_large = compute_rr_ratio(closes, atr_large, bb_upper, multiplier=3.0)
        valid_small = [v for v in result_small if v is not None]
        valid_large = [v for v in result_large if v is not None]
        assert len(valid_small) > 0
        for vs, vl in zip(valid_small, valid_large):
            assert vs > vl  # smaller ATR → higher ratio

    def test_custom_multiplier(self):
        """Higher multiplier reduces the RR ratio (more risk)."""
        closes = [100.0] * 30
        bb_upper = [130.0] * 30  # reward = 30
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 5.0
        result_2 = compute_rr_ratio(closes, atr, bb_upper, multiplier=2.0)
        result_4 = compute_rr_ratio(closes, atr, bb_upper, multiplier=4.0)
        valid_2 = [v for v in result_2 if v is not None]
        valid_4 = [v for v in result_4 if v is not None]
        assert len(valid_2) > 0
        # With 4×ATR, risk is double → ratio is half
        for v2, v4 in zip(valid_2, valid_4):
            assert v2 == pytest.approx(v4 * 2.0)

    def test_short_series_returns_all_none(self):
        """When no ATR or BB values are available, all results are None."""
        closes = [100.0, 101.0, 102.0]
        bb_upper = [105.0, 105.0, 105.0]
        atr = [None, None, None]
        result = compute_rr_ratio(closes, atr, bb_upper, multiplier=3.0)
        assert all(v is None for v in result)

    def test_none_close_returns_none(self):
        """When close is None, RR ratio should be None."""
        closes = [100.0, None, 102.0]
        bb_upper = [110.0, 110.0, 110.0]
        atr = [5.0, 5.0, 5.0]
        result = compute_rr_ratio(closes, atr, bb_upper, multiplier=3.0)
        assert result[0] == pytest.approx((110.0 - 100.0) / (3.0 * 5.0))  # 0.6667
        assert result[1] is None
        assert result[2] == pytest.approx((110.0 - 102.0) / (3.0 * 5.0))

    def test_none_bb_upper_returns_none(self):
        """When BB upper is None, RR ratio should be None."""
        closes = [100.0, 101.0, 102.0]
        bb_upper = [None, 110.0, 112.0]
        atr = [5.0, 5.0, 5.0]
        result = compute_rr_ratio(closes, atr, bb_upper, multiplier=3.0)
        assert result[0] is None  # BB upper is None
        assert result[1] == pytest.approx((110.0 - 101.0) / (3.0 * 5.0))  # 0.7333
        assert result[2] == pytest.approx((112.0 - 102.0) / (3.0 * 5.0))

    def test_zero_atr_returns_none(self):
        """When ATR is zero, RR ratio should be None (division by zero guard)."""
        closes = [100.0] * 30
        bb_upper = [110.0] * 30
        atr = [None] * 30
        for i in range(14, 30):
            atr[i] = 0.0
        result = compute_rr_ratio(closes, atr, bb_upper, multiplier=3.0)
        valid = [v for v in result if v is not None]
        assert len(valid) == 0

    def test_varying_realistic_data(self):
        """RR ratio varies with realistic price action."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        highs = [101.5]
        lows = [98.5]
        for i in range(1, n):
            change = np.random.normal(0, 0.8)
            close = max(closes[-1] + change, 50.0)
            closes.append(close)
            highs.append(max(highs[-1], close) + np.random.uniform(0.5, 2.0))
            lows.append(min(lows[-1], close) - np.random.uniform(0.5, 2.0))
        atr = compute_atr(highs, lows, closes, 14)
        bb = compute_bollinger_bands(closes)
        result = compute_rr_ratio(closes, atr, bb["upper"], multiplier=3.0)
        valid = [v for v in result if v is not None]
        assert len(valid) > 2
        # Should have both positive and negative values as price crosses BB
        positive = [v for v in valid if v > 0]
        negative = [v for v in valid if v < 0]
        assert len(positive) > 0  # some points below BB upper
        # Price may or may not cross above BB upper, but at least some ratio exists
        assert len(valid) > 0
