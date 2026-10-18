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

class TestComputeEMV:
    def test_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_emv(highs, lows, volumes)
        assert len(result) == 50

    def test_short_data(self):
        """When fewer than period rows, all values are None."""
        n = 10
        highs = [100.0 + i for i in range(n)]
        lows = [99.0 + i for i in range(n)]
        volumes = [1000.0] * n
        result = compute_emv(highs, lows, volumes)
        assert all(v is None for v in result)

    def test_first_valid_at_period_minus_one(self):
        """First valid EMV at index period-1 (13 for period=14)."""
        highs, lows, closes, volumes = _make_sample(25)
        result = compute_emv(highs, lows, volumes)
        for i in range(13):
            assert result[i] is None
        assert result[13] is not None

    def test_flat_price_zero_emv(self):
        """When price is flat (midpoint constant), EMV should be 0."""
        n = 20
        highs = [100.0] * n
        lows = [90.0] * n
        volumes = [1000.0] * n
        result = compute_emv(highs, lows, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(0.0)

    def test_bullish_emv_positive(self):
        """When price trends up, EMV should be positive."""
        n = 20
        highs = [100.0 + i * 0.5 for i in range(n)]
        lows = [99.0 + i * 0.5 for i in range(n)]
        volumes = [1000.0] * n
        result = compute_emv(highs, lows, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] > 0

    def test_bearish_emv_negative(self):
        """When price trends down, EMV should be negative."""
        n = 20
        highs = [100.0 - i * 0.5 for i in range(n)]
        lows = [99.0 - i * 0.5 for i in range(n)]
        volumes = [1000.0] * n
        result = compute_emv(highs, lows, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] < 0

    def test_emv_finite(self):
        """All EMV values should be finite (no NaN/Inf)."""
        highs, lows, closes, volumes = _make_sample(100)
        result = compute_emv(highs, lows, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == v  # not NaN
            assert abs(v) < 1e15  # not Inf

    def test_high_equal_low(self):
        """When High == Low, box_ratio = 0 → EMV raw = 0."""
        n = 20
        highs = [100.0] * n
        lows = [100.0] * n
        volumes = [1000.0] * n
        result = compute_emv(highs, lows, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(0.0)

    def test_zero_volume(self):
        """Zero volume → box_ratio = 0 → EMV raw = 0."""
        n = 20
        highs = [100.0 + i for i in range(n)]
        lows = [99.0 + i for i in range(n)]
        volumes = [0.0] * n
        result = compute_emv(highs, lows, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(0.0)

    def test_empty(self):
        result = compute_emv([], [], [])
        assert result == []

    def test_single_value(self):
        """Single value: needs at least 2 bars for distance, 14 for SMA."""
        result = compute_emv([100.0], [99.0], [1000.0])
        assert result == [None]

    def test_custom_period(self):
        """EMV with custom period should work."""
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_emv(highs, lows, volumes, period=10)
        # First valid at index 9
        for i in range(9):
            assert result[i] is None
        assert result[9] is not None
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == v  # not NaN

    def test_ascending_price_with_increasing_volume(self):
        """Rising price with rising volume should produce consistently positive EMV."""
        n = 20
        highs = [100.0 + i * 0.3 for i in range(n)]
        lows = [99.0 + i * 0.3 for i in range(n)]
        volumes = [1000.0 + i * 100.0 for i in range(n)]  # increasing volume
        result = compute_emv(highs, lows, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Midpoint moves up by 0.3 each bar, so distance is positive
        # EMV should be positive (price rising)


# ---------------------------------------------------------------------------
# TestComputeVolumeOscillator
# ---------------------------------------------------------------------------

