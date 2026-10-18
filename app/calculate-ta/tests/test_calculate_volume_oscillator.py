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

class TestComputeVolumeOscillator:
    def test_length(self):
        volumes = [1000.0 + i for i in range(50)]
        result = compute_volume_oscillator(volumes)
        assert len(result) == 50

    def test_short_data(self):
        """When fewer than period_slow (28) rows, all values are None."""
        volumes = [1000.0 + i for i in range(20)]
        result = compute_volume_oscillator(volumes)
        assert all(v is None for v in result)

    def test_first_valid_at_period_slow_minus_one(self):
        """First valid VO at index period_slow-1 (27 for default periods)."""
        volumes = [1000.0 + i for i in range(50)]
        result = compute_volume_oscillator(volumes)
        for i in range(27):
            assert result[i] is None
        assert result[27] is not None

    def test_constant_volume_zero_oscillator(self):
        """When all volumes are equal, fast EMA = slow EMA → VO = 0."""
        volumes = [1000.0] * 50
        result = compute_volume_oscillator(volumes)
        # First valid at index 27
        for i in range(27, len(result)):
            assert result[i] == pytest.approx(0.0)

    def test_increasing_volume_positive_oscillator(self):
        """When volumes increase, fast EMA > slow EMA → VO > 0."""
        n = 50
        volumes = [1000.0 + i * 100.0 for i in range(n)]  # linearly increasing
        result = compute_volume_oscillator(volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] > 0

    def test_decreasing_volume_negative_oscillator(self):
        """When volumes decrease, fast EMA < slow EMA → VO < 0."""
        n = 50
        volumes = [6000.0 - i * 100.0 for i in range(n)]  # linearly decreasing
        result = compute_volume_oscillator(volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] < 0

    def test_oscillator_finite(self):
        """All VO values should be finite (no NaN/Inf)."""
        volumes = [1000.0 + i * (i % 3) for i in range(100)]
        result = compute_volume_oscillator(volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == v  # not NaN
            assert abs(v) < 1e15  # not Inf

    def test_empty(self):
        result = compute_volume_oscillator([])
        assert result == []

    def test_single_value(self):
        """Single value needs at least period_slow (28) bars."""
        result = compute_volume_oscillator([1000.0])
        assert result == [None]

    def test_custom_periods(self):
        """VO with custom periods should work."""
        volumes = [1000.0 + i for i in range(50)]
        result = compute_volume_oscillator(volumes, period_fast=5, period_slow=10)
        # First valid at index 9 (period_slow - 1)
        for i in range(9):
            assert result[i] is None
        assert result[9] is not None
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_volatile_volume(self):
        """Highly volatile volumes should produce reasonable VO values."""
        n = 50
        volumes = [1000.0 if i % 2 == 0 else 2000.0 for i in range(n)]
        result = compute_volume_oscillator(volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == v  # not NaN
            assert abs(v) < 1e10  # not Inf

    def test_zero_volume(self):
        """All zero volumes should produce 0 VO."""
        volumes = [0.0] * 50
        result = compute_volume_oscillator(volumes)
        for i in range(27, len(result)):
            assert result[i] == pytest.approx(0.0)

    def test_exact_period_slow_length(self):
        """Exactly period_slow bars should produce one valid value."""
        volumes = [1000.0] * 28
        result = compute_volume_oscillator(volumes)
        for i in range(27):
            assert result[i] is None
        assert result[27] is not None
        assert result[27] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# TestComputeVolumeColumns
# ---------------------------------------------------------------------------

