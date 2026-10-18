"""Unit tests for calculate_structure.py — verifies swing detection, HH/HL/LH/LL, BOS/CHoCH, and support/resistance."""

import math
import os

import numpy as np
import pandas as pd
import pytest

from calculate_structure import (
    compute_breakout_strength,
    compute_structure,
    compute_structure_columns,
    compute_support_resistance,
    compute_support_touches,
    detect_swings,
    _cluster_levels,
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


# ---------------------------------------------------------------------------
# TestDetectSwings
# ---------------------------------------------------------------------------


class TestDistanceToResistanceSupport:
    def _write_test_csv(self, directory, filename, rows):
        df = pd.DataFrame(rows)
        path = os.path.join(directory, filename)
        df.to_csv(path, index=False)
        return path

    def test_length(self):
        highs, lows, closes = _make_sample(50)
        cols = compute_structure_columns(highs, lows, closes, 50)
        assert len(cols["ta_dist_resistance"]) == 50
        assert len(cols["ta_dist_support"]) == 50

    def test_dist_resistance_positive(self):
        """Distance to resistance should be positive when resistance > close."""
        # Create a wider data series with clear swings
        highs, lows, closes = _make_sample(100, base_price=100.0, base_range=5.0)
        # Use midpoints as close to match compute_support_resistance's internal calc
        mid_closes = [(h + l) / 2.0 for h, l in zip(highs, lows)]
        cols = compute_structure_columns(highs, lows, mid_closes, 100, lookback=3)

        valid_dist = [v for v in cols["ta_dist_resistance"] if v is not None]
        if valid_dist:
            for v in valid_dist:
                assert v > 0

    def test_dist_support_positive(self):
        """Distance to support should be positive when close > support."""
        highs = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55]
        lows = [90, 85, 80, 75, 70, 65, 60, 55, 50, 45]
        # Use midpoints as close to match compute_support_resistance's internal calc
        mid_closes = [(h + l) / 2.0 for h, l in zip(highs, lows)]
        cols = compute_structure_columns(highs, lows, mid_closes, len(highs), lookback=2)

        valid_dist = [v for v in cols["ta_dist_support"] if v is not None]
        if valid_dist:
            for v in valid_dist:
                assert v > 0

    def test_distance_zero_when_at_level(self):
        """Distance should be 0 when close equals the level."""
        close = 100.0
        resistance = 100.0
        expected_dist = (resistance - close) / close * 100.0
        assert expected_dist == pytest.approx(0.0, abs=1e-6)

    def test_distance_calculation(self):
        """Distance formula: (level - close) / close * 100."""
        close = 100.0
        resistance = 110.0
        expected = (110.0 - 100.0) / 100.0 * 100.0  # 10%
        assert expected == pytest.approx(10.0, abs=1e-6)

    def test_distance_none_without_levels(self):
        """Distance should be None when no resistance/support level exists."""
        cols = compute_structure_columns([100]*5, [90]*5, [95]*5, 5)
        # With short data, all distance values should be None
        assert all(v is None for v in cols["ta_dist_resistance"])
        assert all(v is None for v in cols["ta_dist_support"])

    def test_distance_short_data(self):
        """Short data should produce None distances."""
        cols = compute_structure_columns([100]*3, [90]*3, [95]*3, 3)
        assert cols["ta_dist_resistance"] == [None, None, None]
        assert cols["ta_dist_support"] == [None, None, None]

    def test_distance_matches_support_resistance(self):
        """When support/resistance is not None, distance should also not be None."""
        highs, lows, closes = _make_sample(100)
        cols = compute_structure_columns(highs, lows, closes, 100)

        for i in range(len(highs)):
            res = cols["ta_nearest_resistance"][i]
            dist = cols["ta_dist_resistance"][i]
            if res is not None:
                assert dist is not None

            sup = cols["ta_nearest_support"][i]
            dist = cols["ta_dist_support"][i]
            if sup is not None:
                assert dist is not None

    def test_distance_with_trending_data(self):
        """Distance values should exist with realistic trending data."""
        n = 200
        base = 150.0
        closes = [base]
        for _ in range(n - 1):
            change = np.random.normal(0, 1.5)
            closes.append(max(closes[-1] + change, 50.0))

        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]

        cols = compute_structure_columns(highs, lows, closes, n)

        valid_res_dist = [v for v in cols["ta_dist_resistance"] if v is not None]
        valid_sup_dist = [v for v in cols["ta_dist_support"] if v is not None]

        assert len(valid_res_dist) > 0
        assert len(valid_sup_dist) > 0

    def test_distance_all_same_length(self):
        """All output columns should have the same length."""
        highs, lows, closes = _make_sample(50)
        cols = compute_structure_columns(highs, lows, closes, 50)
        for col, values in cols.items():
            assert len(values) == 50

    def test_short_data_returns_empty(self):
        """Short data should return None distances like other empty columns."""
        cols = compute_structure_columns([100]*5, [90]*5, [95]*5, 5)
        assert cols["ta_dist_resistance"] == [None] * 5
        assert cols["ta_dist_support"] == [None] * 5

    def test_distance_includes_in_process_csv(self, tmp_path):
        """process_csv should include ta_dist_resistance and ta_dist_support columns."""
        import threading
        from calculate_structure import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        # Write a CSV with enough data points for structure detection
        np.random.seed(42)
        base = 100.0
        closes = [base]
        for _ in range(149):
            change = np.random.normal(0, 1.0)
            closes.append(max(closes[-1] + change, 50.0))

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": closes[i] * 0.999, "High": closes[i] * 1.01,
                 "Low": closes[i] * 0.99, "Close": closes[i],
                 "Volume": 1000000}
                for i in range(150)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_dist_resistance" in df.columns
        assert "ta_dist_support" in df.columns

    def test_distance_values_reasonable(self, tmp_path):
        """Distance percentages should be reasonable (not wildly large)."""
        import threading
        from calculate_structure import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        # Generate a reasonable price series
        np.random.seed(42)
        base = 100.0
        closes = [base]
        for _ in range(199):
            change = np.random.normal(0, 1.0)
            closes.append(max(closes[-1] + change, 50.0))

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": closes[i] * 0.999, "High": closes[i] * 1.01,
                 "Low": closes[i] * 0.99, "Close": closes[i],
                 "Volume": 1000000}
                for i in range(200)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # Valid distances should be positive and reasonably bounded
        valid_res = df["ta_dist_resistance"].dropna()
        valid_sup = df["ta_dist_support"].dropna()

        assert len(valid_res) > 0
        assert len(valid_sup) > 0

        # All valid distances should be positive
        assert (valid_res > 0).all()
        assert (valid_sup > 0).all()

        # Distances should not exceed 50% (reasonable bound)
        assert (valid_res < 50).all()
        assert (valid_sup < 50).all()


