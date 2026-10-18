import math
import os
import tempfile
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from calculate_momentum import (
    compute_cci,
    compute_ema,
    compute_macd,
    compute_momentum_columns,
    compute_roc,
    compute_rsi,
    compute_stochastic,
    compute_tsi,
    compute_williams_r,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_closes(length, base=100.0, slope=0.0, noise_range=0.0):
    """Generate a list of closing prices."""
    np.random.seed(0)
    closes = []
    for i in range(length):
        val = base + slope * i + np.random.uniform(-noise_range, noise_range)
        closes.append(max(val, 1.0))  # keep positive
    return closes


def _make_ohlcv(n=100, base=100.0):
    """Generate synthetic OHLCV data.

    Returns (highs, lows, closes) lists of equal length.
    """
    np.random.seed(42)
    closes = [base]
    for _ in range(n - 1):
        change = np.random.normal(0, 0.01) * closes[-1]
        closes.append(max(closes[-1] + change, 1.0))

    highs = [c * (1 + abs(np.random.normal(0, 0.005))) for c in closes]
    lows = [c * (1 - abs(np.random.normal(0, 0.005))) for c in closes]

    return highs, lows, closes


# ---------------------------------------------------------------------------
# TestComputeEMA
# ---------------------------------------------------------------------------

class TestComputeCCI:
    """Tests for compute_cci (Commodity Channel Index)."""

    def test_cci_length(self):
        highs, lows, closes = _make_ohlcv(100)
        result = compute_cci(highs, lows, closes, 20)
        assert len(result) == 100

    def test_cci_short_data(self):
        """Returns all None when data < period."""
        highs = [101.0] * 10
        lows = [99.0] * 10
        closes = [100.0] * 10
        result = compute_cci(highs, lows, closes, 20)
        assert all(v is None for v in result)

    def test_cci_first_valid_index(self):
        """First valid CCI is at index period-1."""
        highs, lows, closes = _make_ohlcv(50)
        result = compute_cci(highs, lows, closes, 20)
        assert result[0] is None
        for i in range(19):  # indices 0..18
            assert result[i] is None
        assert result[19] is not None  # index 19 = period-1

    def test_cci_mismatched_lengths(self):
        """Raises AssertionError when input lengths differ."""
        with pytest.raises(AssertionError):
            compute_cci([100.0, 101.0], [99.0], [100.0, 101.0], 2)

    def test_cci_constant_prices(self):
        """CCI is None when all prices are constant (mean deviation = 0)."""
        highs = [100.0] * 30
        lows = [100.0] * 30
        closes = [100.0] * 30
        result = compute_cci(highs, lows, closes, 20)
        assert all(v is None for v in result[19:])

    def test_cci_varying_prices_produce_values(self):
        """CCI should produce non-None values when prices vary."""
        highs, lows, closes = _make_ohlcv(50)
        result = compute_cci(highs, lows, closes, 20)
        valid = [v for v in result[20:] if v is not None]
        assert len(valid) > 0

    def test_cci_oversold_condition(self):
        """CCI < -100 when close drops well below typical price range."""
        highs = [100.0] * 60
        lows = [100.0] * 60
        # First 40 closes = 100, last 20 closes = very low (10.0)
        closes = [100.0] * 40 + [10.0] * 20
        result = compute_cci(highs, lows, closes, 20)
        # At index 42, window has 22 high closes + 2 low closes → deep oversold
        assert result[42] is not None
        assert result[42] < -100  # deep oversold

    def test_cci_overbought_condition(self):
        """CCI > +100 when close rises well above typical price range."""
        highs = [200.0] * 60
        lows = [100.0] * 60
        closes = [100.0] * 40 + [190.0] * 20
        result = compute_cci(highs, lows, closes, 20)
        # At index 42, window has 18 high closes + 2 very high closes → overbought
        assert result[42] is not None
        assert result[42] > 100  # overbought

    def test_cci_uptrend_positive_values(self):
        """In a strong uptrend, CCI tends positive after initial period."""
        np.random.seed(99)
        highs = [100.0 + i * 0.5 + np.random.uniform(0, 1) for i in range(50)]
        lows = [98.0 + i * 0.5 + np.random.uniform(0, 1) for i in range(50)]
        closes = [100.0 + i * 0.5 + np.random.uniform(-0.5, 0.5) for i in range(50)]
        result = compute_cci(highs, lows, closes, 20)
        # After the uptrend establishes, CCI should be mostly positive
        valid = [v for v in result[30:] if v is not None]
        if valid:
            avg = sum(valid) / len(valid)
            assert avg > -20  # generally positive bias

    def test_cci_custom_period(self):
        """CCI with a custom period works correctly."""
        highs, lows, closes = _make_ohlcv(50)
        result = compute_cci(highs, lows, closes, 10)
        # First valid at index 9
        for i in range(9):
            assert result[i] is None
        assert result[9] is not None
        assert result[10] is not None

    def test_cci_mean_deviation_zero_edge(self):
        """CCI returns None when mean deviation is exactly zero."""
        # All typical prices are the same → mean deviation = 0
        highs = [105.0] * 30
        lows = [95.0] * 30
        closes = [100.0] * 30
        result = compute_cci(highs, lows, closes, 20)
        for i in range(20, 30):
            assert result[i] is None


# ---------------------------------------------------------------------------
# TestComputeTSI
# ---------------------------------------------------------------------------


