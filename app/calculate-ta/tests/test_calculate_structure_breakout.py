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


class TestComputeBreakoutStrength:
    """Tests for compute_breakout_strength."""

    def test_no_breakout(self):
        """When price doesn't exceed S/R levels, strength should be 0."""
        highs = [105] * 10
        lows = [95] * 10
        resistance = [110] * 10  # above all highs
        support = [90] * 10      # below all lows
        result = compute_breakout_strength(highs, lows, resistance, support)
        assert result == [0.0] * 10

    def test_upside_breakout(self):
        """High exceeding resistance should produce positive strength."""
        highs = [115] * 10  # 15% above resistance
        lows = [90] * 10
        resistance = [100] * 10
        support = [90] * 10
        result = compute_breakout_strength(highs, lows, resistance, support)
        expected = [15.0] * 10  # (115 - 100) / 100 * 100
        assert result == expected

    def test_downside_breakout(self):
        """Low below support should produce positive strength."""
        highs = [110] * 10
        lows = [85] * 10  # 16.67% below support
        resistance = [110] * 10
        support = [100] * 10
        result = compute_breakout_strength(highs, lows, resistance, support)
        expected = [15.0] * 10  # (100 - 85) / 100 * 100
        assert result == expected

    def test_max_breakout_direction(self):
        """Should take the maximum of up and down breakout."""
        highs = [120] * 10  # 20% above resistance
        lows = [80] * 10    # 20% below support
        resistance = [100] * 10
        support = [100] * 10
        result = compute_breakout_strength(highs, lows, resistance, support)
        # Both breakouts are 20%, so max is 20%
        assert result == [20.0] * 10

    def test_none_levels(self):
        """None resistance/support should be skipped."""
        highs = [115] * 10
        lows = [95] * 10
        resistance = [None] * 10
        support = [90] * 10
        result = compute_breakout_strength(highs, lows, resistance, support)
        assert result == [0.0] * 10  # No valid breakout levels

    def test_mixed_breakout(self):
        """Only one bar breaks out, others are 0."""
        highs = [100, 100, 115, 100, 100]
        lows = [95, 95, 95, 95, 95]
        resistance = [100, 100, 100, 100, 100]
        support = [94, 94, 94, 94, 94]
        result = compute_breakout_strength(highs, lows, resistance, support)
        assert result[0] == 0.0       # No breakout (high=100 not > 100)
        assert result[2] == 15.0      # (115 - 100) / 100 * 100
        assert result[4] == 0.0       # No breakout

    def test_zero_length(self):
        """Empty input should return empty list."""
        result = compute_breakout_strength([], [], [], [])
        assert result == []

    def test_partial_none_levels(self):
        """Some bars have None resistance, others don't."""
        highs = [105, 105, 115, 105]
        lows = [95, 95, 95, 95]
        resistance = [100, None, 100, None]
        support = [90, 90, 90, 90]
        result = compute_breakout_strength(highs, lows, resistance, support)
        assert result[0] == 5.0   # (105 - 100) / 100 * 100
        assert result[1] == 0.0   # None resistance, no valid level
        assert result[2] == 15.0  # (115 - 100) / 100 * 100
        assert result[3] == 0.0   # None resistance

    def test_breakout_strength_in_columns(self):
        """Breakout strength should be included in compute_structure_columns output."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(max(closes[-1] + np.random.normal(0, 1.0), 10.0))
        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]

        cols = compute_structure_columns(highs, lows, closes, n)
        assert "ta_breakout_strength" in cols
        assert len(cols["ta_breakout_strength"]) == n
        # All values should be >= 0
        for v in cols["ta_breakout_strength"]:
            assert v >= 0


# ---------------------------------------------------------------------------
# Support Touches Tests
# ---------------------------------------------------------------------------


