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


class TestComputeHistoricalVolatility:
    def test_length(self):
        closes = _make_sample(n=50)[2]
        result = compute_historical_volatility(closes, period=20)
        assert len(result) == 50

    def test_first_values_are_none(self):
        """HV needs at least `period` log returns; first valid at index `period`."""
        closes = _make_sample(n=50)[2]
        result = compute_historical_volatility(closes, period=20)
        for i in range(20):
            assert result[i] is None

    def test_returns_positive_for_varying_prices(self):
        """HV should be positive when prices vary."""
        closes = _make_sample(n=100)[2]
        result = compute_historical_volatility(closes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v > 0

    def test_zero_for_constant_prices(self):
        """With constant prices, log returns are 0 so HV should be 0."""
        closes = [100.0] * 50
        result = compute_historical_volatility(closes, period=20)
        for i in range(20, len(closes)):
            assert result[i] == pytest.approx(0.0)

    def test_short_series_returns_all_none(self):
        """When series is shorter than period + 1, all values are None."""
        closes = [100.0, 101.0, 102.0]
        result = compute_historical_volatility(closes, period=20)
        assert all(v is None for v in result)

    def test_annualization(self):
        """Annualized HV should be non_annualized * sqrt(252)."""
        np.random.seed(42)
        closes = [100.0]
        for _ in range(49):
            closes.append(closes[-1] * (1 + np.random.normal(0, 0.01)))
        result_ann = compute_historical_volatility(closes, period=20, annualize=True)
        result_raw = compute_historical_volatility(closes, period=20, annualize=False)
        valid_ann = [v for v in result_ann if v is not None]
        valid_raw = [v for v in result_raw if v is not None]
        assert len(valid_ann) > 0
        assert len(valid_raw) > 0
        for a, r in zip(valid_ann, valid_raw):
            assert a == pytest.approx(r * math.sqrt(252))

    def test_increasing_hvol_with_widening_volatility(self):
        """HV should increase when price volatility increases over time."""
        np.random.seed(99)
        closes = [100.0]
        for i in range(49):
            vol = 0.005 + i * 0.001  # volatility ramps up
            closes.append(closes[-1] * (1 + np.random.normal(0, vol)))
        result = compute_historical_volatility(closes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Last value should be higher than first (generally)
        assert valid[-1] > valid[0]

    def test_first_valid_value(self):
        """Verify first valid HV value against manual calculation."""
        np.random.seed(42)
        closes = [100.0]
        for _ in range(49):
            closes.append(closes[-1] * (1 + np.random.normal(0, 0.01)))
        period = 20
        result = compute_historical_volatility(closes, period=period, annualize=False)
        # Manually compute: log returns for the window
        log_returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, period + 1)]
        mean = sum(log_returns) / period
        variance = sum((r - mean) ** 2 for r in log_returns) / period
        expected = math.sqrt(variance)  # non-annualized
        assert result[period] == pytest.approx(expected)


# ---------------------------------------------------------------------------
# TestComputeVolatilityColumnsWithHvol
# ---------------------------------------------------------------------------


