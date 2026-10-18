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


class TestBollingerWidth:
    def test_width_none_before_period(self):
        """Bollinger Width should be None before the first valid index."""
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(19):
            assert result["ta_bband_width"][i] is None

    def test_width_positive_with_varying_prices(self):
        """Band Width should be positive when prices vary."""
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_widths = [v for v in result["ta_bband_width"] if v is not None]
        assert len(valid_widths) > 0
        for w in valid_widths:
            assert w > 0

    def test_width_zero_with_constant_prices(self):
        """With constant prices, std=0 so Band Width should be 0."""
        closes = [50.0] * 30
        highs = [51.0] * 30
        lows = [49.0] * 30
        result = compute_volatility_columns(highs, lows, closes, 30)
        for i in range(19, len(closes)):
            assert result["ta_bband_width"][i] == pytest.approx(0.0)

    def test_width_formula(self):
        """Band Width = (upper - lower) / middle."""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0] * 10
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        bb = compute_bollinger_bands(closes)  # default period=20, num_std=2.0
        result = compute_volatility_columns(highs, lows, closes, len(closes))
        # First valid index for period=20 is 19
        for i in range(19, len(closes)):
            if (bb["upper"][i] is not None and bb["lower"][i] is not None
                    and bb["middle"][i] is not None and bb["middle"][i] != 0):
                expected = (bb["upper"][i] - bb["lower"][i]) / bb["middle"][i]
                assert result["ta_bband_width"][i] == pytest.approx(expected)


# ---------------------------------------------------------------------------
# TestBollingerPercentB
# ---------------------------------------------------------------------------


