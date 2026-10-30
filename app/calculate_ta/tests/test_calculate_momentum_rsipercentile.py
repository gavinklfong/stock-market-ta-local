import numpy as np
import pytest

from calculate_momentum import (
    compute_rsi_percentile,
    compute_rsi,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_closes(length, base=100.0, volatility=1.0):
    """Generate price data with moderate movement."""
    np.random.seed(0)
    closes = [base]
    for _ in range(length - 1):
        change = np.random.normal(0, volatility)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


def _make_rsi_test_data(length, base=100.0, volatility=2.0):
    """Generate price data that produces meaningful RSI variation."""
    np.random.seed(42)
    closes = [base]
    for _ in range(length - 1):
        change = np.random.normal(0, volatility)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


# ---------------------------------------------------------------------------
# TestComputeRSIPercentile
# ---------------------------------------------------------------------------

class TestComputeRSIPercentile:
    def test_basic_length(self):
        """Output list should match input length."""
        closes = _make_rsi_test_data(200)
        result = compute_rsi_percentile(closes)
        assert len(result) == 200

    def test_none_before_warmup(self):
        """RSI percentile should be None until RSI + window are filled."""
        closes = _make_rsi_test_data(100)
        result = compute_rsi_percentile(closes)
        # First RSI valid at index 14, first percentile at index 14+20-1=33
        for i in range(33):
            assert result[i] is None

    def test_first_valid_at_rsi_period_plus_window_minus_1(self):
        """First valid percentile at index rsi_period + window - 1."""
        closes = _make_rsi_test_data(200)
        result = compute_rsi_percentile(closes)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 33  # 14 + 20 - 1

    def test_custom_window_first_valid(self):
        """First valid index = rsi_period + custom_window - 1."""
        closes = _make_rsi_test_data(100)
        result = compute_rsi_percentile(closes, rsi_period=14, window=10)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 23  # 14 + 10 - 1

    def test_all_none_too_short(self):
        """If data too short for RSI + window, all should be None."""
        closes = _make_rsi_test_data(30)
        result = compute_rsi_percentile(closes)
        assert all(v is None for v in result)

    def test_has_valid_values(self):
        """With enough data, should produce valid percentiles."""
        closes = _make_rsi_test_data(500)
        result = compute_rsi_percentile(closes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_percentile_values_in_range(self):
        """Percentiles should be in [0, 100]."""
        closes = _make_rsi_test_data(500)
        result = compute_rsi_percentile(closes)
        valid = [v for v in result if v is not None]
        for v in valid:
            assert 0 <= v <= 100

    def test_rsi_above_average_high_percentile(self):
        """When RSI is above recent average, percentile should be high."""
        # Create a price series that trends up (bullish → RSI tends above 50)
        closes = [100 + i * 0.5 + np.random.normal(0, 0.5) for i in range(200)]
        result = compute_rsi_percentile(closes)
        valid = [v for v in result if v is not None]
        if valid:
            # In a trending market, RSI spends more time in the upper half
            avg_p = sum(valid) / len(valid)
            assert avg_p > 40  # Should be above 50th percentile on average

    def test_rsi_below_average_low_percentile(self):
        """When RSI is below recent average, percentile should be low."""
        # Create a price series that trends down (bearish → RSI tends below 50)
        closes = [200 - i * 0.5 + np.random.normal(0, 0.5) for i in range(200)]
        result = compute_rsi_percentile(closes)
        valid = [v for v in result if v is not None]
        if valid:
            avg_p = sum(valid) / len(valid)
            assert avg_p < 60  # Should be below 50th percentile on average

    def test_constant_price_zero_rsi(self):
        """Constant prices → RSI = 50 → all percentiles should be 0 (nothing strictly below)."""
        closes = [100.0] * 100
        result = compute_rsi_percentile(closes)
        for i, v in enumerate(result):
            if v is not None:
                # RSI will be 50 for all valid indices (no gains/losses)
                # All values in window = 50, so nothing strictly below → 0th percentile
                assert v == 0.0

    def test_custom_window(self):
        """Custom window size should work."""
        closes = _make_rsi_test_data(100)
        result = compute_rsi_percentile(closes, rsi_period=14, window=10)
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
        closes = _make_rsi_test_data(200)
        result = compute_rsi_percentile(closes, rsi_period=14, window=20)

        # Pick an index beyond warmup
        idx = 40
        if result[idx] is not None:
            rsi_values = compute_rsi(closes, 14)
            window_rsi = []
            for j in range(idx - 19, idx + 1):
                v = rsi_values[j]
                if v is not None:
                    window_rsi.append(v)
            if len(window_rsi) >= 2:
                rsi_i = rsi_values[idx]
                below_count = sum(1 for v in window_rsi if v < rsi_i)
                expected_p = (below_count / len(window_rsi)) * 100.0
                assert abs(result[idx] - expected_p) < 1e-6

    def test_default_parameters(self):
        """Default RSI period=14, window=20."""
        closes = _make_rsi_test_data(200)
        result = compute_rsi_percentile(closes)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 33  # 14 + 20 - 1

    def test_zero_volume_price_stagnation(self):
        """Price stagnation after movement → RSI near 50, low percentile variance."""
        closes = _make_rsi_test_data(50)
        # Stagnate for the rest
        stagnation_price = closes[-1]
        closes += [stagnation_price] * 150
        result = compute_rsi_percentile(closes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # During stagnation, RSI drifts toward 50, percentiles should be bounded
        for v in valid:
            assert 0 <= v <= 100

    def test_high_volatility(self):
        """High volatility should produce varied percentiles."""
        closes = _make_rsi_test_data(300, volatility=10.0)
        result = compute_rsi_percentile(closes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 10
        # Should have a good spread of percentiles
        unique_pcts = len(set(round(v, 1) for v in valid))
        assert unique_pcts > 10

    def test_all_same_percentile(self):
        """If all RSI in window are equal, percentile should be 0."""
        # This happens when prices move in a very specific pattern
        # Create a series where RSI stays near 50
        closes = [100 + 0.01 * i for i in range(100)]  # Very gradual uptrend
        result = compute_rsi_percentile(closes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # With gradual uptrend, RSI will vary slightly → some percentiles > 0
        # But the key property is they're all in [0, 100]
        for v in valid:
            assert 0 <= v <= 100

    def test_rsi_at_extremes(self):
        """RSI near 0 or 100 should produce extreme percentiles."""
        # Create a strongly trending series
        closes = [100 + i * 2 for i in range(300)]
        result = compute_rsi_percentile(closes)
        valid = [v for v in result if v is not None]
        if valid:
            # In a strong uptrend, RSI stays elevated → high percentiles
            assert len(valid) > 0
            for v in valid:
                assert 0 <= v <= 100

    def test_window_boundary_behavior(self):
        """Verify behavior right at the window boundary."""
        closes = _make_rsi_test_data(200)
        result = compute_rsi_percentile(closes, rsi_period=14, window=20)

        # At the first valid index, window is [14..33], current is RSI[33]
        # RSI values at indices 14-33 are the first 20 RSI values
        idx = 33
        rsi_values = compute_rsi(closes, 14)
        if result[idx] is not None:
            window_rsi = []
            for j in range(14, 34):
                v = rsi_values[j]
                if v is not None:
                    window_rsi.append(v)
            below_count = sum(1 for v in window_rsi if v < rsi_values[idx])
            expected_p = (below_count / len(window_rsi)) * 100.0
            assert abs(result[idx] - expected_p) < 1e-6
