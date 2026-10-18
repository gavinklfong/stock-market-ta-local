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

class TestComputeMACD:
    def test_length(self):
        closes = _make_closes(50)
        macd = compute_macd(closes)
        assert len(macd["macd_line"]) == 50
        assert len(macd["signal_line"]) == 50
        assert len(macd["histogram"]) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        macd = compute_macd(closes)
        assert all(v is None for v in macd["macd_line"])
        assert all(v is None for v in macd["signal_line"])
        assert all(v is None for v in macd["histogram"])

    def test_keys(self):
        closes = _make_closes(50)
        macd = compute_macd(closes)
        assert set(macd.keys()) == {"macd_line", "signal_line", "histogram"}

    def test_first_valid_macd_line(self):
        """MACD line first valid at EMA slow period - 1 (index 25 for slow=26)."""
        closes = _make_closes(50, base=50)
        macd = compute_macd(closes)
        for i in range(25):
            assert macd["macd_line"][i] is None
        assert macd["macd_line"][25] is not None

    def test_histogram_equals_difference(self):
        """Histogram should equal MACD line minus signal line where both are non-None."""
        closes = _make_closes(60, base=50, noise_range=3)
        macd = compute_macd(closes)
        for i in range(len(closes)):
            if macd["macd_line"][i] is not None and macd["signal_line"][i] is not None:
                assert macd["histogram"][i] == pytest.approx(
                    macd["macd_line"][i] - macd["signal_line"][i], abs=1e-9
                )

    def test_macd_positive_trend(self):
        """In an uptrend, MACD line should eventually be positive."""
        closes = [100.0 + i * 0.5 for i in range(50)]
        macd = compute_macd(closes)
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0
        # Last few values should be positive in an uptrend
        assert valid[-1] > 0

    def test_macd_negative_trend(self):
        """In a downtrend, MACD line should eventually be negative."""
        closes = [100.0 - i * 0.5 for i in range(50)]
        macd = compute_macd(closes)
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0
        assert valid[-1] < 0

    def test_custom_params(self):
        """MACD with custom parameters should still produce valid output."""
        closes = _make_closes(50, base=50)
        macd = compute_macd(closes, fast=5, slow=10, signal=3)
        assert len(macd["macd_line"]) == 50
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0

    def test_constant_prices(self):
        """MACD should be zero when prices are constant."""
        closes = [100.0] * 50
        macd = compute_macd(closes)
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# TestComputeROC
# ---------------------------------------------------------------------------

