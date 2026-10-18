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


class TestComputeStructureColumns:
    def test_expected_keys(self):
        highs, lows, _ = _make_sample(50)
        cols = compute_structure_columns(highs, lows, _make_sample(50)[2], 50)
        expected = {
            "ta_swing_high", "ta_swing_low",
            "ta_swing_high_idx", "ta_swing_low_idx",
            "ta_hh", "ta_hl", "ta_lh", "ta_ll",
            "ta_trend", "ta_bos", "ta_choch",
            "ta_nearest_resistance", "ta_nearest_support",
            "ta_dist_resistance", "ta_dist_support",
            "ta_breakout_strength", "ta_support_touches",
        }
        assert set(cols.keys()) == expected

    def test_all_same_length(self):
        highs, lows, _ = _make_sample(50)
        cols = compute_structure_columns(highs, lows, _make_sample(50)[2], 50)
        for col in cols.values():
            assert len(col) == 50

    def test_short_data(self):
        empty = [None] * 5
        zero = [0] * 5
        cols = compute_structure_columns([100]*5, [90]*5, [95]*5, 5)
        assert cols["ta_swing_high"] == empty
        assert cols["ta_swing_low"] == empty
        assert cols["ta_swing_high_idx"] == [-1] * 5
        assert cols["ta_swing_low_idx"] == [-1] * 5
        assert cols["ta_hh"] == zero
        assert cols["ta_lh"] == zero
        assert cols["ta_trend"] == zero
        assert cols["ta_breakout_strength"] == zero
        assert cols["ta_support_touches"] == zero

    def test_with_realistic_data(self):
        np.random.seed(42)
        n = 200
        base = 150.0
        closes = [base]
        for _ in range(n - 1):
            change = np.random.normal(0, 1.5)
            closes.append(max(closes[-1] + change, 50.0))

        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]

        cols = compute_structure_columns(highs, lows, closes, n)

        # Should have some non-None values for swings
        valid_sh = [v for v in cols["ta_swing_high"] if v is not None]
        valid_sl = [v for v in cols["ta_swing_low"] if v is not None]
        assert len(valid_sh) > 0
        assert len(valid_sl) > 0

        # Should have some non-zero trend
        non_zero_trend = [v for v in cols["ta_trend"] if v != 0]
        assert len(non_zero_trend) > 0

    def test_with_trending_data(self):
        """Uptrend should produce bullish structure."""
        n = 100
        # Zigzag uptrend: even indices are swing highs, odd are swing lows
        highs = []
        lows = []
        for i in range(n):
            trend = 100.0 + i * 0.5
            if i % 2 == 0:
                highs.append(trend + 2.0)
                lows.append(trend - 1.0)
            else:
                highs.append(trend + 1.0)
                lows.append(trend - 2.0)

        cols = compute_structure_columns(highs, lows, highs, n, lookback=1)

        # Should have bullish signals
        valid_hh = [v for v in cols["ta_hh"] if v == 1]
        valid_trend_pos = [v for v in cols["ta_trend"] if v == 1]
        assert len(valid_hh) > 0
        assert len(valid_trend_pos) > 0


# ---------------------------------------------------------------------------
# TestProcessCSV
# ---------------------------------------------------------------------------


