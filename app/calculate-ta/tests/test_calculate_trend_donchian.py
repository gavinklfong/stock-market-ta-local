"""Unit tests for calculate_trend.py — verifies EMA, ATR, and SuperTrend calculations."""

import csv
import math
import os
import random
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from calculate_trend import (
    compute_ema,
    compute_atr,
    compute_supertrend,
    compute_trend_columns,
    compute_adx_di,
    compute_aroon,
    compute_donchian,
    compute_keltner,
    process_csv,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_csv(filepath, rows, header=None):
    """Write a minimal OHLCV CSV for testing."""
    if header is None:
        header = ["Date", "Open", "High", "Low", "Close", "Volume"]
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)


def _make_small_ohlcv(n=60):
    """Generate synthetic OHLCV data with ~1% daily moves.

    Returns (highs, lows, closes) lists.
    """
    import random
    random.seed(42)

    closes = [100.0]
    for _ in range(n - 1):
        change = random.uniform(-0.01, 0.01)
        closes.append(closes[-1] * (1 + change))

    highs = []
    lows = []
    for i, c in enumerate(closes):
        if i == 0:
            highs.append(c * 1.005)
            lows.append(c * 0.995)
        else:
            prev_c = closes[i - 1]
            highs.append(max(c, prev_c) * (1 + random.uniform(0, 0.005)))
            lows.append(min(c, prev_c) * (1 - random.uniform(0, 0.005)))

    return highs, lows, closes


def _compute_reference_ema(values, period):
    """Reference EMA using the same recursive formula."""
    k = 2.0 / (period + 1)
    ema = sum(float(v) for v in values[:period]) / period
    result = [None] * len(values)
    for i in range(period - 1, len(values)):
        result[i] = ema
        if i < len(values) - 1:
            ema = float(values[i + 1]) * k + ema * (1 - k)
    return result


# ---------------------------------------------------------------------------
# EMA tests
# ---------------------------------------------------------------------------

