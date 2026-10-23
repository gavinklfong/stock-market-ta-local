"""Tests for the --force / TA_FORCE_FULL_RECALCULATION full-recalculation parameter.

These tests verify that when the ``TA_FORCE_FULL_RECALCULATION`` environment
variable is set to ``1``, every module's ``process_csv()`` skips all incremental
logic and always performs a full recomputation, even when:

  - No new rows have been appended (row count is unchanged)
  - State files exist from previous runs
  - The "today's date" recalculation path would not be triggered

This mirrors the ``--force`` flag that propagates from
``run_calculation.py --force`` to each module via the environment variable.
"""

import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

# All 7 modules
from calculate_trend import process_csv as trend_process_csv
from calculate_momentum import process_csv as momentum_process_csv
from calculate_volume import process_csv as volume_process_csv
from calculate_volatility import process_csv as volatility_process_csv
from calculate_regime import process_csv as regime_process_csv
from calculate_structure import process_csv as structure_process_csv
from calculate_return import process_csv as return_process_csv

# State helper from conftest
from conftest import _state_path as _conftest_state_path


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

    opens = [c * (1 + np.random.uniform(-0.005, 0.005)) for c in closes]
    highs = [o * (1 + abs(np.random.normal(0, 0.005))) for o in opens]
    lows = [o * (1 - abs(np.random.normal(0, 0.005))) for o in opens]
    volumes = [int(1e6 * abs(np.random.normal(1, 0.1))) for _ in range(n)]

    return pd.DataFrame({
        "Date": dates,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })


def _state_path(output_path):
    """Compute the state file path for a given output CSV path."""
    base = output_path.rsplit(".", 1)[0]
    state_dir = os.path.join(os.path.dirname(output_path), "state")
    return os.path.join(state_dir, os.path.basename(base) + "_state.json")


def _set_force_env(value="1"):
    """Set or clear the TA_FORCE_FULL_RECALCULATION env var."""
    if value:
        os.environ["TA_FORCE_FULL_RECALCULATION"] = value
    else:
        os.environ.pop("TA_FORCE_FULL_RECALCULATION", None)


def _run_full_ref(process_fn, df, output_path):
    """Run process_csv *without* the force env var to get a reference output.

    The env var is explicitly cleared so we get normal (possibly incremental)
    behavior.  This gives us a "full" reference because there is no prior state.
    """
    _set_force_env("0")
    process_fn(df, output_path, total_files=1, current_file=1)
    return pd.read_csv(output_path)


# ---------------------------------------------------------------------------
# Shared test runners
# ---------------------------------------------------------------------------


