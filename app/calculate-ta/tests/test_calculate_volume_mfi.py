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

class TestComputeMFI:
    def test_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_mfi(highs, lows, closes, volumes)
        assert len(result) == 50

    def test_short_data(self):
        """When fewer than period+1 rows, all values are None."""
        highs, lows, closes, volumes = _make_sample(10)
        result = compute_mfi(highs, lows, closes, volumes)
        assert all(v is None for v in result)

    def test_first_valid_at_period_minus_one(self):
        """First valid MFI at index period-1 (13 for period=14)."""
        highs, lows, closes, volumes = _make_sample(25)
        result = compute_mfi(highs, lows, closes, volumes)
        for i in range(13):
            assert result[i] is None
        assert result[13] is not None

    def test_mfi_range(self):
        """MFI should be in range [0, 100]."""
        highs, lows, closes, volumes = _make_sample(100)
        result = compute_mfi(highs, lows, closes, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert 0.0 <= v <= 100.0

    def test_bullish_mfi_high(self):
        """When TP always increases, MFI should be 100."""
        n = 20
        closes = [100.0 + i for i in range(n)]
        highs = [c + 0.1 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [1000.0] * n
        result = compute_mfi(highs, lows, closes, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] == pytest.approx(100.0)

    def test_bearish_mfi_zero(self):
        """When TP always decreases, MFI should be 0."""
        n = 20
        closes = [100.0 - i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 0.1 for c in closes]
        volumes = [1000.0] * n
        result = compute_mfi(highs, lows, closes, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] == pytest.approx(0.0)

    def test_flat_mfi_neutral(self):
        """When TP never changes, MFI should be 50 (neutral)."""
        n = 20
        closes = [100.0] * n
        highs = [105.0] * n
        lows = [95.0] * n
        volumes = [1000.0] * n
        result = compute_mfi(highs, lows, closes, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] == pytest.approx(50.0)

    def test_mfi_with_tp_unchanged(self):
        """When TP equals previous TP, both pos and neg sums unchanged."""
        n = 20
        # First few bars: increasing TP, then flat
        closes = [100.0, 101.0, 102.0] + [102.0] * (n - 3)
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [1000.0] * n
        result = compute_mfi(highs, lows, closes, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert 0.0 <= v <= 100.0

    def test_custom_period(self):
        """MFI with custom period should work."""
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_mfi(highs, lows, closes, volumes, period=10)
        # First valid at index 9
        for i in range(9):
            assert result[i] is None
        assert result[9] is not None
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert 0.0 <= v <= 100.0

    def test_zero_volume(self):
        """Zero volume results in zero money flow."""
        n = 30
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [0.0] * n
        result = compute_mfi(highs, lows, closes, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Zero money flow both pos and neg → MFI = 50
        assert all(v == pytest.approx(50.0) for v in valid)

    def test_empty(self):
        result = compute_mfi([], [], [], [])
        assert result == []

    def test_mfi_finite(self):
        """All MFI values should be finite (no NaN/Inf)."""
        highs, lows, closes, volumes = _make_sample(100)
        result = compute_mfi(highs, lows, closes, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == v  # not NaN
            assert abs(v) < 1e15  # not Inf


# ---------------------------------------------------------------------------
# TestComputeEMV
# ---------------------------------------------------------------------------

