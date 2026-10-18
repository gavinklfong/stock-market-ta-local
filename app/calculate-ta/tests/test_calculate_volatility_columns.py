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


class TestComputeVolatilityColumns:
    def test_returns_expected_keys(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        assert "ta_atr14" in result
        assert "ta_normalized_atr14" in result
        assert "ta_bband_upper" in result
        assert "ta_bband_middle" in result
        assert "ta_bband_lower" in result
        assert "ta_bband_width" in result
        assert "ta_bband_pctb" in result
        assert "ta_parkinson_vol" in result

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


# ---------------------------------------------------------------------------
# TestBollingerWidth
# ---------------------------------------------------------------------------