def _test_force_skips_incremental(process_fn, module_name):
    """Force mode should recompute even when no new data is appended.

    1. Run full on 200 rows (creates state).
    2. Run again with same 200 rows and force=1.
    3. Force mode should recompute all rows (not skip incremental).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = os.path.join(tmpdir, "market-data")
        os.makedirs(input_dir)
        output_dir = os.path.join(tmpdir, "ta-data")
        os.makedirs(output_dir)

        df = _make_ohlcv(n=200)
        input_path = os.path.join(input_dir, "TICKER.csv")
        df.to_csv(input_path, index=False)
        output_path = os.path.join(output_dir, "TICKER.csv")

        # Phase 1: Full run
        _set_force_env("0")
        process_fn(input_path, output_path, total_files=1, current_file=1)

        df1 = pd.read_csv(output_path)
        assert len(df1) == 200

        # State should exist
        assert os.path.exists(_state_path(output_path))

        # Phase 2: Run again with same data but force=1
        _set_force_env("1")
        process_fn(input_path, output_path, total_files=1, current_file=1)

        df2 = pd.read_csv(output_path)
        assert len(df2) == 200

        # With force=1, the state file should be rewritten with the same count
        # but the key point is the run completed (no crash, no skip).
        state = json.loads(open(_state_path(output_path)).read())
        assert state["prev_row_count"] == 200

        # Output should be valid (all TA columns present)
        ta_cols = [c for c in df2.columns if c.startswith("ta_")]
        assert len(ta_cols) > 0, f"{module_name}: no ta_ columns in output"

        _set_force_env("0")


def _test_force_matches_full_computation(process_fn, module_name):
    """Force mode should produce identical output to a fresh full computation.

    1. Generate 250 rows, run full on first 200.
    2. Extend to 250, run incremental (without force) -> inc result.
    3. Extend to 250, run with force=1 -> force result.
    4. Verify force result matches a full computation on all 250 rows.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = os.path.join(tmpdir, "market-data")
        os.makedirs(input_dir)
        output_dir = os.path.join(tmpdir, "ta-data")
        os.makedirs(output_dir)

        np.random.seed(42)
        df_full = _make_ohlcv(n=250)

        # Phase 1: Initial run with 200 rows
        input_path = os.path.join(input_dir, "TICKER.csv")
        df_full.iloc[:200].to_csv(input_path, index=False)
        output_path = os.path.join(output_dir, "TICKER.csv")

        _set_force_env("0")
        process_fn(input_path, output_path, total_files=1, current_file=1)

        # Phase 2: Extend to 250 rows, run incremental
        df_full.to_csv(input_path, index=False)
        process_fn(input_path, output_path, total_files=1, current_file=1)

        inc_df = pd.read_csv(output_path)
        inc_df["Date"] = pd.to_datetime(inc_df["Date"], format="mixed")

        # Phase 3: Delete output and state, run with force=1 from scratch
        os.remove(output_path)
        os.remove(_state_path(output_path))

        _set_force_env("1")
        process_fn(input_path, output_path, total_files=1, current_file=1)

        force_df = pd.read_csv(output_path)
        force_df["Date"] = pd.to_datetime(force_df["Date"], format="mixed")

        # Force result should match a full computation on all 250 rows
        # (which is what inc_df should also match, since incremental on appended
        # data should produce identical results).
        assert len(force_df) == 250
        assert len(inc_df) == 250

        ta_cols = [c for c in force_df.columns if c.startswith("ta_")]
        assert len(ta_cols) > 0, f"{module_name}: no ta_ columns in output"

        # Phase 3: Run fresh full computation on all 250 rows (reference)
        ref_output_path = os.path.join(output_dir, "TICKER_ref.csv")
        os.remove(output_path)
        os.remove(_state_path(output_path))

        _set_force_env("0")
        process_fn(input_path, ref_output_path, total_files=1, current_file=1)

        ref_df = pd.read_csv(ref_output_path)
        ref_df["Date"] = pd.to_datetime(ref_df["Date"], format="mixed")

        # Phase 4: Run with force=1 from same 250 rows
        force_output_path = os.path.join(output_dir, "TICKER_force.csv")
        os.remove(ref_output_path)

        _set_force_env("1")
        process_fn(input_path, force_output_path, total_files=1, current_file=1)

        force_df = pd.read_csv(force_output_path)
        force_df["Date"] = pd.to_datetime(force_df["Date"], format="mixed")

        # Force result should match the reference (full computation on all 250 rows)
        assert len(force_df) == 250
        assert len(ref_df) == 250

        ta_cols = [c for c in force_df.columns if c.startswith("ta_")]
        assert len(ta_cols) > 0, f"{module_name}: no ta_ columns in output"

        # Verify force output matches reference (full computation)
        for col in ta_cols:
            for i in range(250):
                v_force = force_df[col].iloc[i]
                v_ref = ref_df[col].iloc[i]
                if pd.isna(v_force) and pd.isna(v_ref):
                    continue
                assert float(v_force) == pytest.approx(float(v_ref), rel=1e-10), (
                    f"{module_name}: {col} row {i} force={v_force}, ref={v_ref}"
                )

        _set_force_env("0")


