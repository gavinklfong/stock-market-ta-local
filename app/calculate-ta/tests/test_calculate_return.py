"""Unit tests for calculate_return.py — verifies forward-looking return computations."""

import os
import math

import numpy as np
import pandas as pd
import pytest

from calculate_return import (
    compute_alpha_beta,
    compute_future_returns,
    compute_past_performance,
    compute_return_columns,
    process_csv,
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


def _make_dates(n):
    """Generate n consecutive dates starting from 2024-01-01."""
    return [pd.Timestamp("2024-01-01") + pd.Timedelta(days=i) for i in range(n)]


# ---------------------------------------------------------------------------
# TestComputeFutureReturns
# ---------------------------------------------------------------------------


class TestComputeFutureReturns:
    def test_length(self):
        _, _, closes = _make_sample(50)
        result = compute_future_returns(closes)
        for h in result:
            assert len(result[h]) == 50

    def test_short_data(self):
        closes = [100.0 + i for i in range(5)]
        result = compute_future_returns(closes, horizons=(5,))
        assert result[5] == [None] * 5

    def test_first_element_has_return(self):
        closes = [100.0, 102.0, 104.0, 106.0, 108.0, 110.0]
        result = compute_future_returns(closes, horizons=(5,))
        assert result[5][0] is not None

    def test_last_rows_none(self):
        closes = [100.0 + i for i in range(20)]
        result = compute_future_returns(closes, horizons=(5, 10))
        # Last 5 rows should be None for 5d horizon
        for i in range(15, 20):
            assert result[5][i] is None
        # Last 10 rows should be None for 10d horizon
        for i in range(10, 20):
            assert result[10][i] is None
        # Earlier rows should have values
        assert result[5][0] is not None
        assert result[10][0] is not None

    def test_positive_return_uptrend(self):
        """Uptrend should produce positive returns."""
        closes = [100.0 + i for i in range(30)]
        result = compute_future_returns(closes, horizons=(5, 10))
        for h in result:
            for i in range(len(closes) - h):
                assert result[h][i] > 0

    def test_negative_return_downtrend(self):
        """Downtrend should produce negative returns."""
        closes = [100.0 - i for i in range(30)]
        result = compute_future_returns(closes, horizons=(5, 10))
        for h in result:
            for i in range(len(closes) - h):
                assert result[h][i] < 0

    def test_constant_prices_zero_return(self):
        """Constant prices should produce zero returns."""
        closes = [100.0] * 20
        result = compute_future_returns(closes, horizons=(5,))
        for i in range(len(closes) - 5):
            assert result[5][i] == 0.0

    def test_multiple_horizons(self):
        """Multiple horizons should all be present."""
        closes = [100.0 + i * 0.5 for i in range(50)]
        horizons = (5, 10, 20)
        result = compute_future_returns(closes, horizons=horizons)
        for h in horizons:
            assert h in result
            assert len(result[h]) == 50

    def test_return_formula(self):
        """Return should match (future_close - close) / close."""
        closes = [100.0, 105.0, 110.0, 115.0, 120.0, 125.0]
        result = compute_future_returns(closes, horizons=(1,))
        # 1-day return at index 0: (105 - 100) / 100 = 0.05
        assert result[1][0] == pytest.approx(0.05, abs=1e-10)
        # 1-day return at index 1: (110 - 105) / 105 ≈ 0.0476
        assert result[1][1] == pytest.approx(5.0 / 105, abs=1e-10)

    def test_horizon_5_returns_larger_than_1(self):
        """In a strong trend, 5d return should exceed 1d return."""
        closes = [100.0 + i for i in range(30)]
        result = compute_future_returns(closes, horizons=(1, 5))
        # At index 0, 5d return should be 5x the 1d return
        assert result[5][0] == pytest.approx(result[1][0] * 5, abs=1e-10)


class TestComputePastPerformance:
    def test_length(self):
        _, _, closes = _make_sample(50)
        result = compute_past_performance(closes)
        for h in result:
            assert len(result[h]) == 50

    def test_short_data(self):
        closes = [100.0 + i for i in range(5)]
        result = compute_past_performance(closes, horizons=(21,))
        assert result[21] == [None] * 5

    def test_first_rows_none(self):
        """First H rows should be None for horizon H."""
        closes = [100.0 + i for i in range(30)]
        result = compute_past_performance(closes, horizons=(21,))
        for i in range(21):
            assert result[21][i] is None
        # First non-None at index 21
        assert result[21][21] is not None

    def test_positive_return_uptrend(self):
        """Uptrend should produce positive past performance."""
        closes = [100.0 + i for i in range(300)]
        result = compute_past_performance(closes, horizons=(21, 63, 126, 252))
        for h in result:
            for i in range(h, len(closes)):
                assert result[h][i] > 0

    def test_negative_return_downtrend(self):
        """Downtrend should produce negative past performance."""
        closes = [1000.0 - i for i in range(300)]
        result = compute_past_performance(closes, horizons=(21,))
        for i in range(21, len(closes)):
            assert result[21][i] < 0

    def test_constant_prices_zero_return(self):
        """Constant prices should produce zero returns."""
        closes = [100.0] * 20
        result = compute_past_performance(closes, horizons=(21,))
        # All should be None since we don't have 21 rows
        assert result[21] == [None] * 20

    def test_constant_prices_nonzero_return(self):
        """Constant prices with enough data should produce zero returns."""
        closes = [100.0] * 25
        result = compute_past_performance(closes, horizons=(21,))
        assert result[21][21] == 0.0
        assert result[21][24] == 0.0

    def test_multiple_horizons(self):
        """Multiple horizons should all be present."""
        closes = [100.0 + i * 0.5 for i in range(300)]
        horizons = (21, 63, 126, 252)
        result = compute_past_performance(closes, horizons=horizons)
        for h in horizons:
            assert h in result
            assert len(result[h]) == 300

    def test_return_formula(self):
        """Past performance should match (current - past) / past * 100."""
        closes = [100.0, 105.0, 110.0, 115.0, 120.0, 125.0]
        result = compute_past_performance(closes, horizons=(5,))
        # At index 5: (125 - 100) / 100 * 100 = 25%
        assert result[5][5] == pytest.approx(25.0, abs=1e-10)

    def test_return_formula_21_days(self):
        """Test 21-day horizon formula."""
        closes = [100.0 + i for i in range(50)]
        result = compute_past_performance(closes, horizons=(21,))
        # At index 21: close=121, past=100 → (121-100)/100*100 = 21%
        assert result[21][21] == pytest.approx(21.0, abs=1e-10)

    def test_percentage_output(self):
        """Past performance should be expressed as percentage."""
        closes = [100.0, 110.0, 90.0] + [100.0] * 50
        result = compute_past_performance(closes, horizons=(1,))
        # At index 1: (110 - 100) / 100 * 100 = 10%
        assert result[1][1] == pytest.approx(10.0, abs=1e-10)
        # At index 2: (90 - 110) / 110 * 100 ≈ -18.18%
        assert result[1][2] == pytest.approx(-20.0 / 11 * 10, abs=1e-10)

    def test_default_horizons(self):
        """Default horizons should be 21, 63, 126, 252."""
        closes = [100.0 + i for i in range(300)]
        result = compute_past_performance(closes)
        assert set(result.keys()) == {21, 63, 126, 252}


class TestComputeAlphaBeta:
    def test_length(self):
        closes = [100.0 + i * 0.5 for i in range(100)]
        bench = [50.0 + i * 0.3 for i in range(100)]
        result = compute_alpha_beta(closes, bench, window=20)
        assert len(result["alpha"]) == 100
        assert len(result["beta"]) == 100

    def test_first_rows_none(self):
        """First window rows should be None (returns start at index 1, need 20 returns)."""
        closes = [100.0 + i for i in range(50)]
        bench = [50.0 + i for i in range(50)]
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20):
            assert result["alpha"][i] is None
            assert result["beta"][i] is None

    def test_first_valid_at_window(self):
        """First non-None value should be at index=window."""
        closes = [100.0 + i for i in range(50)]
        bench = [50.0 + i for i in range(50)]
        result = compute_alpha_beta(closes, bench, window=20)
        assert result["alpha"][20] is not None
        assert result["beta"][20] is not None

    def test_perfect_correlation_beta_1(self):
        """If stock and benchmark have identical % changes, beta should be ~1.0."""
        np.random.seed(42)
        closes = [100.0]
        bench = [50.0]
        for _ in range(99):
            noise = np.random.normal(0, 0.005)
            closes.append(closes[-1] * (1.01 + noise))
            bench.append(bench[-1] * (1.01 + noise))
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["beta"][i] == pytest.approx(1.0, abs=0.01)

    def test_perfect_correlation_alpha_zero(self):
        """Identical % changes → alpha should be ~0."""
        np.random.seed(42)
        closes = [100.0]
        bench = [50.0]
        for _ in range(99):
            noise = np.random.normal(0, 0.005)
            closes.append(closes[-1] * (1.01 + noise))
            bench.append(bench[-1] * (1.01 + noise))
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["alpha"][i] == pytest.approx(0.0, abs=0.05)

    def test_outperformance_positive_alpha(self):
        """Stock with higher % return than benchmark → positive alpha."""
        np.random.seed(42)
        closes = [100.0]
        bench = [100.0]
        for _ in range(99):
            noise = np.random.normal(0, 0.005)
            closes.append(closes[-1] * (1.02 + noise))  # 2% daily
            bench.append(bench[-1] * (1.01 + noise))     # 1% daily
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["alpha"][i] > 0

    def test_underperformance_negative_alpha(self):
        """Stock with lower % return than benchmark → negative alpha."""
        np.random.seed(42)
        closes = [100.0]
        bench = [100.0]
        for _ in range(99):
            noise = np.random.normal(0, 0.005)
            closes.append(closes[-1] * (1.01 + noise))  # 1% daily
            bench.append(bench[-1] * (1.02 + noise))    # 2% daily
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["alpha"][i] < 0

    def test_high_beta(self):
        """Stock with 2x volatility of benchmark → beta ~2."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        bench = [100.0]
        for _ in range(n - 1):
            noise = np.random.normal(0, 0.015)  # shared noise
            s_ret = 0.01 + noise * 2             # 2x noise → 2x vol
            b_ret = 0.005 + noise                # baseline
            closes.append(closes[-1] * (1 + s_ret))
            bench.append(bench[-1] * (1 + b_ret))
        result = compute_alpha_beta(closes, bench, window=20)
        assert result["beta"][20] > 1.0

    def test_negative_beta(self):
        """Inverted return pattern → negative beta."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        bench = [100.0]
        for i in range(n - 1):
            base_ret = 0.01
            noise = np.random.normal(0, 0.015)
            s_ret = base_ret + noise          # positive correlation with noise
            b_ret = base_ret - noise          # opposite sign on noise
            closes.append(closes[-1] * (1 + s_ret))
            bench.append(bench[-1] * (1 + b_ret))
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["beta"][i] < 0

    def test_constant_benchmark(self):
        """Constant benchmark (zero variance) should give beta=0."""
        closes = [100.0 + i for i in range(100)]
        bench = [50.0] * 100
        result = compute_alpha_beta(closes, bench, window=20)
        for i in range(20, 100):
            assert result["beta"][i] == 0.0

    def test_short_data_all_none(self):
        """Data shorter than window should produce all None."""
        closes = [100.0 + i for i in range(10)]
        bench = [50.0 + i for i in range(10)]
        result = compute_alpha_beta(closes, bench, window=20)
        assert all(v is None for v in result["alpha"])
        assert all(v is None for v in result["beta"])

    def test_multiple_windows(self):
        """Different window sizes should produce different results."""
        closes = [100.0 + i * 0.5 for i in range(100)]
        bench = [50.0 + i * 0.3 for i in range(100)]
        r20 = compute_alpha_beta(closes, bench, window=20)
        r50 = compute_alpha_beta(closes, bench, window=50)
        # 50-window should have more None values at the start
        none_count_20 = sum(1 for v in r20["alpha"] if v is None)
        none_count_50 = sum(1 for v in r50["alpha"] if v is None)
        assert none_count_50 > none_count_20

    def test_default_window(self):
        """Default window should be 20."""
        closes = [100.0 + i for i in range(50)]
        bench = [50.0 + i for i in range(50)]
        result = compute_alpha_beta(closes, bench)
        # First 20 should be None (default window=20, returns start at index 1)
        assert result["alpha"][20] is not None


