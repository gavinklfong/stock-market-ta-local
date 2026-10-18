import math
import os

import numpy as np
import pandas as pd
import pytest

from calculate_volume import (
    compute_adl,
    compute_cmf,
    compute_emv,
    compute_mfi,
    compute_obv,
    compute_vwap,
    compute_volume_columns,
    compute_volume_oscillator,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_sample(n=50, base_price=100.0, base_volume=1_000_000):
    """Generate aligned OHLCV data for testing."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 1.0)
        closes.append(max(closes[-1] + change, 10.0))

    highs = [c + abs(np.random.normal(0, 0.5)) for c in closes]
    lows = [max(c - abs(np.random.normal(0, 0.5)), 1.0) for c in closes]
    volumes = [int(base_volume * np.random.uniform(0.5, 1.5)) for _ in range(n)]

    return highs, lows, closes, volumes


# ---------------------------------------------------------------------------
# TestComputeOBV
# ---------------------------------------------------------------------------

class TestComputeOBV:
    def test_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_obv(closes, volumes)
        assert len(result) == 50

    def test_short_data(self):
        result = compute_obv([10.0], [1000])
        assert len(result) == 1

    def test_up_day_adds_volume(self):
        closes = [100.0, 105.0, 103.0]
        volumes = [1000, 2000, 1500]
        result = compute_obv(closes, volumes)
        # Day 0: obv = volume[0]
        assert result[0] == 1000.0
        # Day 1: close > close[0], add volume[1]
        assert result[1] == 1000.0 + 2000.0
        # Day 2: close < close[1], subtract volume[2]
        assert result[2] == 3000.0 - 1500.0

    def test_down_day_subtracts_volume(self):
        closes = [100.0, 95.0, 90.0]
        volumes = [1000, 2000, 3000]
        result = compute_obv(closes, volumes)
        # All down days
        assert result[0] == 1000.0
        assert result[1] == 1000.0 - 2000.0 == -1000.0
        assert result[2] == -1000.0 - 3000.0 == -4000.0

    def test_same_price_no_change(self):
        closes = [100.0, 100.0, 100.0]
        volumes = [1000, 2000, 3000]
        result = compute_obv(closes, volumes)
        # Same price → obv unchanged
        assert result[0] == 1000.0
        assert result[1] == 1000.0
        assert result[2] == 1000.0

    def test_alternating(self):
        closes = [100.0, 110.0, 100.0, 110.0]
        volumes = [1000, 2000, 3000, 4000]
        result = compute_obv(closes, volumes)
        # Up, down, up
        assert result[0] == 1000.0
        assert result[1] == 3000.0
        assert result[2] == 0.0
        assert result[3] == 4000.0

    def test_monotonic_uptrend(self):
        closes = [100.0 + i for i in range(20)]
        volumes = [1000] * 20
        result = compute_obv(closes, volumes)
        # Every day is up → strictly increasing
        for i in range(1, len(result)):
            assert result[i] > result[i - 1]

    def test_monotonic_downtrend(self):
        closes = [100.0 - i for i in range(20)]
        volumes = [1000] * 20
        result = compute_obv(closes, volumes)
        # Every day is down → strictly decreasing
        for i in range(1, len(result)):
            assert result[i] < result[i - 1]


# ---------------------------------------------------------------------------
# TestComputeCMF
# ---------------------------------------------------------------------------