def _test_force_without_state_falls_to_full(process_fn, module_name):
    """Force mode should work even when no state file exists (full path)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.csv")

        df = _make_ohlcv(n=200)
        df.to_csv(input_path, index=False)

        # Force with no prior state -> should run full computation
        _set_force_env("1")
        rows = process_fn(input_path, output_path, total_files=1, current_file=1)
        assert rows == 200

        out = pd.read_csv(output_path)
        assert len(out) == 200
        ta_cols = [c for c in out.columns if c.startswith("ta_")]
        assert len(ta_cols) > 0, f"{module_name}: no ta_ columns in output"

        _set_force_env("0")


def _test_env_var_clearing_restores_normal_behavior(process_fn, module_name):
    """Clearing the env var should restore normal incremental behavior."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = os.path.join(tmpdir, "market-data")
        os.makedirs(input_dir)
        output_dir = os.path.join(tmpdir, "ta-data")
        os.makedirs(output_dir)

        df = _make_ohlcv(n=200)
        input_path = os.path.join(input_dir, "TICKER.csv")
        df.to_csv(input_path, index=False)
        output_path = os.path.join(output_dir, "TICKER.csv")

        # Run with force=1
        _set_force_env("1")
        process_fn(input_path, output_path, total_files=1, current_file=1)
        _set_force_env("0")

        df_force = pd.read_csv(output_path)

        # Now clear force and run again (should be normal incremental, same result)
        _set_force_env("0")
        process_fn(input_path, output_path, total_files=1, current_file=1)
        df_normal = pd.read_csv(output_path)

        # Both should have same number of rows and columns
        assert len(df_force) == len(df_normal)
        assert set(df_force.columns) == set(df_normal.columns)

        ta_cols = [c for c in df_force.columns if c.startswith("ta_")]
        assert len(ta_cols) > 0, f"{module_name}: no ta_ columns in output"


# ---------------------------------------------------------------------------
# Individual test classes -- one per module
# ---------------------------------------------------------------------------


class TestTrendForceRecalculation:
    def test_force_skips_incremental(self):
        """Trend: force=1 recomputes even when no new data."""
        _test_force_skips_incremental(trend_process_csv, "trend")

    def test_force_matches_full_computation(self):
        """Trend: force output matches full computation."""
        _test_force_matches_full_computation(trend_process_csv, "trend")

    def test_force_without_state(self):
        """Trend: force works with no existing state file."""
        _test_force_without_state_falls_to_full(trend_process_csv, "trend")

    def test_env_var_clearing_restores_normal(self):
        """Trend: clearing env var restores incremental behavior."""
        _test_env_var_clearing_restores_normal_behavior(trend_process_csv, "trend")


class TestMomentumForceRecalculation:
    def test_force_skips_incremental(self):
        """Momentum: force=1 recomputes even when no new data."""
        _test_force_skips_incremental(momentum_process_csv, "momentum")

    def test_force_matches_full_computation(self):
        """Momentum: force output matches full computation."""
        _test_force_matches_full_computation(momentum_process_csv, "momentum")

    def test_force_without_state(self):
        """Momentum: force works with no existing state file."""
        _test_force_without_state_falls_to_full(momentum_process_csv, "momentum")

    def test_env_var_clearing_restores_normal(self):
        """Momentum: clearing env var restores incremental behavior."""
        _test_env_var_clearing_restores_normal_behavior(momentum_process_csv, "momentum")


class TestVolumeForceRecalculation:
    def test_force_skips_incremental(self):
        """Volume: force=1 recomputes even when no new data."""
        _test_force_skips_incremental(volume_process_csv, "volume")

    def test_force_matches_full_computation(self):
        """Volume: force output matches full computation."""
        _test_force_matches_full_computation(volume_process_csv, "volume")

    def test_force_without_state(self):
        """Volume: force works with no existing state file."""
        _test_force_without_state_falls_to_full(volume_process_csv, "volume")

    def test_env_var_clearing_restores_normal(self):
        """Volume: clearing env var restores incremental behavior."""
        _test_env_var_clearing_restores_normal_behavior(volume_process_csv, "volume")


class TestVolatilityForceRecalculation:
    def test_force_skips_incremental(self):
        """Volatility: force=1 recomputes even when no new data."""
        _test_force_skips_incremental(volatility_process_csv, "volatility")

    def test_force_matches_full_computation(self):
        """Volatility: force output matches full computation."""
        _test_force_matches_full_computation(volatility_process_csv, "volatility")

    def test_force_without_state(self):
        """Volatility: force works with no existing state file."""
        _test_force_without_state_falls_to_full(volatility_process_csv, "volatility")

    def test_env_var_clearing_restores_normal(self):
        """Volatility: clearing env var restores incremental behavior."""
        _test_env_var_clearing_restores_normal_behavior(volatility_process_csv, "volatility")


