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

class TestComputeEMA:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_ema(closes, 10)
        assert len(result) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        result = compute_ema(closes, 10)
        assert all(v is None for v in result)

    def test_first_valid_at_period_minus_one(self):
        closes = _make_closes(10, base=50)
        result = compute_ema(closes, 10)
        assert result[9] is not None
        for i in range(9):
            assert result[i] is None

    def test_sma_seed(self):
        """First EMA value should equal SMA of first `period` values."""
        closes = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = compute_ema(closes, 5)
        expected_sma = sum(closes[:5]) / 5  # 30.0
        assert result[4] == pytest.approx(expected_sma, abs=1e-9)

    def test_period_one(self):
        """EMA with period=1 should equal the raw values."""
        closes = [1.0, 2.0, 3.0, 4.0]
        result = compute_ema(closes, 1)
        for i in range(len(closes)):
            assert result[i] == closes[i]

    def test_monotonic_ema(self):
        """EMA should be smoother than raw data."""
        closes = list(range(1, 51))  # linearly increasing
        result = compute_ema(closes, 10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # EMA should be monotonically increasing for linear data
        for i in range(1, len(valid)):
            assert valid[i] >= valid[i - 1] - 1e-9

    def test_ema_reference_match(self):
        """Compare with a known recursive EMA implementation."""
        closes = _make_closes(30, base=50, noise_range=5)
        period = 7
        k = 2.0 / (period + 1)
        seed = sum(closes[:period]) / period

        expected = [None] * len(closes)
        expected[period - 1] = seed
        for i in range(period, len(closes)):
            expected[i] = closes[i] * k + expected[i - 1] * (1 - k)

        result = compute_ema(closes, period)
        for i in range(period - 1, len(closes)):
            assert result[i] == pytest.approx(expected[i], abs=1e-9)


# ---------------------------------------------------------------------------
# TestComputeRSI
# ---------------------------------------------------------------------------

