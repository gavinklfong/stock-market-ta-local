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

class TestComputeMomentumColumns:
    def test_expected_keys(self):
        closes = _make_closes(50)
        highs, lows, _ = _make_ohlcv(50)
        cols = compute_momentum_columns(closes, highs, lows, 50)
        assert set(cols.keys()) == {
            "ta_rsi14", "ta_macd_line", "ta_macd_signal",
            "ta_macd_histogram", "ta_roc20", "ta_stoch_k", "ta_stoch_d",
            "ta_williams_r", "ta_cci", "ta_tsi",
        }

    def test_all_same_length(self):
        closes = _make_closes(50)
        highs, lows, _ = _make_ohlcv(50)
        cols = compute_momentum_columns(closes, highs, lows, 50)
        for col in cols.values():
            assert len(col) == 50

    def test_rsi_present(self):
        closes = _make_closes(50)
        highs, lows, _ = _make_ohlcv(50)
        cols = compute_momentum_columns(closes, highs, lows, 50)
        valid = [v for v in cols["ta_rsi14"] if v is not None]
        assert len(valid) > 0

    def test_roc_present(self):
        closes = _make_closes(50)
        highs, lows, _ = _make_ohlcv(50)
        cols = compute_momentum_columns(closes, highs, lows, 50)
        valid = [v for v in cols["ta_roc20"] if v is not None]
        assert len(valid) > 0

    def test_short_data(self):
        closes = [100.0] * 5
        highs = [101.0] * 5
        lows = [99.0] * 5
        cols = compute_momentum_columns(closes, highs, lows, 5)
        assert cols["ta_rsi14"] == [None] * 5
        assert cols["ta_roc20"] == [None] * 5
        assert cols["ta_williams_r"] == [None] * 5
        assert cols["ta_cci"] == [None] * 5
        assert cols["ta_tsi"] == [None] * 5
        # MACD may produce some values even for short data
        assert len(cols["ta_macd_line"]) == 5

    def test_williams_r_present(self):
        """Williams %R should be present and have valid values."""
        highs, lows, closes = _make_ohlcv(100)
        cols = compute_momentum_columns(closes, highs, lows, 100)
        valid = [v for v in cols["ta_williams_r"] if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert -100.0 <= v <= 0.0

    def test_cci_present(self):
        """CCI should be present and have valid values."""
        highs, lows, closes = _make_ohlcv(100)
        cols = compute_momentum_columns(closes, highs, lows, 100)
        valid = [v for v in cols["ta_cci"] if v is not None]
        assert len(valid) > 0

    def test_tsi_present(self):
        """TSI should be present and have valid values."""
        np.random.seed(0)
        closes = [100.0 + i * 0.1 + np.random.uniform(-1, 1) for i in range(100)]
        cols = compute_momentum_columns(closes, [c + 1 for c in closes], [c - 1 for c in closes], 100)
        valid = [v for v in cols["ta_tsi"] if v is not None]
        assert len(valid) > 0

    def test_all_same_length(self):
        closes = _make_closes(100)
        highs, lows, _ = _make_ohlcv(100)
        cols = compute_momentum_columns(closes, highs, lows, 100)
        lengths = [len(v) for v in cols.values()]
        assert len(set(lengths)) == 1
        assert lengths[0] == 100


# ---------------------------------------------------------------------------
# TestProcessCSV
# ---------------------------------------------------------------------------

