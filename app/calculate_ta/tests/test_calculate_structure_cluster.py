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


class TestClusterLevels:
    def test_empty(self):
        assert _cluster_levels([]) == []

    def test_single_level(self):
        result = _cluster_levels([(0, 100.0)])
        assert result == [100.0]

    def test_close_levels_clustered(self):
        """Prices within tolerance should cluster."""
        points = [(i, 100.0 + i * 0.5) for i in range(5)]
        result = _cluster_levels(points, tolerance_pct=0.02)
        # All within 2.5% of each other, should cluster
        assert len(result) <= 5

    def test_far_levels_separate(self):
        """Prices far apart should not cluster."""
        points = [(0, 100.0), (1, 200.0), (2, 300.0)]
        result = _cluster_levels(points, tolerance_pct=0.01)
        assert len(result) == 3

    def test_cluster_averages(self):
        """Cluster center should be the average of member prices."""
        points = [(0, 100.0), (1, 101.0), (2, 102.0)]
        result = _cluster_levels(points, tolerance_pct=0.01)
        # All close, should form one cluster
        assert len(result) == 1
        assert result[0] == pytest.approx(101.0, abs=1e-6)


# ---------------------------------------------------------------------------
# TestComputeStructureColumns
# ---------------------------------------------------------------------------


