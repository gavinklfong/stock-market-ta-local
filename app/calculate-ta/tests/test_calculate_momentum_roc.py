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

class TestComputeROC:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_roc(closes, 20)
        assert len(result) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        result = compute_roc(closes, 20)
        assert all(v is None for v in result)

    def test_first_valid_at_period(self):
        closes = _make_closes(30, base=100)
        result = compute_roc(closes, 20)
        for i in range(20):
            assert result[i] is None
        assert result[20] is not None

    def test_roc_positive(self):
        """ROC should be positive when current > previous."""
        closes = [100.0, 110.0]
        result = compute_roc(closes, 1)
        assert result[1] == pytest.approx(10.0, abs=1e-9)  # (110-100)/100 * 100

    def test_roc_negative(self):
        """ROC should be negative when current < previous."""
        closes = [100.0, 90.0]
        result = compute_roc(closes, 1)
        assert result[1] == pytest.approx(-10.0, abs=1e-9)

    def test_roc_zero(self):
        """ROC should be 0 when current == previous."""
        closes = [100.0, 100.0]
        result = compute_roc(closes, 1)
        assert result[1] == pytest.approx(0.0, abs=1e-9)

    def test_roc_linear(self):
        """ROC for linearly increasing data should be positive."""
        closes = [100.0 + i for i in range(30)]
        result = compute_roc(closes, 5)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] > 0

    def test_roc_custom_period(self):
        """ROC with custom period should work."""
        closes = _make_closes(30, base=100, noise_range=2)
        result = compute_roc(closes, 5)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_roc_with_zero_price(self):
        """ROC should handle zero prices gracefully (skip division)."""
        closes = [0.0, 10.0]
        result = compute_roc(closes, 1)
        assert result[1] is None  # division by zero -> None


# ---------------------------------------------------------------------------
# TestComputeWilliamsR
# ---------------------------------------------------------------------------

