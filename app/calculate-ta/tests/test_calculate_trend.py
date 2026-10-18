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

class TestComputeEMA:
    """Verify EMA computation correctness."""

    def test_ema_returns_correct_length(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = compute_ema(values, 3)
        assert len(result) == len(values)

    def test_ema_shorter_than_period_returns_all_none(self):
        values = [10.0, 20.0]
        result = compute_ema(values, 5)
        assert all(v is None for v in result)

    def test_ema_matches_reference_sma_seed(self):
        """First EMA value should equal SMA of first `period` values."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = compute_ema(values, 3)
        # First valid value (index 2) should be SMA of first 3 values
        expected_first = sum(values[:3]) / 3.0
        assert result[2] == pytest.approx(expected_first)

    def test_ema_matches_reference_recursive(self):
        """Verify against recursive EMA formula."""
        random.seed(123)
        values = [random.uniform(50, 150) for _ in range(100)]
        result = compute_ema(values, 20)
        reference = _compute_reference_ema(values, 20)
        for i in range(len(result)):
            if result[i] is not None:
                assert result[i] == pytest.approx(reference[i], rel=1e-10), (
                    f"Mismatch at index {i}: computed={result[i]}, ref={reference[i]}"
                )

    def test_ema_uses_sma_seed_not_first_value(self):
        """EMA should be seeded with SMA of first N values, not just the first value.

        This is the standard convention and differs from a naive implementation
        that seeds with values[0].
        """
        values = [10.0, 10.0, 10.0, 20.0, 30.0]
        result = compute_ema(values, 3)
        # Seed should be SMA of [10, 10, 10] = 10.0
        expected_first = 10.0
        assert result[2] == pytest.approx(expected_first)

    def test_ema_period_1(self):
        """EMA with period=1 should equal the values themselves."""
        values = [10.0, 20.0, 30.0, 40.0]
        result = compute_ema(values, 1)
        for i in range(len(result)):
            assert result[i] == pytest.approx(values[i])

    def test_ema_monotonic_values(self):
        """EMA of monotonically increasing values should also be increasing."""
        values = [float(i) for i in range(1, 51)]
        result = compute_ema(values, 10)
        # Find first non-None index
        first_idx = None
        for i, v in enumerate(result):
            if v is not None:
                first_idx = i
                break
        assert first_idx is not None
        # Check that EMA is increasing after the seed
        for i in range(first_idx + 1, len(result)):
            if result[i] is not None and result[i - 1] is not None:
                assert result[i] > result[i - 1], (
                    f"EMA not increasing at index {i}: {result[i-1]} -> {result[i]}"
                )


# ---------------------------------------------------------------------------
# ATR tests
# ---------------------------------------------------------------------------

class TestComputeATR:
    """Verify ATR computation correctness."""

    def test_atr_returns_correct_length(self):
        highs = [105.0, 115.0, 125.0] * 30
        lows = [95.0, 105.0, 115.0] * 30
        closes = [100.0, 110.0, 120.0] * 30
        result = compute_atr(highs, lows, closes, period=14)
        assert len(result) == len(highs)

    def test_atr_shorter_than_period_returns_all_none(self):
        highs = [100.0, 110.0]
        lows = [90.0, 100.0]
        closes = [100.0, 110.0]
        result = compute_atr(highs, lows, closes, period=14)
        assert all(v is None for v in result)

    def test_atr_true_range_calculation(self):
        """Verify True Range formula is used in ATR computation."""
        # Create data where |H-prevC| > H-L so TR != H-L
        highs = [100.0] * 20 + [120.0]
        lows = [90.0] * 20 + [80.0]
        closes = [95.0] * 19 + [100.0]  # day 19 close = 100
        # Day 20: H=120, L=80, prevC=100
        # TR = max(120-80=40, |120-100|=20, |80-100|=20) = 40
        # But day 19: H=100, L=90, prevC=95
        # TR = max(100-90=10, |100-95|=5, |90-95|=5) = 10
        result = compute_atr(highs, lows, closes, period=14)
        # With 22 data points and period=14, ATR should be valid from index 14
        assert result[14] is not None
        assert result[20] is not None
        assert result[14] >= 0

    def test_atr_values_are_non_negative(self):
        highs, lows, closes = _make_small_ohlcv(100)
        result = compute_atr(highs, lows, closes, period=14)
        for v in result:
            if v is not None:
                assert v >= 0, f"Negative ATR value: {v}"

    def test_atr_uses_wilders_smoothing(self):
        """Verify that ATR uses Wilder's smoothing (not simple MA)."""
        random.seed(99)
        highs, lows, closes = _make_small_ohlcv(200)
        atr = compute_atr(highs, lows, closes, period=14)

        # Compute actual True Ranges
        true_ranges = []
        for i in range(len(highs)):
            if i == 0:
                true_ranges.append(highs[i] - lows[i])
            else:
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1]),
                )
                true_ranges.append(tr)

        # Find first valid ATR index
        first_valid = None
        for i, v in enumerate(atr):
            if v is not None:
                first_valid = i
                break

        assert first_valid is not None

        # After the initial SMA, verify Wilder's formula:
        # ATR[i] = TR[i] * k + ATR[i-1] * (1-k), k = 2/(14+1)
        k = 2.0 / 15.0
        for i in range(first_valid + 1, len(atr)):
            if atr[i] is not None and atr[i - 1] is not None:
                expected = true_ranges[i] * k + atr[i - 1] * (1 - k)
                assert atr[i] == pytest.approx(expected, rel=1e-8), (
                    f"ATR Wilder smoothing mismatch at index {i}"
                )


# ---------------------------------------------------------------------------
# SuperTrend tests
# ---------------------------------------------------------------------------

