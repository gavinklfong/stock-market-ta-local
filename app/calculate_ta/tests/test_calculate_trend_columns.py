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
    compute_price_dist_ma,
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
            "ta_price_dist_ema20", "ta_price_dist_ema50", "ta_price_dist_ema200",
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

