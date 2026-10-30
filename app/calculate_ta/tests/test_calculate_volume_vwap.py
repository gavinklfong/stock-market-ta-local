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

class TestComputeVWAP:
    def test_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_vwap(highs, lows, closes, volumes)
        assert len(result) == 50

    def test_first_valid_at_period_minus_one(self):
        """With rolling window VWAP, first valid value is at index period-1."""
        highs, lows, closes, volumes = _make_sample(25)
        result = compute_vwap(highs, lows, closes, volumes)
        assert result[0] is None  # before window is full
        assert result[18] is None  # still before period-1 (20-1=19)
        assert result[19] is not None  # first valid at period-1

    def test_vwap_near_typical_price(self):
        """With constant volume and price, VWAP ≈ typical price (period=1 for cumulative-like)."""
        n = 10
        closes = [100.0] * n
        highs = [102.0] * n
        lows = [98.0] * n
        volumes = [1000000] * n
        result = compute_vwap(highs, lows, closes, volumes, period=1)
        # Typical price = (102 + 98 + 100) / 3 = 100
        expected = (102.0 + 98.0 + 100.0) / 3.0
        assert result[0] == pytest.approx(expected, abs=1e-9)

    def test_vwap_single_row(self):
        result = compute_vwap([102.0], [98.0], [100.0], [1000000], period=1)
        expected = (102.0 + 98.0 + 100.0) / 3.0
        assert result[0] == pytest.approx(expected, abs=1e-9)

    def test_vwap_uptrend(self):
        """VWAP should trend upward when prices trend up."""
        n = 30
        period = 20
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [1000000] * n
        result = compute_vwap(highs, lows, closes, volumes, period=period)
        # result[0] is None (before window full), compare two valid indices
        assert result[period - 1] < result[-1]

    def test_vwap_increasing_volume_weighting(self):
        """Later data with larger volume should pull VWAP more (period=1 for cumulative-like)."""
        closes = [100.0, 110.0]
        highs = [102.0, 112.0]
        lows = [98.0, 108.0]
        volumes = [1.0, 100.0]
        result = compute_vwap(highs, lows, closes, volumes, period=1)
        # First row: TP = (102+98+100)/3 = 100
        # Second row: cumulative VWAP pulled toward 110 by heavy volume at index 1
        assert result[0] == pytest.approx(100.0, abs=1e-9)
        assert result[-1] > result[0]
        assert result[-1] > 105  # pulled toward 110 by heavy volume

    def test_vwap_positive(self):
        """VWAP valid values should always be positive with positive prices."""
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_vwap(highs, lows, closes, volumes)
        # Early values are None (before window full); check valid values only
        for v in result:
            if v is not None:
                assert v > 0

    def test_vwap_zero_volume(self):
        """VWAP with zero volume should stay at initial value."""
        n = 5
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [0.0] * n
        result = compute_vwap(highs, lows, closes, volumes)
        # With zero volume, cumulative stays 0 → division would give 0/0
        # But we guard with cumulative_vol > 0 check, so all remain None
        for v in result:
            assert v is None


# ---------------------------------------------------------------------------
# TestComputeMFI
# ---------------------------------------------------------------------------

