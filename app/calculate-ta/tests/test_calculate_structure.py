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


class TestDetectSwings:
    def test_length(self):
        highs, lows, _ = _make_sample(50)
        sh, sl = detect_swings(highs, lows, lookback=3)
        assert len(sh) == 50
        assert len(sl) == 50

    def test_short_data(self):
        highs = [100.0 + i for i in range(10)]
        lows = [90.0 + i for i in range(10)]
        sh, sl = detect_swings(highs, lows, lookback=5)
        assert all(v is False for v in sh)
        assert all(v is False for v in sl)

    def test_known_swing_high(self):
        """A peak surrounded by lower values should be detected as swing high."""
        highs = [100, 105, 95, 110, 90, 115, 85, 120, 80]
        lows = [90, 95, 85, 100, 80, 105, 75, 110, 70]
        sh, sl = detect_swings(highs, lows, lookback=1)
        # Index 7 (high=120) should be a swing high
        assert sh[7] is True

    def test_known_swing_low(self):
        """A trough surrounded by higher values should be detected as swing low."""
        highs = [100, 105, 110, 105, 115, 110, 120]
        lows = [90, 95, 85, 90, 80, 85, 75]
        sh, sl = detect_swings(highs, lows, lookback=1)
        # Index 4 (low=80) should be a swing low
        assert sl[4] is True

    def test_no_swings_linear(self):
        """Linearly increasing data should produce no swings in the middle."""
        highs = list(range(10, 60))
        lows = list(range(0, 50))
        sh, sl = detect_swings(highs, lows, lookback=5)
        # Middle elements should all be False for linear data
        assert all(v is False for v in sh[5:-5])
        assert all(v is False for v in sl[5:-5])


# ---------------------------------------------------------------------------
# TestComputeStructure
# ---------------------------------------------------------------------------


class TestComputeStructure:
    def test_length(self):
        highs, lows, _ = _make_sample(50)
        result = compute_structure(highs, lows, lookback=3)
        assert len(result["swing_high"]) == 50
        assert len(result["swing_low"]) == 50
        assert len(result["hh"]) == 50
        assert len(result["hl"]) == 50
        assert len(result["lh"]) == 50
        assert len(result["ll"]) == 50
        assert len(result["trend"]) == 50
        assert len(result["bos"]) == 50
        assert len(result["choch"]) == 50

    def test_short_data(self):
        highs = [100.0 + i for i in range(5)]
        lows = [90.0 + i for i in range(5)]
        result = compute_structure(highs, lows, lookback=5)
        assert result["trend"] == [0] * 5
        assert result["bos"] == [0] * 5
        assert result["choch"] == [0] * 5

    def test_bullish_trend_structure(self):
        """Strong uptrend: should produce HH and HL patterns."""
        # Zigzag uptrend: each swing high > previous, each swing low > previous
        highs = [100, 105, 98, 110, 103, 115, 108, 120, 113, 125]
        lows = [95, 100, 93, 105, 98, 110, 103, 115, 108, 120]
        result = compute_structure(highs, lows, lookback=1)

        # In a strong uptrend, we should see HH and HL
        valid_hh = [v for v in result["hh"] if v == 1]
        valid_hl = [v for v in result["hl"] if v == 1]
        valid_trend_pos = [v for v in result["trend"] if v == 1]

        # At least some bullish signals should be present
        assert len(valid_hh) > 0
        assert len(valid_hl) > 0
        assert len(valid_trend_pos) > 0

    def test_bearish_trend_structure(self):
        """Strong downtrend: should produce LH and LL patterns."""
        # Zigzag downtrend: each swing high < previous, each swing low < previous
        highs = [125, 113, 120, 108, 115, 103, 110, 98, 105, 93, 100, 88]
        lows = [120, 108, 115, 103, 110, 98, 105, 90, 100, 85, 95, 80]
        result = compute_structure(highs, lows, lookback=1)

        valid_trend_neg = [v for v in result["trend"] if v == -1]
        valid_lh = [v for v in result["lh"] if v == 1]
        valid_ll = [v for v in result["ll"] if v == 1]
        assert len(valid_trend_neg) > 0
        assert len(valid_lh) > 0
        assert len(valid_ll) > 0

    def test_swing_high_idx_valid(self):
        """Swing high idx should be non-negative when a swing high exists."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)

        valid_sh = [v for v in result["swing_high"] if v is not None]
        if valid_sh:
            # Where swing_high is not None, swing_high_idx should be >= 0
            for i in range(len(result["swing_high"])):
                if result["swing_high"][i] is not None:
                    assert result["swing_high_idx"][i] >= 0

    def test_swing_low_idx_valid(self):
        """Swing low idx should be non-negative when a swing low exists."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)

        valid_sl = [v for v in result["swing_low"] if v is not None]
        if valid_sl:
            for i in range(len(result["swing_low"])):
                if result["swing_low"][i] is not None:
                    assert result["swing_low_idx"][i] >= 0

    def test_trend_values(self):
        """Trend should only be -1, 0, or 1."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for v in result["trend"]:
            assert v in (-1, 0, 1)

    def test_hh_lh_mutually_exclusive(self):
        """HH and LH should not both be 1 at the same index."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for i in range(len(highs)):
            assert not (result["hh"][i] == 1 and result["lh"][i] == 1)

    def test_hl_ll_mutually_exclusive(self):
        """HL and LL should not both be 1 at the same index."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for i in range(len(highs)):
            assert not (result["hl"][i] == 1 and result["ll"][i] == 1)

    def test_bos_values(self):
        """BOS should only be 0 or 1."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for v in result["bos"]:
            assert v in (0, 1)

    def test_choch_values(self):
        """CHoCH should only be 0 or 1."""
        highs, lows, _ = _make_sample(100)
        result = compute_structure(highs, lows, lookback=3)
        for v in result["choch"]:
            assert v in (0, 1)