# ---------------------------------------------------------------------------
# TestComputeReturnColumns
# ---------------------------------------------------------------------------


class TestComputeReturnColumns:
    def test_expected_keys(self):
        highs, lows, closes = _make_sample(50)
        cols = compute_return_columns(highs, lows, closes, [1000] * 50, 50, _make_dates(50))
        expected = {
            "ta_return_5d",
            "ta_return_10d",
            "ta_return_20d",
            "ta_performance_1m",
            "ta_performance_3m",
            "ta_performance_6m",
            "ta_performance_1y",
        }
        assert set(cols.keys()) == expected

    def test_all_same_length(self):
        highs, lows, closes = _make_sample(50)
        cols = compute_return_columns(highs, lows, closes, [1000] * 50, 50, _make_dates(50))
        for col in cols.values():
            assert len(col) == 50

    def test_short_data(self):
        n = 5
        cols = compute_return_columns(
            [100.0] * n, [90.0] * n, [95.0] * n, [1000] * n, n, _make_dates(n)
        )
        for col in cols.values():
            assert all(v is None for v in col)

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
        volumes = [int(1e6 * np.random.uniform(0.8, 1.2)) for _ in closes]

        cols = compute_return_columns(highs, lows, closes, volumes, n, _make_dates(n))

        # 5d return should have some non-None values
        valid_5d = [v for v in cols["ta_return_5d"] if v is not None]
        assert len(valid_5d) > 0

        # 20d return should have fewer non-None values
        valid_20d = [v for v in cols["ta_return_20d"] if v is not None]
        assert len(valid_20d) > 0
        assert len(valid_5d) > len(valid_20d)

    def test_positive_returns_in_uptrend(self):
        """Strong uptrend should produce positive returns across horizons."""
        n = 50
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        volumes = [1000] * n

        cols = compute_return_columns(highs, lows, closes, volumes, n, _make_dates(n))
        for h in (5, 10, 20):
            col_name = f"ta_return_{h}d"
            valid = [v for v in cols[col_name] if v is not None]
            assert all(v > 0 for v in valid)


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
        from calculate_return import process_csv

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

    def test_includes_return_columns(self, tmp_path):
        import threading
        from calculate_return import process_csv

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
        assert "ta_return_5d" in df.columns
        assert "ta_return_10d" in df.columns
        assert "ta_return_20d" in df.columns
        assert "ta_performance_1m" in df.columns
        assert "ta_performance_3m" in df.columns
        assert "ta_performance_6m" in df.columns
        assert "ta_performance_1y" in df.columns
        # Rolling alpha and beta vs ^FTSE
        assert "ta_alpha20" in df.columns
        assert "ta_beta20" in df.columns

    def test_returns_are_valid(self, tmp_path):
        import threading
        from calculate_return import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(42)
        base = 150.0
        closes = [base]
        for _ in range(49):
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
                for i in range(50)
            ],
        )

        input_path = str(input_dir / "AAPL.csv")
        output_path = str(output_dir / "AAPL.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # 5d return should have some valid values
        valid_5d = df["ta_return_5d"].dropna()
        assert len(valid_5d) > 0
        # All valid returns should be finite floats
        for v in valid_5d:
            assert math.isfinite(v)

    def test_sort_order(self, tmp_path):
        import threading
        from calculate_return import process_csv

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

    def test_creates_own_columns_only(self, tmp_path):
        """process_csv writes only Date + its own ta_return columns.

        Column merging across modules is handled by run_calculation.py,
        not inside individual modules.
        """
        import threading
        from calculate_return import process_csv

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

        # Simulate a prior module writing other columns
        prior_df = pd.DataFrame({
            "Date": [pd.Timestamp("2024-01-01") + pd.Timedelta(days=i) for i in range(50)],
            "ta_atr14": [5.0 + i * 0.1 for i in range(50)],
        })
        prior_df = prior_df.sort_values("Date").reset_index(drop=True)
        prior_df.to_csv(output_path, index=False)

        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_return_5d" in df.columns
        assert "ta_return_10d" in df.columns
        assert "ta_return_20d" in df.columns
        assert "ta_performance_1m" in df.columns
        assert "ta_performance_3m" in df.columns
        assert "ta_performance_6m" in df.columns
        assert "ta_performance_1y" in df.columns
        # Prior columns are NOT preserved — each module writes only its own
        assert "ta_atr14" not in df.columns
        # Only Date and ta_return_* and ta_performance_* and ta_alpha20/beta20 columns
        allowed = {
            "Date",
            "ta_return_5d",
            "ta_return_10d",
            "ta_return_20d",
            "ta_performance_1m",
            "ta_performance_3m",
            "ta_performance_6m",
            "ta_performance_1y",
            "ta_alpha20",
            "ta_beta20",
        }
        assert set(df.columns) == allowed

    def test_last_rows_have_none_for_longer_horizons(self, tmp_path):
        import threading
        from calculate_return import process_csv

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
                for i in range(25)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # CSV converts None → NaN, so check with pd.isna()
        # Check explicitly: indices 0-4 should have values for 20d
        for i in range(5):
            assert pd.notna(df["ta_return_20d"].iloc[i])
        # Last 20 indices (5-24) should be NaN
        for i in range(5, 25):
            assert pd.isna(df["ta_return_20d"].iloc[i])


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_single_value(self):
        cols = compute_return_columns([100.0], [90.0], [95.0], [1000], 1, _make_dates(1))
        assert cols["ta_return_5d"] == [None]
        assert cols["ta_return_10d"] == [None]
        assert cols["ta_return_20d"] == [None]

    def test_two_values(self):
        cols = compute_return_columns([100.0, 105.0], [90.0, 95.0], [95.0, 100.0], [1000, 1100], 2, _make_dates(2))
        assert len(cols["ta_return_5d"]) == 2
        assert all(v is None for v in cols["ta_return_5d"])

    def test_constant_prices(self):
        """Constant prices should produce zero returns where horizon fits."""
        n = 25
        cols = compute_return_columns(
            [100.0] * n, [90.0] * n, [95.0] * n, [1000] * n, n, _make_dates(n)
        )
        # 5d return should be 0 where available
        for i in range(n - 5):
            assert cols["ta_return_5d"][i] == 0.0
        # Last 5 should be None
        for i in range(n - 5, n):
            assert cols["ta_return_5d"][i] is None

    def test_large_price_range(self):
        """Very large price swings should produce valid returns."""
        n = 30
        closes = [10.0]
        for _ in range(n - 1):
            closes.append(closes[-1] * (1 + np.random.uniform(-0.1, 0.2)))

        highs = [c * 1.02 for c in closes]
        lows = [c * 0.98 for c in closes]
        volumes = [1000] * n

        cols = compute_return_columns(highs, lows, closes, volumes, n, _make_dates(n))

        valid_5d = [v for v in cols["ta_return_5d"] if v is not None]
        assert len(valid_5d) > 0
        for v in valid_5d:
            assert math.isfinite(v)

    def test_very_small_returns(self):
        """Tiny price changes should produce small returns."""
        n = 30
        closes = [100.0 + i * 0.001 for i in range(n)]
        highs = [c + 0.001 for c in closes]
        lows = [c - 0.001 for c in closes]
        volumes = [1000] * n

        cols = compute_return_columns(highs, lows, closes, volumes, n, _make_dates(n))

        valid_5d = [v for v in cols["ta_return_5d"] if v is not None]
        assert len(valid_5d) > 0
        # 5d return for tiny increments should be small positive
        assert all(v > 0 for v in valid_5d)
