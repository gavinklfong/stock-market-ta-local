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


class TestComputeHmmRegime:
    def test_length(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        assert len(result["ta_hmm_regime"]) == 200
        assert len(result["ta_hmm_regime_prob_0"]) == 200
        assert len(result["ta_hmm_regime_prob_1"]) == 200
        assert len(result["ta_hmm_regime_prob_2"]) == 200

    def test_short_data_returns_none(self):
        closes = [100.0 + i for i in range(10)]
        result = compute_hmm_regime(closes, n_states=3)
        assert all(v is None for v in result["ta_hmm_regime"])

    def test_first_element_none(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        assert result["ta_hmm_regime"][0] is None
        assert result["ta_hmm_regime_prob_0"][0] is None

    def test_regime_values_are_valid(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        assert len(valid_regimes) > 0
        assert all(v in (0, 1, 2) for v in valid_regimes)

    def test_probabilities_sum_to_one(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        for i in range(1, len(closes)):  # skip first (None)
            p0 = result["ta_hmm_regime_prob_0"][i]
            p1 = result["ta_hmm_regime_prob_1"][i]
            p2 = result["ta_hmm_regime_prob_2"][i]
            if p0 is not None and p1 is not None and p2 is not None:
                total = p0 + p1 + p2
                assert total == pytest.approx(1.0, rel=1e-6)

    def test_probabilities_are_non_negative(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        for col in ["ta_hmm_regime_prob_0", "ta_hmm_regime_prob_1",
                     "ta_hmm_regime_prob_2"]:
            valid = [v for v in result[col] if v is not None]
            assert len(valid) > 0
            assert all(v >= 0.0 for v in valid)

    def test_multiple_regimes_detected(self):
        closes = _make_sample(500)
        result = compute_hmm_regime(closes, n_states=3)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        unique_regimes = set(valid_regimes)
        # Should detect at least 2 different regimes
        assert len(unique_regimes) >= 2

    def test_uptrend_has_bull_regime(self):
        closes = _make_uptrend(300)
        result = compute_hmm_regime(closes, n_states=3)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        assert 0 in valid_regimes  # Bull state should appear

    def test_volatile_regime_detected(self):
        closes = _make_volatile(300)
        result = compute_hmm_regime(closes, n_states=3)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        assert len(set(valid_regimes)) >= 2

    def test_two_state(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=2)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        assert len(valid_regimes) > 0
        assert all(v in (0, 1) for v in valid_regimes)


# ---------------------------------------------------------------------------
# TestComputeRegimeColumns
# ---------------------------------------------------------------------------


