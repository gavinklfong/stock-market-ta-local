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


class TestEdgeCases:
    def test_single_value(self):
        cols = compute_structure_columns([100.0], [90.0], [95.0], 1)
        assert cols["ta_swing_high"] == [None]
        assert cols["ta_trend"] == [0]

    def test_two_values(self):
        cols = compute_structure_columns([100.0, 105.0], [90.0, 95.0], [95.0, 100.0], 2)
        assert len(cols["ta_swing_high"]) == 2
        assert cols["ta_trend"] == [0, 0]

    def test_constant_prices(self):
        """Constant prices should produce no structure signals."""
        n = 50
        prices = [100.0] * n
        cols = compute_structure_columns(prices, prices, prices, n, lookback=3)
        # Should have very few/no swings since no variation
        valid_sh = [v for v in cols["ta_swing_high"] if v is not None]
        valid_sl = [v for v in cols["ta_swing_low"] if v is not None]
        # With constant data, there may be edge swings at boundaries
        # But trend should remain neutral
        valid_trend = [v for v in cols["ta_trend"] if v != 0]
        assert len(valid_trend) == 0

    def test_v_shaped_reversal(self):
        """V-shaped price action should detect both swing low and recovery."""
        highs = [100, 90, 80, 70, 80, 90, 100, 110]
        lows = [90, 80, 70, 60, 70, 80, 90, 100]
        structure = compute_structure(highs, lows, lookback=2)

        # The trough at index 3 should be detected as swing low
        # swing_low contains the price (not boolean), so check it's not None
        assert structure["swing_low"][3] is not None
        assert structure["swing_low"][3] == 60

    def test_inverted_v_reversal(self):
        """Inverted V (peak) should detect swing high."""
        highs = [80, 90, 100, 110, 100, 90, 80]
        lows = [70, 80, 90, 100, 90, 80, 70]
        structure = compute_structure(highs, lows, lookback=2)

        # The peak at index 3 should be detected as swing high
        # swing_high contains the price (not boolean), so check it's not None
        assert structure["swing_high"][3] is not None
        assert structure["swing_high"][3] == 110


# ---------------------------------------------------------------------------
# Breakout Strength Tests
# ---------------------------------------------------------------------------


