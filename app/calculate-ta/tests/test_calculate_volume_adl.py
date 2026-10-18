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

class TestComputeADL:
    def test_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_adl(highs, lows, closes, volumes)
        assert len(result) == 50

    def test_short_data(self):
        result = compute_adl([102.0], [98.0], [100.0], [1000])
        assert len(result) == 1

    def test_empty(self):
        result = compute_adl([], [], [], [])
        assert result == []

    def test_adl_cumulative(self):
        """ADL should be cumulative: each bar adds CLV × Volume."""
        highs = [110.0, 120.0, 130.0]
        lows = [90.0, 100.0, 110.0]
        closes = [100.0, 110.0, 120.0]
        volumes = [1000.0, 1000.0, 1000.0]

        result = compute_adl(highs, lows, closes, volumes)

        # Day 0: CLV = ((100-90)-(110-100))/(110-90) = 0/20 = 0 → ADL = 0
        assert result[0] == pytest.approx(0.0)
        # Day 1: CLV = ((110-100)-(120-110))/(120-100) = 0/20 = 0 → ADL = 0
        assert result[1] == pytest.approx(0.0)
        # Day 2: same → ADL = 0
        assert result[2] == pytest.approx(0.0)

    def test_adl_bullish_clv(self):
        """When close is at the top of range, CLV is near +1, ADL increases."""
        n = 10
        closes = [100.0 + i for i in range(n)]
        highs = [c + 0.1 for c in closes]   # small upper wick → close near high
        lows = [c - 1.0 for c in closes]    # large lower wick
        volumes = [1000.0] * n

        result = compute_adl(highs, lows, closes, volumes)

        # CLV should be near +1 → ADL should increase
        for i in range(1, len(result)):
            assert result[i] > result[i - 1]

    def test_adl_bearish_clv(self):
        """When close is at the bottom of range, CLV is near -1, ADL decreases."""
        n = 10
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]   # large upper wick
        lows = [c - 0.1 for c in closes]    # small lower wick → close near low
        volumes = [1000.0] * n

        result = compute_adl(highs, lows, closes, volumes)

        # CLV should be near -1 → ADL should decrease
        for i in range(1, len(result)):
            assert result[i] < result[i - 1]

    def test_adl_midpoint_zero_clv(self):
        """When close is at midpoint, CLV ≈ 0, ADL stays flat."""
        n = 10
        closes = [100.0] * n
        highs = [105.0] * n
        lows = [95.0] * n
        volumes = [1000.0] * n

        result = compute_adl(highs, lows, closes, volumes)

        # CLV = 0 → ADL stays at 0
        for v in result:
            assert v == pytest.approx(0.0, abs=1e-9)

    def test_adl_first_bar(self):
        """First bar ADL = CLV[0] × Volume."""
        highs = [110.0]
        lows = [90.0]
        closes = [100.0]  # exact midpoint → CLV = 0
        volumes = [2000.0]

        result = compute_adl(highs, lows, closes, volumes)
        assert result[0] == pytest.approx(0.0)

    def test_adl_close_at_high(self):
        """Close at high → CLV = 1 → ADL = Volume."""
        highs = [110.0]
        lows = [90.0]
        closes = [110.0]  # at high
        volumes = [5000.0]

        result = compute_adl(highs, lows, closes, volumes)
        # CLV = ((110-90)-(110-110))/(110-90) = 20/20 = 1
        assert result[0] == pytest.approx(5000.0)

    def test_adl_close_at_low(self):
        """Close at low → CLV = -1 → ADL = -Volume."""
        highs = [110.0]
        lows = [90.0]
        closes = [90.0]  # at low
        volumes = [5000.0]

        result = compute_adl(highs, lows, closes, volumes)
        # CLV = ((90-90)-(110-90))/(110-90) = -20/20 = -1
        assert result[0] == pytest.approx(-5000.0)

    def test_adl_high_equal_low(self):
        """When high == low, CLV = 0."""
        highs = [100.0, 101.0]
        lows = [100.0, 101.0]
        closes = [100.0, 101.0]
        volumes = [1000.0, 2000.0]

        result = compute_adl(highs, lows, closes, volumes)
        # Day 0: high == low → CLV = 0 → ADL = 0
        assert result[0] == pytest.approx(0.0)
        # Day 1: high == low → CLV = 0 → ADL = 0
        assert result[1] == pytest.approx(0.0)

    def test_adl_variable_volume(self):
        """Different volumes should produce different ADL magnitudes."""
        highs = [110.0, 120.0]
        lows = [90.0, 100.0]
        closes = [110.0, 120.0]  # at high both days → CLV = 1
        volumes = [1000.0, 5000.0]

        result = compute_adl(highs, lows, closes, volumes)

        # Day 0: CLV=1 → ADL = 1000
        assert result[0] == pytest.approx(1000.0)
        # Day 1: CLV=1 → ADL = 1000 + 5000 = 6000
        assert result[1] == pytest.approx(6000.0)

    def test_adl_mixed_direction(self):
        """Mixed up/down days should produce mixed ADL movement."""
        highs = [110.0, 105.0, 115.0]
        lows = [90.0, 95.0, 105.0]
        closes = [110.0, 95.0, 115.0]  # at high, at low, at high
        volumes = [1000.0, 1000.0, 1000.0]

        result = compute_adl(highs, lows, closes, volumes)

        # Day 0: CLV=1 → ADL = 1000
        assert result[0] == pytest.approx(1000.0)
        # Day 1: CLV=-1 → ADL = 1000 - 1000 = 0
        assert result[1] == pytest.approx(0.0)
        # Day 2: CLV=1 → ADL = 0 + 1000 = 1000
        assert result[2] == pytest.approx(1000.0)

    def test_adl_positive_prices(self):
        """ADL values can be positive or negative but should be finite."""
        highs, lows, closes, volumes = _make_sample(100)
        result = compute_adl(highs, lows, closes, volumes)
        for v in result:
            assert v == v  # not NaN
            assert abs(v) < 1e15


# ---------------------------------------------------------------------------
# TestComputeVWAP
# ---------------------------------------------------------------------------

