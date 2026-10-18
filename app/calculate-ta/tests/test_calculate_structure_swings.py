"""Unit tests for calculate_structure.py — verifies swing detection, HH/HL/LH/LL, BOS/CHoCH, and support/resistance."""

import math
import os

import numpy as np
import pandas as pd
import pytest

from calculate_structure import (
    compute_breakout_strength,
    compute_structure,
    compute_structure_columns,
    compute_support_resistance,
    compute_support_touches,
    detect_swings,
    _cluster_levels,
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
# TestDetectSwings
# ---------------------------------------------------------------------------


class TestDetectSwings:
    def test_length(self):
        highs, lows, _ = _make_sample(50)
        sh, sl = detect_swings(highs, lows, lookback=3)
        assert len(sh) == 50
        assert len(sl) == 50

    def test_short_data(self):
        highs = [100.0 + i for i in range(10)]
        lows = [90.0 + i for i in range(10)]
        sh, sl = detect_swings(highs, lows, lookback=5)
        assert all(v is False for v in sh)
        assert all(v is False for v in sl)

    def test_known_swing_high(self):
        """A peak surrounded by lower values should be detected as swing high."""
        highs = [100, 105, 95, 110, 90, 115, 85, 120, 80]
        lows = [90, 95, 85, 100, 80, 105, 75, 110, 70]
        sh, sl = detect_swings(highs, lows, lookback=1)
        # Index 7 (high=120) should be a swing high
        assert sh[7] is True

    def test_known_swing_low(self):
        """A trough surrounded by higher values should be detected as swing low."""
        highs = [100, 105, 110, 105, 115, 110, 120]
        lows = [90, 95, 85, 90, 80, 85, 75]
        sh, sl = detect_swings(highs, lows, lookback=1)
        # Index 4 (low=80) should be a swing low
        assert sl[4] is True

    def test_no_swings_linear(self):
        """Linearly increasing data should produce no swings in the middle."""
        highs = list(range(10, 60))
        lows = list(range(0, 50))
        sh, sl = detect_swings(highs, lows, lookback=5)
        # Middle elements should all be False for linear data
        assert all(v is False for v in sh[5:-5])
        assert all(v is False for v in sl[5:-5])


# ---------------------------------------------------------------------------
# TestComputeStructure
# ---------------------------------------------------------------------------


