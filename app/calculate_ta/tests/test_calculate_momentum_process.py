import math
import os
import tempfile
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from calculate_momentum import (
    compute_cci,
    compute_ema,
    compute_macd,
    compute_momentum_columns,
    compute_rsi_zscore,
    compute_roc,
    compute_rsi,
    compute_stochastic,
    compute_tsi,
    compute_williams_r,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_closes(length, base=100.0, slope=0.0, noise_range=0.0):
    """Generate a list of closing prices."""
    np.random.seed(0)
    closes = []
    for i in range(length):
        val = base + slope * i + np.random.uniform(-noise_range, noise_range)
        closes.append(max(val, 1.0))  # keep positive
    return closes


def _make_ohlcv(n=100, base=100.0):
    """Generate synthetic OHLCV data.

    Returns (highs, lows, closes) lists of equal length.
    """
    np.random.seed(42)
    closes = [base]
    for _ in range(n - 1):
        change = np.random.normal(0, 0.01) * closes[-1]
        closes.append(max(closes[-1] + change, 1.0))

    highs = [c * (1 + abs(np.random.normal(0, 0.005))) for c in closes]
    lows = [c * (1 - abs(np.random.normal(0, 0.005))) for c in closes]

    return highs, lows, closes


# ---------------------------------------------------------------------------
# TestComputeEMA
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
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        assert os.path.exists(output_path)

    def test_includes_momentum_columns(self, tmp_path):
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
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_rsi14" in df.columns
        assert "ta_macd_line" in df.columns
        assert "ta_macd_signal" in df.columns
        assert "ta_macd_histogram" in df.columns
        assert "ta_roc20" in df.columns
        assert "ta_stoch_k" in df.columns
        assert "ta_stoch_d" in df.columns
        assert "ta_rsi_zscore" in df.columns
        assert "ta_rsi_percentile" in df.columns

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
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # RSI should have valid values
        valid_rsi = df["ta_rsi14"].dropna()
        assert len(valid_rsi) > 0
        # ROC should have valid values
        valid_roc = df["ta_roc20"].dropna()
        assert len(valid_roc) > 0

    def test_sort_order(self, tmp_path):
        """Output should be sorted by Date."""
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
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        dates_out = pd.to_datetime(df["Date"])
        assert dates_out.is_monotonic_increasing


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

