"""Unit tests for calculate_trend.py — incremental computation.

Verifies that when new rows are appended to input data, the incremental path
produces identical results to a full recalculation.
"""

import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from calculate_trend import (
    compute_trend_columns,
    process_csv,
    _load_state,
    _save_state,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ohlcv(n=200, base_price=100.0, noise_range=0.01):
    """Generate OHLCV data as a DataFrame suitable for testing."""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, noise_range) * closes[-1]
        closes.append(max(closes[-1] + change, 10.0))

    opens = []
    highs = []
    lows = []
    volumes = []
    for i in range(n):
        if i == 0:
            o = closes[i]
        else:
            o = closes[i - 1]
        opens.append(o)
        c = closes[i]
        h = max(o, c) + abs(np.random.normal(0, 0.5))
        l = min(o, c) - abs(np.random.normal(0, 0.5))
        highs.append(h)
        lows.append(l)
        volumes.append(int(np.random.uniform(1e6, 1e7)))

    return pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })


def _write_csv(df, path):
    """Write a simple OHLCV CSV (single-header format)."""
    df.to_csv(path, index=False)


# ---------------------------------------------------------------------------
# TestStateFile
# ---------------------------------------------------------------------------


class TestStateFile:
    """Tests for state file helpers."""

    def test_save_and_load(self, tmp_path):
        """State should be saved to and loaded from a JSON file."""
        state = {"key": "value", "count": 42}
        path = str(tmp_path / "state.json")
        _save_state(state, path)
        loaded = _load_state(path)
        assert loaded == state

    def test_load_nonexistent(self, tmp_path):
        """Loading a nonexistent state file should return None."""
        result = _load_state(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_load_corrupted(self, tmp_path):
        """Loading a corrupted JSON file should return None."""
        path = str(tmp_path / "corrupted.json")
        with open(path, "w") as f:
            f.write("{invalid json")
        result = _load_state(path)
        assert result is None


# ---------------------------------------------------------------------------
# TestProcessCSVIncremental
# ---------------------------------------------------------------------------


class TestProcessCSVIncremental:
    """Tests for incremental computation in calculate_trend."""

    def _write_test_csv(self, directory, filename, df):
        """Write an OHLCV CSV."""
        path = os.path.join(directory, filename)
        df.to_csv(path, index=False)
        return path

    def test_full_run_creates_state_file(self):
        """A full run (first time) should create a state file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            # Write input
            df = _make_ohlcv(n=200)
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df)

            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # State file should exist
            state_path = _state_path(output_path)
            assert os.path.exists(state_path)

            # State file should have correct version
            state = _load_state(state_path)
            assert state is not None
            assert state["_version"] == 1
            assert "prev_row_count" in state
            assert state["prev_row_count"] == 200

    def test_incremental_matches_full_computation(self):
        """Incremental computation should produce identical results for new rows.

        Generate a full dataset of 250 rows. Run the first 200 rows, then
        append 50 more and run incrementally. The new rows should match
        a full recomputation on all 250.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            # Generate the full dataset once
            np.random.seed(42)
            df_full = _make_ohlcv(n=250)

            # --- Phase 1: Initial run with first 200 rows ---
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # --- Phase 2: Extend to all 250 rows ---
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # --- Reference: full computation on all 250 rows ---
            ref_closes = df_full["Close"].tolist()
            ref_highs = df_full["High"].tolist()
            ref_lows = df_full["Low"].tolist()
            ref_dates = pd.to_datetime(df_full["Date"])
            ref_cols = compute_trend_columns(ref_highs, ref_lows, ref_closes, 250)
            ref_df = pd.DataFrame({"Date": ref_dates})
            for col, values in ref_cols.items():
                ref_df[col] = values[:250]

            # Load incremental result
            inc_df = pd.read_csv(output_path)
            inc_df["Date"] = pd.to_datetime(inc_df["Date"], format="mixed")

            assert len(inc_df) == 250

            # Verify new rows (indices 200-249) match full computation
            inc_subset = inc_df.iloc[200:].reset_index(drop=True)
            ref_subset = ref_df.iloc[200:].reset_index(drop=True)

            ta_cols = [c for c in inc_subset.columns if c != "Date"]
            for col in ta_cols:
                inc_vals = inc_subset[col].values
                ref_vals = ref_subset[col].values
                for i in range(len(inc_vals)):
                    inc_v = inc_vals[i]
                    ref_v = ref_vals[i]
                    if pd.isna(inc_v) and pd.isna(ref_v):
                        continue
                    assert float(inc_v) == pytest.approx(float(ref_v), rel=1e-10), (
                        f"Mismatch in {col} at row {i + 200}: "
                        f"inc={inc_v}, ref={ref_v}"
                    )

    def test_incremental_no_new_rows(self):
        """Running again with no new rows should recompute fully (same result)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            df = _make_ohlcv(n=200)
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df)
            output_path = os.path.join(output_dir, "TICKER.csv")

            # First run
            process_csv(input_path, output_path, total_files=1, current_file=1)
            df1 = pd.read_csv(output_path)

            # Second run (same data)
            process_csv(input_path, output_path, total_files=1, current_file=1)
            df2 = pd.read_csv(output_path)

            # Same number of rows
            assert len(df1) == len(df2)

            # Values should match
            for col in df1.columns:
                if col == "Date":
                    continue
                for i in range(len(df1)):
                    v1 = df1[col].iloc[i]
                    v2 = df2[col].iloc[i]
                    if pd.isna(v1) and pd.isna(v2):
                        continue
                    assert float(v1) == pytest.approx(float(v2), rel=1e-10), (
                        f"Mismatch in {col} at row {i}"
                    )

    def test_incremental_appends_single_row(self):
        """Appending a single new row should produce correct output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            # Generate the full dataset
            np.random.seed(42)
            df_full = _make_ohlcv(n=201)

            # Initial run with first 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Extend to all 201 rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Result should have 201 rows
            inc_df = pd.read_csv(output_path)
            assert len(inc_df) == 201

    def test_incremental_with_missing_state_falls_back_to_full(self):
        """If state file is missing, fall back to full computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            # Generate the full dataset
            np.random.seed(42)
            df_full = _make_ohlcv(n=250)

            # Initial run with first 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Delete state file to simulate missing state
            os.remove(_state_path(output_path))

            # Extend to all 250 rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Output should be complete (250 rows)
            inc_df = pd.read_csv(output_path)
            assert len(inc_df) == 250

    def test_state_file_updated_after_incremental(self):
        """State file should be updated with new row count after incremental run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            df_full = _make_ohlcv(n=250)

            # Initial run
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            state_after_first = _load_state(_state_path(output_path))
            assert state_after_first["prev_row_count"] == 200

            # Append rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            state_after_incremental = _load_state(_state_path(output_path))
            assert state_after_incremental["prev_row_count"] == 250

    def test_output_columns_unchanged_after_incremental(self):
        """Output columns should be identical after incremental run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            df = _make_ohlcv(n=200)
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df)
            output_path = os.path.join(output_dir, "TICKER.csv")

            process_csv(input_path, output_path, total_files=1, current_file=1)
            df1 = pd.read_csv(output_path)
            cols1 = set(df1.columns)

            # Add more data and run again
            np.random.seed(99)
            more = _make_ohlcv(n=50, base_price=df.iloc[-1]["Close"])
            all_data = pd.concat([df, more], ignore_index=True)
            self._write_test_csv(input_dir, "TICKER.csv", all_data)
            process_csv(input_path, output_path, total_files=1, current_file=1)
            df2 = pd.read_csv(output_path)
            cols2 = set(df2.columns)

            assert cols1 == cols2
            assert len(df2) == len(df1) + 50

    def test_first_run_full_computation(self):
        """First run (no previous output) should compute all rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            df = _make_ohlcv(n=200)
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df)
            output_path = os.path.join(output_dir, "TICKER.csv")

            rows = process_csv(input_path, output_path, total_files=1, current_file=1)
            assert rows == 200

            result = pd.read_csv(output_path)
            assert len(result) == 200

            # All expected columns should be present
            expected_cols = {
                "Date",
                "ta_ema20", "ta_ema50", "ta_ema200",
                "ta_supertrend", "ta_supertrend_direction",
                "ta_supertrend_upper", "ta_supertrend_lower",
                "ta_ma20", "ta_ma50", "ta_sma10",
                "ta_ma20_slope", "ta_ma50_slope",
                "ta_price_ma20_ratio",
                "ta_price_dist_ema20", "ta_price_dist_ema50", "ta_price_dist_ema200",
                "ta_aroon_up", "ta_aroon_down",
                "ta_adx14", "ta_plus_di14", "ta_minus_di14",
                "ta_donchian_upper", "ta_donchian_lower",
                "ta_keltner_upper", "ta_keltner_lower",
            }
            assert set(result.columns) == expected_cols

            # EMA20 should have valid values for rows >= 19
            ema20 = result["ta_ema20"].dropna()
            assert len(ema20) == 181  # 200 - 20 + 1

    def test_multiple_incremental_steps(self):
        """Multiple incremental steps should all produce correct results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            # Generate full dataset of 300 rows
            np.random.seed(42)
            df_full = _make_ohlcv(n=300)

            # Initial run with 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Step 1: Add 50 rows (total 250)
            self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:250])
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Step 2: Add 25 more rows (total 275)
            self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:275])
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Step 3: Add 25 more rows (total 300)
            self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:300])
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Final output should have 300 rows
            final = pd.read_csv(output_path)
            assert len(final) == 300

            # State should reflect 300 rows
            state = _load_state(_state_path(output_path))
            assert state["prev_row_count"] == 300

            # Compare all rows with full computation
            ref_closes = df_full["Close"].tolist()
            ref_highs = df_full["High"].tolist()
            ref_lows = df_full["Low"].tolist()
            ref_cols = compute_trend_columns(ref_highs, ref_lows, ref_closes, 300)

            final["Date"] = pd.to_datetime(final["Date"], format="mixed")
            for col in ref_cols:
                for i in range(300):
                    v_final = final[col].iloc[i]
                    v_ref = ref_cols[col][i]
                    if pd.isna(v_final) and pd.isna(v_ref):
                        continue
                    assert float(v_final) == pytest.approx(float(v_ref), rel=1e-10), (
                        f"{col} row {i}: final={v_final}, ref={v_ref}"
                    )

    def test_empty_input_returns_zero(self):
        """If input is empty but output exists, return 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            df = _make_ohlcv(n=200)
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df)
            output_path = os.path.join(output_dir, "TICKER.csv")

            # Initial run
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Empty input
            empty_df = pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
            self._write_test_csv(input_dir, "TICKER.csv", empty_df)

            rows = process_csv(input_path, output_path, total_files=1, current_file=1)
            assert rows == 0

    def test_trend_column_consistency(self):
        """Trend columns should be consistent across incremental runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            np.random.seed(42)
            df_full = _make_ohlcv(n=250)

            # Initial run with 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            df_before = pd.read_csv(output_path)

            # Extend to 250 rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            df_after = pd.read_csv(output_path)

            # Trend columns for old rows should match full computation
            ref_closes = df_full["Close"].tolist()
            ref_highs = df_full["High"].tolist()
            ref_lows = df_full["Low"].tolist()
            ref_cols = compute_trend_columns(ref_highs, ref_lows, ref_closes, 250)

            # Verify old rows (first 200) match full computation
            for col in ref_cols:
                mismatches = 0
                for i in range(200):
                    v_after = df_after[col].iloc[i]
                    v_ref = ref_cols[col][i]
                    if pd.isna(v_after) and pd.isna(v_ref):
                        continue
                    if not pd.isna(v_ref) and float(v_after) != pytest.approx(float(v_ref), rel=1e-10):
                        mismatches += 1
                assert mismatches == 0, f"Column {col} has {mismatches} mismatches in old rows"

    def test_ema_incremental_matches_full(self):
        """EMA values should match between incremental and full computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            np.random.seed(42)
            df_full = _make_ohlcv(n=250)

            # Initial run with 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Extend to 250 rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            inc_df = pd.read_csv(output_path)

            # Reference EMA20/50/200
            ref_closes = df_full["Close"].tolist()
            ref_ema20 = []
            for i in range(250):
                if i >= 19:
                    window = ref_closes[i - 19: i + 1]
                    if i == 19:
                        ema = sum(window) / 20.0
                    else:
                        k = 2.0 / 21.0
                        ema = ref_closes[i] * k + ema * (1 - k)
                    ref_ema20.append(ema)
                else:
                    ref_ema20.append(None)

            # Compare incremental EMA20 with full computation
            inc_ema20 = inc_df["ta_ema20"].tolist()
            for i in range(200, 250):
                if ref_ema20[i] is not None:
                    assert inc_ema20[i] == pytest.approx(ref_ema20[i], rel=1e-10), (
                        f"EMA20 mismatch at row {i}"
                    )

    def test_supertrend_incremental_matches_full(self):
        """SuperTrend values should match between incremental and full computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            np.random.seed(42)
            df_full = _make_ohlcv(n=250)

            # Initial run with 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Extend to 250 rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            inc_df = pd.read_csv(output_path)

            # Reference SuperTrend
            ref_cols = compute_trend_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental SuperTrend with full computation
            for i in range(200, 250):
                ref_st = ref_cols["ta_supertrend"][i]
                inc_st = inc_df["ta_supertrend"].iloc[i]
                if ref_st is not None and not pd.isna(inc_st):
                    assert float(inc_st) == pytest.approx(float(ref_st), rel=1e-10), (
                        f"SuperTrend mismatch at row {i}"
                    )

    def test_adx_di_incremental_matches_full(self):
        """ADX/DI values should match between incremental and full computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            np.random.seed(42)
            df_full = _make_ohlcv(n=250)

            # Initial run with 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Extend to 250 rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            inc_df = pd.read_csv(output_path)

            # Reference ADX/DI
            ref_cols = compute_trend_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental ADX with full computation
            for i in range(200, 250):
                ref_adx = ref_cols["ta_adx14"][i]
                inc_adx = inc_df["ta_adx14"].iloc[i]
                if ref_adx is not None and not pd.isna(inc_adx):
                    assert float(inc_adx) == pytest.approx(float(ref_adx), rel=1e-10), (
                        f"ADX mismatch at row {i}"
                    )

    def test_aroon_incremental_matches_full(self):
        """Aroon values should match between incremental and full computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            np.random.seed(42)
            df_full = _make_ohlcv(n=250)

            # Initial run with 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Extend to 250 rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            inc_df = pd.read_csv(output_path)

            # Reference Aroon
            ref_cols = compute_trend_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental Aroon with full computation
            for i in range(200, 250):
                ref_up = ref_cols["ta_aroon_up"][i]
                inc_up = inc_df["ta_aroon_up"].iloc[i]
                if ref_up is not None and not pd.isna(inc_up):
                    assert float(inc_up) == pytest.approx(float(ref_up), rel=1e-10), (
                        f"Aroon Up mismatch at row {i}"
                    )
                ref_down = ref_cols["ta_aroon_down"][i]
                inc_down = inc_df["ta_aroon_down"].iloc[i]
                if ref_down is not None and not pd.isna(inc_down):
                    assert float(inc_down) == pytest.approx(float(ref_down), rel=1e-10), (
                        f"Aroon Down mismatch at row {i}"
                    )

    def test_donchian_incremental_matches_full(self):
        """Donchian channel values should match between incremental and full computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            np.random.seed(42)
            df_full = _make_ohlcv(n=250)

            # Initial run with 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Extend to 250 rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            inc_df = pd.read_csv(output_path)

            # Reference Donchian
            ref_cols = compute_trend_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental Donchian with full computation
            for i in range(200, 250):
                ref_upper = ref_cols["ta_donchian_upper"][i]
                inc_upper = inc_df["ta_donchian_upper"].iloc[i]
                if ref_upper is not None and not pd.isna(inc_upper):
                    assert float(inc_upper) == pytest.approx(float(ref_upper), rel=1e-10), (
                        f"Donchian Upper mismatch at row {i}"
                    )
                ref_lower = ref_cols["ta_donchian_lower"][i]
                inc_lower = inc_df["ta_donchian_lower"].iloc[i]
                if ref_lower is not None and not pd.isna(inc_lower):
                    assert float(inc_lower) == pytest.approx(float(ref_lower), rel=1e-10), (
                        f"Donchian Lower mismatch at row {i}"
                    )

    def test_keltner_incremental_matches_full(self):
        """Keltner channel values should match between incremental and full computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "market-data")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "ta-data")
            os.makedirs(output_dir)

            np.random.seed(42)
            df_full = _make_ohlcv(n=250)

            # Initial run with 200 rows
            input_path = self._write_test_csv(input_dir, "TICKER.csv", df_full.iloc[:200])
            output_path = os.path.join(output_dir, "TICKER.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Extend to 250 rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            inc_df = pd.read_csv(output_path)

            # Reference Keltner
            ref_cols = compute_trend_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental Keltner with full computation
            for i in range(200, 250):
                ref_upper = ref_cols["ta_keltner_upper"][i]
                inc_upper = inc_df["ta_keltner_upper"].iloc[i]
                if ref_upper is not None and not pd.isna(inc_upper):
                    assert float(inc_upper) == pytest.approx(float(ref_upper), rel=1e-10), (
                        f"Keltner Upper mismatch at row {i}"
                    )
                ref_lower = ref_cols["ta_keltner_lower"][i]
                inc_lower = inc_df["ta_keltner_lower"].iloc[i]
                if ref_lower is not None and not pd.isna(inc_lower):
                    assert float(inc_lower) == pytest.approx(float(ref_lower), rel=1e-10), (
                        f"Keltner Lower mismatch at row {i}"
                    )
