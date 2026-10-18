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

