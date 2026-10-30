"""Unit tests for calculate_return.py — verifies forward-looking return computations."""

import os
import math

import numpy as np
import pandas as pd
import pytest

from calculate_return import (
    compute_alpha_beta,
    compute_future_returns,
    compute_past_performance,
    compute_return_columns,
    process_csv,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sample(n=50, base_price=100.0, base_range=2.0):
    """Generate aligned OHLC data for testing."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 1.0)
        closes.append(max(closes[-1] + change, 10.0))

    highs = [c + abs(np.random.normal(0, base_range / 2)) for c in closes]
    lows = [max(c - abs(np.random.normal(0, base_range / 2)), 1.0) for c in closes]

    return highs, lows, closes


def _make_dates(n):
    """Generate n consecutive dates starting from 2024-01-01."""
    return [pd.Timestamp("2024-01-01") + pd.Timedelta(days=i) for i in range(n)]


# ---------------------------------------------------------------------------
# TestComputeFutureReturns
# ---------------------------------------------------------------------------


class TestComputePastPerformance:
    def test_length(self):
        _, _, closes = _make_sample(50)
        result = compute_past_performance(closes)
        for h in result:
            assert len(result[h]) == 50

    def test_short_data(self):
        closes = [100.0 + i for i in range(5)]
        result = compute_past_performance(closes, horizons=(21,))
        assert result[21] == [None] * 5

    def test_first_rows_none(self):
        """First H rows should be None for horizon H."""
        closes = [100.0 + i for i in range(30)]
        result = compute_past_performance(closes, horizons=(21,))
        for i in range(21):
            assert result[21][i] is None
        # First non-None at index 21
        assert result[21][21] is not None

    def test_positive_return_uptrend(self):
        """Uptrend should produce positive past performance."""
        closes = [100.0 + i for i in range(300)]
        result = compute_past_performance(closes, horizons=(21, 63, 126, 252))
        for h in result:
            for i in range(h, len(closes)):
                assert result[h][i] > 0

    def test_negative_return_downtrend(self):
        """Downtrend should produce negative past performance."""
        closes = [1000.0 - i for i in range(300)]
        result = compute_past_performance(closes, horizons=(21,))
        for i in range(21, len(closes)):
            assert result[21][i] < 0

    def test_constant_prices_zero_return(self):
        """Constant prices should produce zero returns."""
        closes = [100.0] * 20
        result = compute_past_performance(closes, horizons=(21,))
        # All should be None since we don't have 21 rows
        assert result[21] == [None] * 20

    def test_constant_prices_nonzero_return(self):
        """Constant prices with enough data should produce zero returns."""
        closes = [100.0] * 25
        result = compute_past_performance(closes, horizons=(21,))
        assert result[21][21] == 0.0
        assert result[21][24] == 0.0

    def test_multiple_horizons(self):
        """Multiple horizons should all be present."""
        closes = [100.0 + i * 0.5 for i in range(300)]
        horizons = (21, 63, 126, 252)
        result = compute_past_performance(closes, horizons=horizons)
        for h in horizons:
            assert h in result
            assert len(result[h]) == 300

    def test_return_formula(self):
        """Past performance should match (current - past) / past * 100."""
        closes = [100.0, 105.0, 110.0, 115.0, 120.0, 125.0]
        result = compute_past_performance(closes, horizons=(5,))
        # At index 5: (125 - 100) / 100 * 100 = 25%
        assert result[5][5] == pytest.approx(25.0, abs=1e-10)

    def test_return_formula_21_days(self):
        """Test 21-day horizon formula."""
        closes = [100.0 + i for i in range(50)]
        result = compute_past_performance(closes, horizons=(21,))
        # At index 21: close=121, past=100 → (121-100)/100*100 = 21%
        assert result[21][21] == pytest.approx(21.0, abs=1e-10)

    def test_percentage_output(self):
        """Past performance should be expressed as percentage."""
        closes = [100.0, 110.0, 90.0] + [100.0] * 50
        result = compute_past_performance(closes, horizons=(1,))
        # At index 1: (110 - 100) / 100 * 100 = 10%
        assert result[1][1] == pytest.approx(10.0, abs=1e-10)
        # At index 2: (90 - 110) / 110 * 100 ≈ -18.18%
        assert result[1][2] == pytest.approx(-20.0 / 11 * 10, abs=1e-10)

    def test_default_horizons(self):
        """Default horizons should be 21, 63, 126, 252."""
        closes = [100.0 + i for i in range(300)]
        result = compute_past_performance(closes)
        assert set(result.keys()) == {21, 63, 126, 252}


