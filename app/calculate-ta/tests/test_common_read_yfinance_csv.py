"""Unit tests for common.py — read_yfinance_csv optimization.

Tests cover:
  - Standard single-header CSV (fallback path)
  - 3-row yfinance header (Date + Ticker + Price)
  - 2-row yfinance header (Date + Price, no Ticker row)
  - Multi-column CSVs with varying column counts
  - NaN / empty / missing data handling
  - Non-existent files
  - Type correctness and numeric coercion
  - Performance regression check
"""

import csv
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from common import read_yfinance_csv


# ---------------------------------------------------------------------------
# Helpers — CSV writers
# ---------------------------------------------------------------------------


def _write_csv(rows, filename="test.csv"):
    """Write rows as CSV and return the path.

    Parameters
    ----------
    rows : list[list] or list[str]
        CSV rows. If each row is a list, it's written as-is.
        If each row is a string, it's written as a single column.

    Returns
    -------
    str
        Path to the temporary CSV file.
    """
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    # Pad all rows to the same column count (first row's length)
    max_cols = max(len(row) for row in rows) if rows else 0
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            padded = list(row) + [""] * (max_cols - len(row))
            writer.writerow(padded)
    return path


# ---------------------------------------------------------------------------
# Standard single-header CSV (fallback path)
# ---------------------------------------------------------------------------


class TestSingleHeaderCSV:
    """Test the fallback path for standard single-header CSVs."""

    def test_standard_header(self):
        """Standard single-header CSV should be read correctly."""
        path = _write_csv([
            ["Date", "Open", "High", "Low", "Close", "Volume"],
            ["2024-01-01", 100, 102, 98, 101, 1000],
            ["2024-01-02", 101, 103, 99, 102, 1200],
        ])
        df = read_yfinance_csv(path)
        assert df.columns.tolist() == ["Date", "Open", "High", "Low", "Close", "Volume"]
        assert len(df) == 2
        assert pd.api.types.is_numeric_dtype(df["Close"])

    def test_standard_header_extra_columns(self):
        """Single-header CSV with extra columns should pass through."""
        path = _write_csv([
            ["Date", "Open", "High", "Low", "Close", "Volume", "Extra"],
            ["2024-01-01", 100, 102, 98, 101, 1000, "foo"],
        ])
        df = read_yfinance_csv(path)
        assert "Extra" in df.columns
        # Non-numeric values in numeric columns become NaN (pd.to_numeric coercion)
        assert pd.isna(df["Extra"].iloc[0])

    def test_standard_header_no_data(self):
        """Single-header CSV with no data rows should return empty DataFrame."""
        path = _write_csv([
            ["Date", "Open", "High", "Low", "Close", "Volume"],
        ])
        df = read_yfinance_csv(path)
        assert len(df) == 0
        assert df.columns.tolist() == ["Date", "Open", "High", "Low", "Close", "Volume"]


# ---------------------------------------------------------------------------
# 3-row yfinance header (main path)
# ---------------------------------------------------------------------------