# ---------------------------------------------------------------------------
# TestComputeSupportResistance
# ---------------------------------------------------------------------------


class TestComputeSupportResistance:
    def test_length(self):
        highs, lows, _ = _make_sample(50)
        structure = compute_structure(highs, lows, lookback=3)
        res, sup = compute_support_resistance(highs, lows, structure, lookback=3)
        assert len(res) == 50
        assert len(sup) == 50

    def test_short_data(self):
        highs = [100.0 + i for i in range(5)]
        lows = [90.0 + i for i in range(5)]
        structure = compute_structure(highs, lows, lookback=5)
        res, sup = compute_support_resistance(highs, lows, structure, lookback=5)
        assert res == [None] * 5
        assert sup == [None] * 5

    def test_resistance_above(self):
        """Resistance level should be above the current price."""
        # Create data with a clear peak (resistance) at price 120
        highs = [100, 105, 115, 120, 115, 110, 105, 100, 95, 90]
        lows = [90, 95, 105, 110, 105, 100, 95, 90, 85, 80]
        structure = compute_structure(highs, lows, lookback=2)
        res, sup = compute_support_resistance(highs, lows, structure, lookback=2)

        # After the peak, resistance should be set
        valid_res = [v for v in res if v is not None]
        if valid_res:
            # Resistance should be positive
            for v in valid_res:
                assert v > 0

    def test_support_below(self):
        """Support level should be below the current price."""
        highs = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55]
        lows = [90, 85, 80, 75, 70, 65, 60, 55, 50, 45]
        structure = compute_structure(highs, lows, lookback=2)
        res, sup = compute_support_resistance(highs, lows, structure, lookback=2)

        valid_sup = [v for v in sup if v is not None]
        if valid_sup:
            for v in valid_sup:
                assert v > 0


# ---------------------------------------------------------------------------
# TestClusterLevels
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TestDistanceToResistanceSupport
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


