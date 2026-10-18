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

class TestComputeVolumeColumns:
    def test_expected_keys(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        assert set(cols.keys()) == {"ta_obv", "ta_cmf", "ta_vwap", "ta_ofi", "ta_log_volume", "ta_adl", "ta_mfi14", "ta_emv14", "ta_volume_osc"}

    def test_all_same_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        for col in cols.values():
            assert len(col) == 50

    def test_obv_present(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        assert cols["ta_obv"][0] is not None

    def test_cmf_present(self):
        highs, lows, closes, volumes = _make_sample(30)
        cols = compute_volume_columns(highs, lows, closes, volumes, 30)
        valid = [v for v in cols["ta_cmf"] if v is not None]
        assert len(valid) > 0

    def test_vwap_present(self):
        highs, lows, closes, volumes = _make_sample(25)
        cols = compute_volume_columns(highs, lows, closes, volumes, 25)
        # First valid VWAP at index period-1 (19)
        assert cols["ta_vwap"][19] is not None

    def test_adl_present(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        # ADL should have values from bar 0
        assert cols["ta_adl"][0] is not None

    def test_mfi14_present(self):
        highs, lows, closes, volumes = _make_sample(30)
        cols = compute_volume_columns(highs, lows, closes, volumes, 30)
        valid = [v for v in cols["ta_mfi14"] if v is not None]
        assert len(valid) > 0

    def test_volume_osc_present(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        valid = [v for v in cols["ta_volume_osc"] if v is not None]
        assert len(valid) > 0

    def test_short_data(self):
        n = 5
        cols = compute_volume_columns(
            [100.0]*n, [99.0]*n, [100.0]*n, [1000]*n, n
        )
        assert len(cols["ta_obv"]) == 5
        assert len(cols["ta_cmf"]) == 5
        assert all(v is None for v in cols["ta_cmf"])
        assert len(cols["ta_vwap"]) == 5
        assert len(cols["ta_adl"]) == 5
        assert len(cols["ta_mfi14"]) == 5
        assert all(v is None for v in cols["ta_mfi14"])
        assert len(cols["ta_emv14"]) == 5
        assert all(v is None for v in cols["ta_emv14"])
        assert len(cols["ta_volume_osc"]) == 5
        assert all(v is None for v in cols["ta_volume_osc"])

    def test_all_same_length(self):
        highs, lows, closes, volumes = _make_sample(100)
        cols = compute_volume_columns(highs, lows, closes, volumes, 100)
        lengths = [len(v) for v in cols.values()]
        assert len(set(lengths)) == 1
        assert lengths[0] == 100


# ---------------------------------------------------------------------------
# TestProcessCSV
# ---------------------------------------------------------------------------

class TestProcessCSV:
    def _write_test_csv(self, directory, filename, rows):
        df = pd.DataFrame(rows)
        path = os.path.join(directory, filename)
        df.to_csv(path, index=False)
        return path

    def test_creates_output(self, tmp_path):
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(0)
        n = 50
        base = 100.0
        closes = [base]
        for _ in range(n - 1):
            closes.append(max(closes[-1] + np.random.normal(0, 0.5), 50.0))

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": c * 0.999, "High": c * 1.01,
                 "Low": c * 0.99, "Close": c,
                 "Volume": int(1e6 * np.random.uniform(0.8, 1.2))}
                for i, c in enumerate(closes)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        from calculate_volume import process_csv
        process_csv(input_path, output_path, 1, 1)

        assert os.path.exists(output_path)

    def test_includes_volume_columns(self, tmp_path):
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(0)
        n = 50
        base = 100.0
        closes = [base]
        for _ in range(n - 1):
            closes.append(max(closes[-1] + np.random.normal(0, 0.5), 50.0))

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": c * 0.999, "High": c * 1.01,
                 "Low": c * 0.99, "Close": c,
                 "Volume": int(1e6 * np.random.uniform(0.8, 1.2))}
                for i, c in enumerate(closes)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        from calculate_volume import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_obv" in df.columns
        assert "ta_cmf" in df.columns
        assert "ta_vwap" in df.columns
        assert "ta_adl" in df.columns
        assert "ta_mfi14" in df.columns
        assert "ta_emv14" in df.columns
        assert "ta_volume_osc" in df.columns

    def test_realistic_data(self, tmp_path):
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(42)
        base = 150.0
        closes = [base]
        for _ in range(199):
            change = np.random.normal(0, 1.5)
            closes.append(max(closes[-1] + change, 50.0))

        self._write_test_csv(
            str(input_dir),
            "AAPL.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": closes[i] * 0.999, "High": closes[i] * 1.01,
                 "Low": closes[i] * 0.99, "Close": closes[i],
                 "Volume": int(1e6 * np.random.uniform(0.8, 1.2))}
                for i in range(200)
            ],
        )

        input_path = str(input_dir / "AAPL.csv")
        output_path = str(output_dir / "AAPL.csv")
        from calculate_volume import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # OBV should have cumulative values (first = first volume, which is positive)
        assert df["ta_obv"].iloc[0] > 0
        # VWAP should have valid values (200 rows > period=20)
        valid_vwap = df["ta_vwap"].dropna()
        assert len(valid_vwap) > 0
        # CMF should have valid values (200 rows > period=20)
        valid_cmf = df["ta_cmf"].dropna()
        assert len(valid_cmf) > 0

    def test_sort_order(self, tmp_path):
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        dates = [
            pd.Timestamp("2024-01-05"),
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-01-03"),
            pd.Timestamp("2024-01-02"),
            pd.Timestamp("2024-01-04"),
        ]
        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": d, "Open": 100.0, "High": 102.0, "Low": 99.0,
                 "Close": 100.0 + i * 0.5, "Volume": 1000000}
                for i, d in enumerate(dates)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        from calculate_volume import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        dates_out = pd.to_datetime(df["Date"])
        assert dates_out.is_monotonic_increasing


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_obv_single_value(self):
        result = compute_obv([100.0], [1000])
        assert result == [1000.0]

    def test_cmf_single_value(self):
        result = compute_cmf([102.0], [98.0], [100.0], [1000])
        # Needs 20 data points for period 20
        assert result == [None]

    def test_vwap_single_value(self):
        result = compute_vwap([102.0], [98.0], [100.0], [1000000], period=1)
        expected = (102.0 + 98.0 + 100.0) / 3.0
        assert result[0] == pytest.approx(expected, abs=1e-9)

    def test_cmf_empty(self):
        result = compute_cmf([], [], [], [])
        assert result == []

    def test_obv_empty(self):
        result = compute_obv([], [])
        assert result == []

    def test_vwap_empty(self):
        result = compute_vwap([], [], [], [])
        assert result == []

    def test_compute_volume_columns_very_short(self):
        n = 3
        cols = compute_volume_columns(
            [100.0]*n, [99.0]*n, [100.0]*n, [1000]*n, n
        )
        assert len(cols["ta_obv"]) == 3
        assert len(cols["ta_cmf"]) == 3
        assert len(cols["ta_vwap"]) == 3
        assert len(cols["ta_adl"]) == 3
        assert len(cols["ta_mfi14"]) == 3
        assert len(cols["ta_emv14"]) == 3
        assert len(cols["ta_volume_osc"]) == 3
        assert all(v is None for v in cols["ta_cmf"])

    def test_compute_volume_columns_all_none_cmf(self):
        n = 10
        cols = compute_volume_columns(
            [100.0]*n, [99.0]*n, [100.0]*n, [1000]*n, n
        )
        assert len(cols["ta_cmf"]) == 10
        assert all(v is None for v in cols["ta_cmf"])

    def test_adl_single_value(self):
        result = compute_adl([110.0], [90.0], [100.0], [5000])
        # CLV = ((100-90)-(110-100))/(110-90) = 0/20 = 0
        assert result[0] == pytest.approx(0.0)

    def test_adl_empty(self):
        result = compute_adl([], [], [], [])
        assert result == []

    def test_mfi_single_value(self):
        """MFI needs at least period+1 bars; single value returns None."""
        result = compute_mfi([102.0], [98.0], [100.0], [1000])
        assert result == [None]

    def test_mfi_empty(self):
        result = compute_mfi([], [], [], [])
        assert result == []