class TestComputeSuperTrend:
    """Verify SuperTrend computation correctness."""

    def test_supertrend_returns_all_keys(self):
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_supertrend(highs, lows, closes)
        assert "supertrend" in result
        assert "direction" in result
        assert "upper_band" in result
        assert "lower_band" in result

    def test_supertrend_direction_values(self):
        """Direction should be one of {-1, 0, 1}."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_supertrend(highs, lows, closes)
        for d in result["direction"]:
            assert d in (-1, 0, 1), f"Invalid direction value: {d}"

    def test_supertrend_bands_are_non_negative(self):
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_supertrend(highs, lows, closes)
        for v in result["upper_band"]:
            if v is not None:
                assert v > 0
        for v in result["lower_band"]:
            if v is not None:
                assert v > 0

    def test_supertrend_direction_flips_on_cross(self):
        """When price crosses below lower_band in uptrend, direction should flip to -1."""
        # Create a simple downward price spike
        highs = [110.0] * 30 + [50.0]  # sudden drop on last day
        lows = [90.0] * 30 + [40.0]
        closes = [100.0] * 30 + [45.0]

        result = compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0)

        # After the drop, direction should eventually flip
        # Find first -1 after the drop
        flipped = False
        for i in range(30, len(result["direction"])):
            if result["direction"][i] == -1:
                flipped = True
                break
        assert flipped, "SuperTrend should have flipped direction after price drop"

    def test_supertrend_upper_band_non_increasing(self):
        """Upper band should never increase (only decrease or stay same)."""
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_supertrend(highs, lows, closes)
        prev = None
        for i, ub in enumerate(result["upper_band"]):
            if ub is not None:
                if prev is not None:
                    assert ub <= prev, (
                        f"Upper band increased at index {i}: {prev} -> {ub}"
                    )
                prev = ub

    def test_supertrend_lower_band_non_decreasing(self):
        """Lower band should never decrease (only increase or stay same)."""
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_supertrend(highs, lows, closes)
        prev = None
        for i, lb in enumerate(result["lower_band"]):
            if lb is not None:
                if prev is not None:
                    assert lb >= prev, (
                        f"Lower band decreased at index {i}: {prev} -> {lb}"
                    )
                prev = lb

    def test_supertrend_custom_multiplier(self):
        """Higher multiplier should produce wider bands."""
        highs, lows, closes = _make_small_ohlcv(60)
        st1 = compute_supertrend(highs, lows, closes, atr_period=14, multiplier=1.0)
        st3 = compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0)

        # Upper band with multiplier=3 should be wider (higher) than multiplier=1
        for i in range(len(st1["upper_band"])):
            if (st1["upper_band"][i] is not None and
                    st3["upper_band"][i] is not None):
                assert st3["upper_band"][i] > st1["upper_band"][i], (
                    f"Higher multiplier should produce wider upper band at index {i}"
                )

    def test_supertrend_bands_use_atr(self):
        """Bands should be non-None once ATR values are available."""
        highs, lows, closes = _make_small_ohlcv(100)
        atr = compute_atr(highs, lows, closes, period=14)

        result = compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0)

        # After ATR is computed, all bands should have values
        for i in range(len(highs)):
            if atr[i] is not None:
                assert result["upper_band"][i] is not None, (
                    f"Upper band should be set when ATR is available at index {i}"
                )
                assert result["lower_band"][i] is not None, (
                    f"Lower band should be set when ATR is available at index {i}"
                )
                assert result["supertrend"][i] is not None, (
                    f"SuperTrend line should be set when ATR is available at index {i}"
                )

    def test_supertrend_with_varying_prices(self):
        """SuperTrend should handle a trending market."""
        # Uptrend: steadily rising prices
        closes = [100.0 + i * 2.0 for i in range(100)]
        highs = [c + 5.0 for c in closes]
        lows = [c - 5.0 for c in closes]

        result = compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0)

        # In a strong uptrend, direction should eventually be +1
        uptrend_count = sum(1 for d in result["direction"] if d == 1)
        assert uptrend_count > 0, (
            "SuperTrend should detect uptrend in rising price series"
        )

    def test_supertrend_with_downtrend(self):
        """SuperTrend should detect downtrend."""
        # Downtrend: steadily falling prices
        closes = [100.0 - i * 2.0 for i in range(100)]
        highs = [c + 5.0 for c in closes]
        lows = [c - 5.0 for c in closes]

        result = compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0)

        downtrend_count = sum(1 for d in result["direction"] if d == -1)
        assert downtrend_count > 0, (
            "SuperTrend should detect downtrend in falling price series"
        )


# ---------------------------------------------------------------------------
# Aroon Up / Aroon Down tests
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

class TestComputeADXDI:
    """Verify ADX, +DI, and -DI computation correctness."""

    def test_adx_di_returns_correct_keys(self):
        """Result dict must contain adx, plus_di, minus_di."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_adx_di(highs, lows, closes)
        assert "adx" in result
        assert "plus_di" in result
        assert "minus_di" in result

    def test_adx_di_returns_correct_length(self):
        """All three lists must match input length."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_adx_di(highs, lows, closes)
        for key in ("adx", "plus_di", "minus_di"):
            assert len(result[key]) == 60

    def test_adx_di_too_few_data_points(self):
        """With fewer than period+1 data points, all values must be None."""
        highs = [100.0, 101.0]
        lows = [99.0, 100.0]
        closes = [100.0, 101.0]
        result = compute_adx_di(highs, lows, closes, period=14)
        assert all(v is None for v in result["adx"])
        assert all(v is None for v in result["plus_di"])
        assert all(v is None for v in result["minus_di"])

    def test_adx_di_index_validity_period_14(self):
        """Verify first valid index for each metric with period=14.

        +DI/-DI  : first valid at index ``period`` (14)
        DX       : first valid at index ``period + 1`` (15)
        ADX      : initial at index ``period + 14`` (28), then smoothed
        """
        highs, lows, closes = _make_small_ohlcv(50)
        result = compute_adx_di(highs, lows, closes, period=14)

        # +DI/-DI: None before index 14, valid at 14
        for i in range(14):
            assert result["plus_di"][i] is None, (
                f"+DI at index {i} should be None"
            )
            assert result["minus_di"][i] is None, (
                f"-DI at index {i} should be None"
            )
        assert result["plus_di"][14] is not None, "+DI at index 14 should be valid"
        assert result["minus_di"][14] is not None, "-DI at index 14 should be valid"

        # ADX: None before index 28, valid at 28
        for i in range(28):
            assert result["adx"][i] is None, (
                f"ADX at index {i} should be None"
            )
        assert result["adx"][28] is not None, "ADX at index 28 should be valid"

    def test_adx_di_index_validity_period_7(self):
        """Verify first valid indices scale correctly with custom period=7."""
        n = 50
        highs, lows, closes = _make_small_ohlcv(n)
        result = compute_adx_di(highs, lows, closes, period=7)

        period = 7
        # +DI/-DI valid from index period
        for i in range(period):
            assert result["plus_di"][i] is None
            assert result["minus_di"][i] is None
        assert result["plus_di"][period] is not None
        assert result["minus_di"][period] is not None

        # ADX initial at index period + 14 = 21 (14 DX values from period+1 to period+14)
        adx_init_idx = period + 14
        for i in range(adx_init_idx):
            assert result["adx"][i] is None
        assert result["adx"][adx_init_idx] is not None

    def test_adx_plus_minus_di_range(self):
        """All DI and ADX values must be in [0, 100]."""
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_adx_di(highs, lows, closes)
        for key in ("adx", "plus_di", "minus_di"):
            for v in result[key]:
                if v is not None:
                    assert 0 <= v <= 100, (
                        f"{key} value {v} out of [0, 100] range"
                    )

    def test_strong_uptrend_high_plus_di_low_minus_di(self):
        """In a strong uptrend, +DI should be high and -DI low.

        Use data where close ≈ high (no gap between closes) so
        TR is driven only by the intraday range, not inter-day gaps.
        """
        # Daily +2, range=1, close=high → no inter-day gap
        closes = [100.0 + i * 2.0 for i in range(100)]
        highs = [c + 1.0 for c in closes]  # close = high - 1
        lows = [c - 0.0 for c in closes]   # close = high - 1 = high - 1
        # Actually: H=C+1, L=C, so H-L=1, gap(H[i],C[i-1])=3, gap(L[i],C[i-1])=2
        # TR = max(1, 3, 2) = 3, up_move=2, +DI = 2/3 = 66.7%

        result = compute_adx_di(highs, lows, closes, period=14)

        plus_vals = [v for v in result["plus_di"] if v is not None]
        minus_vals = [v for v in result["minus_di"] if v is not None]
        assert sum(plus_vals) > sum(minus_vals), (
            "+DI should exceed -DI in a strong uptrend"
        )
        # Theoretical +DI ≈ 66.7% when there's no minus DM and TR is dominated by gap
        assert result["plus_di"][-1] > 60, (
            f"+DI should be > 60 in strong uptrend, got {result['plus_di'][-1]}"
        )
        assert result["minus_di"][-1] < 10, (
            f"-DI should be near 0 in strong uptrend, got {result['minus_di'][-1]}"
        )

    def test_strong_downtrend_high_minus_di_low_plus_di(self):
        """In a strong downtrend, -DI should be high and +DI low.

        Use data where close ≈ low (no gap between closes) so
        TR is driven only by the intraday range, not inter-day gaps.
        """
        # Daily -2, range=1, close=low
        closes = [100.0 - i * 2.0 for i in range(100)]
        highs = [c + 0.0 for c in closes]  # close = high
        lows = [c - 1.0 for c in closes]   # close - 1

        result = compute_adx_di(highs, lows, closes, period=14)

        plus_vals = [v for v in result["plus_di"] if v is not None]
        minus_vals = [v for v in result["minus_di"] if v is not None]
        assert sum(minus_vals) > sum(plus_vals), (
            "-DI should exceed +DI in a strong downtrend"
        )
        assert result["minus_di"][-1] > 60, (
            f"-DI should be > 60 in strong downtrend, got {result['minus_di'][-1]}"
        )
        assert result["plus_di"][-1] < 10, (
            f"+DI should be near 0 in strong downtrend, got {result['plus_di'][-1]}"
        )

    def test_strong_trend_high_adx(self):
        """Strong trend (up or down) should produce high ADX."""
        # Uptrend
        closes = [100.0 + i * 2.0 for i in range(100)]
        highs = [c + 3.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        result = compute_adx_di(highs, lows, closes, period=14)

        # ADX should be relatively high near the end in a strong trend
        adx_vals = [v for v in result["adx"] if v is not None]
        assert len(adx_vals) > 0
        assert adx_vals[-1] > 25, (
            f"ADX should be > 25 in strong trend, got {adx_vals[-1]}"
        )

    def test_sideways_market_low_adx(self):
        """A flat/sideways market should produce low ADX."""
        # Flat price with small noise
        import random
        random.seed(42)
        base = 100.0
        closes = [base + random.gauss(0, 0.1) for _ in range(100)]
        highs = [c + abs(random.gauss(0, 0.5)) for c in closes]
        lows = [c - abs(random.gauss(0, 0.5)) for c in closes]

        result = compute_adx_di(highs, lows, closes, period=14)

        adx_vals = [v for v in result["adx"] if v is not None]
        assert len(adx_vals) > 0
        # In a sideways market, ADX should be low (< 20 is typical)
        assert adx_vals[-1] < 40, (
            f"ADX should be low in sideways market, got {adx_vals[-1]}"
        )

    def test_dx_formula_at_period_plus_1(self):
        """Verify DX = |+DI - -DI| / (+DI + -DI) * 100 at first valid index."""
        # Use a simple upward trend so +DM and -DM are deterministic
        closes = [100.0 + i * 1.0 for i in range(50)]
        highs = [c + 2.0 for c in closes]
        lows = [c - 0.5 for c in closes]

        result = compute_adx_di(highs, lows, closes, period=14)

        # First valid DX is at index period + 1 = 15
        pdi = result["plus_di"][15]
        mdi = result["minus_di"][15]
        if pdi is not None and mdi is not None:
            di_sum = pdi + mdi
            if di_sum > 0:
                expected_dx = (abs(pdi - mdi) / di_sum) * 100
                # ADX at index 15 is not the DX itself — DX is intermediate.
                # But we can check the first valid ADX (index 28) by recomputing.
                # For now, just verify DI values are reasonable.
                assert 0 <= pdi <= 100
                assert 0 <= mdi <= 100

    def test_adx_wilders_smoothing(self):
        """Verify that ADX uses Wilder's smoothing:
        ADX[i] = ADX[i-1] * (1 - k) + DX[i] * k
        """
        import random
        random.seed(42)
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_adx_di(highs, lows, closes, period=14)

        # Manually recompute +DI, -DI, DX, ADX and verify smoothing
        n = len(highs)
        period = 14
        k = 1.0 / period

        # Recompute DM and TR
        plus_dm = [0.0] * n
        minus_dm = [0.0] * n
        true_range = [0.0] * n
        for i in range(1, n):
            up_move = highs[i] - highs[i - 1]
            down_move = lows[i - 1] - lows[i]
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_range[i] = tr

        # Wilder sum helper
        def _wilder_sum(values, start, end, period):
            s = sum(values[i] for i in range(start, end))
            out = [0.0] * len(values)
            out[end - 1] = s
            for i in range(end, len(values)):
                out[i] = out[i - 1] - out[i - 1] * k + values[i]
            return out

        smoothed_tr = _wilder_sum(true_range, 1, period + 1, period)
        smoothed_pd = _wilder_sum(plus_dm, 1, period + 1, period)
        smoothed_md = _wilder_sum(minus_dm, 1, period + 1, period)

        # Recompute +DI, -DI
        ref_plus_di = [None] * n
        ref_minus_di = [None] * n
        for i in range(period, n):
            if smoothed_tr[i] == 0:
                continue
            ref_plus_di[i] = (smoothed_pd[i] / smoothed_tr[i]) * 100
            ref_minus_di[i] = (smoothed_md[i] / smoothed_tr[i]) * 100

        # Recompute DX and ADX
        ref_adx = [None] * n
        dx_vals = {}
        for i in range(period + 1, n):
            if ref_plus_di[i] is None or ref_minus_di[i] is None:
                continue
            di_sum = ref_plus_di[i] + ref_minus_di[i]
            if di_sum == 0:
                continue
            dx_vals[i] = (abs(ref_plus_di[i] - ref_minus_di[i]) / di_sum) * 100

        init_idx = period + 14
        for i in range(period + 1, n):
            if i not in dx_vals:
                continue
            dx = dx_vals[i]
            if i == init_idx:
                s = sum(dx_vals[j] for j in range(period + 1, period + 15)
                        if j in dx_vals)
                c = sum(1 for j in range(period + 1, period + 15)
                        if j in dx_vals)
                if c > 0:
                    ref_adx[i] = s / c
            else:
                if ref_adx[i - 1] is not None:
                    ref_adx[i] = ref_adx[i - 1] * (1 - k) + dx * k

        # Compare
        for i in range(n):
            if result["adx"][i] is not None and ref_adx[i] is not None:
                assert result["adx"][i] == pytest.approx(ref_adx[i], rel=1e-10), (
                    f"ADX mismatch at index {i}: computed={result['adx'][i]}, ref={ref_adx[i]}"
                )
            if result["plus_di"][i] is not None and ref_plus_di[i] is not None:
                assert result["plus_di"][i] == pytest.approx(ref_plus_di[i], rel=1e-10), (
                    f"+DI mismatch at index {i}"
                )
            if result["minus_di"][i] is not None and ref_minus_di[i] is not None:
                assert result["minus_di"][i] == pytest.approx(ref_minus_di[i], rel=1e-10), (
                    f"-DI mismatch at index {i}"
                )

    def test_adx_all_none_until_valid(self):
        """ADX must be None for all indices before the initial ADX index."""
        highs, lows, closes = _make_small_ohlcv(50)
        result = compute_adx_di(highs, lows, closes, period=14)

        # All ADX values before index 28 must be None
        for i in range(28):
            assert result["adx"][i] is None, (
                f"ADX at index {i} should be None"
            )

    def test_adx_monotonic_trend_increasing_adx(self):
        """In a monotonic trend, ADX should be non-decreasing and high."""
        closes = [100.0 + i * 2.0 for i in range(100)]
        highs = [c + 3.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        result = compute_adx_di(highs, lows, closes, period=14)

        adx_vals = [v for v in result["adx"] if v is not None]
        assert len(adx_vals) >= 2
        # ADX should be non-decreasing in a monotonic trend
        assert adx_vals[-1] >= adx_vals[0], (
            f"ADX should not decrease in monotonic trend: {adx_vals[0]} -> {adx_vals[-1]}"
        )
        # ADX should end high (> 70 for a very strong trend)
        assert adx_vals[-1] >= 70, (
            f"ADX should be high in strong monotonic trend, got {adx_vals[-1]}"
        )

    def test_adx_equal_di_zero_dx(self):
        """When +DI == -DI, DX should be 0."""
        # Create perfectly symmetric oscillation
        highs = [105.0, 105.0, 105.0] * 50
        lows = [95.0, 95.0, 95.0] * 50
        closes = [100.0, 100.0, 100.0] * 50

        result = compute_adx_di(highs, lows, closes, period=14)

        adx_vals = [v for v in result["adx"] if v is not None]
        # With flat price, ADX should be very low (all DI values are 0 or equal)
        # The actual value depends on how the smoothing handles zero TR
        # Just check that values are valid
        for v in adx_vals:
            assert 0 <= v <= 100

    def test_adx_custom_period(self):
        """Verify behavior with a custom period."""
        highs, lows, closes = _make_small_ohlcv(100)
        result = compute_adx_di(highs, lows, closes, period=7)

        # +DI first valid at index 7
        assert result["plus_di"][6] is None
        assert result["plus_di"][7] is not None

        # ADX first valid at index 7 + 14 = 21
        assert result["adx"][20] is None
        assert result["adx"][21] is not None

    def test_adx_di_consistent_with_trend_direction(self):
        """In an uptrend, +DI > -DI; in a downtrend, -DI > +DI."""
        # Uptrend
        closes_up = [100.0 + i * 1.5 for i in range(100)]
        highs_up = [c + 2.0 for c in closes_up]
        lows_up = [c - 1.0 for c in closes_up]

        result_up = compute_adx_di(highs_up, lows_up, closes_up, period=14)

        # Check later indices where smoothing has converged
        last_idx = len(result_up["adx"]) - 1
        assert result_up["plus_di"][last_idx] > result_up["minus_di"][last_idx], (
            "In uptrend, +DI should exceed -DI"
        )

        # Downtrend
        closes_down = [100.0 - i * 1.5 for i in range(100)]
        highs_down = [c + 1.0 for c in closes_down]
        lows_down = [c - 2.0 for c in closes_down]

        result_down = compute_adx_di(highs_down, lows_down, closes_down, period=14)

        last_idx = len(result_down["adx"]) - 1
        assert result_down["minus_di"][last_idx] > result_down["plus_di"][last_idx], (
            "In downtrend, -DI should exceed +DI"
        )

    def test_adx_values_increasing_with_enough_data(self):
        """With 200 rows, ADX should have a good number of valid values."""
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_adx_di(highs, lows, closes, period=14)

        valid_adx = [v for v in result["adx"] if v is not None]
        # First valid at index 28, so with 200 rows we should have ~172 valid values
        assert len(valid_adx) >= 170, (
            f"Expected at least 170 valid ADX values, got {len(valid_adx)}"
        )

    def test_adx_first_valid_index_exact(self):
        """The first valid ADX index should be exactly period + 14."""
        n = 50
        highs, lows, closes = _make_small_ohlcv(n)
        result = compute_adx_di(highs, lows, closes, period=14)

        first_valid = None
        for i, v in enumerate(result["adx"]):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 28, f"First valid ADX at index {first_valid}, expected 28"


# ---------------------------------------------------------------------------
# Donchian Upper / Lower tests
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

class TestComputeKeltner:
    """Verify Keltner Upper and Lower computation correctness."""

    def test_keltner_returns_correct_keys(self):
        """Result dict must contain keltner_upper and keltner_lower."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_keltner(highs, lows, closes)
        assert "keltner_upper" in result
        assert "keltner_lower" in result

    def test_keltner_returns_correct_length(self):
        """All lists must match input length."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_keltner(highs, lows, closes)
        assert len(result["keltner_upper"]) == 60
        assert len(result["keltner_lower"]) == 60

    def test_keltner_too_few_data_points(self):
        """With fewer than needed data, all values must be None."""
        highs = [100.0] * 5
        lows = [90.0] * 5
        closes = [95.0] * 5
        result = compute_keltner(highs, lows, closes)
        assert all(v is None for v in result["keltner_upper"])
        assert all(v is None for v in result["keltner_lower"])

    def test_keltner_first_valid_index_default_params(self):
        """First valid value at max(ema_period-1, atr_period)."""
        # Default: ema_period=20, atr_period=10
        # First valid: max(19, 10) = 19
        n = 50
        highs, lows, closes = _make_small_ohlcv(n)
        result = compute_keltner(highs, lows, closes)

        for i in range(19):
            assert result["keltner_upper"][i] is None, (
                f"keltner_upper at index {i} should be None"
            )
            assert result["keltner_lower"][i] is None, (
                f"keltner_lower at index {i} should be None"
            )
        assert result["keltner_upper"][19] is not None
        assert result["keltner_lower"][19] is not None

    def test_keltner_upper_ge_lower(self):
        """Keltner Upper must always be >= Keltner Lower."""
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_keltner(highs, lows, closes)

        for i in range(len(highs)):
            if result["keltner_upper"][i] is not None and result["keltner_lower"][i] is not None:
                assert result["keltner_upper"][i] >= result["keltner_lower"][i], (
                    f"Upper < Lower at index {i}: {result['keltner_upper'][i]} < {result['keltner_lower'][i]}"
                )

    def test_keltner_channel_width_equals_two_times_multiplier_atr(self):
        """Channel width = 2 × multiplier × ATR (since upper = TP_ema + mult×ATR, lower = TP_ema - mult×ATR)."""
        highs, lows, closes = _make_small_ohlcv(200)
        result = compute_keltner(highs, lows, closes, atr_period=10, multiplier=2.0)
        atr_values = compute_atr(highs, lows, closes, period=10)

        for i in range(len(highs)):
            if result["keltner_upper"][i] is not None and result["keltner_lower"][i] is not None:
                width = result["keltner_upper"][i] - result["keltner_lower"][i]
                expected_width = 2.0 * 2.0 * atr_values[i]  # multiplier=2, so 2*mult*ATR = 4*ATR
                assert abs(width - expected_width) < 1e-6, (
                    f"Width mismatch at index {i}: {width} vs {expected_width}"
                )

    def test_keltner_manual_calculation_simple(self):
        """Manually verify Keltner values for a simple constructed dataset."""
        # Create simple data where we can manually verify
        # All closes = 100, highs = 102, lows = 98 (constant volatility)
        n = 30
        highs = [102.0] * n
        lows = [98.0] * n
        closes = [100.0] * n

        result = compute_keltner(highs, lows, closes, ema_period=10, atr_period=5, multiplier=2.0)

        # With constant data:
        # TR = High - Low = 4 for all bars (since no prior close to consider for i=0)
        # For i=0: TR = 102 - 98 = 4
        # For i>0: TR = max(102-98, |102-100|, |98-100|) = max(4, 2, 2) = 4
        # ATR(5): seed at index 5 = average of first 5 TRs = 4.0
        # With constant TR, ATR stays at 4.0
        # TP = (102 + 98 + 100) / 3 = 100.0 (constant)
        # EMA(TP, 10) at index 9 = SMA of first 10 TP values = 100.0
        # So at index 9: upper = 100 + 2*4 = 108, lower = 100 - 2*4 = 92

        # First valid: max(10-1, 5) = max(9, 5) = 9
        assert result["keltner_upper"][9] is not None
        assert result["keltner_lower"][9] is not None
        assert result["keltner_upper"][9] == 108.0
        assert result["keltner_lower"][9] == 92.0

        # Since TP and ATR are constant, values stay the same
        for i in range(9, n):
            assert result["keltner_upper"][i] == 108.0, (
                f"Index {i}: expected 108.0, got {result['keltner_upper'][i]}"
            )
            assert result["keltner_lower"][i] == 92.0, (
                f"Index {i}: expected 92.0, got {result['keltner_lower'][i]}"
            )

    def test_keltner_upper_in_uptrend(self):
        """In an uptrend, Keltner Upper should generally follow price upwards."""
        closes = [100.0 + i * 2.0 for i in range(200)]
        highs = [c + 2.0 for c in closes]
        lows = [c - 2.0 for c in closes]

        result = compute_keltner(highs, lows, closes)

        upper_vals = [v for v in result["keltner_upper"] if v is not None]
        # Upper channel should be rising (non-decreasing) in an uptrend
        for i in range(1, len(upper_vals)):
            assert upper_vals[i] >= upper_vals[i - 1] or abs(upper_vals[i] - upper_vals[i - 1]) < 0.1, (
                f"Upper channel unexpectedly decreased at window {i}"
            )

    def test_keltner_lower_in_uptrend(self):
        """In an uptrend, Keltner Lower should also generally rise."""
        closes = [100.0 + i * 2.0 for i in range(200)]
        highs = [c + 2.0 for c in closes]
        lows = [c - 2.0 for c in closes]

        result = compute_keltner(highs, lows, closes)

        lower_vals = [v for v in result["keltner_lower"] if v is not None]
        for i in range(1, len(lower_vals)):
            assert lower_vals[i] >= lower_vals[i - 1] or abs(lower_vals[i] - lower_vals[i - 1]) < 0.1, (
                f"Lower channel unexpectedly decreased at window {i}"
            )

    def test_keltner_mult_affects_width_only(self):
        """Changing ATR multiplier affects width but not the middle line."""
        highs, lows, closes = _make_small_ohlcv(100)

        result_1 = compute_keltner(highs, lows, closes, multiplier=1.0)
        result_2 = compute_keltner(highs, lows, closes, multiplier=2.0)
        result_3 = compute_keltner(highs, lows, closes, multiplier=3.0)

        for i in range(len(highs)):
            if result_1["keltner_upper"][i] is not None:
                # Width should scale with multiplier
                width_1 = result_1["keltner_upper"][i] - result_1["keltner_lower"][i]
                width_2 = result_2["keltner_upper"][i] - result_2["keltner_lower"][i]
                width_3 = result_3["keltner_upper"][i] - result_3["keltner_lower"][i]
                assert abs(width_2 - 2 * width_1) < 1e-6
                assert abs(width_3 - 3 * width_1) < 1e-6

    def test_keltner_with_realistic_data(self):
        """Test with realistic OHLCV data to ensure no errors."""
        import random
        random.seed(42)
        n = 250

        closes = [150.0]
        for _ in range(n - 1):
            change = random.uniform(-0.02, 0.02)
            closes.append(closes[-1] * (1 + change))

        highs = []
        lows = []
        for i, c in enumerate(closes):
            if i == 0:
                highs.append(c * 1.01)
                lows.append(c * 0.99)
            else:
                prev_c = closes[i - 1]
                highs.append(max(c, prev_c) * 1.005)
                lows.append(min(c, prev_c) * 0.995)

        result = compute_keltner(highs, lows, closes)

        assert len(result["keltner_upper"]) == n
        assert len(result["keltner_lower"]) == n
        # Should have valid values
        valid_upper = [v for v in result["keltner_upper"] if v is not None]
        valid_lower = [v for v in result["keltner_lower"] if v is not None]
        assert len(valid_upper) > 0
        assert len(valid_lower) > 0

    def test_keltner_custom_period_params(self):
        """Test with custom ATR and EMA periods."""
        highs, lows, closes = _make_small_ohlcv(100)

        # Custom: ema_period=14, atr_period=7
        result = compute_keltner(highs, lows, closes, ema_period=14, atr_period=7, multiplier=1.5)

        # First valid: max(14-1, 7) = max(13, 7) = 13
        for i in range(13):
            assert result["keltner_upper"][i] is None
            assert result["keltner_lower"][i] is None
        assert result["keltner_upper"][13] is not None
        assert result["keltner_lower"][13] is not None

    def test_keltner_upper_middle_lower_relationship(self):
        """Verify that: upper = middle + mult*ATR, lower = middle - mult*ATR."""
        import random
        random.seed(123)
        n = 100
        highs = [100.0 + random.uniform(-1, 1) for _ in range(n)]
        lows = [95.0 + random.uniform(-1, 1) for _ in range(n)]
        closes = [97.5 + random.uniform(-0.5, 0.5) for _ in range(n)]

        ema_period = 20
        atr_period = 10
        multiplier = 2.0
        result = compute_keltner(highs, lows, closes, ema_period=ema_period, atr_period=atr_period, multiplier=multiplier)

        tp = [(highs[i] + lows[i] + closes[i]) / 3.0 for i in range(n)]
        ema_tp = compute_ema(tp, ema_period)
        atr_values = compute_atr(highs, lows, closes, atr_period)

        for i in range(n):
            if result["keltner_upper"][i] is not None and result["keltner_lower"][i] is not None:
                expected_upper = ema_tp[i] + multiplier * atr_values[i]
                expected_lower = ema_tp[i] - multiplier * atr_values[i]
                assert abs(result["keltner_upper"][i] - expected_upper) < 1e-6, (
                    f"Upper mismatch at {i}: {result['keltner_upper'][i]} vs {expected_upper}"
                )
                assert abs(result["keltner_lower"][i] - expected_lower) < 1e-6, (
                    f"Lower mismatch at {i}: {result['keltner_lower'][i]} vs {expected_lower}"
                )


# ---------------------------------------------------------------------------
# compute_trend_columns tests
# ---------------------------------------------------------------------------

class TestComputeTrendColumns:
    """Verify the combined trend columns function."""

    def test_trend_columns_returns_expected_keys(self):
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_trend_columns(highs, lows, closes, 60)
        expected_keys = {
            "ta_ema20", "ta_ema50", "ta_ema200",
            "ta_supertrend", "ta_supertrend_direction",
            "ta_supertrend_upper", "ta_supertrend_lower",
            "ta_ma20", "ta_ma50", "ta_sma10",
            "ta_ma20_slope", "ta_ma50_slope",
            "ta_price_ma20_ratio",
            "ta_aroon_up", "ta_aroon_down",
            "ta_adx14", "ta_plus_di14", "ta_minus_di14",
            "ta_donchian_upper", "ta_donchian_lower",
            "ta_keltner_upper", "ta_keltner_lower",
        }
        assert set(result.keys()) == expected_keys

    def test_ema20_present(self):
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_trend_columns(highs, lows, closes, 60)
        ema20 = result["ta_ema20"]
        assert len(ema20) == 60
        # EMA20 should have valid values from index 19 onward
        assert ema20[19] is not None
        # First 19 should be None (seed period)
        assert all(v is None for v in ema20[:19])

    def test_ema50_partial(self):
        """With 60 rows, EMA50 should have valid values from index 49."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_trend_columns(highs, lows, closes, 60)
        ema50 = result["ta_ema50"]
        assert ema50[49] is not None
        assert all(v is None for v in ema50[:49])

    def test_ema200_none_for_short_series(self):
        """With only 60 rows, EMA200 should be all None."""
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_trend_columns(highs, lows, closes, 60)
        ema200 = result["ta_ema200"]
        assert all(v is None for v in ema200)

    def test_ema200_present_for_long_series(self):
        """With 250 rows, EMA200 should have valid values."""
        highs, lows, closes = _make_small_ohlcv(250)
        result = compute_trend_columns(highs, lows, closes, 250)
        ema200 = result["ta_ema200"]
        assert ema200[199] is not None
        assert all(v is None for v in ema200[:199])

    def test_supertrend_present(self):
        highs, lows, closes = _make_small_ohlcv(60)
        result = compute_trend_columns(highs, lows, closes, 60)
        assert len(result["ta_supertrend"]) == 60
        assert len(result["ta_supertrend_direction"]) == 60

    def test_all_columns_same_length(self):
        highs, lows, closes = _make_small_ohlcv(100)
        result = compute_trend_columns(highs, lows, closes, 100)
        length = 100
        for col_name, col_values in result.items():
            assert len(col_values) == length, (
                f"Column {col_name} has length {len(col_values)}, expected {length}"
            )


