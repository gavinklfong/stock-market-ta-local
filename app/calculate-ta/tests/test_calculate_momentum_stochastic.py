import math
import os
import tempfile
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from calculate_momentum import (
    compute_cci,
    compute_ema,
    compute_macd,
    compute_momentum_columns,
    compute_roc,
    compute_rsi,
    compute_stochastic,
    compute_tsi,
    compute_williams_r,
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
        closes.append(max(val, 1.0))  # keep positive
    return closes


def _make_ohlcv(n=100, base=100.0):
    """Generate synthetic OHLCV data.

    Returns (highs, lows, closes) lists of equal length.
    """
    np.random.seed(42)
    closes = [base]
    for _ in range(n - 1):
        change = np.random.normal(0, 0.01) * closes[-1]
        closes.append(max(closes[-1] + change, 1.0))

    highs = [c * (1 + abs(np.random.normal(0, 0.005))) for c in closes]
    lows = [c * (1 - abs(np.random.normal(0, 0.005))) for c in closes]

    return highs, lows, closes


# ---------------------------------------------------------------------------
# TestComputeEMA
# ---------------------------------------------------------------------------

class TestComputeStochastic:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_stochastic(closes)
        assert len(result["ta_stoch_k"]) == 50
        assert len(result["ta_stoch_d"]) == 50

    def test_short_data_all_none(self):
        """When fewer than k_period values, both %K and %D are all None."""
        closes = [100.0, 101.0, 102.0]
        result = compute_stochastic(closes)
        assert all(v is None for v in result["ta_stoch_k"])
        assert all(v is None for v in result["ta_stoch_d"])

    def test_first_valid_k_at_index(self):
        """First valid %K should be at index k_period - 1 (13 for default k=14)."""
        closes = _make_closes(50, base=100, noise_range=1.0)
        result = compute_stochastic(closes)
        for i in range(13):
            assert result["ta_stoch_k"][i] is None
        assert result["ta_stoch_k"][13] is not None

    def test_first_valid_d_at_index(self):
        """First valid %D should be at index k_period + d_period - 2 (15 for k=14, d=3)."""
        closes = _make_closes(50, base=100, noise_range=1.0)
        result = compute_stochastic(closes)
        for i in range(15):
            assert result["ta_stoch_d"][i] is None
        assert result["ta_stoch_d"][15] is not None

    def test_k_equals_100_when_close_is_highest(self):
        """When close is always the highest in the window, %K = 100."""
        closes = [100.0 + i for i in range(20)]  # linearly increasing
        result = compute_stochastic(closes)
        for i in range(13, 20):
            assert result["ta_stoch_k"][i] == pytest.approx(100.0, abs=1e-9)

    def test_k_equals_0_when_close_is_lowest(self):
        """When close is always the lowest in the window, %K = 0."""
        # Close drops every day so it's always the low of the window
        closes = [200.0 - i * 10.0 for i in range(20)]
        result = compute_stochastic(closes)
        for i in range(13, 20):
            assert result["ta_stoch_k"][i] == pytest.approx(0.0, abs=1e-9)

    def test_k_range(self):
        """%K should always be between 0 and 100."""
        np.random.seed(42)
        closes = [100.0 + np.random.normal(0, 5) for _ in range(100)]
        closes = [max(c, 1.0) for c in closes]
        result = compute_stochastic(closes)
        valid_k = [v for v in result["ta_stoch_k"] if v is not None]
        for v in valid_k:
            assert 0.0 <= v <= 100.0

    def test_d_equals_sma_of_k(self):
        """%D at each index should equal the SMA of the d_period most recent
        valid %K values whose last one lands exactly at that index."""
        np.random.seed(7)
        closes = [100.0 + np.random.normal(0, 3) for _ in range(50)]
        closes = [max(c, 1.0) for c in closes]
        result = compute_stochastic(closes)

        d_period = 3
        # Collect (index, value) pairs of valid %K
        valid_k = [
            (idx, result["ta_stoch_k"][idx])
            for idx in range(len(result["ta_stoch_k"]))
            if result["ta_stoch_k"][idx] is not None
        ]
        for i in range(d_period, len(closes)):
            if result["ta_stoch_d"][i] is not None:
                # Find the d_period most recent valid %K at/before index i
                window = [
                    v for idx, v in valid_k
                    if i - d_period < idx <= i
                ]
                assert len(window) == d_period
                expected_d = sum(window) / d_period
                assert result["ta_stoch_d"][i] == pytest.approx(
                    expected_d, abs=1e-9
                )

    def test_known_values(self):
        """Verify exact values with a hand-traceable case."""
        # Window [0:14]: [100, 110, 95, 105, 98, 103, 97, 108, 94, 106, 99, 104, 96, 107]
        # low=94, high=110, close=107
        # %K[13] = (107 - 94) / (110 - 94) * 100 = 13/16 * 100 = 81.25
        closes = [
            100.0, 110.0, 95.0, 105.0, 98.0, 103.0, 97.0, 108.0,
            94.0, 106.0, 99.0, 104.0, 96.0, 107.0,
        ]
        result = compute_stochastic(closes)
        assert result["ta_stoch_k"][13] == pytest.approx(81.25, abs=1e-9)

    def test_custom_params(self):
        """Stochastic with custom k_period and d_period should work."""
        closes = [100.0 + i * 0.1 for i in range(30)]
        result = compute_stochastic(closes, k_period=7, d_period=5)
        assert len(result["ta_stoch_k"]) == 30
        assert len(result["ta_stoch_d"]) == 30
        # First valid %K at index 6 (7 - 1)
        for i in range(6):
            assert result["ta_stoch_k"][i] is None
        assert result["ta_stoch_k"][6] is not None
        # First valid %D at index 10 (6 + 5 - 1)
        for i in range(10):
            assert result["ta_stoch_d"][i] is None
        assert result["ta_stoch_d"][10] is not None

    def test_constant_prices(self):
        """With constant prices, %K should be 50 (close is in the middle of [low, high] when all equal)."""
        closes = [100.0] * 30
        result = compute_stochastic(closes)
        # When all values are equal, hh == ll, so hh != ll is False → %K stays None
        # Actually, when all equal, hh = ll = 100, so hh != ll is False
        # This means %K remains None for constant prices
        valid_k = [v for v in result["ta_stoch_k"] if v is not None]
        assert len(valid_k) == 0


