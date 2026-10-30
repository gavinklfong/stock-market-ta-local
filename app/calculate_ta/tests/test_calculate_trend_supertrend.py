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

