"""Unit tests for compute_price_dist_ma in calculate_trend.py."""

import pytest

from calculate_trend import (
    compute_price_dist_ma,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_price_series(n=100, base=100.0, trend=0.1):
    """Generate a price series with optional linear trend."""
    prices = [base + i * trend for i in range(n)]
    return prices


def _make_ema_series(n=100, base=100.0, start_seed=None):
    """Generate a flat EMA-like series for testing."""
    if start_seed is None:
        start_seed = base
    return [start_seed] * n


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestComputePriceDistMA:
    """Verify compute_price_dist_ma function."""

    def test_length_matches_input(self):
        """Output list should match input length."""
        closes = _make_price_series(100)
        ema = _make_ema_series(100, base=100.0)
        result = compute_price_dist_ma(closes, ema)
        assert len(result) == 100

    def test_none_where_ema_is_none(self):
        """Result should be None where EMA is None."""
        closes = _make_price_series(100, base=100.0, trend=0.5)
        ema = [None] * 100
        result = compute_price_dist_ma(closes, ema)
        assert all(v is None for v in result)

    def test_none_where_close_is_none(self):
        """Result should be None where close is None."""
        closes = [None] * 100
        ema = _make_ema_series(100, base=100.0)
        result = compute_price_dist_ma(closes, ema)
        assert all(v is None for v in result)

    def test_positive_when_price_above_ema(self):
        """Price above EMA should yield positive distance."""
        closes = [110.0 + i for i in range(10)]  # rising above EMA
        ema = [100.0] * 10
        result = compute_price_dist_ma(closes, ema)
        # dist = (110 - 100) / 100 * 100 = 10%
        assert result[0] == pytest.approx(10.0)
        # (111 - 100) / 100 * 100 = 11%
        assert result[1] == pytest.approx(11.0)

    def test_negative_when_price_below_ema(self):
        """Price below EMA should yield negative distance."""
        closes = [90.0 + i for i in range(10)]  # below EMA
        ema = [100.0] * 10
        result = compute_price_dist_ma(closes, ema)
        assert result[0] == pytest.approx(-10.0)
        assert result[1] == pytest.approx(-9.0)

    def test_zero_when_price_equals_ema(self):
        """Price equal to EMA should yield 0% distance."""
        closes = [100.0] * 10
        ema = [100.0] * 10
        result = compute_price_dist_ma(closes, ema)
        assert all(v == 0.0 for v in result)

    def test_formula_correctness(self):
        """Verify the formula: (close - ema) / ema * 100."""
        closes = [105.0]
        ema = [100.0]
        result = compute_price_dist_ma(closes, ema)
        assert result[0] == pytest.approx(5.0)  # (105-100)/100 * 100

    def test_none_where_ema_is_zero(self):
        """Result should be None where EMA is zero."""
        closes = [100.0] * 5
        ema = [0.0] * 5
        result = compute_price_dist_ma(closes, ema)
        assert all(v is None for v in result)

    def test_aligned_with_real_ema(self):
        """Test with EMA computed from same price series."""
        from calculate_trend import compute_ema

        closes = _make_price_series(100, base=100.0, trend=0.2)
        ema20 = compute_ema(closes, 20)
        result = compute_price_dist_ma(closes, ema20)

        # Length should match
        assert len(result) == 100

        # First 19 should be None (EMA20 seed period)
        assert all(v is None for v in result[:19])

        # Index 19 should have a value
        assert result[19] is not None

        # Verify formula at index 19
        if result[19] is not None:
            expected = (closes[19] - ema20[19]) / ema20[19] * 100.0
            assert abs(result[19] - expected) < 1e-6

    def test_longer_period_ema(self):
        """Test with EMA50."""
        from calculate_trend import compute_ema

        closes = _make_price_series(200, base=100.0, trend=0.3)
        ema50 = compute_ema(closes, 50)
        result = compute_price_dist_ma(closes, ema50)

        # First 49 should be None
        assert all(v is None for v in result[:49])
        assert result[49] is not None

    def test_short_series(self):
        """Short series should produce all None."""
        closes = [100.0, 101.0, 102.0]
        ema = [None, None, None]
        result = compute_price_dist_ma(closes, ema)
        assert result == [None, None, None]

    def test_mixed_none_and_values(self):
        """Mix of None and valid EMA values."""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0]
        ema = [None, None, 100.5, 101.5, 102.5]
        result = compute_price_dist_ma(closes, ema)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == pytest.approx((102.0 - 100.5) / 100.5 * 100)
        assert result[3] == pytest.approx((103.0 - 101.5) / 101.5 * 100)
        assert result[4] == pytest.approx((104.0 - 102.5) / 102.5 * 100)

    def test_price_oscillates_around_ema(self):
        """Price oscillating above and below EMA should produce mixed signs."""
        closes = [105, 95, 105, 95, 105, 95, 105, 95, 105, 95]
        ema = [100] * 10
        result = compute_price_dist_ma(closes, ema)
        assert result[0] == pytest.approx(5.0)   # above
        assert result[1] == pytest.approx(-5.0)  # below
        assert result[2] == pytest.approx(5.0)
        assert result[3] == pytest.approx(-5.0)

    def test_large_percentages(self):
        """Large price deviations should produce large percentages."""
        closes = [200.0]
        ema = [100.0]
        result = compute_price_dist_ma(closes, ema)
        assert result[0] == pytest.approx(100.0)  # 100% above

    def test_small_percentages(self):
        """Small deviations should produce small percentages."""
        closes = [100.1]
        ema = [100.0]
        result = compute_price_dist_ma(closes, ema)
        assert result[0] == pytest.approx(0.1, abs=1e-6)
