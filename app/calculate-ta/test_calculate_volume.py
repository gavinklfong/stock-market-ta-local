import math
import os

import numpy as np
import pandas as pd
import pytest

from calculate_volume import (
    compute_cmf,
    compute_obv,
    compute_vwap,
    compute_volume_columns,
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

class TestComputeOBV:
    def test_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_obv(closes, volumes)
        assert len(result) == 50

    def test_short_data(self):
        result = compute_obv([10.0], [1000])
        assert len(result) == 1

    def test_up_day_adds_volume(self):
        closes = [100.0, 105.0, 103.0]
        volumes = [1000, 2000, 1500]
        result = compute_obv(closes, volumes)
        # Day 0: obv = volume[0]
        assert result[0] == 1000.0
        # Day 1: close > close[0], add volume[1]
        assert result[1] == 1000.0 + 2000.0
        # Day 2: close < close[1], subtract volume[2]
        assert result[2] == 3000.0 - 1500.0

    def test_down_day_subtracts_volume(self):
        closes = [100.0, 95.0, 90.0]
        volumes = [1000, 2000, 3000]
        result = compute_obv(closes, volumes)
        # All down days
        assert result[0] == 1000.0
        assert result[1] == 1000.0 - 2000.0 == -1000.0
        assert result[2] == -1000.0 - 3000.0 == -4000.0

    def test_same_price_no_change(self):
        closes = [100.0, 100.0, 100.0]
        volumes = [1000, 2000, 3000]
        result = compute_obv(closes, volumes)
        # Same price → obv unchanged
        assert result[0] == 1000.0
        assert result[1] == 1000.0
        assert result[2] == 1000.0

    def test_alternating(self):
        closes = [100.0, 110.0, 100.0, 110.0]
        volumes = [1000, 2000, 3000, 4000]
        result = compute_obv(closes, volumes)
        # Up, down, up
        assert result[0] == 1000.0
        assert result[1] == 3000.0
        assert result[2] == 0.0
        assert result[3] == 4000.0

    def test_monotonic_uptrend(self):
        closes = [100.0 + i for i in range(20)]
        volumes = [1000] * 20
        result = compute_obv(closes, volumes)
        # Every day is up → strictly increasing
        for i in range(1, len(result)):
            assert result[i] > result[i - 1]

    def test_monotonic_downtrend(self):
        closes = [100.0 - i for i in range(20)]
        volumes = [1000] * 20
        result = compute_obv(closes, volumes)
        # Every day is down → strictly decreasing
        for i in range(1, len(result)):
            assert result[i] < result[i - 1]


# ---------------------------------------------------------------------------
# TestComputeCMF
# ---------------------------------------------------------------------------

class TestComputeCMF:
    def test_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_cmf(highs, lows, closes, volumes)
        assert len(result) == 50

    def test_short_data(self):
        highs, lows, closes, volumes = _make_sample(10)
        result = compute_cmf(highs, lows, closes, volumes)
        assert all(v is None for v in result)

    def test_first_valid_at_period(self):
        highs, lows, closes, volumes = _make_sample(25)
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        for i in range(19):
            assert result[i] is None
        assert result[19] is not None

    def test_cmf_range(self):
        """CMF should be in range [-1, 1]."""
        highs, lows, closes, volumes = _make_sample(100)
        result = compute_cmf(highs, lows, closes, volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert -1.0 <= v <= 1.0

    def test_bullish_cmf_positive(self):
        """When closes are near highs, CMF should be positive."""
        n = 30
        closes = [100.0 + i * 0.5 for i in range(n)]
        highs = [c + 0.1 for c in closes]  # small upper wick → close near high
        lows = [c - 1.0 for c in closes]  # large lower wick
        volumes = [1000000] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] > 0

    def test_bearish_cmf_negative(self):
        """When closes are near lows, CMF should be negative."""
        n = 30
        closes = [100.0 + i * 0.5 for i in range(n)]
        highs = [c + 1.0 for c in closes]  # large upper wick
        lows = [c - 0.1 for c in closes]  # small lower wick → close near low
        volumes = [1000000] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] < 0

    def test_midpoint_cmf_near_zero(self):
        """When closes are at midpoint, CMF should be near zero."""
        n = 30
        closes = [100.0] * n
        highs = [105.0] * n
        lows = [95.0] * n
        volumes = [1000000] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert abs(valid[-1]) < 0.01

    def test_period_zero_high_low(self):
        """Handle high == low gracefully."""
        n = 30
        closes = [100.0 + i for i in range(n)]
        highs = [100.0] * n
        lows = [100.0] * n
        volumes = [1000000] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        # When high == low, MFMF = 0 → CMF = 0
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_custom_period(self):
        """CMF with custom period should work."""
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_cmf(highs, lows, closes, volumes, period=10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert -1.0 <= v <= 1.0

    def test_zero_volume(self):
        """Zero volume should result in CMF of 0, not NaN."""
        n = 30
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [0] * n
        result = compute_cmf(highs, lows, closes, volumes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == 0.0


# ---------------------------------------------------------------------------
# TestComputeVWAP
# ---------------------------------------------------------------------------

class TestComputeVWAP:
    def test_length(self):
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_vwap(highs, lows, closes, volumes)
        assert len(result) == 50

    def test_first_valid_at_zero(self):
        highs, lows, closes, volumes = _make_sample(10)
        result = compute_vwap(highs, lows, closes, volumes)
        assert result[0] is not None

    def test_vwap_near_typical_price(self):
        """With constant volume and price, VWAP ≈ typical price."""
        n = 10
        closes = [100.0] * n
        highs = [102.0] * n
        lows = [98.0] * n
        volumes = [1000000] * n
        result = compute_vwap(highs, lows, closes, volumes)
        # Typical price = (102 + 98 + 100) / 3 = 100
        expected = (102.0 + 98.0 + 100.0) / 3.0
        assert result[0] == pytest.approx(expected, abs=1e-9)

    def test_vwap_single_row(self):
        highs, lows, closes, volumes = [102.0], [98.0], [100.0], [1000000]
        result = compute_vwap(highs, lows, closes, volumes)
        expected = (102.0 + 98.0 + 100.0) / 3.0
        assert result[0] == pytest.approx(expected, abs=1e-9)

    def test_vwap_uptrend(self):
        """VWAP should trend upward when prices trend up."""
        n = 30
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [1000000] * n
        result = compute_vwap(highs, lows, closes, volumes)
        assert result[-1] > result[0]

    def test_vwap_increasing_volume_weighting(self):
        """Later data with larger volume should pull VWAP more."""
        closes = [100.0, 110.0]
        highs = [102.0, 112.0]
        lows = [98.0, 108.0]
        volumes = [1.0, 100.0]
        result = compute_vwap(highs, lows, closes, volumes)
        # First row: TP = (102+98+100)/3 = 100
        # Second row: weighted by large volume at ~110
        assert result[-1] > result[0]
        assert result[-1] > 105  # pulled toward 110 by heavy volume

    def test_vwap_positive(self):
        """VWAP should always be positive with positive prices."""
        highs, lows, closes, volumes = _make_sample(50)
        result = compute_vwap(highs, lows, closes, volumes)
        for v in result:
            assert v is not None
            assert v > 0

    def test_vwap_zero_volume(self):
        """VWAP with zero volume should stay at initial value."""
        n = 5
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [0.0] * n
        result = compute_vwap(highs, lows, closes, volumes)
        # With zero volume, cumulative stays 0 → division would give 0/0
        # But we guard with cumulative_vol > 0 check, so all remain None
        for v in result:
            assert v is None


# ---------------------------------------------------------------------------
# TestComputeVolumeColumns
# ---------------------------------------------------------------------------

class TestComputeVolumeColumns:
    def test_expected_keys(self):
        highs, lows, closes, volumes = _make_sample(50)
        cols = compute_volume_columns(highs, lows, closes, volumes, 50)
        assert set(cols.keys()) == {"ta_obv", "ta_cmf", "ta_vwap"}

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
        highs, lows, closes, volumes = _make_sample(10)
        cols = compute_volume_columns(highs, lows, closes, volumes, 10)
        assert cols["ta_vwap"][0] is not None

    def test_short_data(self):
        n = 5
        cols = compute_volume_columns(
            [100.0]*n, [99.0]*n, [100.0]*n, [1000]*n, n
        )
        assert len(cols["ta_obv"]) == 5
        assert len(cols["ta_cmf"]) == 5
        assert all(v is None for v in cols["ta_cmf"])
        assert len(cols["ta_vwap"]) == 5

    def test_all_same_length(self):
        highs, lows, closes, volumes = _make_sample(100)
        cols = compute_volume_columns(highs, lows, closes, volumes, 100)
        lengths = [len(v) for v in cols.values()]
        assert len(set(lengths)) == 1
        assert lengths[0] == 100


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
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(0)
        n = 50
        base = 100.0
        closes = [base]
        for _ in range(n - 1):
            closes.append(max(closes[-1] + np.random.normal(0, 0.5), 50.0))

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": c * 0.999, "High": c * 1.01,
                 "Low": c * 0.99, "Close": c,
                 "Volume": int(1e6 * np.random.uniform(0.8, 1.2))}
                for i, c in enumerate(closes)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        from calculate_volume import process_csv
        process_csv(input_path, output_path, 1, 1)

        assert os.path.exists(output_path)

    def test_includes_volume_columns(self, tmp_path):
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(0)
        n = 50
        base = 100.0
        closes = [base]
        for _ in range(n - 1):
            closes.append(max(closes[-1] + np.random.normal(0, 0.5), 50.0))

        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": c * 0.999, "High": c * 1.01,
                 "Low": c * 0.99, "Close": c,
                 "Volume": int(1e6 * np.random.uniform(0.8, 1.2))}
                for i, c in enumerate(closes)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        from calculate_volume import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_obv" in df.columns
        assert "ta_cmf" in df.columns
        assert "ta_vwap" in df.columns

    def test_realistic_data(self, tmp_path):
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
        from calculate_volume import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # OBV should have cumulative values
        assert df["ta_obv"].iloc[0] == df["Volume"].iloc[0]
        # VWAP should have valid values
        valid_vwap = df["ta_vwap"].dropna()
        assert len(valid_vwap) > 0
        # CMF should have valid values (200 > 20)
        valid_cmf = df["ta_cmf"].dropna()
        assert len(valid_cmf) > 0

    def test_sort_order(self, tmp_path):
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
        from calculate_volume import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        dates_out = pd.to_datetime(df["Date"])
        assert dates_out.is_monotonic_increasing


# ---------------------------------------------------------------------------
# TestEdgeCases
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
        result = compute_vwap([102.0], [98.0], [100.0], [1000000])
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
        assert all(v is None for v in cols["ta_cmf"])

    def test_compute_volume_columns_all_none_cmf(self):
        n = 10
        cols = compute_volume_columns(
            [100.0]*n, [99.0]*n, [100.0]*n, [1000]*n, n
        )
        assert len(cols["ta_cmf"]) == 10
        assert all(v is None for v in cols["ta_cmf"])