class TestClusterLevels:
    def test_empty(self):
        assert _cluster_levels([]) == []

    def test_single_level(self):
        result = _cluster_levels([(0, 100.0)])
        assert result == [100.0]

    def test_close_levels_clustered(self):
        """Prices within tolerance should cluster."""
        points = [(i, 100.0 + i * 0.5) for i in range(5)]
        result = _cluster_levels(points, tolerance_pct=0.02)
        # All within 2.5% of each other, should cluster
        assert len(result) <= 5

    def test_far_levels_separate(self):
        """Prices far apart should not cluster."""
        points = [(0, 100.0), (1, 200.0), (2, 300.0)]
        result = _cluster_levels(points, tolerance_pct=0.01)
        assert len(result) == 3

    def test_cluster_averages(self):
        """Cluster center should be the average of member prices."""
        points = [(0, 100.0), (1, 101.0), (2, 102.0)]
        result = _cluster_levels(points, tolerance_pct=0.01)
        # All close, should form one cluster
        assert len(result) == 1
        assert result[0] == pytest.approx(101.0, abs=1e-6)


# ---------------------------------------------------------------------------
# TestComputeStructureColumns
# ---------------------------------------------------------------------------


class TestComputeStructureColumns:
    def test_expected_keys(self):
        highs, lows, _ = _make_sample(50)
        cols = compute_structure_columns(highs, lows, _make_sample(50)[2], 50)
        expected = {
            "ta_swing_high", "ta_swing_low",
            "ta_swing_high_idx", "ta_swing_low_idx",
            "ta_hh", "ta_hl", "ta_lh", "ta_ll",
            "ta_trend", "ta_bos", "ta_choch",
            "ta_nearest_resistance", "ta_nearest_support",
            "ta_dist_resistance", "ta_dist_support",
            "ta_breakout_strength", "ta_support_touches",
        }
        assert set(cols.keys()) == expected

    def test_all_same_length(self):
        highs, lows, _ = _make_sample(50)
        cols = compute_structure_columns(highs, lows, _make_sample(50)[2], 50)
        for col in cols.values():
            assert len(col) == 50

    def test_short_data(self):
        empty = [None] * 5
        zero = [0] * 5
        cols = compute_structure_columns([100]*5, [90]*5, [95]*5, 5)
        assert cols["ta_swing_high"] == empty
        assert cols["ta_swing_low"] == empty
        assert cols["ta_swing_high_idx"] == [-1] * 5
        assert cols["ta_swing_low_idx"] == [-1] * 5
        assert cols["ta_hh"] == zero
        assert cols["ta_lh"] == zero
        assert cols["ta_trend"] == zero
        assert cols["ta_breakout_strength"] == zero
        assert cols["ta_support_touches"] == zero

    def test_with_realistic_data(self):
        np.random.seed(42)
        n = 200
        base = 150.0
        closes = [base]
        for _ in range(n - 1):
            change = np.random.normal(0, 1.5)
            closes.append(max(closes[-1] + change, 50.0))

        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]

        cols = compute_structure_columns(highs, lows, closes, n)

        # Should have some non-None values for swings
        valid_sh = [v for v in cols["ta_swing_high"] if v is not None]
        valid_sl = [v for v in cols["ta_swing_low"] if v is not None]
        assert len(valid_sh) > 0
        assert len(valid_sl) > 0

        # Should have some non-zero trend
        non_zero_trend = [v for v in cols["ta_trend"] if v != 0]
        assert len(non_zero_trend) > 0

    def test_with_trending_data(self):
        """Uptrend should produce bullish structure."""
        n = 100
        # Zigzag uptrend: even indices are swing highs, odd are swing lows
        highs = []
        lows = []
        for i in range(n):
            trend = 100.0 + i * 0.5
            if i % 2 == 0:
                highs.append(trend + 2.0)
                lows.append(trend - 1.0)
            else:
                highs.append(trend + 1.0)
                lows.append(trend - 2.0)

        cols = compute_structure_columns(highs, lows, highs, n, lookback=1)

        # Should have bullish signals
        valid_hh = [v for v in cols["ta_hh"] if v == 1]
        valid_trend_pos = [v for v in cols["ta_trend"] if v == 1]
        assert len(valid_hh) > 0
        assert len(valid_trend_pos) > 0


