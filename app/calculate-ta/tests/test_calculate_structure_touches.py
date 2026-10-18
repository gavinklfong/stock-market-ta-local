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


class TestComputeSupportTouches:
    """Tests for compute_support_touches."""

    def test_no_support(self):
        """When no support level, count should be 0."""
        lows = [95] * 10
        support = [None] * 10
        result = compute_support_touches(lows, support)
        assert result == [0] * 10

    def test_support_never_touched(self):
        """When price is far from support, count stays 0."""
        lows = [100] * 10  # 10% above support
        support = [90] * 10
        result = compute_support_touches(lows, support, tolerance_pct=0.02)
        # Default tolerance is 2%, so 100 is not within 2% of 90
        assert result == [0] * 10

    def test_support_touches_count(self):
        """Price touching support should increment count."""
        np.random.seed(42)
        # Generate prices that repeatedly touch the support level
        support_level = 100.0
        tolerance = 0.02  # 2%
        # Lows just within tolerance of support (100-102 range)
        lows = [100.0, 100.5, 101.0, 101.5, 102.0]
        support = [support_level] * 5
        result = compute_support_touches(lows, support, tolerance_pct=tolerance)
        # All lows are within [98, 102], so all should count as touches
        assert result == [1, 2, 3, 4, 5]

    def test_support_broken_resets(self):
        """When support breaks (low drops below), count resets to 0."""
        lows = [100, 97, 100, 101]  # 97 breaks below 98 (100 * 0.98)
        support = [100] * 4
        result = compute_support_touches(lows, support, tolerance_pct=0.02)
        # Index 0: low=100, within [98, 102], touch=1
        # Index 1: low=97, below 98, support broken, count=0
        # Index 2: low=100, within [98, 102], touch=1
        # Index 3: low=101, within [98, 102], touch=2
        assert result == [1, 0, 1, 2]

    def test_none_support_preserves_count(self):
        """When support is None, count is preserved (not reset)."""
        lows = [100] * 3
        support = [100, None, 100]
        result = compute_support_touches(lows, support, tolerance_pct=0.02)
        assert result == [1, 1, 2]  # None preserves current count

    def test_zero_length(self):
        """Empty input should return empty list."""
        result = compute_support_touches([], [])
        assert result == []

    def test_support_touches_in_columns(self):
        """Support touches should be included in compute_structure_columns output."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(max(closes[-1] + np.random.normal(0, 1.0), 10.0))
        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]

        cols = compute_structure_columns(highs, lows, closes, n)
        assert "ta_support_touches" in cols
        assert len(cols["ta_support_touches"]) == n
        # All values should be >= 0
        for v in cols["ta_support_touches"]:
            assert v >= 0
        # Values should be integers (counts)
        for v in cols["ta_support_touches"]:
            assert isinstance(v, int)
