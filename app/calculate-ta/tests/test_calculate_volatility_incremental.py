"""Unit tests for calculate_volatility.py — incremental computation.

Verifies that when new rows are appended to input data, the incremental path
produces identical results to a full recalculation.
"""

import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from calculate_volatility import (
    compute_volatility_columns,
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
    """Tests for incremental computation in calculate_volatility."""

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
            state_path = output_path.replace(".csv", "_state.json")
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
            ref_cols = compute_volatility_columns(ref_highs, ref_lows, ref_closes, 250)
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
            os.remove(output_path.replace(".csv", "_state.json"))

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

            state_after_first = _load_state(output_path.replace(".csv", "_state.json"))
            assert state_after_first["prev_row_count"] == 200

            # Append rows
            self._write_test_csv(input_dir, "TICKER.csv", df_full)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            state_after_incremental = _load_state(output_path.replace(".csv", "_state.json"))
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
                "ta_atr14", "ta_normalized_atr14",
                "ta_bband_upper", "ta_bband_middle", "ta_bband_lower",
                "ta_bband_width", "ta_bband_pctb",
                "ta_hvol20", "ta_parkinson_vol",
                "ta_atr_stop_dist", "ta_atr_position",
                "ta_rr_ratio", "ta_atr_percentile",
            }
            assert set(result.columns) == expected_cols

            # ATR(14) should have valid values for rows >= 14
            atr = result["ta_atr14"].dropna()
            assert len(atr) == 186  # 200 - 14

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
            state = _load_state(output_path.replace(".csv", "_state.json"))
            assert state["prev_row_count"] == 300

            # Compare all rows with full computation
            ref_closes = df_full["Close"].tolist()
            ref_highs = df_full["High"].tolist()
            ref_lows = df_full["Low"].tolist()
            ref_cols = compute_volatility_columns(ref_highs, ref_lows, ref_closes, 300)

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

    def test_volatility_column_consistency(self):
        """Volatility columns should be consistent across incremental runs."""
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

            # Volatility columns for old rows should match full computation
            ref_closes = df_full["Close"].tolist()
            ref_highs = df_full["High"].tolist()
            ref_lows = df_full["Low"].tolist()
            ref_cols = compute_volatility_columns(ref_highs, ref_lows, ref_closes, 250)

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

    def test_atr_incremental_matches_full(self):
        """ATR values should match between incremental and full computation."""
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

            # Reference ATR
            ref_cols = compute_volatility_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental ATR with full computation
            for i in range(200, 250):
                ref_atr = ref_cols["ta_atr14"][i]
                inc_atr = inc_df["ta_atr14"].iloc[i]
                if ref_atr is not None and not pd.isna(inc_atr):
                    assert float(inc_atr) == pytest.approx(float(ref_atr), rel=1e-10), (
                        f"ATR mismatch at row {i}"
                    )

    def test_bollinger_bands_incremental_matches_full(self):
        """Bollinger Bands values should match between incremental and full computation."""
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

            # Reference Bollinger Bands
            ref_cols = compute_volatility_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental BB with full computation
            for i in range(200, 250):
                ref_upper = ref_cols["ta_bband_upper"][i]
                inc_upper = inc_df["ta_bband_upper"].iloc[i]
                if ref_upper is not None and not pd.isna(inc_upper):
                    assert float(inc_upper) == pytest.approx(float(ref_upper), rel=1e-10), (
                        f"BB Upper mismatch at row {i}"
                    )
                ref_lower = ref_cols["ta_bband_lower"][i]
                inc_lower = inc_df["ta_bband_lower"].iloc[i]
                if ref_lower is not None and not pd.isna(inc_lower):
                    assert float(inc_lower) == pytest.approx(float(ref_lower), rel=1e-10), (
                        f"BB Lower mismatch at row {i}"
                    )

    def test_hvol_incremental_matches_full(self):
        """Historical Volatility values should match between incremental and full computation."""
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

            # Reference HV
            ref_cols = compute_volatility_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental HV with full computation
            for i in range(200, 250):
                ref_hv = ref_cols["ta_hvol20"][i]
                inc_hv = inc_df["ta_hvol20"].iloc[i]
                if ref_hv is not None and not pd.isna(inc_hv):
                    assert float(inc_hv) == pytest.approx(float(ref_hv), rel=1e-10), (
                        f"HV mismatch at row {i}"
                    )

    def test_parkinson_incremental_matches_full(self):
        """Parkinson Volatility values should match between incremental and full computation."""
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

            # Reference Parkinson
            ref_cols = compute_volatility_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental Parkinson with full computation
            for i in range(200, 250):
                ref_pv = ref_cols["ta_parkinson_vol"][i]
                inc_pv = inc_df["ta_parkinson_vol"].iloc[i]
                if ref_pv is not None and not pd.isna(inc_pv):
                    assert float(inc_pv) == pytest.approx(float(ref_pv), rel=1e-10), (
                        f"Parkinson mismatch at row {i}"
                    )

    def test_atr_percentile_incremental_matches_full(self):
        """ATR Percentile values should match between incremental and full computation."""
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

            # Reference ATR Percentile
            ref_cols = compute_volatility_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental ATR Percentile with full computation
            for i in range(200, 250):
                ref_pct = ref_cols["ta_atr_percentile"][i]
                inc_pct = inc_df["ta_atr_percentile"].iloc[i]
                if ref_pct is not None and not pd.isna(inc_pct):
                    assert float(inc_pct) == pytest.approx(float(ref_pct), rel=1e-10), (
                        f"ATR Percentile mismatch at row {i}"
                    )

    def test_rr_ratio_incremental_matches_full(self):
        """RR Ratio values should match between incremental and full computation."""
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

            # Reference RR Ratio
            ref_cols = compute_volatility_columns(
                df_full["High"].tolist(), df_full["Low"].tolist(),
                df_full["Close"].tolist(), 250
            )

            # Compare incremental RR Ratio with full computation
            for i in range(200, 250):
                ref_rr = ref_cols["ta_rr_ratio"][i]
                inc_rr = inc_df["ta_rr_ratio"].iloc[i]
                if ref_rr is not None and not pd.isna(inc_rr):
                    assert float(inc_rr) == pytest.approx(float(ref_rr), rel=1e-10), (
                        f"RR Ratio mismatch at row {i}"
                    )
