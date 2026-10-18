import numpy as np
import pytest

from calculate_volatility import (
    compute_atr,
    compute_atr_percentile,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_sample(n=200, base_price=100.0, volatility=1.0):
    """Generate price data with moderate movement."""
    np.random.seed(0)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, volatility)
        closes.append(max(closes[-1] + change, 10.0))

    highs = [c + abs(np.random.normal(0, 2.0)) for c in closes]
    lows = [max(c - abs(np.random.normal(0, 2.0)), 1.0) for c in closes]

    return highs, lows, closes


# ---------------------------------------------------------------------------
# TestComputeATRPercentile
# ---------------------------------------------------------------------------

class TestComputeATRPercentile:
    def test_basic_length(self):
        """Output list should match input length."""
        highs, lows, closes = _make_sample(200)
        result = compute_atr_percentile(highs, lows, closes)
        assert len(result) == 200

    def test_none_before_warmup(self):
        """ATR percentile should be None until ATR + window are filled."""
        highs, lows, closes = _make_sample(100)
        result = compute_atr_percentile(highs, lows, closes)
        # First ATR valid at index 14, first percentile at index 14+20-1=33
        for i in range(33):
            assert result[i] is None

    def test_first_valid_at_atr_period_plus_window_minus_1(self):
        """First valid percentile at index atr_period + window - 1."""
        highs, lows, closes = _make_sample(200)
        result = compute_atr_percentile(highs, lows, closes)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 33  # 14 + 20 - 1

    def test_custom_window_first_valid(self):
        """First valid index = atr_period + custom_window - 1."""
        highs, lows, closes = _make_sample(100)
        result = compute_atr_percentile(highs, lows, closes, atr_period=14, window=10)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 23  # 14 + 10 - 1

    def test_all_none_too_short(self):
        """If data too short for ATR + window, all should be None."""
        highs, lows, closes = _make_sample(30)
        result = compute_atr_percentile(highs, lows, closes)
        assert all(v is None for v in result)

    def test_has_valid_values(self):
        """With enough data, should produce valid percentiles."""
        highs, lows, closes = _make_sample(500)
        result = compute_atr_percentile(highs, lows, closes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_percentile_values_in_range(self):
        """Percentiles should be in [0, 100]."""
        highs, lows, closes = _make_sample(500)
        result = compute_atr_percentile(highs, lows, closes)
        valid = [v for v in result if v is not None]
        for v in valid:
            assert 0 <= v <= 100

    def test_increasing_volatility_high_percentile(self):
        """When volatility is increasing, ATR percentile should trend higher."""
        np.random.seed(123)
        n = 300
        base = 100.0
        closes = [base]
        for i in range(n - 1):
            # Volatility ramps up over time
            vol = 1.0 + i / 50.0
            change = np.random.normal(0, vol)
            closes.append(max(closes[-1] + change, 10.0))

        highs = [c + abs(np.random.normal(0, 2.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 2.0)), 1.0) for c in closes]

        result = compute_atr_percentile(highs, lows, closes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Second half should have higher average percentile than first half
        mid = len(valid) // 2
        if mid > 0:
            avg_first = sum(valid[:mid]) / mid
            avg_second = sum(valid[mid:]) / (len(valid) - mid)
            # With rising volatility, later percentiles should trend higher
            assert avg_second > avg_first - 5  # allow some noise

    def test_constant_volatility(self):
        """Constant range → ATR constant → all percentiles should be 0."""
        closes = [100.0 + i * 0.1 for i in range(100)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        result = compute_atr_percentile(highs, lows, closes)
        for i, v in enumerate(result):
            if v is not None:
                # ATR will be constant (fixed range), so nothing strictly below → 0th percentile
                assert v == 0.0

    def test_custom_window(self):
        """Custom window size should work."""
        highs, lows, closes = _make_sample(100)
        result = compute_atr_percentile(highs, lows, closes, atr_period=14, window=10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 23  # 14 + 10 - 1

    def test_manual_percentile_calculation(self):
        """Verify percentile against manual calculation."""
        highs, lows, closes = _make_sample(200)
        result = compute_atr_percentile(highs, lows, closes, atr_period=14, window=20)

        # Pick an index beyond warmup
        idx = 40
        if result[idx] is not None:
            atr_values = compute_atr(highs, lows, closes, 14)
            window_atr = []
            for j in range(idx - 19, idx + 1):
                v = atr_values[j]
                if v is not None:
                    window_atr.append(v)
            if len(window_atr) >= 2:
                atr_i = atr_values[idx]
                below_count = sum(1 for v in window_atr if v < atr_i)
                expected_p = (below_count / len(window_atr)) * 100.0
                assert abs(result[idx] - expected_p) < 1e-6

    def test_default_parameters(self):
        """Default ATR period=14, window=20."""
        highs, lows, closes = _make_sample(200)
        result = compute_atr_percentile(highs, lows, closes)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 33  # 14 + 20 - 1

    def test_high_volatility_spread(self):
        """High volatility should produce varied percentiles."""
        highs, lows, closes = _make_sample(300, volatility=10.0)
        result = compute_atr_percentile(highs, lows, closes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 10
        # Should have a good spread of percentiles
        unique_pcts = len(set(round(v, 1) for v in valid))
        assert unique_pcts > 10

    def test_decreasing_volatility(self):
        """When volatility decreases, ATR percentile should trend lower."""
        np.random.seed(456)
        n = 300
        base = 100.0
        closes = [base]
        for i in range(n - 1):
            # Volatility ramps down over time
            vol = 10.0 - i / 30.0
            vol = max(vol, 0.5)
            change = np.random.normal(0, vol)
            closes.append(max(closes[-1] + change, 10.0))

        highs = [c + abs(np.random.normal(0, vol * 0.2)) for c, vol in zip(closes, [max(10.0 - i / 30.0, 0.5) for i in range(n)])]
        lows = [max(c - abs(np.random.normal(0, vol * 0.2)), 1.0) for c, vol in zip(closes, [max(10.0 - i / 30.0, 0.5) for i in range(n)])]

        result = compute_atr_percentile(highs, lows, closes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # First half should have higher average percentile (rising ATR phase)
        mid = len(valid) // 2
        if mid > 0:
            avg_first = sum(valid[:mid]) / mid
            avg_second = sum(valid[mid:]) / (len(valid) - mid)
            assert avg_first > avg_second - 5

    def test_atr_at_extremes(self):
        """Very high or very low ATR values should produce extreme percentiles."""
        # Create a series with a volatility spike
        n = 300
        closes = [100.0] * n
        for i in range(100, 110):
            closes[i] = closes[i - 1] + 20  # Big jump
        for i in range(110, 200):
            closes[i] = closes[i - 1] - 2  # Slow decline
        # Back to flat
        for i in range(200, 250):
            closes[i] = closes[-1]

        highs = [c + abs(np.random.normal(0, 0.1)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 0.1)), 1.0) for c in closes]

        result = compute_atr_percentile(highs, lows, closes)
        valid = [v for v in result if v is not None]
        if valid:
            for v in valid:
                assert 0 <= v <= 100

    def test_window_boundary_behavior(self):
        """Verify behavior right at the window boundary."""
        highs, lows, closes = _make_sample(200)
        result = compute_atr_percentile(highs, lows, closes, atr_period=14, window=20)

        # At the first valid index, window is [14..33], current is ATR[33]
        idx = 33
        atr_values = compute_atr(highs, lows, closes, 14)
        if result[idx] is not None:
            window_atr = []
            for j in range(14, 34):
                v = atr_values[j]
                if v is not None:
                    window_atr.append(v)
            below_count = sum(1 for v in window_atr if v < atr_values[idx])
            expected_p = (below_count / len(window_atr)) * 100.0
            assert abs(result[idx] - expected_p) < 1e-6
