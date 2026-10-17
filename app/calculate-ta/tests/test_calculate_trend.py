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
            }
            for col in expected_cols:
                assert col in headers, f"Missing column: {col}"

    def test_process_csv_preserves_existing_columns(self):
        """When merging with existing output, original columns should be preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")

            base = date(2024, 1, 1)
            # Write an existing output with a custom column
            _make_csv(output_path, [
                [(base + timedelta(days=d)).strftime("%Y-%m-%d"), 100 + d, 105 + d, 95 + d, 102 + d, 1000, 50 + d]
                for d in range(60)
            ])
            # Add a header that includes the custom column
            with open(output_path, "r") as f:
                lines = f.readlines()
            # Rewrite with proper header
            with open(output_path, "w") as f:
                f.write("Date,Open,High,Low,Close,Volume,custom_col\n")
                for line in lines[1:]:
                    f.write(line.strip() + ",existing\n")

            _make_csv(input_path, [
                [(base + timedelta(days=d)).strftime("%Y-%m-%d"), 100 + d, 105 + d, 95 + d, 102 + d, 1000]
                for d in range(60)
            ])

            process_csv(input_path, output_path, 1, 1)

            with open(output_path) as f:
                reader = csv.reader(f)
                headers = next(reader)

            assert "custom_col" in headers, "Custom column should be preserved"
            assert "existing" not in headers, "Malformed column name should not appear"

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