class TestYFinance3RowHeader:
    """Test the 3-row yfinance header format: Price-row, Ticker-row, Date-row."""

    def _make_3row_csv(self, cols=("Open", "High", "Low", "Close", "Volume"),
                       extra_data=None):
        """Build a 3-row header CSV with the given column names."""
        ticker = "NG.L"
        ncols = len(cols)
        header_rows = [
            ["Price"] + list(cols),                      # Row 0: Price labels
            ["Ticker"] + [ticker] * ncols,               # Row 1: ticker values
            ["Date"] + [""] * ncols,                     # Row 2: Date marker
        ]
        if extra_data is not None:
            data_rows = extra_data
        else:
            data_rows = [
                ["2024-01-01", 100, 102, 98, 101, 1000],
                ["2024-01-02", 101, 103, 99, 102, 1200],
                ["2024-01-03", 102, 104, 100, 103, 1100],
            ]
        return _write_csv(header_rows + data_rows)

    def test_basic_3row_header(self):
        """Basic 3-row header should resolve column names correctly."""
        path = self._make_3row_csv()
        df = read_yfinance_csv(path)
        expected = ["Date", "Open", "High", "Low", "Close", "Volume"]
        assert df.columns.tolist() == expected
        assert len(df) == 3

    def test_3row_numeric_conversion(self):
        """Numeric columns should be numeric, Date should remain string."""
        path = self._make_3row_csv()
        df = read_yfinance_csv(path)
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} should be numeric, got {df[col].dtype}"
        # Date column stays as string dtype (object or StringDtype depending on pandas version)
        assert pd.api.types.is_string_dtype(df["Date"]) or df["Date"].dtype == object

    def test_3row_values(self):
        """Data values should be correct after reading."""
        path = self._make_3row_csv()
        df = read_yfinance_csv(path)
        assert df["Close"].tolist() == [101.0, 102.0, 103.0]
        assert df["Open"].tolist() == [100.0, 101.0, 102.0]

    def test_3row_with_adj_close(self):
        """3-row header with Adj Close column."""
        path = self._make_3row_csv(("Adj Close", "Open", "High", "Low", "Close", "Volume"))
        df = read_yfinance_csv(path)
        assert "Adj Close" in df.columns
        assert pd.api.types.is_numeric_dtype(df["Adj Close"])

    def test_3row_with_weekday_extra(self):
        """3-row header with extra trailing columns (weekday)."""
        data_rows = [
            ["2024-01-01", 100, 102, 98, 101, 1000, 0.0],
            ["2024-01-02", 101, 103, 99, 102, 1200, 1.0],
            ["2024-01-03", 102, 104, 100, 103, 1100, 2.0],
        ]
        path = self._make_3row_csv(
            ("Open", "High", "Low", "Close", "Volume", "weekday"),
            extra_data=data_rows,
        )
        df = read_yfinance_csv(path)
        assert "weekday" in df.columns
        assert df["weekday"].tolist() == [0.0, 1.0, 2.0]

    def test_3row_special_ticker(self):
        """3-row header with special characters in ticker (^FTSE)."""
        path = _write_csv([
            ["Price", "Close", "Volume"],
            ["Ticker", "^FTSE", "^FTSE"],
            ["Date", "", ""],
            ["2024-01-01", 7500.0, 1000000],
            ["2024-01-02", 7550.0, 1100000],
        ])
        df = read_yfinance_csv(path)
        assert df.columns.tolist() == ["Date", "Close", "Volume"]
        assert len(df) == 2


# ---------------------------------------------------------------------------
# 2-row yfinance header (no Ticker row)
# ---------------------------------------------------------------------------


class TestYFinance2RowHeader:
    """Test the 2-row yfinance header format: Price-row, Date-row."""

    def _make_2row_csv(self, cols=("Open", "High", "Low", "Close", "Volume")):
        """Build a 2-row header CSV without a Ticker row."""
        ncols = len(cols)
        header_rows = [
            ["Price"] + list(cols),              # Row 0: Price labels
            ["Date"] + [""] * ncols,             # Row 1: Date marker
        ]
        return _write_csv(header_rows + [
            ["2024-01-01", 100, 102, 98, 101, 1000],
            ["2024-01-02", 101, 103, 99, 102, 1200],
        ])

    def test_basic_2row_header(self):
        """Basic 2-row header should resolve column names correctly."""
        path = self._make_2row_csv()
        df = read_yfinance_csv(path)
        expected = ["Date", "Open", "High", "Low", "Close", "Volume"]
        assert df.columns.tolist() == expected

    def test_2row_numeric_conversion(self):
        """Numeric columns should be float after 2-row header."""
        path = self._make_2row_csv()
        df = read_yfinance_csv(path)
        for col in ["Open", "Close"]:
            assert pd.api.types.is_numeric_dtype(df[col])

    def test_2row_values(self):
        """Data values should be correct after 2-row header."""
        path = self._make_2row_csv()
        df = read_yfinance_csv(path)
        assert df["Close"].tolist() == [101.0, 102.0]


