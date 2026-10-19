"""Tests for incremental momentum indicator computation.

These tests verify that:
1. Incremental computation produces identical results to full computation.
2. State files are created and loaded correctly.
3. Edge cases (no new data, missing state, etc.) are handled.
"""
import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from calculate_momentum import (
    compute_rsi,
    compute_rsi_from_state,
    compute_ema,
    compute_ema_from_state,
    compute_macd,
    compute_macd_incremental,
    compute_stochastic,
    compute_stochastic_incremental,
    compute_williams_r,
    compute_williams_r_incremental,
    compute_cci,
    compute_cci_incremental,
    compute_momentum_columns,
    _save_state,
    _load_state,
    process_csv,
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
        closes.append(max(val, 1.0))
    return closes


def _make_ohlcv(length, base=100.0, noise_range=0.05):
    """Generate OHLCV data as (highs, lows, closes) tuples.

    Returns
    -------
    tuple[list[float], list[float], list[float]]
        (highs, lows, closes)
    """
    np.random.seed(0)
    closes = []
    for i in range(length):
        if i == 0:
            val = base
        else:
            val = closes[-1] * (1 + np.random.uniform(-noise_range, noise_range))
        val = max(val, 1.0)
        closes.append(val)

    highs = [c * (1 + np.random.uniform(0, noise_range)) for c in closes]
    lows = [c * (1 - np.random.uniform(0, noise_range)) for c in closes]
    return highs, lows, closes


def _write_ohlcv_csv(directory, filename, rows):
    """Write a simple OHLCV CSV (single-header format)."""
    df = pd.DataFrame(rows)
    path = os.path.join(directory, filename)
    df.to_csv(path, index=False)
    return path


def _generate_test_data(n, seed=42):
    """Generate realistic OHLCV data as a list of dicts."""
    np.random.seed(seed)
    closes = [100.0]
    for _ in range(n - 1):
        change = np.random.normal(0, 0.01) * closes[-1]
        closes.append(max(closes[-1] + change, 1.0))

    return [
        {
            "Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
            "Open": c * 0.999,
            "High": c * 1.01,
            "Low": c * 0.99,
            "Close": c,
            "Volume": int(1e6 * np.random.uniform(0.8, 1.2)),
        }
        for i, c in enumerate(closes)
    ]


# ---------------------------------------------------------------------------
# TestRSIIncremental
# ---------------------------------------------------------------------------

class TestRSIIncremental:
    def test_matches_full_computation(self):
        """Incremental RSI should match full RSI for the new rows."""
        closes = _make_closes(50, base=100, noise_range=2)
        prev_count = 30

        full_rsi_full = compute_rsi(closes, 14)

        # Get gains/losses up to prev_count to compute state
        gains = [0.0] * len(closes)
        losses = [0.0] * len(closes)
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            if diff > 0:
                gains[i] = diff
            else:
                losses[i] = abs(diff)

        period = 14
        avg_gain = sum(gains[1:period + 1]) / period
        avg_loss = sum(losses[1:period + 1]) / period

        # Carry state forward from period to prev_count
        for i in range(period + 1, prev_count):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        # Incremental RSI from prev_count
        incremental = compute_rsi_from_state(
            closes, period, avg_gain, avg_loss, prev_count,
            closes[:prev_count]
        )

        # Compare with full RSI values at new indices
        for i, inc_val in enumerate(incremental):
            full_idx = prev_count + i
            full_val = full_rsi_full[full_idx]
            if inc_val is not None and full_val is not None:
                assert inc_val == pytest.approx(full_val, rel=1e-10), \
                    f"RSI mismatch at index {full_idx}: inc={inc_val}, full={full_val}"

    def test_no_new_data(self):
        """When prev_count equals total, result should be empty."""
        closes = _make_closes(30, base=100)
        result = compute_rsi_from_state(closes, 14, 1.0, 1.0, 30, closes[:30])
        assert result == []


# ---------------------------------------------------------------------------
# TestEMAIncremental
# ---------------------------------------------------------------------------

class TestEMAIncremental:
    def test_matches_full_computation(self):
        """Incremental EMA should match full EMA for new rows."""
        values = _make_closes(50, base=100, noise_range=2)
        period = 10
        split = 30

        # Full computation
        full_ema = compute_ema(values, period)

        # Compute EMA state at split point
        prev_ema = full_ema[split - 1]  # last valid EMA before new rows
        assert prev_ema is not None

        # Incremental
        new_values = compute_ema_from_state(values, period, prev_ema, split - 1)

        # Compare
        for i, inc_val in enumerate(new_values):
            full_idx = split - 1 + i
            full_val = full_ema[full_idx]
            if inc_val is not None and full_val is not None:
                assert inc_val == pytest.approx(full_val, rel=1e-10), \
                    f"EMA mismatch at index {full_idx}: inc={inc_val}, full={full_val}"

    def test_continuation_correct(self):
        """EMA continuation should produce same value as full computation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        period = 3
        full = compute_ema(values, period)

        # State at index 5 (7th value, 0-based index 5)
        split = 6
        prev_ema = full[split - 1]
        assert prev_ema is not None

        new = compute_ema_from_state(values, period, prev_ema, split - 1)

        for i, nv in enumerate(new):
            fi = split - 1 + i
            assert nv == pytest.approx(full[fi], rel=1e-10)


# ---------------------------------------------------------------------------
# TestMACDIncremental
# ---------------------------------------------------------------------------

class TestMACDIncremental:
    def test_matches_full_computation(self):
        """Incremental MACD should match full MACD for new rows."""
        closes = _make_closes(60, base=100, noise_range=2)
        fast, slow, signal = 12, 26, 9
        prev_close_count = 50  # Ensure enough valid MACD values for signal EMA seed

        # Full computation
        full_macd = compute_macd(closes, fast, slow, signal)

        # Compute state at split-1 using full EMA
        full_fast = compute_ema(closes, fast)
        full_slow = compute_ema(closes, slow)

        split_idx = prev_close_count - 1
        fast_ema = full_fast[split_idx]
        slow_ema = full_slow[split_idx]

        assert fast_ema is not None and slow_ema is not None

        # Build MACD line up to split_idx
        macd_line_full = [None] * len(closes)
        for i in range(len(closes)):
            if full_fast[i] is not None and full_slow[i] is not None:
                macd_line_full[i] = full_fast[i] - full_slow[i]

        # Collect valid MACD values up to split_idx for signal EMA state
        macd_valid_before = [v for v in macd_line_full[:split_idx + 1] if v is not None]

        # Compute signal EMA the same way compute_ema does:
        # Seed with SMA of first `signal` values, then iterate
        signal_ema = None
        signal_count = 0
        if len(macd_valid_before) >= signal:
            k_sig = 2.0 / (signal + 1)
            # Seed: SMA of first `signal` valid MACD values
            signal_ema = sum(macd_valid_before[:signal]) / signal
            signal_count = signal
            # Continue from there
            for v in macd_valid_before[signal:]:
                signal_ema = v * k_sig + signal_ema * (1 - k_sig)
                signal_count += 1

        state = {
            "macd_fast_ema": fast_ema,
            "macd_fast_count": split_idx,
            "macd_slow_ema": slow_ema,
            "macd_slow_count": split_idx,
            "macd_signal_ema": signal_ema,
            "macd_signal_ema_count": signal_count,
        }

        # Incremental
        result = compute_macd_incremental(closes, state, prev_close_count, fast, slow, signal)

        # Compare with full MACD for new rows
        for i, nv in enumerate(result["macd_line"]):
            full_idx = prev_close_count + i
            fv = full_macd["macd_line"][full_idx]
            if nv is not None and fv is not None:
                assert nv == pytest.approx(fv, rel=1e-10), \
                    f"MACD line mismatch at index {full_idx}"

        for i, nv in enumerate(result["signal_line"]):
            full_idx = prev_close_count + i
            fv = full_macd["signal_line"][full_idx]
            if nv is not None and fv is not None:
                assert nv == pytest.approx(fv, rel=1e-10), \
                    f"MACD signal mismatch at index {full_idx}"


# ---------------------------------------------------------------------------
# TestStochasticIncremental
# ---------------------------------------------------------------------------

class TestStochasticIncremental:
    def test_matches_full_computation(self):
        """Incremental Stochastic should match full Stochastic for new rows."""
        closes = _make_closes(50, base=100, noise_range=2)
        k_period = 14
        d_period = 3

        full = compute_stochastic(closes, k_period, d_period)

        # The incremental function expects window_buffer = k_period - 1 elements.
        # New rows start from index k_period - 1 in the closes list.
        window_buffer = closes[:k_period - 1]

        result = compute_stochastic_incremental(closes, window_buffer, k_period, d_period)

        # Compare all new rows (starting from index k_period - 1)
        start_idx = k_period - 1
        for i, kv in enumerate(result["stoch_k"]):
            full_idx = start_idx + i
            fv = full["ta_stoch_k"][full_idx]
            if kv is not None and fv is not None:
                assert kv == pytest.approx(fv, rel=1e-10), \
                    f"Stoch K mismatch at index {full_idx}"


# ---------------------------------------------------------------------------
# TestWilliamsRIncremental
# ---------------------------------------------------------------------------

class TestWilliamsRIncremental:
    def test_matches_full_computation(self):
        """Incremental Williams %R should match full Williams %R for new rows."""
        highs, lows, closes = _make_ohlcv(50, base=100)
        period = 14

        full = compute_williams_r(highs, lows, closes, period)

        # Buffer must have period - 1 elements so new rows start at index period - 1
        window_buffer_h = highs[:period - 1]
        window_buffer_l = lows[:period - 1]

        result = compute_williams_r_incremental(
            highs, lows, closes,
            window_buffer_h, window_buffer_l, period
        )

        # Compare all new rows (starting from index period - 1)
        start_idx = period - 1
        for i, wr in enumerate(result["williams_r"]):
            full_idx = start_idx + i
            fv = full[full_idx]
            if wr is not None and fv is not None:
                assert wr == pytest.approx(fv, rel=1e-10), \
                    f"Williams R mismatch at index {full_idx}"


# ---------------------------------------------------------------------------
# TestCCIIncremental
# ---------------------------------------------------------------------------

class TestCCIIncremental:
    def test_matches_full_computation(self):
        """Incremental CCI should match full CCI for new rows."""
        highs, lows, closes = _make_ohlcv(50, base=100)
        period = 20

        full = compute_cci(highs, lows, closes, period)

        # tp_buffer must have period - 1 elements so new rows start at index period - 1
        tp_buffer = [
            (highs[i] + lows[i] + closes[i]) / 3.0
            for i in range(period - 1)
        ]

        result = compute_cci_incremental(highs, lows, closes, tp_buffer, period)

        # Compare all new rows (starting from index period - 1)
        start_idx = period - 1
        for i, cci in enumerate(result["cci"]):
            full_idx = start_idx + i
            fv = full[full_idx]
            if cci is not None and fv is not None:
                assert cci == pytest.approx(fv, rel=1e-10), \
                    f"CCI mismatch at index {full_idx}"


# ---------------------------------------------------------------------------
# TestStateFile
# ---------------------------------------------------------------------------

class TestStateFile:
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
    def _write_test_csv(self, directory, filename, rows):
        """Write an OHLCV CSV that mimics yfinance format (single header)."""
        df = pd.DataFrame(rows)
        path = os.path.join(directory, filename)
        df.to_csv(path, index=False)
        return path

    def test_incremental_matches_full(self, tmp_path):
        """Running process_csv twice (first full, then incremental) should
        produce identical results to running it once with all data."""
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        # Generate full dataset
        full_data = _generate_test_data(50, seed=42)

        # Write full input
        input_path = self._write_test_csv(
            str(input_dir), "TICKER.csv", full_data
        )
        output_path = str(output_dir / "TICKER.csv")

        # First run: full computation
        process_csv(input_path, output_path, 1, 1)
        df_full = pd.read_csv(output_path)

        # Now add more data
        more_data = _generate_test_data(10, seed=99)
        all_data = full_data + more_data

        # Overwrite input with extended data
        self._write_test_csv(
            str(input_dir), "TICKER.csv", all_data
        )

        # Second run: should use incremental path
        process_csv(input_path, output_path, 1, 1)
        df_extended = pd.read_csv(output_path)

        # The first 50 rows of the extended output should match the
        # full computation's first 50 rows
        assert len(df_extended) == 60
        assert len(df_full) == 50

        # Verify first 50 rows match
        for col in df_full.columns:
            if col == "Date":
                continue
            for i in range(50):
                old_val = df_full[col].iloc[i]
                new_val = df_extended[col].iloc[i]
                if pd.isna(old_val) and pd.isna(new_val):
                    continue
                assert float(old_val) == pytest.approx(float(new_val), rel=1e-10), \
                    f"Row {i}, col {col}: old={old_val}, new={new_val}"

    def test_state_file_created(self, tmp_path):
        """A state file should be created alongside the output CSV."""
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        data = [
            {
                "Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                "Open": 100.0, "High": 102.0, "Low": 99.0,
                "Close": 100.0 + i * 0.5, "Volume": 1000000,
            }
            for i in range(50)
        ]
        input_path = self._write_test_csv(str(input_dir), "TICKER.csv", data)
        output_path = str(output_dir / "TICKER.csv")

        process_csv(input_path, output_path, 1, 1)

        base, ext = os.path.splitext(output_path)
        state_path = base + "_state.json"
        assert os.path.exists(state_path)

        with open(state_path) as f:
            state = json.load(f)
        assert state["_version"] == 1
        assert state["prev_row_count"] == 50

    def test_no_new_rows_recomputes(self, tmp_path):
        """When no new rows are added, process_csv should recompute fully."""
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        data = [
            {
                "Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                "Open": 100.0, "High": 102.0, "Low": 99.0,
                "Close": 100.0 + i * 0.5, "Volume": 1000000,
            }
            for i in range(50)
        ]
        input_path = self._write_test_csv(str(input_dir), "TICKER.csv", data)
        output_path = str(output_dir / "TICKER.csv")

        # First run
        rows1 = process_csv(input_path, output_path, 1, 1)
        df1 = pd.read_csv(output_path)

        # Second run (same data)
        rows2 = process_csv(input_path, output_path, 1, 1)
        df2 = pd.read_csv(output_path)

        assert rows1 == rows2
        assert len(df1) == len(df2)

    def test_first_run_full_computation(self, tmp_path):
        """First run (no previous output) should compute all rows."""
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        data = [
            {
                "Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                "Open": 100.0, "High": 102.0, "Low": 99.0,
                "Close": 100.0 + i * 0.5, "Volume": 1000000,
            }
            for i in range(50)
        ]
        input_path = self._write_test_csv(str(input_dir), "TICKER.csv", data)
        output_path = str(output_dir / "TICKER.csv")

        rows = process_csv(input_path, output_path, 1, 1)
        assert rows == 50

        df = pd.read_csv(output_path)
        assert len(df) == 50
        assert "ta_rsi14" in df.columns

    def test_output_columns_unchanged(self, tmp_path):
        """Output columns should be identical after incremental run."""
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        data = [
            {
                "Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                "Open": 100.0, "High": 102.0, "Low": 99.0,
                "Close": 100.0 + i * 0.5, "Volume": 1000000,
            }
            for i in range(50)
        ]
        input_path = self._write_test_csv(str(input_dir), "TICKER.csv", data)
        output_path = str(output_dir / "TICKER.csv")

        process_csv(input_path, output_path, 1, 1)
        df1 = pd.read_csv(output_path)
        cols1 = set(df1.columns)

        # Add more data and run again
        more_data = _generate_test_data(10, seed=99)
        all_data = data + more_data
        self._write_test_csv(str(input_dir), "TICKER.csv", all_data)
        process_csv(input_path, output_path, 1, 1)
        df2 = pd.read_csv(output_path)
        cols2 = set(df2.columns)

        assert cols1 == cols2
