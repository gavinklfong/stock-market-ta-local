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


class TestComputeVolatilityColumnsWithHvol:
    def test_returns_hvol20_key(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        assert "ta_hvol20" in result
        assert "ta_atr_stop_dist" in result
        assert "ta_atr_position" in result
        assert "ta_rr_ratio" in result

    def test_hvol20_none_before_period(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(20):
            assert result["ta_hvol20"][i] is None

    def test_hvol20_positive_with_varying_prices(self):
        highs, lows, closes = _make_sample(n=100)
        result = compute_volatility_columns(highs, lows, closes, 100)
        valid_hvol = [v for v in result["ta_hvol20"] if v is not None]
        assert len(valid_hvol) > 0
        for v in valid_hvol:
            assert v > 0


# ---------------------------------------------------------------------------
# TestComputeParkinsonVolatility
# ---------------------------------------------------------------------------