# ---------------------------------------------------------------------------
# NaN / empty / missing data handling
# ---------------------------------------------------------------------------


class TestNaNHandling:
    """Test handling of NaN, empty, and missing data."""

    def test_nan_values_become_float_nan(self):
        """NaN values in data should be preserved as float NaN."""
        path = _write_csv([
            ["Date", "Open", "High", "Low", "Close", "Volume"],
            ["2024-01-01", 100, 102, 98, 101, 1000],
            ["2024-01-02", "NaN", 103, 99, 102, 1200],
            ["2024-01-03", 102, 104, 100, "", 1100],
        ])
        df = read_yfinance_csv(path)
        assert pd.isna(df["Open"].iloc[1])
        assert pd.isna(df["Close"].iloc[2])

    def test_non_numeric_becomes_nan(self):
        """Non-numeric values in numeric columns should become NaN."""
        path = _write_csv([
            ["Date", "Open", "High", "Low", "Close", "Volume"],
            ["2024-01-01", 100, 102, 98, 101, 1000],
            ["2024-01-02", "abc", 103, 99, 102, 1200],
        ])
        df = read_yfinance_csv(path)
        assert pd.isna(df["Open"].iloc[1])
        assert df["Close"].tolist() == [101.0, 102.0]

    def test_empty_file(self):
        """Empty file should raise EmptyDataError."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        # File is empty
        with pytest.raises(Exception):  # pd.errors.EmptyDataError
            read_yfinance_csv(path)

    def test_header_only(self):
        """File with only header rows should return empty DataFrame."""
        path = _write_csv([
            ["Price", "Close", "Volume"],
            ["Ticker", "AAPL", "AAPL"],
            ["Date", "", ""],
        ])
        df = read_yfinance_csv(path)
        assert len(df) == 0
        assert df.columns.tolist() == ["Date", "Close", "Volume"]


# ---------------------------------------------------------------------------
# Column count edge cases
# ---------------------------------------------------------------------------


class TestColumnCountEdgeCases:
    """Test edge cases related to column counts and alignment."""

    def test_single_data_column(self):
        """CSV with just Date and one data column."""
        path = _write_csv([
            ["Date", "Close"],
            ["2024-01-01", 100],
            ["2024-01-02", 101],
        ])
        df = read_yfinance_csv(path)
        assert df.columns.tolist() == ["Date", "Close"]
        assert len(df) == 2

    def test_many_columns(self):
        """CSV with many columns should handle correctly."""
        cols = ["Open", "High", "Low", "Close", "Volume", "Adj Close",
                "Return", "VWAP", "ROC", "ATR", "RSI", "MACD"]
        path = _write_csv([
            ["Price"] + cols,
            ["Ticker"] + ["X"] * len(cols) + [""],
            ["Date"] + [""] * len(cols) + [""],
            ["2024-01-01"] + list(range(len(cols))) + [""],
            ["2024-01-02"] + list(range(1, len(cols) + 1)) + [""],
        ])
        df = read_yfinance_csv(path)
        assert "Date" in df.columns
        assert "Close" in df.columns
        assert "MACD" in df.columns
        assert len(df) == 2

    def test_extra_trailing_empty_columns(self):
        """Extra trailing empty columns from yfinance header should be handled."""
        path = _write_csv([
            ["Price", "Close", "Volume"],
            ["Ticker", "NG.L", "NG.L", ""],
            ["Date", "", "", ""],
            ["2024-01-01", 100, 1000, ""],
            ["2024-01-02", 101, 1100, ""],
        ])
        df = read_yfinance_csv(path)
        assert df.columns.tolist() == ["Date", "Close", "Volume"]
        assert len(df) == 2


# ---------------------------------------------------------------------------
# Real file verification
# ---------------------------------------------------------------------------


class TestRealFiles:
    """Test against actual yfinance CSV files in the data directory."""

    @pytest.fixture
    def data_dir(self):
        """Path to the market-data directory."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        return os.path.join(base, "data", "market-data")

    def test_ng_l(self, data_dir):
        """NG.L should read with correct columns and data."""
        path = os.path.join(data_dir, "NG.L.csv")
        if not os.path.exists(path):
            pytest.skip("NG.L.csv not found")
        df = read_yfinance_csv(path)
        assert "Date" in df.columns
        assert "Close" in df.columns
        assert "Volume" in df.columns
        assert len(df) > 0
        assert df["Close"].dtype == np.float64

    def test_ftse(self, data_dir):
        """^FTSE should read with correct columns."""
        path = os.path.join(data_dir, "^FTSE.csv")
        if not os.path.exists(path):
            pytest.skip("^FTSE.csv not found")
        df = read_yfinance_csv(path)
        assert "Date" in df.columns
        assert "Close" in df.columns
        assert len(df) > 0

    def test_all_csv_files_readable(self, data_dir):
        """All CSV files in market-data should be readable."""
        if not os.path.isdir(data_dir):
            pytest.skip("market-data directory not found")
        csv_files = sorted(f for f in os.listdir(data_dir) if f.endswith(".csv"))
        for filename in csv_files:
            path = os.path.join(data_dir, filename)
            df = read_yfinance_csv(path)
            assert len(df) > 0, f"{filename} returned empty DataFrame"
            assert "Date" in df.columns, f"{filename} missing Date column"
            assert "Close" in df.columns, f"{filename} missing Close column"


