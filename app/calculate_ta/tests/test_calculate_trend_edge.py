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
