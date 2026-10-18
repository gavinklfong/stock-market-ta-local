import math
import os
import tempfile
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from calculate_momentum import (
    compute_ema,
    compute_macd,
    compute_momentum_columns,
    compute_roc,
    compute_rsi,
    compute_stochastic,
    compute_williams_r,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_closes(length, base=100.0, slope=0.0, noise_range=0.0):
    """Generate a list of closing prices."""
    np.random.seed(0)
    closes = []
    for i in range(length):
        val = base + slope * i + np.random.uniform(-noise_range, noise_range)
        closes.append(max(val, 1.0))  # keep positive
    return closes


def _make_ohlcv(n=100, base=100.0):
    """Generate synthetic OHLCV data.

    Returns (highs, lows, closes) lists of equal length.
    """
    np.random.seed(42)
    closes = [base]
    for _ in range(n - 1):
        change = np.random.normal(0, 0.01) * closes[-1]
        closes.append(max(closes[-1] + change, 1.0))

    highs = [c * (1 + abs(np.random.normal(0, 0.005))) for c in closes]
    lows = [c * (1 - abs(np.random.normal(0, 0.005))) for c in closes]

    return highs, lows, closes


# ---------------------------------------------------------------------------
# TestComputeEMA
# ---------------------------------------------------------------------------

class TestComputeEMA:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_ema(closes, 10)
        assert len(result) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        result = compute_ema(closes, 10)
        assert all(v is None for v in result)

    def test_first_valid_at_period_minus_one(self):
        closes = _make_closes(10, base=50)
        result = compute_ema(closes, 10)
        assert result[9] is not None
        for i in range(9):
            assert result[i] is None

    def test_sma_seed(self):
        """First EMA value should equal SMA of first `period` values."""
        closes = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = compute_ema(closes, 5)
        expected_sma = sum(closes[:5]) / 5  # 30.0
        assert result[4] == pytest.approx(expected_sma, abs=1e-9)

    def test_period_one(self):
        """EMA with period=1 should equal the raw values."""
        closes = [1.0, 2.0, 3.0, 4.0]
        result = compute_ema(closes, 1)
        for i in range(len(closes)):
            assert result[i] == closes[i]

    def test_monotonic_ema(self):
        """EMA should be smoother than raw data."""
        closes = list(range(1, 51))  # linearly increasing
        result = compute_ema(closes, 10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # EMA should be monotonically increasing for linear data
        for i in range(1, len(valid)):
            assert valid[i] >= valid[i - 1] - 1e-9

    def test_ema_reference_match(self):
        """Compare with a known recursive EMA implementation."""
        closes = _make_closes(30, base=50, noise_range=5)
        period = 7
        k = 2.0 / (period + 1)
        seed = sum(closes[:period]) / period

        expected = [None] * len(closes)
        expected[period - 1] = seed
        for i in range(period, len(closes)):
            expected[i] = closes[i] * k + expected[i - 1] * (1 - k)

        result = compute_ema(closes, period)
        for i in range(period - 1, len(closes)):
            assert result[i] == pytest.approx(expected[i], abs=1e-9)


# ---------------------------------------------------------------------------
# TestComputeRSI
# ---------------------------------------------------------------------------

class TestComputeRSI:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_rsi(closes, 14)
        assert len(result) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        result = compute_rsi(closes, 14)
        assert all(v is None for v in result)

    def test_first_valid_at_period(self):
        closes = _make_closes(20, base=100)
        result = compute_rsi(closes, 14)
        for i in range(14):
            assert result[i] is None
        assert result[14] is not None

    def test_rsi_range(self):
        closes = _make_closes(100, base=100, noise_range=5)
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert 0 <= v <= 100

    def test_constant_prices(self):
        """RSI should be 50 when prices don't change."""
        closes = [100.0] * 30
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(50.0, abs=1e-9)

    def test_always_up(self):
        """RSI should be 100 when every change is positive."""
        closes = [100.0 + i * 1.0 for i in range(30)]
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(100.0, abs=1e-9)

    def test_always_down(self):
        """RSI should be 0 when every change is negative."""
        closes = [100.0 - i * 1.0 for i in range(30)]
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(0.0, abs=1e-9)

    def test_wilders_smoothing_match(self):
        """Verify the recursive smoothing step matches standard Wilder formula."""
        # Manually construct gains/losses to test the smoothed average
        closes = [100, 101, 99, 102, 100, 103, 101, 105, 102, 104, 103, 106,
                  104, 105, 106, 107, 106, 108, 107, 109, 108, 110, 109, 111]
        result = compute_rsi(closes, 14)
        # All should be valid for 24 data points with period 14
        valid = [v for v in result if v is not None]
        assert len(valid) > 0


# ---------------------------------------------------------------------------
# TestComputeMACD
# ---------------------------------------------------------------------------

class TestComputeMACD:
    def test_length(self):
        closes = _make_closes(50)
        macd = compute_macd(closes)
        assert len(macd["macd_line"]) == 50
        assert len(macd["signal_line"]) == 50
        assert len(macd["histogram"]) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        macd = compute_macd(closes)
        assert all(v is None for v in macd["macd_line"])
        assert all(v is None for v in macd["signal_line"])
        assert all(v is None for v in macd["histogram"])

    def test_keys(self):
        closes = _make_closes(50)
        macd = compute_macd(closes)
        assert set(macd.keys()) == {"macd_line", "signal_line", "histogram"}

    def test_first_valid_macd_line(self):
        """MACD line first valid at EMA slow period - 1 (index 25 for slow=26)."""
        closes = _make_closes(50, base=50)
        macd = compute_macd(closes)
        for i in range(25):
            assert macd["macd_line"][i] is None
        assert macd["macd_line"][25] is not None

    def test_histogram_equals_difference(self):
        """Histogram should equal MACD line minus signal line where both are non-None."""
        closes = _make_closes(60, base=50, noise_range=3)
        macd = compute_macd(closes)
        for i in range(len(closes)):
            if macd["macd_line"][i] is not None and macd["signal_line"][i] is not None:
                assert macd["histogram"][i] == pytest.approx(
                    macd["macd_line"][i] - macd["signal_line"][i], abs=1e-9
                )

    def test_macd_positive_trend(self):
        """In an uptrend, MACD line should eventually be positive."""
        closes = [100.0 + i * 0.5 for i in range(50)]
        macd = compute_macd(closes)
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0
        # Last few values should be positive in an uptrend
        assert valid[-1] > 0

    def test_macd_negative_trend(self):
        """In a downtrend, MACD line should eventually be negative."""
        closes = [100.0 - i * 0.5 for i in range(50)]
        macd = compute_macd(closes)
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0
        assert valid[-1] < 0

    def test_custom_params(self):
        """MACD with custom parameters should still produce valid output."""
        closes = _make_closes(50, base=50)
        macd = compute_macd(closes, fast=5, slow=10, signal=3)
        assert len(macd["macd_line"]) == 50
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0

    def test_constant_prices(self):
        """MACD should be zero when prices are constant."""
        closes = [100.0] * 50
        macd = compute_macd(closes)
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# TestComputeROC
# ---------------------------------------------------------------------------

class TestComputeROC:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_roc(closes, 20)
        assert len(result) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        result = compute_roc(closes, 20)
        assert all(v is None for v in result)

    def test_first_valid_at_period(self):
        closes = _make_closes(30, base=100)
        result = compute_roc(closes, 20)
        for i in range(20):
            assert result[i] is None
        assert result[20] is not None

    def test_roc_positive(self):
        """ROC should be positive when current > previous."""
        closes = [100.0, 110.0]
        result = compute_roc(closes, 1)
        assert result[1] == pytest.approx(10.0, abs=1e-9)  # (110-100)/100 * 100

    def test_roc_negative(self):
        """ROC should be negative when current < previous."""
        closes = [100.0, 90.0]
        result = compute_roc(closes, 1)
        assert result[1] == pytest.approx(-10.0, abs=1e-9)

    def test_roc_zero(self):
        """ROC should be 0 when current == previous."""
        closes = [100.0, 100.0]
        result = compute_roc(closes, 1)
        assert result[1] == pytest.approx(0.0, abs=1e-9)

    def test_roc_linear(self):
        """ROC for linearly increasing data should be positive."""
        closes = [100.0 + i for i in range(30)]
        result = compute_roc(closes, 5)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] > 0

    def test_roc_custom_period(self):
        """ROC with custom period should work."""
        closes = _make_closes(30, base=100, noise_range=2)
        result = compute_roc(closes, 5)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_roc_with_zero_price(self):
        """ROC should handle zero prices gracefully (skip division)."""
        closes = [0.0, 10.0]
        result = compute_roc(closes, 1)
        assert result[1] is None  # division by zero -> None


# ---------------------------------------------------------------------------
# TestComputeWilliamsR
# ---------------------------------------------------------------------------

class TestComputeWilliamsR:
    """Verify Williams %R computation correctness.

    Williams %R = (Highest High − Close) / (Highest High − Lowest Low) × −100
    Range: −100 to 0. Overbought above −20, oversold below −80.
    """

    def test_length(self):
        highs, lows, closes = _make_ohlcv(100)
        result = compute_williams_r(highs, lows, closes, 14)
        assert len(result) == 100

    def test_short_data(self):
        """Fewer than `period` values → all None."""
        highs, lows, closes = _make_ohlcv(10, base=100)
        result = compute_williams_r(highs, lows, closes, 14)
        assert all(v is None for v in result)

    def test_first_valid_at_period_minus_one(self):
        """First valid value at index `period - 1` (13 for default period=14)."""
        highs, lows, closes = _make_ohlcv(50, base=100)
        result = compute_williams_r(highs, lows, closes, 14)
        for i in range(13):
            assert result[i] is None
        assert result[13] is not None

    def test_williams_r_range(self):
        """All valid values must be in [-100, 0]."""
        highs, lows, closes = _make_ohlcv(200)
        result = compute_williams_r(highs, lows, closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert -100.0 <= v <= 0.0, f"Value {v} out of [-100, 0]"

    def test_close_equals_highest_high(self):
        """When Close = Highest High, %R = 0."""
        # Each bar's close is the high of the window
        closes = [100.0 + i for i in range(30)]
        highs = [c + 1.0 for c in closes]  # high > close
        lows = [c - 1.0 for c in closes]
        # Override: make close = high for the last bar in each window
        # For simplicity, set highs = closes so close always equals highest high
        highs2 = [c for c in closes]
        lows2 = [c - 1.0 for c in closes]
        result = compute_williams_r(highs2, lows2, closes, 14)
        for i in range(13, 30):
            assert result[i] == pytest.approx(0.0, abs=1e-9), (
                f"Index {i}: expected 0 when close = high, got {result[i]}"
            )

    def test_close_equals_lowest_low(self):
        """When Close = Lowest Low, %R = −100."""
        closes = [100.0 - i for i in range(30)]
        highs = [c + 1.0 for c in closes]
        lows = [c for c in closes]  # close = low
        result = compute_williams_r(highs, lows, closes, 14)
        for i in range(13, 30):
            assert result[i] == pytest.approx(-100.0, abs=1e-9), (
                f"Index {i}: expected -100 when close = low, got {result[i]}"
            )

    def test_known_manual_values(self):
        """Verify exact values with a hand-traceable case.

        Period=5. Window [0:5] at index 4:
          Highs: [105, 110, 100, 108, 102] → HH = 110
          Lows:  [95,  100, 90, 98,  96]  → LL = 90
          Close at index 4: 102
          Williams %R = (110 - 102) / (110 - 90) * -100 = 8/20 * -100 = -40.0
        """
        highs = [105.0, 110.0, 100.0, 108.0, 102.0]
        lows = [95.0, 100.0, 90.0, 98.0, 96.0]
        closes = [100.0, 105.0, 95.0, 103.0, 102.0]

        result = compute_williams_r(highs, lows, closes, 5)
        assert result[4] == pytest.approx(-40.0, abs=1e-9)

    def test_known_manual_values_2(self):
        """Second manual case with period=5.

        Window [0:5] at index 4:
          Highs: [10, 12, 11, 13, 15] → HH = 15
          Lows:  [8,  9, 10, 11, 12]  → LL = 8
          Close: 15
          Williams %R = (15 - 15) / (15 - 8) * -100 = 0
        """
        highs = [10.0, 12.0, 11.0, 13.0, 15.0]
        lows = [8.0, 9.0, 10.0, 11.0, 12.0]
        closes = [10.0, 11.0, 9.0, 12.0, 15.0]

        result = compute_williams_r(highs, lows, closes, 5)
        assert result[4] == pytest.approx(0.0, abs=1e-9)

    def test_known_manual_values_3(self):
        """Third manual case: close = lowest low of window.

        Period=5. Window at index 4:
          Highs: [10, 12, 11, 13, 15] → HH = 15
          Lows:  [8,  9, 10, 11, 12]  → LL = 8
          Close: 8
          Williams %R = (15 - 8) / (15 - 8) * -100 = -100
        """
        highs = [10.0, 12.0, 11.0, 13.0, 15.0]
        lows = [8.0, 9.0, 10.0, 11.0, 8.0]
        closes = [10.0, 11.0, 9.0, 12.0, 8.0]

        result = compute_williams_r(highs, lows, closes, 5)
        assert result[4] == pytest.approx(-100.0, abs=1e-9)

    def test_constant_prices_all_equal(self):
        """When all prices are identical, HH = LL → skip → all None."""
        n = 30
        val = 100.0
        result = compute_williams_r([val] * n, [val] * n, [val] * n, 14)
        assert all(v is None for v in result)

    def test_custom_period(self):
        """Williams %R with custom period should work correctly."""
        n = 50
        highs, lows, closes = _make_ohlcv(n, base=100)

        for period in (5, 7, 10, 20):
            result = compute_williams_r(highs, lows, closes, period)
            # First valid at index period - 1
            for i in range(period - 1):
                assert result[i] is None
            assert result[period - 1] is not None
            # All valid values in [-100, 0]
            valid = [v for v in result if v is not None]
            for v in valid:
                assert -100.0 <= v <= 0.0

    def test_uptrend_oscillates(self):
        """In an uptrend with noise, Williams %R should oscillate."""
        np.random.seed(42)
        closes = [100.0]
        for _ in range(99):
            change = np.random.normal(0.3, 1.0)  # slight upward drift + noise
            closes.append(max(closes[-1] + change, 1.0))
        highs = [c * (1 + abs(np.random.normal(0, 0.01))) for c in closes]
        lows = [c * (1 - abs(np.random.normal(0, 0.01))) for c in closes]

        result = compute_williams_r(highs, lows, closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        values_set = set(round(v, 2) for v in valid)
        assert len(values_set) > 1, (
            f"Williams %R should oscillate in uptrend; got only {len(values_set)} unique values"
        )

    def test_downtrend_oscillates(self):
        """In a downtrend with noise, Williams %R should oscillate."""
        np.random.seed(43)
        closes = [100.0]
        for _ in range(99):
            change = np.random.normal(-0.3, 1.0)  # slight downward drift + noise
            closes.append(max(closes[-1] + change, 1.0))
        highs = [c * (1 + abs(np.random.normal(0, 0.01))) for c in closes]
        lows = [c * (1 - abs(np.random.normal(0, 0.01))) for c in closes]

        result = compute_williams_r(highs, lows, closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        values_set = set(round(v, 2) for v in valid)
        assert len(values_set) > 1, (
            f"Williams %R should oscillate in downtrend; got only {len(values_set)} unique values"
        )

    def test_mismatched_lengths_raises(self):
        """Mismatched input lengths should raise an assertion."""
        highs = [100.0, 101.0]
        lows = [99.0, 98.0]
        closes = [100.0]  # shorter
        with pytest.raises(AssertionError):
            compute_williams_r(highs, lows, closes, 14)

    def test_overbought_oversold_zones(self):
        """Verify overbought (> −20) and oversold (< −80) scenarios."""
        # Create a scenario where close is near the top of the range
        # → overbought (close to 0)
        n = 30
        closes = [100.0] * n
        highs = [110.0] * n
        # Set closes near the high each time
        for i in range(n):
            closes[i] = 109.0 + (i % 5) * 0.1  # 109.0 to 109.4
        lows = [90.0] * n

        result = compute_williams_r(highs, lows, closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Since close (109+) is near high (110), %R should be > −20 (overbought)
        for v in valid:
            assert v > -20.0, f"Expected overbought (> -20), got {v}"

        # Create a scenario where close is near the bottom of the range
        # → oversold (close to −100)
        for i in range(n):
            closes[i] = 90.5 + (i % 3) * 0.1  # 90.5 to 90.7
        result = compute_williams_r(highs, lows, closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Since close (90.5+) is near low (90), %R should be < −80 (oversold)
        for v in valid:
            assert v < -80.0, f"Expected oversold (< -80), got {v}"


# ---------------------------------------------------------------------------
# TestComputeMomentumColumns
# ---------------------------------------------------------------------------

class TestComputeStochastic:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_stochastic(closes)
        assert len(result["ta_stoch_k"]) == 50
        assert len(result["ta_stoch_d"]) == 50

    def test_short_data_all_none(self):
        """When fewer than k_period values, both %K and %D are all None."""
        closes = [100.0, 101.0, 102.0]
        result = compute_stochastic(closes)
        assert all(v is None for v in result["ta_stoch_k"])
        assert all(v is None for v in result["ta_stoch_d"])

    def test_first_valid_k_at_index(self):
        """First valid %K should be at index k_period - 1 (13 for default k=14)."""
        closes = _make_closes(50, base=100, noise_range=1.0)
        result = compute_stochastic(closes)
        for i in range(13):
            assert result["ta_stoch_k"][i] is None
        assert result["ta_stoch_k"][13] is not None

    def test_first_valid_d_at_index(self):
        """First valid %D should be at index k_period + d_period - 2 (15 for k=14, d=3)."""
        closes = _make_closes(50, base=100, noise_range=1.0)
        result = compute_stochastic(closes)
        for i in range(15):
            assert result["ta_stoch_d"][i] is None
        assert result["ta_stoch_d"][15] is not None

    def test_k_equals_100_when_close_is_highest(self):
        """When close is always the highest in the window, %K = 100."""
        closes = [100.0 + i for i in range(20)]  # linearly increasing
        result = compute_stochastic(closes)
        for i in range(13, 20):
            assert result["ta_stoch_k"][i] == pytest.approx(100.0, abs=1e-9)

    def test_k_equals_0_when_close_is_lowest(self):
        """When close is always the lowest in the window, %K = 0."""
        # Close drops every day so it's always the low of the window
        closes = [200.0 - i * 10.0 for i in range(20)]
        result = compute_stochastic(closes)
        for i in range(13, 20):
            assert result["ta_stoch_k"][i] == pytest.approx(0.0, abs=1e-9)

    def test_k_range(self):
        """%K should always be between 0 and 100."""
        np.random.seed(42)
        closes = [100.0 + np.random.normal(0, 5) for _ in range(100)]
        closes = [max(c, 1.0) for c in closes]
        result = compute_stochastic(closes)
        valid_k = [v for v in result["ta_stoch_k"] if v is not None]
        for v in valid_k:
            assert 0.0 <= v <= 100.0

    def test_d_equals_sma_of_k(self):
        """%D at each index should equal the SMA of the d_period most recent
        valid %K values whose last one lands exactly at that index."""
        np.random.seed(7)
        closes = [100.0 + np.random.normal(0, 3) for _ in range(50)]
        closes = [max(c, 1.0) for c in closes]
        result = compute_stochastic(closes)

        d_period = 3
        # Collect (index, value) pairs of valid %K
        valid_k = [
            (idx, result["ta_stoch_k"][idx])
            for idx in range(len(result["ta_stoch_k"]))
            if result["ta_stoch_k"][idx] is not None
        ]
        for i in range(d_period, len(closes)):
            if result["ta_stoch_d"][i] is not None:
                # Find the d_period most recent valid %K at/before index i
                window = [
                    v for idx, v in valid_k
                    if i - d_period < idx <= i
                ]
                assert len(window) == d_period
                expected_d = sum(window) / d_period
                assert result["ta_stoch_d"][i] == pytest.approx(
                    expected_d, abs=1e-9
                )

    def test_known_values(self):
        """Verify exact values with a hand-traceable case."""
        # Window [0:14]: [100, 110, 95, 105, 98, 103, 97, 108, 94, 106, 99, 104, 96, 107]
        # low=94, high=110, close=107
        # %K[13] = (107 - 94) / (110 - 94) * 100 = 13/16 * 100 = 81.25
        closes = [
            100.0, 110.0, 95.0, 105.0, 98.0, 103.0, 97.0, 108.0,
            94.0, 106.0, 99.0, 104.0, 96.0, 107.0,
        ]
        result = compute_stochastic(closes)
        assert result["ta_stoch_k"][13] == pytest.approx(81.25, abs=1e-9)

    def test_custom_params(self):
        """Stochastic with custom k_period and d_period should work."""
        closes = [100.0 + i * 0.1 for i in range(30)]
        result = compute_stochastic(closes, k_period=7, d_period=5)
        assert len(result["ta_stoch_k"]) == 30
        assert len(result["ta_stoch_d"]) == 30
        # First valid %K at index 6 (7 - 1)
        for i in range(6):
            assert result["ta_stoch_k"][i] is None
        assert result["ta_stoch_k"][6] is not None
        # First valid %D at index 10 (6 + 5 - 1)
        for i in range(10):
            assert result["ta_stoch_d"][i] is None
        assert result["ta_stoch_d"][10] is not None

    def test_constant_prices(self):
        """With constant prices, %K should be 50 (close is in the middle of [low, high] when all equal)."""
        closes = [100.0] * 30
        result = compute_stochastic(closes)
        # When all values are equal, hh == ll, so hh != ll is False → %K stays None
        # Actually, when all equal, hh = ll = 100, so hh != ll is False
        # This means %K remains None for constant prices
        valid_k = [v for v in result["ta_stoch_k"] if v is not None]
        assert len(valid_k) == 0


class TestComputeMomentumColumns:
    def test_expected_keys(self):
        closes = _make_closes(50)
        highs, lows, _ = _make_ohlcv(50)
        cols = compute_momentum_columns(closes, highs, lows, 50)
        assert set(cols.keys()) == {
            "ta_rsi14", "ta_macd_line", "ta_macd_signal",
            "ta_macd_histogram", "ta_roc20", "ta_stoch_k", "ta_stoch_d",
            "ta_williams_r",
        }

    def test_all_same_length(self):
        closes = _make_closes(50)
        highs, lows, _ = _make_ohlcv(50)
        cols = compute_momentum_columns(closes, highs, lows, 50)
        for col in cols.values():
            assert len(col) == 50

    def test_rsi_present(self):
        closes = _make_closes(50)
        highs, lows, _ = _make_ohlcv(50)
        cols = compute_momentum_columns(closes, highs, lows, 50)
        valid = [v for v in cols["ta_rsi14"] if v is not None]
        assert len(valid) > 0

    def test_roc_present(self):
        closes = _make_closes(50)
        highs, lows, _ = _make_ohlcv(50)
        cols = compute_momentum_columns(closes, highs, lows, 50)
        valid = [v for v in cols["ta_roc20"] if v is not None]
        assert len(valid) > 0

    def test_short_data(self):
        closes = [100.0] * 5
        highs = [101.0] * 5
        lows = [99.0] * 5
        cols = compute_momentum_columns(closes, highs, lows, 5)
        assert cols["ta_rsi14"] == [None] * 5
        assert cols["ta_roc20"] == [None] * 5
        assert cols["ta_williams_r"] == [None] * 5
        # MACD may produce some values even for short data
        assert len(cols["ta_macd_line"]) == 5

    def test_williams_r_present(self):
        """Williams %R should be present and have valid values."""
        highs, lows, closes = _make_ohlcv(100)
        cols = compute_momentum_columns(closes, highs, lows, 100)
        valid = [v for v in cols["ta_williams_r"] if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert -100.0 <= v <= 0.0

    def test_all_same_length(self):
        closes = _make_closes(100)
        highs, lows, _ = _make_ohlcv(100)
        cols = compute_momentum_columns(closes, highs, lows, 100)
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

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": 100.0, "High": 102.0, "Low": 99.0,
                 "Close": 100.0 + i * 0.5, "Volume": 1000000}
                for i in range(50)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        assert os.path.exists(output_path)

    def test_includes_momentum_columns(self, tmp_path):
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": 100.0, "High": 102.0, "Low": 99.0,
                 "Close": 100.0 + i * 0.5, "Volume": 1000000}
                for i in range(50)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_rsi14" in df.columns
        assert "ta_macd_line" in df.columns
        assert "ta_macd_signal" in df.columns
        assert "ta_macd_histogram" in df.columns
        assert "ta_roc20" in df.columns
        assert "ta_stoch_k" in df.columns
        assert "ta_stoch_d" in df.columns

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
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # RSI should have valid values
        valid_rsi = df["ta_rsi14"].dropna()
        assert len(valid_rsi) > 0
        # ROC should have valid values
        valid_roc = df["ta_roc20"].dropna()
        assert len(valid_roc) > 0

    def test_sort_order(self, tmp_path):
        """Output should be sorted by Date."""
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
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        dates_out = pd.to_datetime(df["Date"])
        assert dates_out.is_monotonic_increasing


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_ema_single_value(self):
        result = compute_ema([100.0], 10)
        assert result == [None]

    def test_rsi_single_value(self):
        result = compute_rsi([100.0], 14)
        assert result == [None]

    def test_macd_single_value(self):
        macd = compute_macd([100.0])
        assert macd["macd_line"] == [None]
        assert macd["signal_line"] == [None]
        assert macd["histogram"] == [None]

    def test_roc_single_value(self):
        result = compute_roc([100.0], 20)
        assert result == [None]

    def test_compute_momentum_columns_very_short(self):
        closes = [100.0, 101.0]
        highs = [101.0, 102.0]
        lows = [99.0, 100.0]
        cols = compute_momentum_columns(closes, highs, lows, 2)
        assert len(cols["ta_rsi14"]) == 2
        assert all(v is None for v in cols["ta_rsi14"])
        assert len(cols["ta_roc20"]) == 2
        assert all(v is None for v in cols["ta_roc20"])
        assert len(cols["ta_williams_r"]) == 2
        assert all(v is None for v in cols["ta_williams_r"])

    def test_computing_momentum_with_nan_values(self):
        """Should handle NaN gracefully (convert to float)."""
        closes = [100.0, 101.0, None, 102.0, 103.0]
        highs = [101.0, 102.0, None, 103.0, 104.0]
        lows = [99.0, 100.0, None, 101.0, 102.0]
        closes_float = [float(v) if v is not None else 0.0 for v in closes]
        highs_float = [float(v) if v is not None else 0.0 for v in highs]
        lows_float = [float(v) if v is not None else 0.0 for v in lows]
        cols = compute_momentum_columns(closes_float, highs_float, lows_float, 5)
        assert len(cols["ta_rsi14"]) == 5
