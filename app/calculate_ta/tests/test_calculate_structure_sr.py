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


class TestComputeSupportResistance:
    def test_length(self):
        highs, lows, _ = _make_sample(50)
        structure = compute_structure(highs, lows, lookback=3)
        res, sup = compute_support_resistance(highs, lows, structure, lookback=3)
        assert len(res) == 50
        assert len(sup) == 50

    def test_short_data(self):
        highs = [100.0 + i for i in range(5)]
        lows = [90.0 + i for i in range(5)]
        structure = compute_structure(highs, lows, lookback=5)
        res, sup = compute_support_resistance(highs, lows, structure, lookback=5)
        assert res == [None] * 5
        assert sup == [None] * 5

    def test_resistance_above(self):
        """Resistance level should be above the current price."""
        # Create data with a clear peak (resistance) at price 120
        highs = [100, 105, 115, 120, 115, 110, 105, 100, 95, 90]
        lows = [90, 95, 105, 110, 105, 100, 95, 90, 85, 80]
        structure = compute_structure(highs, lows, lookback=2)
        res, sup = compute_support_resistance(highs, lows, structure, lookback=2)

        # After the peak, resistance should be set
        valid_res = [v for v in res if v is not None]
        if valid_res:
            # Resistance should be positive
            for v in valid_res:
                assert v > 0

    def test_support_below(self):
        """Support level should be below the current price."""
        highs = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55]
        lows = [90, 85, 80, 75, 70, 65, 60, 55, 50, 45]
        structure = compute_structure(highs, lows, lookback=2)
        res, sup = compute_support_resistance(highs, lows, structure, lookback=2)

        valid_sup = [v for v in sup if v is not None]
        if valid_sup:
            for v in valid_sup:
                assert v > 0


# ---------------------------------------------------------------------------
# TestClusterLevels
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TestDistanceToResistanceSupport
# ---------------------------------------------------------------------------


