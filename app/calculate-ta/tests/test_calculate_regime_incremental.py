"""Unit tests for calculate_regime.py — incremental computation.

Verifies that when new rows are appended to input data, the incremental path
produces identical results to a full recalculation.
"""

import json
import os
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest

warnings.filterwarnings("ignore")

from calculate_regime import (
    compute_garch_volatility,
    compute_hmm_regime,
    compute_regime_columns,
    process_csv,
    _load_state,
    _save_state,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ohlcv(n=200, base_price=100.0, base_range=2.0):
    """Generate OHLCV data as a DataFrame suitable for testing."""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, base_range / 2)
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
    """Write a yfinance-style CSV with multi-row header."""
    df.to_csv(path, index=False)


def _run_full(closes, n, dates=None):
    """Run compute_regime_columns for all rows and return a DataFrame."""
    cols = compute_regime_columns(closes, n)
    if dates is None:
        dates = pd.date_range("2020-01-01", periods=n, freq="B")
    result = pd.DataFrame({"Date": dates})
    for col, values in cols.items():
        result[col] = values[:n]
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIncrementalRegime:
    """Tests for incremental computation in calculate_regime."""

    def test_full_run_creates_state_file(self):
        """A full run (first time) should create a state file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write input
            input_path = os.path.join(tmpdir, "test.csv")
            df = _make_ohlcv(n=200)
            _write_csv(df, input_path)

            # Output path
            output_path = os.path.join(tmpdir, "test_regime.csv")

            # Run
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # State file should exist
            state_path = _state_path(output_path)
            assert os.path.exists(state_path)

            # State file should have correct version
            state = _load_state(state_path)
            assert state is not None
            assert state["_version"] == 1
            assert "prev_row_count" in state
            assert "last_close" in state

    def test_incremental_matches_full_computation(self):
        """Incremental computation should produce identical values for new rows.

        Generate a full dataset of 250 rows. Run the first 200 rows, then
        append 50 more and run incrementally. The new rows should match
        a full recomputation on all 250.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate the full dataset once
            df_full = _make_ohlcv(n=250)

            # --- Phase 1: Initial run with first 200 rows ---
            input_path = os.path.join(tmpdir, "test.csv")
            df_initial = df_full.iloc[:200].copy()
            _write_csv(df_initial, input_path)

            output_path = os.path.join(tmpdir, "test_regime.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # --- Phase 2: Extend to all 250 rows ---
            _write_csv(df_full, input_path)

            # Run incremental (detects 50 new rows)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # --- Reference: full computation on all 250 rows ---
            ref_dates = pd.to_datetime(df_full["Date"])
            ref_df = _run_full(df_full["Close"].tolist(), 250, dates=ref_dates)

            # Load incremental result
            inc_df = pd.read_csv(output_path)
            inc_df["Date"] = pd.to_datetime(inc_df["Date"], format="mixed")

            assert len(inc_df) == 250

            # Verify new rows (indices 200-249) match full computation
            inc_subset = inc_df.iloc[200:].reset_index(drop=True)
            ref_subset = ref_df.iloc[200:].reset_index(drop=True)

            # Check TA columns match
            ta_cols = [c for c in inc_subset.columns if c != "Date"]
            for col in ta_cols:
                inc_vals = inc_subset[col].values
                ref_vals = ref_subset[col].values

                # Handle None/NaN values
                for i in range(len(inc_vals)):
                    inc_v = inc_vals[i]
                    ref_v = ref_vals[i]
                    if pd.isna(inc_v) and pd.isna(ref_v):
                        continue
                    # GARCH MLE fitting has minor non-determinism (numba); use
                    # 1e-4 tolerance to absorb tiny optimizer jitter.
                    tol = 1e-4 if col.startswith("ta_garch") else 1e-8
                    assert abs(float(inc_v) - float(ref_v)) < tol, (
                        f"Mismatch in {col} at row {i+200}: "
                        f"inc={inc_v}, ref={ref_v}"
                    )

    def test_incremental_no_new_rows(self):
        """Running again with no new rows should not change the output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initial run
            input_path = os.path.join(tmpdir, "test.csv")
            df = _make_ohlcv(n=200)
            _write_csv(df, input_path)

            output_path = os.path.join(tmpdir, "test_regime.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Capture state after first run
            state1 = _load_state(_state_path(output_path))
            with open(output_path, "r") as f:
                output1 = f.read()

            # Run again with same data
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # State should be updated (prev_row_count = 200 still)
            state2 = _load_state(_state_path(output_path))
            assert state2["prev_row_count"] == 200

            # Output should be the same (full computation path, same results)
            with open(output_path, "r") as f:
                output2 = f.read()
            assert output1 == output2

    def test_incremental_appends_single_row(self):
        """Appending a single new row should produce correct output.

        Generate a full dataset of 201 rows. Run the first 200, then append
        the 201st row and run incrementally.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate the full dataset once
            df_full = _make_ohlcv(n=201)

            # Initial run with first 200 rows
            input_path = os.path.join(tmpdir, "test.csv")
            df_initial = df_full.iloc[:200].copy()
            _write_csv(df_initial, input_path)

            output_path = os.path.join(tmpdir, "test_regime.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Extend to all 201 rows
            _write_csv(df_full, input_path)

            # Run incremental
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Reference: full computation
            ref_dates = pd.to_datetime(df_full["Date"])
            ref_df = _run_full(df_full["Close"].tolist(), 201, dates=ref_dates)

            # Load incremental result
            inc_df = pd.read_csv(output_path)
            inc_df["Date"] = pd.to_datetime(inc_df["Date"], format="mixed")
            assert len(inc_df) == 201

            # Verify last row (the new one) matches
            inc_last = inc_df.iloc[-1:].reset_index(drop=True)
            ref_last = ref_df.iloc[-1:].reset_index(drop=True)

            ta_cols = [c for c in inc_last.columns if c != "Date"]
            for col in ta_cols:
                inc_v = inc_last[col].iloc[0]
                ref_v = ref_last[col].iloc[0]
                if pd.isna(inc_v) and pd.isna(ref_v):
                    continue
                # GARCH MLE fitting has minor non-determinism (numba); use
                # 1e-4 tolerance to absorb tiny optimizer jitter.
                tol = 1e-4 if col.startswith("ta_garch") else 1e-8
                assert abs(float(inc_v) - float(ref_v)) < tol, (
                    f"Mismatch in {col} at last row: inc={inc_v}, ref={ref_v}"
                )

    def test_incremental_with_missing_state_falls_back_to_full(self):
        """If state file is missing, fall back to full computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate the full dataset once
            df_full = _make_ohlcv(n=250)

            # Initial run with first 200 rows
            input_path = os.path.join(tmpdir, "test.csv")
            df_initial = df_full.iloc[:200].copy()
            _write_csv(df_initial, input_path)

            output_path = os.path.join(tmpdir, "test_regime.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Delete state file to simulate missing state
            os.remove(_state_path(output_path))

            # Extend to all 250 rows
            _write_csv(df_full, input_path)

            # Run — should fall back to full computation
            process_csv(input_path, output_path, total_files=1, current_file=1)

            # Output should be complete (250 rows)
            inc_df = pd.read_csv(output_path)
            inc_df["Date"] = pd.to_datetime(inc_df["Date"], format="mixed")
            assert len(inc_df) == 250

            # Reference: full computation
            ref_dates = pd.to_datetime(df_full["Date"])
            ref_df = _run_full(df_full["Close"].tolist(), 250, dates=ref_dates)

            # All rows should match
            ta_cols = [c for c in inc_df.columns if c != "Date"]
            for col in ta_cols:
                for i in range(250):
                    inc_v = inc_df[col].iloc[i]
                    ref_v = ref_df[col].iloc[i]
                    if pd.isna(inc_v) and pd.isna(ref_v):
                        continue
                    # GARCH MLE fitting has minor non-determinism (numba); use
                    # 1e-4 tolerance to absorb tiny optimizer jitter.
                    tol = 1e-4 if col.startswith("ta_garch") else 1e-8
                    assert abs(float(inc_v) - float(ref_v)) < tol, (
                        f"Mismatch in {col} at row {i}: inc={inc_v}, ref={ref_v}"
                    )

    def test_state_file_updated_after_incremental(self):
        """State file should be updated with new row count after incremental run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df_full = _make_ohlcv(n=250)

            # Initial run
            input_path = os.path.join(tmpdir, "test.csv")
            _write_csv(df_full.iloc[:200], input_path)
            output_path = os.path.join(tmpdir, "test_regime.csv")
            process_csv(input_path, output_path, total_files=1, current_file=1)

            state_after_first = _load_state(_state_path(output_path))
            assert state_after_first["prev_row_count"] == 200

            # Append rows
            _write_csv(df_full, input_path)
            process_csv(input_path, output_path, total_files=1, current_file=1)

            state_after_incremental = _load_state(_state_path(output_path))
            assert state_after_incremental["prev_row_count"] == 250
            assert state_after_incremental["last_close"] is not None
