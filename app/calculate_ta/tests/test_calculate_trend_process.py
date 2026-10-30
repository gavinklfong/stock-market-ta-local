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
                             "ta_price_dist_ema20", "ta_price_dist_ema50", "ta_price_dist_ema200",
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

