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


class TestProcessCSV:
    def _write_test_csv(self, directory, filename, rows):
        df = pd.DataFrame(rows)
        path = os.path.join(directory, filename)
        df.to_csv(path, index=False)
        return path

    def test_creates_output(self, tmp_path):
        from calculate_regime import process_csv

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
                for i in range(100)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        assert os.path.exists(output_path)

    def test_includes_regime_columns(self, tmp_path):
        from calculate_regime import process_csv

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
                for i in range(100)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_garch_vol" in df.columns
        assert "ta_garch_sq" in df.columns
        assert "ta_hmm_regime" in df.columns
        assert "ta_hmm_regime_prob_0" in df.columns
        assert "ta_hmm_regime_prob_1" in df.columns
        assert "ta_hmm_regime_prob_2" in df.columns

    def test_realistic_data(self, tmp_path):
        from calculate_regime import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(42)
        base = 150.0
        closes = [base]
        for _ in range(299):
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
                for i in range(300)
            ],
        )

        input_path = str(input_dir / "AAPL.csv")
        output_path = str(output_dir / "AAPL.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # GARCH vol should have valid values
        valid_garch = df["ta_garch_vol"].dropna()
        assert len(valid_garch) > 0
        # HMM regime should have valid values
        valid_regime = df["ta_hmm_regime"].dropna()
        assert len(valid_regime) > 0
        assert df["ta_hmm_regime"].dropna().isin([0, 1, 2]).all()

    def test_sort_order(self, tmp_path):
        from calculate_regime import process_csv

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
        """process_csv writes only its own Date + regime columns, not merged with existing."""
        from calculate_regime import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        # Also write the input file
        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": 100.0, "High": 102.0, "Low": 99.0,
                 "Close": 100.0 + i * 0.5, "Volume": 1000000}
                for i in range(100)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # Should contain only Date + regime columns
        assert "Date" in df.columns
        assert "ta_garch_vol" in df.columns
        assert "ta_garch_sq" in df.columns
        assert "ta_hmm_regime" in df.columns
        # Should NOT contain columns from other modules (merge is done at orchestration level)
        assert "ta_rsi14" not in df.columns
        assert "ta_macd_line" not in df.columns
