"""Unit tests for calculate_regime.py — verifies GARCH(1,1) volatility and 3-state HMM regime detection."""

import math
import os
import warnings

import numpy as np
import pandas as pd
import pytest

warnings.filterwarnings("ignore")

from calculate_regime import (
    compute_garch_volatility,
    compute_hmm_regime,
    compute_regime_columns,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sample(n=200, base_price=100.0, base_range=2.0):
    """Generate aligned close prices for testing."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, base_range / 2)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


def _make_uptrend(n=200, base_price=100.0):
    """Generate a clear uptrend with some noise."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = 0.3 + np.random.normal(0, 1.0)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


def _make_downtrend(n=200, base_price=200.0):
    """Generate a clear downtrend with some noise."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = -0.3 + np.random.normal(0, 1.0)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


def _make_volatile(n=200, base_price=100.0):
    """Generate a high-volatility regime with no clear trend."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 5.0)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


# ---------------------------------------------------------------------------
# TestComputeGarchVolatility
# ---------------------------------------------------------------------------


class TestComputeRegimeColumns:
    def test_expected_keys(self):
        closes = _make_sample(200)
        cols = compute_regime_columns(closes, 200)
        expected = {
            "ta_garch_vol", "ta_garch_sq",
            "ta_hmm_regime",
            "ta_hmm_regime_prob_0", "ta_hmm_regime_prob_1", "ta_hmm_regime_prob_2",
        }
        assert set(cols.keys()) == expected

    def test_all_same_length(self):
        closes = _make_sample(200)
        cols = compute_regime_columns(closes, 200)
        for col in cols.values():
            assert len(col) == 200

    def test_short_data(self):
        closes = [100.0 + i for i in range(10)]
        cols = compute_regime_columns(closes, 10)
        assert all(v is None for v in cols["ta_garch_vol"])
        assert all(v is None for v in cols["ta_garch_sq"])
        assert all(v is None for v in cols["ta_hmm_regime"])

    def test_with_uptrend_data(self):
        closes = _make_uptrend(300)
        cols = compute_regime_columns(closes, 300)
        valid_vol = [v for v in cols["ta_garch_vol"] if v is not None]
        valid_regimes = [v for v in cols["ta_hmm_regime"] if v is not None]
        assert len(valid_vol) > 0
        assert len(valid_regimes) > 0

    def test_trim_to_n(self):
        """When n < len(closes), columns should be trimmed."""
        closes = _make_sample(200)
        cols = compute_regime_columns(closes, 100)
        for col in cols.values():
            assert len(col) == 100

    def test_padded_to_n(self):
        """When n > len(closes), columns should be padded with None."""
        closes = _make_sample(50)
        cols = compute_regime_columns(closes, 100)
        for col in cols.values():
            assert len(col) == 100


# ---------------------------------------------------------------------------
# TestProcessCSV
# ---------------------------------------------------------------------------