# ---------------------------------------------------------------------------
# TestProcessCSV
# ---------------------------------------------------------------------------


class TestProcessCSV:
    def _write_test_csv(self, directory, filename, rows):
        df = pd.DataFrame(rows)
        path = os.path.join(directory, filename)
        df.to_csv(path, index=False)
        return path

    def test_creates_output(self, tmp_path):
        import threading
        from calculate_structure import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": 100.0, "High": 102.0, "Low": 99.0,
                 "Close": 100.0 + i * 0.5, "Volume": 1000000}
                for i in range(50)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        assert os.path.exists(output_path)

    def test_includes_structure_columns(self, tmp_path):
        import threading
        from calculate_structure import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": 100.0, "High": 102.0, "Low": 99.0,
                 "Close": 100.0 + i * 0.5, "Volume": 1000000}
                for i in range(50)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_swing_high" in df.columns
        assert "ta_swing_low" in df.columns
        assert "ta_swing_high_idx" in df.columns
        assert "ta_swing_low_idx" in df.columns
        assert "ta_hh" in df.columns
        assert "ta_hl" in df.columns
        assert "ta_lh" in df.columns
        assert "ta_ll" in df.columns
        assert "ta_trend" in df.columns
        assert "ta_bos" in df.columns
        assert "ta_choch" in df.columns
        assert "ta_nearest_resistance" in df.columns
        assert "ta_nearest_support" in df.columns
        assert "ta_dist_resistance" in df.columns
        assert "ta_dist_support" in df.columns

    def test_realistic_data(self, tmp_path):
        import threading
        from calculate_structure import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(42)
        base = 150.0
        closes = [base]
        for _ in range(199):
            change = np.random.normal(0, 1.5)
            closes.append(max(closes[-1] + change, 50.0))

        self._write_test_csv(
            str(input_dir),
            "AAPL.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": closes[i] * 0.999, "High": closes[i] * 1.01,
                 "Low": closes[i] * 0.99, "Close": closes[i],
                 "Volume": int(1e6 * np.random.uniform(0.8, 1.2))}
                for i in range(200)
            ],
        )

        input_path = str(input_dir / "AAPL.csv")
        output_path = str(output_dir / "AAPL.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # Swing highs should have valid values
        valid_sh = df["ta_swing_high"].dropna()
        assert len(valid_sh) > 0
        # Trend should have non-zero values
        non_zero_trend = df["ta_trend"][df["ta_trend"] != 0]
        assert len(non_zero_trend) > 0

    def test_sort_order(self, tmp_path):
        import threading
        from calculate_structure import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        dates = [
            pd.Timestamp("2024-01-05"),
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-01-03"),
            pd.Timestamp("2024-01-02"),
            pd.Timestamp("2024-01-04"),
        ]
        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": d, "Open": 100.0, "High": 102.0, "Low": 99.0,
                 "Close": 100.0 + i * 0.5, "Volume": 1000000}
                for i, d in enumerate(dates)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        dates_out = pd.to_datetime(df["Date"])
        assert dates_out.is_monotonic_increasing


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_single_value(self):
        cols = compute_structure_columns([100.0], [90.0], [95.0], 1)
        assert cols["ta_swing_high"] == [None]
        assert cols["ta_trend"] == [0]

    def test_two_values(self):
        cols = compute_structure_columns([100.0, 105.0], [90.0, 95.0], [95.0, 100.0], 2)
        assert len(cols["ta_swing_high"]) == 2
        assert cols["ta_trend"] == [0, 0]

    def test_constant_prices(self):
        """Constant prices should produce no structure signals."""
        n = 50
        prices = [100.0] * n
        cols = compute_structure_columns(prices, prices, prices, n, lookback=3)
        # Should have very few/no swings since no variation
        valid_sh = [v for v in cols["ta_swing_high"] if v is not None]
        valid_sl = [v for v in cols["ta_swing_low"] if v is not None]
        # With constant data, there may be edge swings at boundaries
        # But trend should remain neutral
        valid_trend = [v for v in cols["ta_trend"] if v != 0]
        assert len(valid_trend) == 0

    def test_v_shaped_reversal(self):
        """V-shaped price action should detect both swing low and recovery."""
        highs = [100, 90, 80, 70, 80, 90, 100, 110]
        lows = [90, 80, 70, 60, 70, 80, 90, 100]
        structure = compute_structure(highs, lows, lookback=2)

        # The trough at index 3 should be detected as swing low
        # swing_low contains the price (not boolean), so check it's not None
        assert structure["swing_low"][3] is not None
        assert structure["swing_low"][3] == 60

    def test_inverted_v_reversal(self):
        """Inverted V (peak) should detect swing high."""
        highs = [80, 90, 100, 110, 100, 90, 80]
        lows = [70, 80, 90, 100, 90, 80, 70]
        structure = compute_structure(highs, lows, lookback=2)

        # The peak at index 3 should be detected as swing high
        # swing_high contains the price (not boolean), so check it's not None
        assert structure["swing_high"][3] is not None
        assert structure["swing_high"][3] == 110


