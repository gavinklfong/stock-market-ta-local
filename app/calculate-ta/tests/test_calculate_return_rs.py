"""Unit tests for calculate_return.py — relative strength (ta_rs_ftse100)."""

import numpy as np
import pandas as pd
import pytest

from calculate_return import (
    compute_relative_strength,
    compute_return_columns,
    process_csv,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dates(n):
    """Generate n consecutive dates starting from 2024-01-01."""
    return [pd.Timestamp("2024-01-01") + pd.Timedelta(days=i) for i in range(n)]


# ---------------------------------------------------------------------------
# TestComputeRelativeStrength
# ---------------------------------------------------------------------------


class TestComputeRelativeStrength:
    def test_length_matches_input(self):
        stock = [100.0 + i for i in range(50)]
        bench = [50.0 + i * 0.5 for i in range(50)]
        result = compute_relative_strength(stock, bench)
        assert len(result) == 50

    def test_first_row_is_valid(self):
        """First row should have a valid RS value (no rolling window)."""
        stock = [100.0 + i for i in range(50)]
        bench = [50.0 + i * 0.5 for i in range(50)]
        result = compute_relative_strength(stock, bench)
        assert result[0] is not None

    def test_perfectly_proportional(self):
        """Stock exactly 2x benchmark → RS = 200."""
        stock = [200.0, 210.0, 220.0, 230.0]
        bench = [100.0, 105.0, 110.0, 115.0]
        result = compute_relative_strength(stock, bench)
        for v in result:
            assert v == pytest.approx(200.0)

    def test_stock_underperformance(self):
        """Stock cheaper than benchmark → RS < 100."""
        stock = [50.0, 55.0, 60.0]
        bench = [100.0, 110.0, 120.0]
        result = compute_relative_strength(stock, bench)
        for v in result:
            assert v == pytest.approx(50.0)

    def test_stock_outperformance(self):
        """Stock more expensive than benchmark → RS > 100."""
        stock = [200.0, 220.0, 240.0]
        bench = [100.0, 110.0, 120.0]
        result = compute_relative_strength(stock, bench)
        for v in result:
            assert v == pytest.approx(200.0)

    def test_constant_ratio(self):
        """Same % changes → constant RS regardless of level."""
        stock = [100.0]
        bench = [50.0]
        for _ in range(99):
            stock.append(stock[-1] * 1.01)
            bench.append(bench[-1] * 1.01)
        result = compute_relative_strength(stock, bench)
        for v in result:
            assert v == pytest.approx(200.0)

    def test_diverging_stock_and_benchmark(self):
        """Stock outpacing benchmark → RS should increase."""
        stock = [100.0]
        bench = [100.0]
        for _ in range(49):
            stock.append(stock[-1] * 1.02)   # 2% daily
            bench.append(bench[-1] * 1.005)  # 0.5% daily
        result = compute_relative_strength(stock, bench)
        assert result[0] == pytest.approx(100.0)
        assert result[-1] > result[0]  # RS should increase

    def test_benchmark_diverging(self):
        """Benchmark outpacing stock → RS should decrease."""
        stock = [100.0]
        bench = [100.0]
        for _ in range(49):
            stock.append(stock[-1] * 1.01)   # 1% daily
            bench.append(bench[-1] * 1.03)   # 3% daily
        result = compute_relative_strength(stock, bench)
        assert result[0] == pytest.approx(100.0)
        assert result[-1] < result[0]  # RS should decrease

    def test_zero_benchmark_returns_none(self):
        """Zero benchmark price should produce None."""
        stock = [100.0, 110.0, 120.0]
        bench = [0.0, 0.0, 0.0]
        result = compute_relative_strength(stock, bench)
        assert all(v is None for v in result)

    def test_mixed_zero_benchmark(self):
        """Some zero benchmark prices → partial None values."""
        stock = [100.0, 110.0, 120.0, 130.0]
        bench = [50.0, 0.0, 60.0, 0.0]
        result = compute_relative_strength(stock, bench)
        assert result[0] is not None
        assert result[1] is None
        assert result[2] is not None
        assert result[3] is None

    def test_finite_values(self):
        """All non-None values should be finite."""
        np.random.seed(42)
        stock = [100.0]
        bench = [50.0]
        for _ in range(99):
            stock.append(max(stock[-1] * np.random.uniform(0.95, 1.05), 1.0))
            bench.append(max(bench[-1] * np.random.uniform(0.95, 1.05), 1.0))
        result = compute_relative_strength(stock, bench)
        for v in result:
            if v is not None:
                assert np.isfinite(v)

    def test_large_price_range(self):
        """Very different price levels should still produce valid RS."""
        stock = [10000.0, 10100.0, 10200.0, 10300.0]
        bench = [1.0, 1.01, 1.02, 1.03]
        result = compute_relative_strength(stock, bench)
        assert all(v is not None for v in result)
        for v in result:
            assert np.isfinite(v)


# ---------------------------------------------------------------------------
# TestRelativeStrengthColumns
# ---------------------------------------------------------------------------


class TestRelativeStrengthColumns:
    def test_rs_in_columns_with_benchmark(self):
        """RS column should appear when benchmark_df is provided."""
        np.random.seed(42)
        n = 50
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(closes[-1] * np.random.uniform(0.98, 1.02))

        highs = [c * 1.01 for c in closes]
        lows = [c * 0.99 for c in closes]
        volumes = [1000] * n
        dates = _make_dates(n)

        bench_df = pd.DataFrame({
            "Date": dates,
            "Close": [50.0] + [50.0 * np.random.uniform(0.98, 1.02) for _ in range(n - 1)],
        })

        cols = compute_return_columns(
            highs, lows, closes, volumes, n, dates, benchmark_df=bench_df
        )
        assert "ta_rs_ftse100" in cols

    def test_rs_not_in_columns_without_benchmark(self):
        """RS column should NOT appear when benchmark_df is None."""
        n = 50
        closes = [100.0] * n
        cols = compute_return_columns(
            closes, closes, closes, [1000] * n, n, _make_dates(n),
            benchmark_df=None
        )
        assert "ta_rs_ftse100" not in cols

    def test_rs_all_same_length(self):
        """RS column should be same length as input."""
        n = 50
        closes = [100.0 + i for i in range(n)]
        bench_df = pd.DataFrame({
            "Date": _make_dates(n),
            "Close": [50.0 + i * 0.5 for i in range(n)],
        })
        cols = compute_return_columns(
            closes, closes, closes, [1000] * n, n, _make_dates(n),
            benchmark_df=bench_df
        )
        assert len(cols["ta_rs_ftse100"]) == n

    def test_rs_first_value_valid(self):
        """First RS value should be valid when dates align."""
        n = 50
        dates = _make_dates(n)
        closes = [100.0 + i for i in range(n)]
        bench_df = pd.DataFrame({
            "Date": dates,
            "Close": [50.0 + i * 0.5 for i in range(n)],
        })
        cols = compute_return_columns(
            closes, closes, closes, [1000] * n, n, dates,
            benchmark_df=bench_df
        )
        assert cols["ta_rs_ftse100"][0] is not None

    def test_rs_value_matches_direct_computation(self):
        """RS from columns should match direct compute_relative_strength."""
        n = 50
        dates = _make_dates(n)
        closes = [100.0 + i for i in range(n)]
        bench_closes = [50.0 + i * 0.5 for i in range(n)]
        bench_df = pd.DataFrame({
            "Date": dates,
            "Close": bench_closes,
        })
        cols = compute_return_columns(
            closes, closes, closes, [1000] * n, n, dates,
            benchmark_df=bench_df
        )
        direct = compute_relative_strength(closes, bench_closes)
        for i in range(n):
            assert cols["ta_rs_ftse100"][i] == pytest.approx(direct[i], rel=1e-10)

    def test_rs_with_partial_date_overlap(self):
        """RS should handle partial date overlap (benchmark has fewer dates)."""
        n = 50
        stock_dates = _make_dates(n)
        closes = [100.0 + i for i in range(n)]

        # Benchmark has only even-indexed dates (subset)
        bench_dates = stock_dates[::2]
        bench_closes = [50.0 + i * 0.5 for i in range(0, n, 2)]
        bench_df = pd.DataFrame({"Date": bench_dates, "Close": bench_closes})

        cols = compute_return_columns(
            closes, closes, closes, [1000] * n, n, stock_dates,
            benchmark_df=bench_df
        )
        rs = cols["ta_rs_ftse100"]
        # Values at odd stock indices (no matching benchmark date) should be None
        assert rs[0] is not None      # date 0 matches
        assert rs[1] is None          # date 1 doesn't match
        assert rs[2] is not None      # date 2 matches

    def test_rs_short_benchmark(self):
        """Very short benchmark data (< 2 rows) should not produce RS."""
        n = 50
        dates = _make_dates(n)
        closes = [100.0] * n
        bench_df = pd.DataFrame({"Date": [dates[0]], "Close": [50.0]})

        cols = compute_return_columns(
            closes, closes, closes, [1000] * n, n, dates,
            benchmark_df=bench_df
        )
        assert "ta_rs_ftse100" not in cols


# ---------------------------------------------------------------------------
# TestProcessCSVRelativeStrength
# ---------------------------------------------------------------------------


class TestProcessCSVRelativeStrength:
    def test_rs_output_in_csv(self):
        """process_csv should write RS column to output."""
        import tempfile

        np.random.seed(42)
        n = 100
        dates = pd.date_range("2024-01-01", periods=n)
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(max(closes[-1] * np.random.uniform(0.98, 1.02), 10.0))

        raw_df = pd.DataFrame({
            "Date": dates,
            "Open": [c * 0.99 for c in closes],
            "High": [c * 1.01 for c in closes],
            "Low": [c * 0.99 for c in closes],
            "Close": closes,
            "Volume": [1000] * n,
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            input_path = os.path.join(tmpdir, "TEST.csv")
            output_path = os.path.join(tmpdir, "TEST_ta_return.csv")

            # Write input with yfinance header
            raw_df.to_csv(input_path, index=False)

            rows = process_csv(input_path, output_path, 1, 1)

            # Read output and verify RS column exists
            output_df = pd.read_csv(output_path)
            assert "ta_rs_ftse100" in output_df.columns
