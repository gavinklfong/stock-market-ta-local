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


class TestComputeGarchVolatility:
    def test_length(self):
        closes = _make_sample(200)
        result = compute_garch_volatility(closes)
        assert len(result["ta_garch_vol"]) == 200
        assert len(result["ta_garch_sq"]) == 200

    def test_short_data_returns_none(self):
        closes = [100.0 + i for i in range(10)]
        result = compute_garch_volatility(closes)
        assert all(v is None for v in result["ta_garch_vol"])
        assert all(v is None for v in result["ta_garch_sq"])

    def test_first_element_none(self):
        closes = _make_sample(200)
        result = compute_garch_volatility(closes)
        assert result["ta_garch_vol"][0] is None
        assert result["ta_garch_sq"][0] is None

    def test_positive_volatility(self):
        closes = _make_sample(200)
        result = compute_garch_volatility(closes)
        valid_vol = [v for v in result["ta_garch_vol"] if v is not None]
        assert len(valid_vol) > 0
        assert all(v > 0 for v in valid_vol)

    def test_variance_equals_vol_squared(self):
        closes = _make_sample(200)
        result = compute_garch_volatility(closes)
        for i in range(len(closes)):
            vol = result["ta_garch_vol"][i]
            sq = result["ta_garch_sq"][i]
            if vol is not None:
                assert sq is not None
                assert sq == pytest.approx(vol ** 2, rel=1e-3)

    def test_uptrend_has_volatility(self):
        closes = _make_uptrend(300)
        result = compute_garch_volatility(closes)
        valid_vol = [v for v in result["ta_garch_vol"] if v is not None]
        assert len(valid_vol) > 0

    def test_constant_prices(self):
        closes = [100.0] * 50
        # Constant prices → all-zero log returns → GARCH optimizer warnings
        # (divide-by-zero, incompatibility constraints). Wrap to suppress
        # expected warnings for this pathological input.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = compute_garch_volatility(closes)
        # With constant prices, log returns are all zero; GARCH should still
        # produce some values (though small). At minimum it should not crash.
        assert len(result["ta_garch_vol"]) == 50

    def test_garch11_default(self):
        """Default p=1, q=1 should produce valid results."""
        closes = _make_sample(200)
        result = compute_garch_volatility(closes, p=1, q=1)
        valid_vol = [v for v in result["ta_garch_vol"] if v is not None]
        assert len(valid_vol) > 0

    def test_returns_match_log_returns_scale(self):
        """GARCH vol should be in a reasonable scale relative to returns."""
        closes = _make_sample(300)
        result = compute_garch_volatility(closes)
        valid_vol = [v for v in result["ta_garch_vol"] if v is not None]
        # With rescale=True in arch_model, conditional volatility is on the
        # original log-return scale; values should still be bounded.
        if valid_vol:
            assert max(valid_vol) < 3.0  # sanity check


# ---------------------------------------------------------------------------
# TestComputeHmmRegime
# ---------------------------------------------------------------------------


