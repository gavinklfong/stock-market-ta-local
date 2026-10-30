"""Unit tests for calculate_volume.py -- incremental computation.

Verifies that when new rows are appended to input data, the incremental path
produces identical results to a full recalculation.
"""

import json
import math
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from calculate_volume import (
    compute_volume_columns,
    compute_volume_columns_incremental,
    process_csv,
    load_state,
    save_state,
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

    def test_save_and_load_state(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state_path = f.name
        try:
            state = {"_version": 1, "prev_row_count": 100, "last_obv": 5000.0}
            save_state(state, state_path)
            loaded = load_state(state_path)
            assert loaded == state
        finally:
            os.unlink(state_path)

    def testload_state_missing_file(self):
        assert load_state("/nonexistent/path.json") is None

    def testload_state_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            state_path = f.name
        try:
            assert load_state(state_path) is None
        finally:
            os.unlink(state_path)


# ---------------------------------------------------------------------------
# TestIncrementalVolumeColumns
# ---------------------------------------------------------------------------


class TestIncrementalVolumeColumns:
    """Tests that incremental computation matches full recomputation."""

    def _run_full_and_incremental(self, n_initial=150, n_appended=50):
        """Helper to create data, run full then incremental, return column dicts."""
        df_full = _make_ohlcv(n=n_initial)
        appended_df = _make_ohlcv(n=n_appended, base_price=150.0)
        appended_df["Date"] = appended_df["Date"] + pd.DateOffset(days=n_initial)

        df_combined = pd.concat([df_full, appended_df], ignore_index=True)
        n_total = len(df_combined)

        highs = df_combined["High"].tolist()
        lows = df_combined["Low"].tolist()
        closes = df_combined["Close"].tolist()
        volumes = df_combined["Volume"].tolist()
        opens = df_combined["Open"].tolist()

        # Full recomputation
        full_cols = compute_volume_columns(highs, lows, closes, volumes, n_total, opens=opens)

        # Create state from the first n_initial rows
        first_part = _make_ohlcv(n=n_initial)
        h = first_part["High"].tolist()
        lo = first_part["Low"].tolist()
        c = first_part["Close"].tolist()
        v = first_part["Volume"].tolist()
        state = {
            "_version": 1,
            "prev_row_count": n_initial,
            "last_obv": c[0],  # placeholder; actual OBV computed in process
            "last_obv_idx": n_initial - 1,
            "last_adl": c[0],  # placeholder
            "last_adl_idx": n_initial - 1,
        }
        if n_initial >= 28:
            from calculate_volume import _get_volume_oscillator_state
            osc_state = _get_volume_oscillator_state(v)
            state["last_fast_ema"] = osc_state["last_fast_ema"]
            state["last_slow_ema"] = osc_state["last_slow_ema"]
            state["last_osc_idx"] = n_initial - 1

        # Incremental computation
        incr_cols = compute_volume_columns_incremental(
            highs, lows, closes, volumes, n_total,
            opens=opens, state=state, prev_row_count=n_initial
        )

        return full_cols, incr_cols, n_initial, n_total

    def _compare_columns(self, full_cols, incr_cols, start_row, tol=1e-10):
        """Compare columns starting from start_row, ignoring None values."""
        for col in full_cols:
            for i in range(start_row, len(full_cols[col])):
                fv = full_cols[col][i]
                iv = incr_cols[col][i]
                if fv is None and iv is None:
                    continue
                if fv is None or iv is None:
                    pytest.fail(f"Column {col}: row {i} mismatch: {fv} vs {iv}")
                assert abs(fv - iv) <= tol, (
                    f"Column {col}: row {i} mismatch: full={fv}, incr={iv}"
                )

    def test_obv_incremental(self):
        """Test OBV incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        start = max(n_initial - 50, 0)
        self._compare_columns({"ta_obv": full_cols["ta_obv"]},
                              {"ta_obv": incr_cols["ta_obv"]}, start)

    def test_adl_incremental(self):
        """Test ADL incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        start = max(n_initial - 50, 0)
        self._compare_columns({"ta_adl": full_cols["ta_adl"]},
                              {"ta_adl": incr_cols["ta_adl"]}, start)

    def test_cmf_incremental(self):
        """Test CMF incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        # CMF first valid at period-1=19
        start = max(n_initial - 50, 20)
        self._compare_columns({"ta_cmf": full_cols["ta_cmf"]},
                              {"ta_cmf": incr_cols["ta_cmf"]}, start)

    def test_vwap_incremental(self):
        """Test VWAP incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        start = max(n_initial - 50, 20)
        self._compare_columns({"ta_vwap": full_cols["ta_vwap"]},
                              {"ta_vwap": incr_cols["ta_vwap"]}, start)

    def test_ofi_incremental(self):
        """Test OFI incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        # OFI needs at least 2 rows
        start = max(n_initial - 50, 2)
        self._compare_columns({"ta_ofi": full_cols["ta_ofi"]},
                              {"ta_ofi": incr_cols["ta_ofi"]}, start)

    def test_mfi_incremental(self):
        """Test MFI incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        # MFI first valid at period=14
        start = max(n_initial - 50, 15)
        self._compare_columns({"ta_mfi14": full_cols["ta_mfi14"]},
                              {"ta_mfi14": incr_cols["ta_mfi14"]}, start)

    def test_emv_incremental(self):
        """Test EMV incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        # EMV first valid at period=14
        start = max(n_initial - 50, 15)
        self._compare_columns({"ta_emv14": full_cols["ta_emv14"]},
                              {"ta_emv14": incr_cols["ta_emv14"]}, start)

    def test_volume_oscillator_incremental(self):
        """Test Volume Oscillator incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        # Volume Oscillator first valid at period_slow-1=27
        start = max(n_initial - 50, 28)
        self._compare_columns({"ta_volume_osc": full_cols["ta_volume_osc"]},
                              {"ta_volume_osc": incr_cols["ta_volume_osc"]}, start)

    def test_volume_zscore_incremental(self):
        """Test Volume Z-Score incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        start = max(n_initial - 50, 20)
        self._compare_columns({"ta_volume_zscore": full_cols["ta_volume_zscore"]},
                              {"ta_volume_zscore": incr_cols["ta_volume_zscore"]}, start)

    def test_volume_percentile_incremental(self):
        """Test Volume Percentile incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        start = max(n_initial - 50, 20)
        self._compare_columns({"ta_volume_percentile": full_cols["ta_volume_percentile"]},
                              {"ta_volume_percentile": incr_cols["ta_volume_percentile"]}, start)

    def test_log_volume_incremental(self):
        """Test log_volume incremental computation."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        start = max(n_initial - 50, 0)
        self._compare_columns({"ta_log_volume": full_cols["ta_log_volume"]},
                              {"ta_log_volume": incr_cols["ta_log_volume"]}, start)

    def test_all_columns_together(self):
        """Test all columns match at once."""
        full_cols, incr_cols, n_initial, n_total = self._run_full_and_incremental()
        start = max(n_initial - 50, 30)  # start after all warmup periods
        self._compare_columns(full_cols, incr_cols, start)


# ---------------------------------------------------------------------------
# TestProcessCsvIncremental
# ---------------------------------------------------------------------------


class TestProcessCsvIncremental:
    """Tests for process_csv with state detection."""

    def test_process_csv_creates_state_file(self):
        """Test that process_csv creates a state file after first run."""
        df = _make_ohlcv(n=100)
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            df.to_csv(input_path, index=False)

            rows = process_csv(input_path, output_path, 1, 1)
            assert rows == 100

            state_path = _state_path(output_path)
            assert os.path.exists(state_path)
            state = load_state(state_path)
            assert state["_version"] == 1
            assert state["prev_row_count"] == 100

    def test_process_csv_uses_incremental_path(self):
        """Test that process_csv detects new rows and uses incremental computation."""
        # First run with initial data
        df_initial = _make_ohlcv(n=150)
        appended_df = _make_ohlcv(n=50, base_price=150.0)
        # 150 business days ≈ 210 calendar days; 250 gives a safety margin
        appended_df["Date"] = appended_df["Date"] + pd.DateOffset(days=250)
        df_combined = pd.concat([df_initial, appended_df], ignore_index=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")

            # Initial run
            df_initial.to_csv(input_path, index=False)
            rows1 = process_csv(input_path, output_path, 1, 1)
            assert rows1 == 150

            # Append rows
            df_combined.to_csv(input_path, index=False)
            rows2 = process_csv(input_path, output_path, 1, 1)
            assert rows2 == 200  # 150 + 50

            # Compare outputs
            df_out1 = pd.read_csv(output_path)
            # Re-run with only initial data to get baseline
            df_initial.to_csv(input_path, index=False)
            process_csv(input_path, output_path, 1, 1)
            df_out1_full = pd.read_csv(output_path)

            # Full recompute with combined data
            process_csv(input_path, output_path, 1, 1)
            # Write combined data
            df_combined.to_csv(input_path, index=False)
            process_csv(input_path, output_path, 1, 1)
            df_out2 = pd.read_csv(output_path)

            # Check that the first 150 rows match between incremental and full
            for col in df_out1_full.columns:
                if col == "Date":
                    continue
                for i in range(150):
                    v1 = df_out1_full.iloc[i][col]
                    v2 = df_out2.iloc[i][col]
                    if pd.isna(v1) and pd.isna(v2):
                        continue
                    assert v1 == v2, (
                        f"Mismatch in column {col} row {i}"
                    )

    def test_process_csv_no_state_runs_full(self):
        """Test that process_csv without state file runs full computation."""
        df = _make_ohlcv(n=100)
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            df.to_csv(input_path, index=False)

            # No state file exists
            rows = process_csv(input_path, output_path, 1, 1)
            assert rows == 100

            df_out = pd.read_csv(output_path)
            assert len(df_out) == 100
            assert "ta_obv" in df_out.columns
            assert "ta_adl" in df_out.columns
            assert "ta_cmf" in df_out.columns

    def test_process_csv_state_version_mismatch_runs_full(self):
        """Test that process_csv with wrong state version runs full computation."""
        df = _make_ohlcv(n=100)
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            state_path = _state_path(output_path)

            df.to_csv(input_path, index=False)
            # Create state directory (process_csv creates it, but we need it here)
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            # Create a state file with wrong version
            save_state({"_version": 99, "prev_row_count": 50}, state_path)

            rows = process_csv(input_path, output_path, 1, 1)
            assert rows == 100

            # Should have overwritten with correct state
            state = load_state(state_path)
            assert state["_version"] == 1
            assert state["prev_row_count"] == 100