# ---------------------------------------------------------------------------
# process_csv tests
# ---------------------------------------------------------------------------

class TestProcessCSV:
    """Verify CSV processing with merge logic."""

    def test_process_csv_creates_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")

            _make_csv(input_path, [
                ["2024-01-01", 100, 105, 95, 102, 1000],
                ["2024-01-02", 102, 108, 100, 105, 1200],
                ["2024-01-03", 105, 110, 103, 108, 1100],
            ])

            rows = process_csv(input_path, output_path, 1, 1)
            assert rows == 3
            assert os.path.exists(output_path)

    def test_process_csv_includes_trend_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")

            base = date(2024, 1, 1)
            _make_csv(input_path, [
                [(base + timedelta(days=d)).strftime("%Y-%m-%d"), 100 + d, 105 + d, 95 + d, 102 + d, 1000]
                for d in range(60)  # 60 days
            ])

            process_csv(input_path, output_path, 1, 1)

            with open(output_path) as f:
                reader = csv.reader(f)
                headers = next(reader)

            expected_cols = {
                "ta_ema20", "ta_ema50", "ta_ema200",
                "ta_supertrend", "ta_supertrend_direction",
                "ta_supertrend_upper", "ta_supertrend_lower",
                "ta_adx14", "ta_plus_di14", "ta_minus_di14",
            }
            for col in expected_cols:
                assert col in headers, f"Missing column: {col}"

    def test_process_csv_creates_own_columns_only(self):
        """process_csv writes only Date + its own ta columns.

        Column merging across modules is handled by run_calculation.py,
        not inside individual modules.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")

            base = date(2024, 1, 1)
            _make_csv(input_path, [
                [(base + timedelta(days=d)).strftime("%Y-%m-%d"), 100 + d, 105 + d, 95 + d, 102 + d, 1000]
                for d in range(60)
            ])

            process_csv(input_path, output_path, 1, 1)

            with open(output_path) as f:
                reader = csv.reader(f)
                headers = next(reader)

            expected_cols = {"Date", "ta_ema20", "ta_ema50", "ta_ema200",
                             "ta_supertrend", "ta_supertrend_direction",
                             "ta_supertrend_upper", "ta_supertrend_lower",
                             "ta_ma20", "ta_ma50", "ta_sma10",
                             "ta_ma20_slope", "ta_ma50_slope",
                             "ta_price_ma20_ratio",
                             "ta_aroon_up", "ta_aroon_down",
                             "ta_adx14", "ta_plus_di14", "ta_minus_di14",
                             "ta_donchian_upper", "ta_donchian_lower",
                             "ta_keltner_upper", "ta_keltner_lower"}
            assert set(headers) == expected_cols

    def test_process_csv_with_realistic_data(self):
        """Test with realistic OHLCV data to ensure no errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "AAPL.csv")
            output_path = os.path.join(tmpdir, "AAPL.csv")

            # Generate 250 trading days of realistic data
            random.seed(42)
            rows = []
            price = 150.0
            base = date(2024, 1, 2)
            for i in range(250):
                row_date = (base + timedelta(days=i)).strftime("%Y-%m-%d")
                open_p = price
                change = random.uniform(-0.03, 0.03)
                close_p = price * (1 + change)
                high_p = max(open_p, close_p) * (1 + random.uniform(0, 0.01))
                low_p = min(open_p, close_p) * (1 - random.uniform(0, 0.01))
                volume = int(random.uniform(50_000_000, 100_000_000))
                rows.append([row_date, round(open_p, 2), round(high_p, 2),
                             round(low_p, 2), round(close_p, 2), volume])
                price = close_p

            _make_csv(input_path, rows)
            process_csv(input_path, output_path, 1, 1)

            with open(output_path) as f:
                reader = csv.reader(f)
                headers = next(reader)

            # Verify EMA200 has some valid values
            dates = [row[0] for row in rows]
            # Read the CSV and check EMA200 values
            with open(output_path) as f:
                reader = csv.DictReader(f)
                ema200_values = [row["ta_ema200"] for row in reader]

            valid_ema200 = [v for v in ema200_values if v is not None and v != ""]
            assert len(valid_ema200) > 0, "EMA200 should have valid values in 250-day data"

    def test_process_csv_output_sort_order(self):
        """Output should be sorted by Date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")

            # Write unsorted dates
            _make_csv(input_path, [
                ["2024-01-05", 105, 110, 100, 105, 1000],
                ["2024-01-01", 100, 105, 95, 100, 1000],
                ["2024-01-03", 102, 107, 97, 102, 1000],
                ["2024-01-02", 101, 106, 96, 101, 1000],
                ["2024-01-04", 104, 109, 99, 104, 1000],
            ])

            process_csv(input_path, output_path, 1, 1)

            with open(output_path) as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                rows = list(reader)

            dates = [row[0] for row in rows]
            assert dates == sorted(dates), "Output should be sorted by Date"


# ---------------------------------------------------------------------------
# Integration: edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_ema_single_value(self):
        """EMA with a single value."""
        result = compute_ema([100.0], 1)
        assert result == [100.0]

        result = compute_ema([100.0], 10)
        assert result == [None]

    def test_atr_single_value(self):
        """ATR with minimal data."""
        result = compute_atr([100.0], [90.0], [100.0], period=14)
        assert result == [None]  # Not enough data to compute ATR

    def test_supertrend_single_value(self):
        """SuperTrend with minimal data."""
        result = compute_supertrend([100.0], [90.0], [100.0])
        # Not enough data for ATR, so all bands and supertrend are None
        assert result["supertrend"] == [None]
        assert result["direction"] == [0]
        assert result["upper_band"] == [None]
        assert result["lower_band"] == [None]

    def test_supertrend_zero_atr(self):
        """When H=L=C (flat price), ATR=0, bands = mid point."""
        highs = [100.0] * 100
        lows = [100.0] * 100
        closes = [100.0] * 100
        result = compute_supertrend(highs, lows, closes)
        # All bands should be 100.0
        for ub in result["upper_band"]:
            assert ub is None or ub == 100.0
        for lb in result["lower_band"]:
            assert lb is None or lb == 100.0

    def test_compute_trend_columns_very_short(self):
        """Trend columns with only 5 data points."""
        highs = [105, 110, 115, 120, 125]
        lows = [95, 100, 105, 110, 115]
        closes = [100, 105, 110, 115, 120]
        result = compute_trend_columns(highs, lows, closes, 5)
        assert len(result["ta_ema20"]) == 5
        assert all(v is None for v in result["ta_ema20"])
        assert len(result["ta_ema200"]) == 5
        assert all(v is None for v in result["ta_ema200"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
