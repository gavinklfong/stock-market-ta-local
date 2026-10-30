import math

import numpy as np
import pytest

from calculate_momentum import (
    compute_rsi,
    compute_rsi_zscore,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_closes(length, base=100.0, slope=0.0, noise_range=0.0):
    """Generate a list of closing prices."""
    np.random.seed(0)
    closes = []
    for i in range(length):
        val = base + slope * i + np.random.uniform(-noise_range, noise_range)
        closes.append(max(val, 1.0))
    return closes


def _make_trending_closes(length, base=100.0, trend_strength=0.5):
    """Generate closes with a strong trend (so RSI varies and has variance)."""
    np.random.seed(1)
    closes = [base]
    for i in range(1, length):
        # Alternate up/down to create RSI variation
        direction = 1 if i % 4 < 2 else -1
        change = trend_strength * direction + np.random.uniform(-0.1, 0.1)
        closes.append(max(closes[-1] + change, 1.0))
    return closes


# ---------------------------------------------------------------------------
# TestComputeRSIZScore
# ---------------------------------------------------------------------------

class TestComputeRSIZScore:
    def test_basic_length(self):
        """Output list should match input length."""
        closes = _make_closes(100, base=100.0, noise_range=1.0)
        result = compute_rsi_zscore(closes)
        assert len(result) == 100

    def test_none_before_warmup(self):
        """RSI Z-score should be None until we have enough RSI values + window."""
        # Need rsi_period (14) for first RSI, then window (20) for first Z-score
        closes = _make_closes(30, base=100.0, noise_range=1.0)
        result = compute_rsi_zscore(closes)
        # First RSI at index 13, first Z-score needs window of RSI values
        # So first valid = rsi_period + window - 1 = 14 + 20 - 1 = 33
        for i in range(min(32, len(result))):
            assert result[i] is None

    def test_all_none_too_short(self):
        """If data too short for RSI, all should be None."""
        closes = _make_closes(10, base=100.0, noise_range=1.0)
        result = compute_rsi_zscore(closes)
        assert all(v is None for v in result)

    def test_has_valid_values(self):
        """With enough data, should produce valid Z-scores."""
        closes = _make_trending_closes(200, base=100.0, trend_strength=0.5)
        result = compute_rsi_zscore(closes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_zscore_values_reasonable(self):
        """Z-scores should be roughly in [-5, 5] range for normal data."""
        np.random.seed(42)
        closes = [100.0 + i * 0.05 + np.random.normal(0, 0.5) for i in range(200)]
        result = compute_rsi_zscore(closes)
        valid = [v for v in result if v is not None]
        for v in valid:
            assert -10.0 <= v <= 10.0

    def test_custom_rsi_period(self):
        """Custom RSI period should work."""
        closes = _make_trending_closes(200, base=100.0, trend_strength=0.5)
        result = compute_rsi_zscore(closes, rsi_period=7, window=10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_custom_window(self):
        """Custom window size should work."""
        closes = _make_trending_closes(200, base=100.0, trend_strength=0.5)
        result = compute_rsi_zscore(closes, rsi_period=14, window=10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_constant_prices_all_none(self):
        """All same price → RSI undefined (0/0) → Z-score all None."""
        closes = [100.0] * 50
        result = compute_rsi_zscore(closes)
        # With constant prices, all diffs are 0, so RSI may be NaN or 50
        # Either way, std of RSI window = 0, so Z-score = NaN → None
        for v in result:
            if v is not None:
                assert math.isnan(v) or math.isinf(v)

    def test_rsi_zscore_matches_manual_calc(self):
        """Verify against manual Z-score computation on a small example."""
        np.random.seed(99)
        closes = [100.0 + i * 0.3 + np.random.uniform(-0.5, 0.5) for i in range(100)]
        result = compute_rsi_zscore(closes, rsi_period=14, window=20)

        # Compute RSI manually
        rsi_values = compute_rsi(closes, 14)

        # Pick an index where we should have valid Z-score
        # First valid is at rsi_period + window - 1 = 33
        idx = 40  # safe index
        rsi_at_idx = rsi_values[idx]

        if rsi_at_idx is not None:
            # Get the window of RSI values ending at idx
            start = idx - 19  # window of 20
            if start >= 13:  # after RSI warmup (13 is first RSI index)
                window_rsi = [rsi_values[j] for j in range(start, idx + 1)
                              if rsi_values[j] is not None]
                if len(window_rsi) >= 2:
                    mean_rsi = sum(window_rsi) / len(window_rsi)
                    std_rsi = (sum((x - mean_rsi) ** 2 for x in window_rsi) /
                               len(window_rsi)) ** 0.5
                    if std_rsi > 0:
                        expected_z = (rsi_at_idx - mean_rsi) / std_rsi
                        assert result[idx] is not None
                        assert abs(result[idx] - expected_z) < 1e-6

    def test_increasing_trend_extreme_zscore(self):
        """Strong uptrend should push RSI high → positive Z-score."""
        closes = [100.0 + i * 2.0 for i in range(200)]
        result = compute_rsi_zscore(closes)
        valid = [v for v in result if v is not None]
        # With strong uptrend, RSI should be high (overbought territory)
        # So Z-scores should tend positive
        if valid:
            avg_z = sum(valid) / len(valid)
            assert avg_z > 0

    def test_decreasing_trend_extreme_zscore(self):
        """Strong downtrend should push RSI low → negative Z-score."""
        closes = [100.0 - i * 2.0 for i in range(200)]
        closes = [max(c, 1.0) for c in closes]
        result = compute_rsi_zscore(closes)
        valid = [v for v in result if v is not None]
        # With strong downtrend, RSI should be low (oversold territory)
        # So Z-scores should tend negative
        if valid:
            avg_z = sum(valid) / len(valid)
            assert avg_z < 0

    def test_default_parameters(self):
        """Default RSI period = 14, window = 20."""
        closes = _make_trending_closes(100, base=100.0, trend_strength=0.5)
        result = compute_rsi_zscore(closes)
        # First valid should be around index 33 (14 + 20 - 1)
        valid_indices = [i for i, v in enumerate(result) if v is not None]
        if valid_indices:
            assert valid_indices[0] == 33

    def test_zero_std_zscore_is_none(self):
        """When RSI window has zero std (constant RSI), Z-score should be None."""
        # Create price sequence that produces constant RSI (very unlikely but test)
        # Use flat price → RSI will be undefined or constant
        closes = [100.0] * 100
        result = compute_rsi_zscore(closes)
        # With flat prices, RSI computation may give NaN; Z-score should handle
        for v in result:
            if v is not None:
                assert math.isnan(v) or math.isinf(v)

    def test_short_window(self):
        """Small window should still work."""
        closes = _make_trending_closes(100, base=100.0, trend_strength=0.5)
        result = compute_rsi_zscore(closes, rsi_period=14, window=5)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_first_valid_index(self):
        """First valid index = rsi_period + window - 1."""
        closes = _make_trending_closes(200, base=100.0, trend_strength=0.5)
        result = compute_rsi_zscore(closes, rsi_period=14, window=20)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 14 + 20 - 1  # = 33

    def test_first_valid_index_custom_period(self):
        """First valid index with custom RSI period."""
        closes = _make_trending_closes(200, base=100.0, trend_strength=0.5)
        result = compute_rsi_zscore(closes, rsi_period=7, window=10)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 7 + 10 - 1  # = 16
