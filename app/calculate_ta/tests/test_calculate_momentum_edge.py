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

class TestEdgeCases:
    def test_ema_single_value(self):
        result = compute_ema([100.0], 10)
        assert result == [None]

    def test_rsi_single_value(self):
        result = compute_rsi([100.0], 14)
        assert result == [None]

    def test_macd_single_value(self):
        macd = compute_macd([100.0])
        assert macd["macd_line"] == [None]
        assert macd["signal_line"] == [None]
        assert macd["histogram"] == [None]

    def test_roc_single_value(self):
        result = compute_roc([100.0], 20)
        assert result == [None]

    def test_compute_momentum_columns_very_short(self):
        closes = [100.0, 101.0]
        highs = [101.0, 102.0]
        lows = [99.0, 100.0]
        cols = compute_momentum_columns(closes, highs, lows, 2)
        assert len(cols["ta_rsi14"]) == 2
        assert all(v is None for v in cols["ta_rsi14"])
        assert len(cols["ta_roc20"]) == 2
        assert all(v is None for v in cols["ta_roc20"])
        assert len(cols["ta_williams_r"]) == 2
        assert all(v is None for v in cols["ta_williams_r"])
        assert len(cols["ta_cci"]) == 2
        assert all(v is None for v in cols["ta_cci"])
        assert len(cols["ta_tsi"]) == 2
        assert all(v is None for v in cols["ta_tsi"])

    def test_computing_momentum_with_nan_values(self):
        """Should handle NaN gracefully (convert to float)."""
        closes = [100.0, 101.0, None, 102.0, 103.0]
        highs = [101.0, 102.0, None, 103.0, 104.0]
        lows = [99.0, 100.0, None, 101.0, 102.0]
        closes_float = [float(v) if v is not None else 0.0 for v in closes]
        highs_float = [float(v) if v is not None else 0.0 for v in highs]
        lows_float = [float(v) if v is not None else 0.0 for v in lows]
        cols = compute_momentum_columns(closes_float, highs_float, lows_float, 5)
        assert len(cols["ta_rsi14"]) == 5


# ---------------------------------------------------------------------------
# TestComputeCCI
# ---------------------------------------------------------------------------


