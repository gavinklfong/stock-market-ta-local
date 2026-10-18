import math
import os
import tempfile
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from calculate_momentum import (
    compute_cci,
    compute_ema,
    compute_macd,
    compute_momentum_columns,
    compute_roc,
    compute_rsi,
    compute_stochastic,
    compute_tsi,
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

