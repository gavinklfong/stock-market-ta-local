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
    compute_volume_percentile,
    compute_volume_zscore,
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

class TestComputeVolumeColumns:
    def test_expected_keys(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        assert set(cols.keys()) == {"ta_obv", "ta_cmf", "ta_vwap", "ta_ofi", "ta_log_volume", "ta_adl", "ta_mfi14", "ta_emv14", "ta_volume_osc", "ta_volume_zscore", "ta_volume_percentile"}

    def test_all_same_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        for col in cols.values():
            assert len(col) == 50

    def test_obv_present(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        assert cols["ta_obv"][0] is not None

    def test_cmf_present(self):
        highs, lows, closes, volumes = _make_sample(30)
        cols = compute_volume_columns(highs, lows, closes, volumes, 30)
        valid = [v for v in cols["ta_cmf"] if v is not None]
        assert len(valid) > 0

    def test_vwap_present(self):
        highs, lows, closes, volumes = _make_sample(25)
        cols = compute_volume_columns(highs, lows, closes, volumes, 25)
        # First valid VWAP at index period-1 (19)
        assert cols["ta_vwap"][19] is not None

    def test_adl_present(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        # ADL should have values from bar 0
        assert cols["ta_adl"][0] is not None

    def test_mfi14_present(self):
        highs, lows, closes, volumes = _make_sample(30)
        cols = compute_volume_columns(highs, lows, closes, volumes, 30)
        valid = [v for v in cols["ta_mfi14"] if v is not None]
        assert len(valid) > 0

    def test_volume_osc_present(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        valid = [v for v in cols["ta_volume_osc"] if v is not None]
        assert len(valid) > 0

    def test_volume_zscore_present(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        valid = [v for v in cols["ta_volume_zscore"] if v is not None]
        assert len(valid) > 0

    def test_volume_percentile_present(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        valid = [v for v in cols["ta_volume_percentile"] if v is not None]
        assert len(valid) > 0

    def test_short_data(self):
        n = 5
        cols = compute_volume_columns(
            [100.0]*n, [99.0]*n, [100.0]*n, [1000]*n, n
        )
        assert len(cols["ta_obv"]) == 5
        assert len(cols["ta_cmf"]) == 5
        assert all(v is None for v in cols["ta_cmf"])
        assert len(cols["ta_vwap"]) == 5
        assert len(cols["ta_adl"]) == 5
        assert len(cols["ta_mfi14"]) == 5
        assert all(v is None for v in cols["ta_mfi14"])
        assert len(cols["ta_emv14"]) == 5
        assert all(v is None for v in cols["ta_emv14"])
        assert len(cols["ta_volume_osc"]) == 5
        assert all(v is None for v in cols["ta_volume_osc"])
        assert len(cols["ta_volume_zscore"]) == 5
        assert all(v is None for v in cols["ta_volume_zscore"])
        assert len(cols["ta_volume_percentile"]) == 5
        assert all(v is None for v in cols["ta_volume_percentile"])

    def test_all_same_length(self):
        highs, lows, closes, volumes = _make_sample(100)
        cols = compute_volume_columns(highs, lows, closes, volumes, 100)
        lengths = [len(v) for v in cols.values()]
        assert len(set(lengths)) == 1
        assert lengths[0] == 100


# ---------------------------------------------------------------------------
# TestProcessCSV
# ---------------------------------------------------------------------------

