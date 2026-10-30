"""Unit tests for calculate_return.py — benchmark caching.

Verifies that the module-level ``_bench_cached`` variable correctly caches
the ``^FTSE`` benchmark DataFrame across multiple ``_load_benchmark()`` calls.
"""

import os
import tempfile

import numpy as np
import pandas as pd
import pytest

# Reset the cache before each test so tests are independent.
import calculate_return

calculate_return._bench_cached = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_benchmark_csv(path: str, n: int = 200, base_price: float = 7500.0) -> str:
    """Generate ^FTSE benchmark data and write it as a yfinance-style CSV."""
    np.random.seed(99)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 0.008) * closes[-1]
        closes.append(max(closes[-1] + change, 100.0))

    df = pd.DataFrame({
        "Date": dates,
        "Open": closes,
        "High": [c * 1.01 for c in closes],
        "Low": [c * 0.99 for c in closes],
        "Close": closes,
        "Volume": [int(1e8) for _ in range(n)],
    })
    df.to_csv(path, index=False)
    return path


def _write_empty_dir(tmpdir: str) -> str:
    """Write an empty ^FTSE.csv so _load_benchmark finds the file but nothing useful."""
    empty_path = os.path.join(tmpdir, "^FTSE.csv")
    pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"]).to_csv(
        empty_path, index=False
    )
    return empty_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBenchmarkCacheInitialState:
    """Verify _bench_cached starts as None."""

    def setup_method(self):
        """Reset the cache before each test."""
        calculate_return._bench_cached = None

    def test_cached_is_none_initially(self):
        """_bench_cached should be None at module load time."""
        assert calculate_return._bench_cached is None


class TestBenchmarkLoadNoCache:
    """Verify _load_benchmark works correctly without any cache set."""

    def setup_method(self):
        """Reset the cache before each test."""
        calculate_return._bench_cached = None

    def test_returns_dataframe_when_file_exists(self, tmp_path):
        """_load_benchmark should return a DataFrame when the benchmark CSV exists."""
        bench_path = _make_benchmark_csv(str(tmp_path / "^FTSE.csv"))
        result = calculate_return._load_benchmark(str(tmp_path))
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert "Date" in result.columns
        assert "Close" in result.columns
        assert len(result) > 0

    def test_returns_none_when_file_missing(self, tmp_path):
        """_load_benchmark should return None when the benchmark CSV does not exist."""
        result = calculate_return._load_benchmark(str(tmp_path))
        assert result is None

    def test_caches_result_on_first_call(self, tmp_path):
        """After first call, _bench_cached should hold the DataFrame."""
        _make_benchmark_csv(str(tmp_path / "^FTSE.csv"))
        calculate_return._load_benchmark(str(tmp_path))
        assert calculate_return._bench_cached is not None
        assert isinstance(calculate_return._bench_cached, pd.DataFrame)

    def test_returns_none_does_not_cache(self, tmp_path):
        """When file is missing, _bench_cached should remain None."""
        result = calculate_return._load_benchmark(str(tmp_path))
        assert result is None
        assert calculate_return._bench_cached is None


class TestBenchmarkCacheHit:
    """Verify subsequent calls return the cached DataFrame (identity)."""

    def setup_method(self):
        """Reset the cache before each test."""
        calculate_return._bench_cached = None

    def test_second_call_returns_same_object(self, tmp_path):
        """Subsequent calls should return the exact same DataFrame object."""
        _make_benchmark_csv(str(tmp_path / "^FTSE.csv"))
        first = calculate_return._load_benchmark(str(tmp_path))
        second = calculate_return._load_benchmark(str(tmp_path))
        assert first is second

    def test_multiple_calls_all_same(self, tmp_path):
        """Ten calls should all return the same cached object."""
        _make_benchmark_csv(str(tmp_path / "^FTSE.csv"))
        results = [calculate_return._load_benchmark(str(tmp_path)) for _ in range(10)]
        for r in results:
            assert r is results[0]

    def test_cached_dataframe_unchanged(self, tmp_path):
        """The cached DataFrame should not be modified by repeated calls."""
        _make_benchmark_csv(str(tmp_path / "^FTSE.csv"))
        first = calculate_return._load_benchmark(str(tmp_path))
        first_len = len(first)
        first_close_mean = first["Close"].mean()
        # Call again
        calculate_return._load_benchmark(str(tmp_path))
        assert len(first) == first_len
        assert first["Close"].mean() == first_close_mean


class TestBenchmarkCacheCrossCall:
    """Verify caching persists across calls with different (or same) input_dir."""

    def setup_method(self):
        """Reset the cache before each test."""
        calculate_return._bench_cached = None

    def test_cached_across_different_input_dirs(self, tmp_path):
        """Once cached, _load_benchmark should return the cache regardless of input_dir."""
        # First call populates cache
        tmpdir1 = tmp_path / "dir1"
        tmpdir1.mkdir()
        _make_benchmark_csv(str(tmpdir1 / "^FTSE.csv"))
        first = calculate_return._load_benchmark(str(tmpdir1))

        # Second call with a different (non-existent) directory should return cached
        tmpdir2 = tmp_path / "dir2"
        tmpdir2.mkdir()
        second = calculate_return._load_benchmark(str(tmpdir2))

        assert first is second

    def test_cached_dataframe_is_sorted_and_clean(self, tmp_path):
        """The cached DataFrame should be sorted by Date and have only Date + Close."""
        _make_benchmark_csv(str(tmp_path / "^FTSE.csv"), n=200)
        result = calculate_return._load_benchmark(str(tmp_path))
        assert list(result.columns) == ["Date", "Close"]
        # Dates should be in ascending order
        assert result["Date"].is_monotonic_increasing


class TestBenchmarkProcessCSVIntegration:
    """Verify that process_csv benefits from the cached benchmark (same DF object)."""

    def setup_method(self):
        """Reset the cache before each test."""
        calculate_return._bench_cached = None

    def test_process_csv_uses_cached_benchmark(self, tmp_path):
        """Multiple process_csv calls should share the same cached benchmark DF."""
        # Create market-data directory with benchmark and stock CSVs
        market_dir = tmp_path / "market-data"
        market_dir.mkdir()
        _make_benchmark_csv(str(market_dir / "^FTSE.csv"), n=300)

        # Create a stock CSV
        np.random.seed(42)
        dates = pd.date_range("2020-01-01", periods=250, freq="B")
        closes = [100.0]
        for _ in range(249):
            change = np.random.normal(0, 0.01) * closes[-1]
            closes.append(max(closes[-1] + change, 10.0))
        stock = pd.DataFrame({
            "Date": dates,
            "Open": closes,
            "High": [c * 1.01 for c in closes],
            "Low": [c * 0.99 for c in closes],
            "Close": closes,
            "Volume": [int(1e6) for _ in range(250)],
        })
        stock.to_csv(str(market_dir / "TEST.L.csv"), index=False)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        out1 = str(output_dir / "TEST.L_return.csv")
        out2 = str(output_dir / "TEST.L_return2.csv")

        # First call
        calculate_return._bench_cached = None
        calculate_return.process_csv(
            str(market_dir / "TEST.L.csv"), out1, total_files=1, current_file=1
        )
        cached_after_first = calculate_return._bench_cached

        # Second call — should use cache
        calculate_return.process_csv(
            str(market_dir / "TEST.L.csv"), out2, total_files=1, current_file=1
        )
        cached_after_second = calculate_return._bench_cached

        assert cached_after_first is cached_after_second
