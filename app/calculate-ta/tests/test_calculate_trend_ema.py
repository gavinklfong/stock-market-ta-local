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

