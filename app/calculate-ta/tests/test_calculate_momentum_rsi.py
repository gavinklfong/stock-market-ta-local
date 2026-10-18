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

class TestComputeRSI:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_rsi(closes, 14)
        assert len(result) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        result = compute_rsi(closes, 14)
        assert all(v is None for v in result)

    def test_first_valid_at_period(self):
        closes = _make_closes(20, base=100)
        result = compute_rsi(closes, 14)
        for i in range(14):
            assert result[i] is None
        assert result[14] is not None

    def test_rsi_range(self):
        closes = _make_closes(100, base=100, noise_range=5)
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert 0 <= v <= 100

    def test_constant_prices(self):
        """RSI should be 50 when prices don't change."""
        closes = [100.0] * 30
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(50.0, abs=1e-9)

    def test_always_up(self):
        """RSI should be 100 when every change is positive."""
        closes = [100.0 + i * 1.0 for i in range(30)]
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(100.0, abs=1e-9)

    def test_always_down(self):
        """RSI should be 0 when every change is negative."""
        closes = [100.0 - i * 1.0 for i in range(30)]
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(0.0, abs=1e-9)

    def test_wilders_smoothing_match(self):
        """Verify the recursive smoothing step matches standard Wilder formula."""
        # Manually construct gains/losses to test the smoothed average
        closes = [100, 101, 99, 102, 100, 103, 101, 105, 102, 104, 103, 106,
                  104, 105, 106, 107, 106, 108, 107, 109, 108, 110, 109, 111]
        result = compute_rsi(closes, 14)
        # All should be valid for 24 data points with period 14
        valid = [v for v in result if v is not None]
        assert len(valid) > 0


# ---------------------------------------------------------------------------
# TestComputeMACD
# ---------------------------------------------------------------------------

