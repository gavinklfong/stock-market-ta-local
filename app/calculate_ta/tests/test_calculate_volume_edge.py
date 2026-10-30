import math
import os

import numpy as np
import pandas as pd
import pytest

from calculate_volume import (
    compute_adl,
    compute_cmf,
    compute_emv,
    compute_mfi,
    compute_obv,
    compute_vwap,
    compute_volume_columns,
    compute_volume_oscillator,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_sample(n=50, base_price=100.0, base_volume=1_000_000):
    """Generate aligned OHLCV data for testing."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 1.0)
        closes.append(max(closes[-1] + change, 10.0))

    highs = [c + abs(np.random.normal(0, 0.5)) for c in closes]
    lows = [max(c - abs(np.random.normal(0, 0.5)), 1.0) for c in closes]
    volumes = [int(base_volume * np.random.uniform(0.5, 1.5)) for _ in range(n)]

    return highs, lows, closes, volumes


# ---------------------------------------------------------------------------
# TestComputeOBV
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_obv_single_value(self):
        result = compute_obv([100.0], [1000])
        assert result == [1000.0]

    def test_cmf_single_value(self):
        result = compute_cmf([102.0], [98.0], [100.0], [1000])
        # Needs 20 data points for period 20
        assert result == [None]

    def test_vwap_single_value(self):
        result = compute_vwap([102.0], [98.0], [100.0], [1000000], period=1)
        expected = (102.0 + 98.0 + 100.0) / 3.0
        assert result[0] == pytest.approx(expected, abs=1e-9)

    def test_cmf_empty(self):
        result = compute_cmf([], [], [], [])
        assert result == []

    def test_obv_empty(self):
        result = compute_obv([], [])
        assert result == []

    def test_vwap_empty(self):
        result = compute_vwap([], [], [], [])
        assert result == []

    def test_compute_volume_columns_very_short(self):
        n = 3
        cols = compute_volume_columns(
            [100.0]*n, [99.0]*n, [100.0]*n, [1000]*n, n
        )
        assert len(cols["ta_obv"]) == 3
        assert len(cols["ta_cmf"]) == 3
        assert len(cols["ta_vwap"]) == 3
        assert len(cols["ta_adl"]) == 3
        assert len(cols["ta_mfi14"]) == 3
        assert len(cols["ta_emv14"]) == 3
        assert len(cols["ta_volume_osc"]) == 3
        assert all(v is None for v in cols["ta_cmf"])

    def test_compute_volume_columns_all_none_cmf(self):
        n = 10
        cols = compute_volume_columns(
            [100.0]*n, [99.0]*n, [100.0]*n, [1000]*n, n
        )
        assert len(cols["ta_cmf"]) == 10
        assert all(v is None for v in cols["ta_cmf"])

    def test_adl_single_value(self):
        result = compute_adl([110.0], [90.0], [100.0], [5000])
        # CLV = ((100-90)-(110-100))/(110-90) = 0/20 = 0
        assert result[0] == pytest.approx(0.0)

    def test_adl_empty(self):
        result = compute_adl([], [], [], [])
        assert result == []

    def test_mfi_single_value(self):
        """MFI needs at least period+1 bars; single value returns None."""
        result = compute_mfi([102.0], [98.0], [100.0], [1000])
        assert result == [None]

    def test_mfi_empty(self):
        result = compute_mfi([], [], [], [])
        assert result == []
