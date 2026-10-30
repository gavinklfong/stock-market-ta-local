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


class TestComputeStructure:
    def test_length(self):
        highs, lows, _ = _make_sample(50)
        result = compute_structure(highs, lows, lookback=3)
        assert len(result["swing_high"]) == 50
        assert len(result["swing_low"]) == 50
        assert len(result["hh"]) == 50
        assert len(result["hl"]) == 50
        assert len(result["lh"]) == 50
        assert len(result["ll"]) == 50
        assert len(result["trend"]) == 50
        assert len(result["bos"]) == 50
        assert len(result["choch"]) == 50

    def test_short_data(self):
        highs = [100.0 + i for i in range(5)]
        lows = [90.0 + i for i in range(5)]
        result = compute_structure(highs, lows, lookback=5)
        assert result["trend"] == [0] * 5
        assert result["bos"] == [0] * 5
        assert result["choch"] == [0] * 5

    def test_bullish_trend_structure(self):
        """Strong uptrend: should produce HH and HL patterns."""
        # Zigzag uptrend: each swing high > previous, each swing low > previous
        highs = [100, 105, 98, 110, 103, 115, 108, 120, 113, 125]
        lows = [95, 100, 93, 105, 98, 110, 103, 115, 108, 120]
        result = compute_structure(highs, lows, lookback=1)

        # In a strong uptrend, we should see HH and HL
        valid_hh = [v for v in result["hh"] if v == 1]
        valid_hl = [v for v in result["hl"] if v == 1]
        valid_trend_pos = [v for v in result["trend"] if v == 1]

        # At least some bullish signals should be present
        assert len(valid_hh) > 0
        assert len(valid_hl) > 0
        assert len(valid_trend_pos) > 0

    def test_bearish_trend_structure(self):
        """Strong downtrend: should produce LH and LL patterns."""
        # Zigzag downtrend: each swing high < previous, each swing low < previous
        highs = [125, 113, 120, 108, 115, 103, 110, 98, 105, 93, 100, 88]
        lows = [120, 108, 115, 103, 110, 98, 105, 90, 100, 85, 95, 80]
        result = compute_structure(highs, lows, lookback=1)

        valid_trend_neg = [v for v in result["trend"] if v == -1]
        valid_lh = [v for v in result["lh"] if v == 1]
        valid_ll = [v for v in result["ll"] if v == 1]
        assert len(valid_trend_neg) > 0
        assert len(valid_lh) > 0
        assert len(valid_ll) > 0

    def test_swing_high_idx_valid(self):
        """Swing high idx should be non-negative when a swing high exists."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)

        valid_sh = [v for v in result["swing_high"] if v is not None]
        if valid_sh:
            # Where swing_high is not None, swing_high_idx should be >= 0
            for i in range(len(result["swing_high"])):
                if result["swing_high"][i] is not None:
                    assert result["swing_high_idx"][i] >= 0

    def test_swing_low_idx_valid(self):
        """Swing low idx should be non-negative when a swing low exists."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)

        valid_sl = [v for v in result["swing_low"] if v is not None]
        if valid_sl:
            for i in range(len(result["swing_low"])):
                if result["swing_low"][i] is not None:
                    assert result["swing_low_idx"][i] >= 0

    def test_trend_values(self):
        """Trend should only be -1, 0, or 1."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for v in result["trend"]:
            assert v in (-1, 0, 1)

    def test_hh_lh_mutually_exclusive(self):
        """HH and LH should not both be 1 at the same index."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for i in range(len(highs)):
            assert not (result["hh"][i] == 1 and result["lh"][i] == 1)

    def test_hl_ll_mutually_exclusive(self):
        """HL and LL should not both be 1 at the same index."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for i in range(len(highs)):
            assert not (result["hl"][i] == 1 and result["ll"][i] == 1)

    def test_bos_values(self):
        """BOS should only be 0 or 1."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for v in result["bos"]:
            assert v in (0, 1)

    def test_choch_values(self):
        """CHoCH should only be 0 or 1."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for v in result["choch"]:
            assert v in (0, 1)


# ---------------------------------------------------------------------------
# TestComputeSupportResistance
# ---------------------------------------------------------------------------