# ---------------------------------------------------------------------------
# Performance regression test
# ---------------------------------------------------------------------------


class TestPerformance:
    """Verify the optimized version is not slower than before.

    The original implementation used:
      - Python loop for header detection
      - Per-column merge with .iloc lookups
      - Per-column pd.to_numeric calls

    The optimized version uses:
      - Vectorized numpy search for header
      - Vectorized merge with numpy arrays
      - Batch df.apply() for numeric conversion
    """

    def test_single_file_timing(self):
        """Single file read should complete in reasonable time."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        path = os.path.join(base, "data", "market-data", "NG.L.csv")
        if not os.path.exists(path):
            pytest.skip("NG.L.csv not found")
        import time
        start = time.perf_counter()
        for _ in range(5):
            read_yfinance_csv(path)
        elapsed = time.perf_counter() - start
        # Should be well under 1 second for 5 reads of a 10k-row file
        assert elapsed < 1.0, f"5 reads took {elapsed:.3f}s (> 1s budget)"

    def test_many_files_timing(self):
        """Multiple file reads should scale reasonably."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        data_dir = os.path.join(base, "data", "market-data")
        if not os.path.isdir(data_dir):
            pytest.skip("market-data directory not found")
        csv_files = sorted(f for f in os.listdir(data_dir) if f.endswith(".csv"))
        import time
        start = time.perf_counter()
        for _ in range(3):
            for filename in csv_files:
                read_yfinance_csv(os.path.join(data_dir, filename))
        elapsed = time.perf_counter() - start
        # All files 3x should complete in reasonable time
        assert elapsed < 10.0, f"All files x3 took {elapsed:.3f}s (> 10s budget)"


# ---------------------------------------------------------------------------
# Determinism / correctness
# ---------------------------------------------------------------------------


class TestDeterminism:
    """Verify that repeated reads produce identical results."""

    def test_deterministic_output(self):
        """Multiple reads of the same file should produce identical DataFrames."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        path = os.path.join(base, "data", "market-data", "BP.L.csv")
        if not os.path.exists(path):
            pytest.skip("BP.L.csv not found")
        results = [read_yfinance_csv(path) for _ in range(5)]
        for df in results[1:]:
            pd.testing.assert_frame_equal(df, results[0])
