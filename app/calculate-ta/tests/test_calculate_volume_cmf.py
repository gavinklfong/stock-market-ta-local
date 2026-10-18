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

class TestComputeCMF:
    def test_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_cmf(highs, lows, closes, volumes)
        assert len(result) == 50

    def test_short_data(self):
        highs, lows, closes, volumes = _make_sample(10)
        result = compute_cmf(highs, lows, closes, volumes)
        assert all(v is None for v in result)

    def test_first_valid_at_period(self):
        highs, lows, closes, volumes = _make_sample(25)
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        for i in range(19):
            assert result[i] is None
        assert result[19] is not None

    def test_cmf_range(self):
        """CMF should be in range [-1, 1]."""
        highs, lows, closes, volumes = _make_sample(100)
        result = compute_cmf(highs, lows, closes, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert -1.0 <= v <= 1.0

    def test_bullish_cmf_positive(self):
        """When closes are near highs, CMF should be positive."""
        n = 30
        closes = [100.0 + i * 0.5 for i in range(n)]
        highs = [c + 0.1 for c in closes]  # small upper wick → close near high
        lows = [c - 1.0 for c in closes]  # large lower wick
        volumes = [1000000] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] > 0

    def test_bearish_cmf_negative(self):
        """When closes are near lows, CMF should be negative."""
        n = 30
        closes = [100.0 + i * 0.5 for i in range(n)]
        highs = [c + 1.0 for c in closes]  # large upper wick
        lows = [c - 0.1 for c in closes]  # small lower wick → close near low
        volumes = [1000000] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] < 0

    def test_midpoint_cmf_near_zero(self):
        """When closes are at midpoint, CMF should be near zero."""
        n = 30
        closes = [100.0] * n
        highs = [105.0] * n
        lows = [95.0] * n
        volumes = [1000000] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert abs(valid[-1]) < 0.01

    def test_period_zero_high_low(self):
        """Handle high == low gracefully."""
        n = 30
        closes = [100.0 + i for i in range(n)]
        highs = [100.0] * n
        lows = [100.0] * n
        volumes = [1000000] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        # When high == low, MFMF = 0 → CMF = 0
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_custom_period(self):
        """CMF with custom period should work."""
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_cmf(highs, lows, closes, volumes, period=10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert -1.0 <= v <= 1.0

    def test_zero_volume(self):
        """Zero volume should result in CMF of 0, not NaN."""
        n = 30
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [0] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == 0.0


# ---------------------------------------------------------------------------
# TestComputeADL
# ---------------------------------------------------------------------------

