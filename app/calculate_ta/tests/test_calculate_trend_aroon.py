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

class TestComputeAroon:
    """Verify Aroon Up and Aroon Down computation correctness."""

    def test_aroon_returns_correct_keys(self):
        """Result dict must contain aroon_up and aroon_down."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_aroon(highs, lows)
        assert "aroon_up" in result
        assert "aroon_down" in result

    def test_aroon_returns_correct_length(self):
        """All lists must match input length."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_aroon(highs, lows)
        assert len(result["aroon_up"]) == 60
        assert len(result["aroon_down"]) == 60

    def test_aroon_too_few_data_points(self):
        """With fewer than period data points, all values must be None."""
        highs = [100.0, 101.0]
        lows = [99.0, 100.0]
        result = compute_aroon(highs, lows, period=25)
        assert all(v is None for v in result["aroon_up"])
        assert all(v is None for v in result["aroon_down"])

    def test_aroon_first_valid_index_default_period(self):
        """First valid value should be at index period-1 (24 for period=25)."""
        n = 50
        highs, lows, closes = _make_small_ohlcv(n)
        result = compute_aroon(highs, lows, period=25)

        for i in range(24):
            assert result["aroon_up"][i] is None, (
                f"aroon_up at index {i} should be None"
            )
            assert result["aroon_down"][i] is None, (
                f"aroon_down at index {i} should be None"
            )
        assert result["aroon_up"][24] is not None
        assert result["aroon_down"][24] is not None

    def test_aroon_first_valid_index_custom_period(self):
        """First valid index scales with period: period-1."""
        highs, lows, closes = _make_small_ohlcv(30)

        for period in (5, 7, 10, 15, 20):
            result = compute_aroon(highs, lows, period=period)
            first_valid = period - 1
            for i in range(first_valid):
                assert result["aroon_up"][i] is None
                assert result["aroon_down"][i] is None
            assert result["aroon_up"][first_valid] is not None
            assert result["aroon_down"][first_valid] is not None

    def test_aroon_formula_perfect_uptrend(self):
        """In a perfect monotonic uptrend (both highs and lows climbing),
        the highest high in any window is always the rightmost bar
        (Aroon Up = 100), while the lowest low is always the leftmost bar
        (Aroon Down = 1/period * 100 = 4.0 for period=25)."""
        closes = [100.0 + i * 2.0 for i in range(100)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        result = compute_aroon(highs, lows, period=25)

        # First valid at index 24
        au = result["aroon_up"][24]
        ad = result["aroon_down"][24]
        assert au == 100.0, f"Aroon Up at first window should be 100, got {au}"
        # Lowest low is at index 0 (left edge of window), 24 days ago
        assert ad == 4.0, f"Aroon Down at first window should be 4.0, got {ad}"

        # All subsequent windows: highest at right (100), lowest at left (4)
        for i in range(25, 100):
            assert result["aroon_up"][i] == 100.0, (
                f"Aroon Up at index {i} should be 100 in perfect uptrend"
            )
            assert result["aroon_down"][i] == 4.0, (
                f"Aroon Down at index {i} should be 4.0 in perfect uptrend, got {result['aroon_down'][i]}"
            )

    def test_aroon_formula_perfect_downtrend(self):
        """In a perfect monotonic downtrend (both highs and lows falling),
        the lowest low is always the rightmost bar (Aroon Down = 100),
        while the highest high is always the leftmost bar
        (Aroon Up = 1/period * 100 = 4.0 for period=25)."""
        closes = [100.0 - i * 2.0 for i in range(100)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        result = compute_aroon(highs, lows, period=25)

        au = result["aroon_up"][24]
        ad = result["aroon_down"][24]
        assert au == 4.0, f"Aroon Up at first window should be 4.0, got {au}"
        assert ad == 100.0, f"Aroon Down at first window should be 100, got {ad}"

        for i in range(25, 100):
            assert result["aroon_up"][i] == 4.0, (
                f"Aroon Up at index {i} should be 4.0 in perfect downtrend, got {result['aroon_up'][i]}"
            )
            assert result["aroon_down"][i] == 100.0, (
                f"Aroon Down at index {i} should be 100 in perfect downtrend"
            )

    def test_aroon_formula_manual_calculation(self):
        """Manually verify Aroon values for a simple constructed dataset."""
        # Period=5, create data where we can manually check:
        # Index: 0  1  2  3   4   5   6   7
        # High:  10 12 11 13  15  14  16  10
        # Low:   8  9  10 11  12  13  11  14
        highs = [10.0, 12.0, 11.0, 13.0, 15.0, 14.0, 16.0, 10.0]
        lows = [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 11.0, 14.0]
        closes = [10.0] * 8  # close values don't matter for Aroon

        result = compute_aroon(highs, lows, period=5)

        # Index 4 (first valid, window [0..4]):
        #   highs[0..4] = [10, 12, 11, 13, 15], highest_idx = 4
        #   lows[0..4] = [8, 9, 10, 11, 12], lowest_idx = 0
        #   days_since_high = 4 - 4 = 0 → Aroon Up = 100
        #   days_since_low = 4 - 0 = 4 → Aroon Down = (5-4)/5*100 = 20
        assert result["aroon_up"][4] == 100.0
        assert result["aroon_down"][4] == 20.0

        # Index 5 (window [1..5]):
        #   highs[1..5] = [12, 11, 13, 15, 14], highest_idx = 4
        #   lows[1..5] = [9, 10, 11, 12, 13], lowest_idx = 1
        #   days_since_high = 5 - 4 = 1 → Aroon Up = (5-1)/5*100 = 80
        #   days_since_low = 5 - 1 = 4 → Aroon Down = (5-4)/5*100 = 20
        assert result["aroon_up"][5] == 80.0
        assert result["aroon_down"][5] == 20.0

        # Index 6 (window [2..6]):
        #   highs[2..6] = [11, 13, 15, 14, 16], highest_idx = 6
        #   lows[2..6] = [10, 11, 12, 13, 11], lowest_idx = 2
        #   days_since_high = 6 - 6 = 0 → Aroon Up = 100
        #   days_since_low = 6 - 2 = 4 → Aroon Down = 20
        assert result["aroon_up"][6] == 100.0
        assert result["aroon_down"][6] == 20.0

        # Index 7 (window [3..7]):
        #   highs[3..7] = [13, 15, 14, 16, 10], highest_idx = 6
        #   lows[3..7] = [11, 12, 13, 11, 14], lowest_idx = 3 (strict < keeps idx 3
        #     since lows[6]=11 == lows[3]=11, not less)
        #   days_since_high = 7 - 6 = 1 → Aroon Up = 80
        #   days_since_low = 7 - 3 = 4 → Aroon Down = 20
        assert result["aroon_up"][7] == 80.0
        assert result["aroon_down"][7] == 20.0

    def test_aroon_range(self):
        """All Aroon values must be in [0, 100]."""
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_aroon(highs, lows)
        for key in ("aroon_up", "aroon_down"):
            for v in result[key]:
                if v is not None:
                    assert 0 <= v <= 100, (
                        f"{key} value {v} out of [0, 100] range"
                    )

    def test_aroon_not_both_100(self):
        """Aroon Up and Down cannot both be 100 unless highs==lows for all."""
        highs, lows, closes = _make_small_ohlcv(100)
        # In real data, highs > lows, so they can't both be at the same index
        result = compute_aroon(highs, lows)
        for i in range(len(highs)):
            au = result["aroon_up"][i]
            ad = result["aroon_down"][i]
            if au is not None and ad is not None:
                assert not (au == 100 and ad == 100), (
                    f"At index {i}, both Aroon Up and Down are 100"
                )

    def test_aroon_sideways_market(self):
        """In a sideways market, Aroon should oscillate between extremes
        as new highs and lows form periodically."""
        import random
        random.seed(42)

        # Create a cyclical price with ~25-period cycles
        closes = [100.0 + 5 * math.sin(2 * math.pi * i / 25)
                  for i in range(200)]
        highs = [c + abs(random.gauss(0, 0.5)) for c in closes]
        lows = [c - abs(random.gauss(0, 0.5)) for c in closes]

        result = compute_aroon(highs, lows, period=25)

        valid_up = [v for v in result["aroon_up"] if v is not None]
        valid_down = [v for v in result["aroon_down"] if v is not None]
        assert len(valid_up) > 0
        # In a cyclical market, Aroon Up should occasionally hit 100
        assert max(valid_up) > 80, (
            f"Max Aroon Up should be high in cyclical market, got {max(valid_up)}"
        )
        assert max(valid_down) > 80, (
            f"Max Aroon Down should be high in cyclical market, got {max(valid_down)}"
        )

    def test_aroon_values_decrease_with_age_of_extremum(self):
        """As time passes since a high/low, the corresponding Aroon value
        should decrease (and vice versa when a new extremum forms)."""
        # Create a clean dataset where we know when the highest high occurs
        # in the window: put a big peak at index 10
        highs = [10.0] * 30
        lows = [5.0] * 30
        # Override: big peak at index 10
        highs[10] = 100.0
        closes = [10.0] * 30

        result = compute_aroon(highs, lows, period=10)

        # At index 9 (first valid, window [0..9]):
        #   highest in window is 10.0 at various positions (no 100 yet)
        #   All highs are 10.0 except we don't have 100 yet
        #   So highest_idx = 0 (first), days_since = 9, Aroon Up = 10
        au_first = result["aroon_up"][9]
        assert au_first is not None

        # At index 10 (window [1..10]): peak at right edge
        #   highest_idx = 10, days_since = 0, Aroon Up = 100
        assert result["aroon_up"][10] == 100.0

        # At index 18 (window [9..18]): peak at left edge (idx 9 is in window...
        # wait, window is [10-10+1=1, ...])
        # Let me reconsider: at index 18, window_start = 18-10+1 = 9
        #   highs[9..18] includes highs[10]=100 at position 1 (relative)
        #   highest_idx = 10, days_since = 18-10 = 8, Aroon Up = 20
        au_idx18 = result["aroon_up"][18]
        assert au_idx18 == 20.0, f"Expected 20, got {au_idx18}"

        # At index 19 (window [10..19]): peak at left edge
        #   highs[10..19], highest_idx = 10, days_since = 9, Aroon Up = 10
        au_idx19 = result["aroon_up"][19]
        assert au_idx19 == 10.0, f"Expected 10, got {au_idx19}"

        # At index 20 (window [11..20]): peak is outside the window
        #   All highs in window are 10.0, so highest_idx = 11 (first),
        #   days_since = 20-11 = 9, Aroon Up = 10
        au_idx20 = result["aroon_up"][20]
        assert au_idx20 is not None

    def test_aroon_tie_breaking_first_wins(self):
        """When multiple equal highs/lows exist in the window,
        the first occurrence (lowest index) should win due to strict >."""
        highs = [10.0, 10.0, 10.0, 10.0, 10.0]
        lows = [5.0, 5.0, 5.0, 5.0, 5.0]
        closes = [10.0] * 5

        result = compute_aroon(highs, lows, period=5)

        # All highs are 10, all lows are 5
        # highest_idx = 0 (first), lowest_idx = 0 (first)
        # days_since_high = 4, Aroon Up = (5-4)/5*100 = 20
        # days_since_low = 4, Aroon Down = 20
        assert result["aroon_up"][4] == 20.0
        assert result["aroon_down"][4] == 20.0

    def test_aroon_single_high_in_window(self):
        """Aroon values when only one extreme exists in the window."""
        # Create data where only one day has the highest high
        highs = [10.0, 20.0, 10.0, 10.0, 10.0]
        lows = [5.0, 5.0, 5.0, 5.0, 5.0]
        closes = [10.0] * 5

        result = compute_aroon(highs, lows, period=5)

        # Window [0..4]: highest at idx 1 (value 20), lowest at idx 0 (value 5)
        # days_since_high = 4-1 = 3 → Aroon Up = 40
        # days_since_low = 4-0 = 4 → Aroon Down = 20
        assert result["aroon_up"][4] == 40.0
        assert result["aroon_down"][4] == 20.0

    def test_aroon_inverse_relationship(self):
        """In an uptrend, Aroon Up stays at 100 (highest always recent);
        in a downtrend, Aroon Down stays at 100 (lowest always recent)."""
        # Uptrend: both highs and lows climbing
        closes_up = [100.0 + i for i in range(100)]
        highs_up = [c + 2.0 for c in closes_up]
        lows_up = [c - 1.0 for c in closes_up]

        result_up = compute_aroon(highs_up, lows_up, period=25)

        valid_up = [v for v in result_up["aroon_up"] if v is not None]
        valid_down = [v for v in result_up["aroon_down"] if v is not None]
        assert len(valid_up) > 0
        # In uptrend, highest high is always at the right edge
        assert all(v == 100.0 for v in valid_up)
        # Lowest low is always at the left edge (24 days ago) → 4.0
        assert all(v == 4.0 for v in valid_down)

        # Downtrend: both highs and lows falling
        closes_down = [100.0 - i for i in range(100)]
        highs_down = [c + 2.0 for c in closes_down]
        lows_down = [c - 1.0 for c in closes_down]

        result_down = compute_aroon(highs_down, lows_down, period=25)

        valid_up = [v for v in result_down["aroon_up"] if v is not None]
        valid_down = [v for v in result_down["aroon_down"] if v is not None]
        # In downtrend, lowest low is always at the right edge
        assert all(v == 100.0 for v in valid_down)
        # Highest high is always at the left edge → 4.0
        assert all(v == 4.0 for v in valid_up)

    def test_aroon_with_large_period(self):
        """Test with a larger period to verify scaling."""
        n = 200
        highs, lows, closes = _make_small_ohlcv(n)
        result = compute_aroon(highs, lows, period=50)

        # First valid at index 49
        for i in range(49):
            assert result["aroon_up"][i] is None
            assert result["aroon_down"][i] is None
        assert result["aroon_up"][49] is not None
        assert result["aroon_down"][49] is not None

        valid_up = [v for v in result["aroon_up"] if v is not None]
        valid_down = [v for v in result["aroon_down"] if v is not None]
        assert len(valid_up) >= 149  # 200 - 50 + 1 = 151 valid values

    def test_aroon_all_same_price(self):
        """When all highs are equal and all lows are equal,
        both Aroon values should be equal."""
        highs = [100.0] * 50
        lows = [90.0] * 50
        closes = [95.0] * 50

        result = compute_aroon(highs, lows, period=25)

        # All highs equal → first wins → days_since = period-1
        # Aroon Up = Aroon Down = (period - (period-1)) / period * 100 = 100/period
        expected = (1.0 / 25) * 100  # = 4.0
        for i in range(25, 50):
            assert result["aroon_up"][i] == expected, (
                f"Index {i}: expected {expected}, got {result['aroon_up'][i]}"
            )
            assert result["aroon_down"][i] == expected, (
                f"Index {i}: expected {expected}, got {result['aroon_down'][i]}"
            )


# ---------------------------------------------------------------------------
# ADX / +DI / -DI tests
# ---------------------------------------------------------------------------

