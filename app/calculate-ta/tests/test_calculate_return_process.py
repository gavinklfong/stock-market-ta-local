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


