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

