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

class TestComputeTSI:
    """Tests for compute_tsi (True Strength Index)."""

    def test_tsi_length(self):
        closes = _make_closes(100)
        result = compute_tsi(closes, 25, 13)
        assert len(result) == 100

    def test_tsi_short_data(self):
        """Returns all None when data < fast + slow + 1."""
        closes = [100.0] * 30
        result = compute_tsi(closes, 25, 13)
        assert all(v is None for v in result)

    def test_tsi_first_valid_index(self):
        """First valid TSI is approximately at index fast + slow - 1."""
        np.random.seed(0)
        closes = [100.0 + i * 0.1 + np.random.uniform(-1, 1) for i in range(100)]
        result = compute_tsi(closes, 25, 13)
        # First valid value should be well after fast + slow
        valid_indices = [i for i, v in enumerate(result) if v is not None]
        assert len(valid_indices) > 0
        first_valid = valid_indices[0]
        # Should be >= fast - 1 (first EMA1 valid) + slow - 1 (second EMA valid)
        assert first_valid >= 25 + 13 - 3  # loose bound accounting for EMA seeding

    def test_tsi_mismatched_input(self):
        """TSI only takes closes, no mismatch possible."""
        closes = _make_closes(50)
        result = compute_tsi(closes, 25, 13)
        assert len(result) == 50

    def test_tsi_constant_prices(self):
        """TSI is None when all prices are constant (changes = 0, abs changes = 0)."""
        closes = [100.0] * 50
        result = compute_tsi(closes, 25, 13)
        valid = [v for v in result if v is not None]
        assert len(valid) == 0  # all zero changes → double EMA = 0 → den = 0

    def test_tsi_varying_prices_produce_values(self):
        """TSI should produce non-None values when prices vary."""
        np.random.seed(0)
        closes = [100.0 + i * 0.1 + np.random.uniform(-1, 1) for i in range(100)]
        result = compute_tsi(closes, 25, 13)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_tsi_uptrend_positive(self):
        """In a strong uptrend, TSI tends positive."""
        np.random.seed(0)
        closes = [100.0 + i * 0.5 + np.random.uniform(-0.5, 0.5)
                  for i in range(100)]
        result = compute_tsi(closes, 25, 13)
        valid = [v for v in result if v is not None]
        if valid:
            avg = sum(valid) / len(valid)
            assert avg > 0  # uptrend → positive TSI

    def test_tsi_downtrend_negative(self):
        """In a strong downtrend, TSI tends negative."""
        np.random.seed(0)
        closes = [200.0 - i * 0.5 + np.random.uniform(-0.5, 0.5)
                  for i in range(100)]
        result = compute_tsi(closes, 25, 13)
        valid = [v for v in result if v is not None]
        if valid:
            avg = sum(valid) / len(valid)
            assert avg < 0  # downtrend → negative TSI

    def test_tsi_custom_periods(self):
        """TSI with custom fast/slow periods works correctly."""
        np.random.seed(0)
        closes = [100.0 + i * 0.5 + np.random.uniform(-0.5, 0.5)
                  for i in range(80)]
        result = compute_tsi(closes, 10, 5)
        # Should have values since n=80 >= fast+slow+1=16
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_tsi_ranging_market_near_zero(self):
        """In a ranging market, TSI oscillates near zero."""
        np.random.seed(42)
        closes = [100.0 + np.random.uniform(-2, 2) for _ in range(100)]
        result = compute_tsi(closes, 25, 13)
        valid = [v for v in result if v is not None]
        if valid:
            avg = sum(valid) / len(valid)
            # Average should be near zero for ranging market
            assert -30 < avg < 30  # loose bound