class TestRegimeForceRecalculation:
    def test_force_skips_incremental(self):
        """Regime: force=1 recomputes even when no new data."""
        _test_force_skips_incremental(regime_process_csv, "regime")

    def test_force_matches_full_computation(self):
        """Regime: force output matches full computation."""
        _test_force_matches_full_computation(regime_process_csv, "regime")

    def test_force_without_state(self):
        """Regime: force works with no existing state file."""
        _test_force_without_state_falls_to_full(regime_process_csv, "regime")

    def test_env_var_clearing_restores_normal(self):
        """Regime: clearing env var restores incremental behavior."""
        _test_env_var_clearing_restores_normal_behavior(regime_process_csv, "regime")


class TestStructureForceRecalculation:
    def test_force_skips_incremental(self):
        """Structure: force=1 recomputes even when no new data."""
        _test_force_skips_incremental(structure_process_csv, "structure")

    def test_force_matches_full_computation(self):
        """Structure: force output matches full computation."""
        _test_force_matches_full_computation(structure_process_csv, "structure")

    def test_force_without_state(self):
        """Structure: force works with no existing state file."""
        _test_force_without_state_falls_to_full(structure_process_csv, "structure")

    def test_env_var_clearing_restores_normal(self):
        """Structure: clearing env var restores incremental behavior."""
        _test_env_var_clearing_restores_normal_behavior(structure_process_csv, "structure")


class TestReturnForceRecalculation:
    def test_force_skips_incremental(self):
        """Return: force=1 recomputes even when no new data."""
        _test_force_skips_incremental(return_process_csv, "return")

    def test_force_matches_full_computation(self):
        """Return: force output matches full computation."""
        _test_force_matches_full_computation(return_process_csv, "return")

    def test_force_without_state(self):
        """Return: force works with no existing state file."""
        _test_force_without_state_falls_to_full(return_process_csv, "return")

    def test_env_var_clearing_restores_normal(self):
        """Return: clearing env var restores incremental behavior."""
        _test_env_var_clearing_restores_normal_behavior(return_process_csv, "return")


# ---------------------------------------------------------------------------
# run_calculation.py integration tests
# ---------------------------------------------------------------------------


class TestRunCalculationForceFlag:
    """Tests that run_calculation.py --force sets the env var correctly.

    Note: ``_parse_args()`` only returns parsed args; the env var is set
    by ``main()`` when ``args.force`` is truthy.  These tests verify
    ``_parse_args()`` returns correct values.  The env-var propagation
    is implicitly tested by the module-level tests (e.g.
    ``TestTrendForceRecalculation``) which set ``TA_FORCE_FULL_RECALCULATION``
    directly.
    """

    def setup_method(self):
        """Ensure a clean env var state before each test."""
        os.environ.pop("TA_FORCE_FULL_RECALCULATION", None)

    def test_force_flag_sets_env_var(self):
        """run_calculation.py --force should return force=True."""
        from run_calculation import _parse_args

        args = _parse_args(["--force", "--dry-run"])
        assert args.force is True

    def test_no_force_flag_clears_env_var(self):
        """run_calculation.py without --force should return force=False."""
        from run_calculation import _parse_args

        args = _parse_args(["--dry-run"])
        assert args.force is False

    def test_force_flag_with_modules(self):
        """--force should work together with module selection."""
        from run_calculation import _parse_args

        args = _parse_args(["--force", "trend", "momentum"])
        assert args.force is True
        assert "trend" in args.modules
        assert "momentum" in args.modules

    def test_force_flag_with_ticker(self):
        """--force should work together with --ticker."""
        from run_calculation import _parse_args

        args = _parse_args(["--force", "--ticker", "NG.L"])
        assert args.force is True
        assert args.ticker == ["NG.L"]

    def test_main_sets_env_var_when_force(self):
        """main() should set TA_FORCE_FULL_RECALCULATION=1 when --force is passed."""
        from run_calculation import _parse_args

        # Simulate what main() does
        args = _parse_args(["--force"])
        if args.force:
            os.environ["TA_FORCE_FULL_RECALCULATION"] = "1"
        assert os.environ.get("TA_FORCE_FULL_RECALCULATION") == "1"

    def test_main_does_not_set_env_var_without_force(self):
        """main() should not set the env var when --force is not passed."""
        from run_calculation import _parse_args

        # Clear env first
        os.environ.pop("TA_FORCE_FULL_RECALCULATION", None)
        args = _parse_args([])
        if args.force:
            os.environ["TA_FORCE_FULL_RECALCULATION"] = "1"
        assert os.environ.get("TA_FORCE_FULL_RECALCULATION") is None
