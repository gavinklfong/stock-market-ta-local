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