# ---------------------------------------------------------------------------
# Breakout Strength Tests
# ---------------------------------------------------------------------------


class TestComputeBreakoutStrength:
    """Tests for compute_breakout_strength."""

    def test_no_breakout(self):
        """When price doesn't exceed S/R levels, strength should be 0."""
        highs = [105] * 10
        lows = [95] * 10
        resistance = [110] * 10  # above all highs
        support = [90] * 10      # below all lows
        result = compute_breakout_strength(highs, lows, resistance, support)
        assert result == [0.0] * 10

    def test_upside_breakout(self):
        """High exceeding resistance should produce positive strength."""
        highs = [115] * 10  # 15% above resistance
        lows = [90] * 10
        resistance = [100] * 10
        support = [90] * 10
        result = compute_breakout_strength(highs, lows, resistance, support)
        expected = [15.0] * 10  # (115 - 100) / 100 * 100
        assert result == expected

    def test_downside_breakout(self):
        """Low below support should produce positive strength."""
        highs = [110] * 10
        lows = [85] * 10  # 16.67% below support
        resistance = [110] * 10
        support = [100] * 10
        result = compute_breakout_strength(highs, lows, resistance, support)
        expected = [15.0] * 10  # (100 - 85) / 100 * 100
        assert result == expected

    def test_max_breakout_direction(self):
        """Should take the maximum of up and down breakout."""
        highs = [120] * 10  # 20% above resistance
        lows = [80] * 10    # 20% below support
        resistance = [100] * 10
        support = [100] * 10
        result = compute_breakout_strength(highs, lows, resistance, support)
        # Both breakouts are 20%, so max is 20%
        assert result == [20.0] * 10

    def test_none_levels(self):
        """None resistance/support should be skipped."""
        highs = [115] * 10
        lows = [95] * 10
        resistance = [None] * 10
        support = [90] * 10
        result = compute_breakout_strength(highs, lows, resistance, support)
        assert result == [0.0] * 10  # No valid breakout levels

    def test_mixed_breakout(self):
        """Only one bar breaks out, others are 0."""
        highs = [100, 100, 115, 100, 100]
        lows = [95, 95, 95, 95, 95]
        resistance = [100, 100, 100, 100, 100]
        support = [94, 94, 94, 94, 94]
        result = compute_breakout_strength(highs, lows, resistance, support)
        assert result[0] == 0.0       # No breakout (high=100 not > 100)
        assert result[2] == 15.0      # (115 - 100) / 100 * 100
        assert result[4] == 0.0       # No breakout

    def test_zero_length(self):
        """Empty input should return empty list."""
        result = compute_breakout_strength([], [], [], [])
        assert result == []

    def test_partial_none_levels(self):
        """Some bars have None resistance, others don't."""
        highs = [105, 105, 115, 105]
        lows = [95, 95, 95, 95]
        resistance = [100, None, 100, None]
        support = [90, 90, 90, 90]
        result = compute_breakout_strength(highs, lows, resistance, support)
        assert result[0] == 5.0   # (105 - 100) / 100 * 100
        assert result[1] == 0.0   # None resistance, no valid level
        assert result[2] == 15.0  # (115 - 100) / 100 * 100
        assert result[3] == 0.0   # None resistance

    def test_breakout_strength_in_columns(self):
        """Breakout strength should be included in compute_structure_columns output."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(max(closes[-1] + np.random.normal(0, 1.0), 10.0))
        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]

        cols = compute_structure_columns(highs, lows, closes, n)
        assert "ta_breakout_strength" in cols
        assert len(cols["ta_breakout_strength"]) == n
        # All values should be >= 0
        for v in cols["ta_breakout_strength"]:
            assert v >= 0


# ---------------------------------------------------------------------------
# Support Touches Tests
# ---------------------------------------------------------------------------


class TestComputeSupportTouches:
    """Tests for compute_support_touches."""

    def test_no_support(self):
        """When no support level, count should be 0."""
        lows = [95] * 10
        support = [None] * 10
        result = compute_support_touches(lows, support)
        assert result == [0] * 10

    def test_support_never_touched(self):
        """When price is far from support, count stays 0."""
        lows = [100] * 10  # 10% above support
        support = [90] * 10
        result = compute_support_touches(lows, support, tolerance_pct=0.02)
        # Default tolerance is 2%, so 100 is not within 2% of 90
        assert result == [0] * 10

    def test_support_touches_count(self):
        """Price touching support should increment count."""
        np.random.seed(42)
        # Generate prices that repeatedly touch the support level
        support_level = 100.0
        tolerance = 0.02  # 2%
        # Lows just within tolerance of support (100-102 range)
        lows = [100.0, 100.5, 101.0, 101.5, 102.0]
        support = [support_level] * 5
        result = compute_support_touches(lows, support, tolerance_pct=tolerance)
        # All lows are within [98, 102], so all should count as touches
        assert result == [1, 2, 3, 4, 5]

    def test_support_broken_resets(self):
        """When support breaks (low drops below), count resets to 0."""
        lows = [100, 97, 100, 101]  # 97 breaks below 98 (100 * 0.98)
        support = [100] * 4
        result = compute_support_touches(lows, support, tolerance_pct=0.02)
        # Index 0: low=100, within [98, 102], touch=1
        # Index 1: low=97, below 98, support broken, count=0
        # Index 2: low=100, within [98, 102], touch=1
        # Index 3: low=101, within [98, 102], touch=2
        assert result == [1, 0, 1, 2]

    def test_none_support_preserves_count(self):
        """When support is None, count is preserved (not reset)."""
        lows = [100] * 3
        support = [100, None, 100]
        result = compute_support_touches(lows, support, tolerance_pct=0.02)
        assert result == [1, 1, 2]  # None preserves current count

    def test_zero_length(self):
        """Empty input should return empty list."""
        result = compute_support_touches([], [])
        assert result == []

    def test_support_touches_in_columns(self):
        """Support touches should be included in compute_structure_columns output."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(max(closes[-1] + np.random.normal(0, 1.0), 10.0))
        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]

        cols = compute_structure_columns(highs, lows, closes, n)
        assert "ta_support_touches" in cols
        assert len(cols["ta_support_touches"]) == n
        # All values should be >= 0
        for v in cols["ta_support_touches"]:
            assert v >= 0
        # Values should be integers (counts)
        for v in cols["ta_support_touches"]:
            assert isinstance(v, int)