class TestComputeDonchian:
    """Verify Donchian Upper and Lower computation correctness."""

    def test_donchian_returns_correct_keys(self):
        """Result dict must contain donchian_upper and donchian_lower."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_donchian(highs, lows)
        assert "donchian_upper" in result
        assert "donchian_lower" in result

    def test_donchian_returns_correct_length(self):
        """All lists must match input length."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_donchian(highs, lows)
        assert len(result["donchian_upper"]) == 60
        assert len(result["donchian_lower"]) == 60

    def test_donchian_too_few_data_points(self):
        """With fewer than period data points, all values must be None."""
        highs = [100.0, 101.0]
        lows = [99.0, 100.0]
        result = compute_donchian(highs, lows, period=20)
        assert all(v is None for v in result["donchian_upper"])
        assert all(v is None for v in result["donchian_lower"])

    def test_donchian_first_valid_index_default_period(self):
        """First valid value should be at index period-1 (19 for period=20)."""
        n = 50
        highs, lows, closes = _make_small_ohlcv(n)
        result = compute_donchian(highs, lows, period=20)

        for i in range(19):
            assert result["donchian_upper"][i] is None, (
                f"donchian_upper at index {i} should be None"
            )
            assert result["donchian_lower"][i] is None, (
                f"donchian_lower at index {i} should be None"
            )
        assert result["donchian_upper"][19] is not None
        assert result["donchian_lower"][19] is not None

    def test_donchian_first_valid_index_custom_period(self):
        """First valid index scales with period: period-1."""
        highs, lows, closes = _make_small_ohlcv(30)

        for period in (5, 7, 10, 15, 20):
            result = compute_donchian(highs, lows, period=period)
            first_valid = period - 1
            for i in range(first_valid):
                assert result["donchian_upper"][i] is None
                assert result["donchian_lower"][i] is None
            assert result["donchian_upper"][first_valid] is not None
            assert result["donchian_lower"][first_valid] is not None

    def test_donchian_upper_is_highest_in_window(self):
        """Donchian Upper should equal the highest high in the lookback window."""
        # Create a window where we know the max
        highs = [10.0] * 50
        lows = [5.0] * 50
        closes = [10.0] * 50
        # Override a peak at index 10
        highs[10] = 100.0

        result = compute_donchian(highs, lows, period=10)

        # At index 9 (first valid, window [0..9]): no 100 yet
        # All highs are 10, so upper = 10
        assert result["donchian_upper"][9] == 10.0

        # At index 10 (window [1..10]): 100 at right edge
        assert result["donchian_upper"][10] == 100.0

        # At index 18 (window [9..18]): 100 still in window
        assert result["donchian_upper"][18] == 100.0

        # At index 19 (window [10..19]): 100 still in window (at idx 10)
        assert result["donchian_upper"][19] == 100.0

        # At index 20 (window [11..20]): 100 is outside, all back to 10
        assert result["donchian_upper"][20] == 10.0

    def test_donchian_lower_is_lowest_in_window(self):
        """Donchian Lower should equal the lowest low in the lookback window."""
        highs = [10.0] * 50
        lows = [5.0] * 50
        closes = [10.0] * 50
        # Override a trough at index 10
        lows[10] = -50.0

        result = compute_donchian(highs, lows, period=10)

        # At index 9 (window [0..9]): all lows are 5, so lower = 5
        assert result["donchian_lower"][9] == 5.0

        # At index 10 (window [1..10]): -50 at right edge
        assert result["donchian_lower"][10] == -50.0

        # At index 18 (window [9..18]): -50 still in window
        assert result["donchian_lower"][18] == -50.0

        # At index 19 (window [10..19]): -50 still in window
        assert result["donchian_lower"][19] == -50.0

        # At index 20 (window [11..20]): -50 is outside
        assert result["donchian_lower"][20] == 5.0

    def test_donchian_manual_calculation(self):
        """Manually verify Donchian values for a simple constructed dataset."""
        highs = [10.0, 12.0, 11.0, 13.0, 15.0, 14.0, 16.0, 10.0]
        lows = [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 11.0, 14.0]
        closes = [10.0] * 8

        result = compute_donchian(highs, lows, period=5)

        # Index 4 (first valid, window [0..4]):
        #   highs = [10, 12, 11, 13, 15], max = 15
        #   lows = [8, 9, 10, 11, 12], min = 8
        assert result["donchian_upper"][4] == 15.0
        assert result["donchian_lower"][4] == 8.0

        # Index 5 (window [1..5]):
        #   highs = [12, 11, 13, 15, 14], max = 15
        #   lows = [9, 10, 11, 12, 13], min = 9
        assert result["donchian_upper"][5] == 15.0
        assert result["donchian_lower"][5] == 9.0

        # Index 6 (window [2..6]):
        #   highs = [11, 13, 15, 14, 16], max = 16
        #   lows = [10, 11, 12, 13, 11], min = 10
        assert result["donchian_upper"][6] == 16.0
        assert result["donchian_lower"][6] == 10.0

        # Index 7 (window [3..7]):
        #   highs = [13, 15, 14, 16, 10], max = 16
        #   lows = [11, 12, 13, 11, 14], min = 11
        assert result["donchian_upper"][7] == 16.0
        assert result["donchian_lower"][7] == 11.0

    def test_donchian_upper_non_decreasing_in_uptrend(self):
        """In a monotonic uptrend, Donchian Upper should be non-decreasing."""
        closes = [100.0 + i * 2.0 for i in range(100)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        result = compute_donchian(highs, lows, period=20)

        upper_vals = [v for v in result["donchian_upper"] if v is not None]
        for i in range(1, len(upper_vals)):
            assert upper_vals[i] >= upper_vals[i - 1], (
                f"Upper channel decreased at window {i}: {upper_vals[i-1]} -> {upper_vals[i]}"
            )

    def test_donchian_lower_non_decreasing_in_uptrend(self):
        """In a monotonic uptrend, Donchian Lower should also be non-decreasing."""
        closes = [100.0 + i * 2.0 for i in range(100)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        result = compute_donchian(highs, lows, period=20)

        lower_vals = [v for v in result["donchian_lower"] if v is not None]
        for i in range(1, len(lower_vals)):
            assert lower_vals[i] >= lower_vals[i - 1], (
                f"Lower channel decreased at window {i}: {lower_vals[i-1]} -> {lower_vals[i]}"
            )

    def test_donchian_upper_non_increasing_in_downtrend(self):
        """In a monotonic downtrend, Donchian Upper should be non-increasing."""
        closes = [100.0 - i * 2.0 for i in range(100)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        result = compute_donchian(highs, lows, period=20)

        upper_vals = [v for v in result["donchian_upper"] if v is not None]
        for i in range(1, len(upper_vals)):
            assert upper_vals[i] <= upper_vals[i - 1], (
                f"Upper channel increased at window {i}: {upper_vals[i-1]} -> {upper_vals[i]}"
            )

    def test_donchian_lower_non_increasing_in_downtrend(self):
        """In a monotonic downtrend, Donchian Lower should be non-increasing."""
        closes = [100.0 - i * 2.0 for i in range(100)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        result = compute_donchian(highs, lows, period=20)

        lower_vals = [v for v in result["donchian_lower"] if v is not None]
        for i in range(1, len(lower_vals)):
            assert lower_vals[i] <= lower_vals[i - 1], (
                f"Lower channel increased at window {i}: {lower_vals[i-1]} -> {lower_vals[i]}"
            )

    def test_donchian_upper_ge_lower(self):
        """Donchian Upper must always be >= Donchian Lower."""
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_donchian(highs, lows)

        for i in range(len(highs)):
            if result["donchian_upper"][i] is not None and result["donchian_lower"][i] is not None:
                assert result["donchian_upper"][i] >= result["donchian_lower"][i], (
                    f"Upper < Lower at index {i}: {result['donchian_upper'][i]} < {result['donchian_lower'][i]}"
                )

    def test_donchian_channel_width(self):
        """Channel width (upper - lower) should be positive in volatile data."""
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_donchian(highs, lows)

        valid_indices = [i for i in range(len(highs))
                         if result["donchian_upper"][i] is not None
                         and result["donchian_lower"][i] is not None]
        assert len(valid_indices) > 0

        for i in valid_indices:
            width = result["donchian_upper"][i] - result["donchian_lower"][i]
            assert width > 0, f"Negative channel width at index {i}: {width}"

    def test_donchian_with_varying_period(self):
        """Larger period should produce wider channels on average."""
        highs, lows, closes = _make_small_ohlcv(200)

        result_5 = compute_donchian(highs, lows, period=5)
        result_20 = compute_donchian(highs, lows, period=20)
        result_50 = compute_donchian(highs, lows, period=50)

        # Average channel width should increase with period
        avg_5 = sum(result_5["donchian_upper"][i] - result_5["donchian_lower"][i]
                     for i in range(len(highs))
                     if result_5["donchian_upper"][i] is not None)
        count_5 = sum(1 for i in range(len(highs))
                      if result_5["donchian_upper"][i] is not None)

        avg_20 = sum(result_20["donchian_upper"][i] - result_20["donchian_lower"][i]
                      for i in range(len(highs))
                      if result_20["donchian_upper"][i] is not None)
        count_20 = sum(1 for i in range(len(highs))
                       if result_20["donchian_upper"][i] is not None)

        avg_50 = sum(result_50["donchian_upper"][i] - result_50["donchian_lower"][i]
                      for i in range(len(highs))
                      if result_50["donchian_upper"][i] is not None)
        count_50 = sum(1 for i in range(len(highs))
                       if result_50["donchian_upper"][i] is not None)

        # Longer lookback windows should generally have wider channels
        assert avg_50 / count_50 >= avg_5 / count_5, (
            f"50-period channel {avg_50/count_50} should be >= 5-period {avg_5/count_5}"
        )

    def test_donchian_all_same_high_low(self):
        """When all highs are equal and all lows are equal, channels are constant."""
        highs = [100.0] * 50
        lows = [90.0] * 50
        closes = [95.0] * 50

        result = compute_donchian(highs, lows, period=20)

        for i in range(19, 50):
            assert result["donchian_upper"][i] == 100.0, (
                f"Index {i}: expected 100.0, got {result['donchian_upper'][i]}"
            )
            assert result["donchian_lower"][i] == 90.0, (
                f"Index {i}: expected 90.0, got {result['donchian_lower'][i]}"
            )

    def test_donchian_channel_width_is_positive(self):
        """In any real data, channel width should be strictly positive."""
        import random
        random.seed(42)
        highs = [100.0 + i * 0.5 for i in range(100)]
        lows = [95.0 + i * 0.5 for i in range(100)]
        closes = [97.5 + i * 0.5 for i in range(100)]

        result = compute_donchian(highs, lows)

        for i in range(19, 100):
            width = result["donchian_upper"][i] - result["donchian_lower"][i]
            assert width > 0, f"Channel width should be positive at index {i}: {width}"


# ---------------------------------------------------------------------------
# Keltner Upper / Lower tests
# ---------------------------------------------------------------------------

