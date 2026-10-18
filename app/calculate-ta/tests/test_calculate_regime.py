"""Unit tests for calculate_regime.py — verifies GARCH(1,1) volatility and 3-state HMM regime detection."""

import math
import os
import warnings

import numpy as np
import pandas as pd
import pytest

warnings.filterwarnings("ignore")

from calculate_regime import (
    compute_garch_volatility,
    compute_hmm_regime,
    compute_regime_columns,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sample(n=200, base_price=100.0, base_range=2.0):
    """Generate aligned close prices for testing."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, base_range / 2)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


def _make_uptrend(n=200, base_price=100.0):
    """Generate a clear uptrend with some noise."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = 0.3 + np.random.normal(0, 1.0)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


def _make_downtrend(n=200, base_price=200.0):
    """Generate a clear downtrend with some noise."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = -0.3 + np.random.normal(0, 1.0)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


def _make_volatile(n=200, base_price=100.0):
    """Generate a high-volatility regime with no clear trend."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 5.0)
        closes.append(max(closes[-1] + change, 10.0))
    return closes


# ---------------------------------------------------------------------------
# TestComputeGarchVolatility
# ---------------------------------------------------------------------------


class TestComputeGarchVolatility:
    def test_length(self):
        closes = _make_sample(200)
        result = compute_garch_volatility(closes)
        assert len(result["ta_garch_vol"]) == 200
        assert len(result["ta_garch_sq"]) == 200

    def test_short_data_returns_none(self):
        closes = [100.0 + i for i in range(10)]
        result = compute_garch_volatility(closes)
        assert all(v is None for v in result["ta_garch_vol"])
        assert all(v is None for v in result["ta_garch_sq"])

    def test_first_element_none(self):
        closes = _make_sample(200)
        result = compute_garch_volatility(closes)
        assert result["ta_garch_vol"][0] is None
        assert result["ta_garch_sq"][0] is None

    def test_positive_volatility(self):
        closes = _make_sample(200)
        result = compute_garch_volatility(closes)
        valid_vol = [v for v in result["ta_garch_vol"] if v is not None]
        assert len(valid_vol) > 0
        assert all(v > 0 for v in valid_vol)

    def test_variance_equals_vol_squared(self):
        closes = _make_sample(200)
        result = compute_garch_volatility(closes)
        for i in range(len(closes)):
            vol = result["ta_garch_vol"][i]
            sq = result["ta_garch_sq"][i]
            if vol is not None:
                assert sq is not None
                assert sq == pytest.approx(vol ** 2, rel=1e-3)

    def test_uptrend_has_volatility(self):
        closes = _make_uptrend(300)
        result = compute_garch_volatility(closes)
        valid_vol = [v for v in result["ta_garch_vol"] if v is not None]
        assert len(valid_vol) > 0

    def test_constant_prices(self):
        closes = [100.0] * 50
        # Constant prices → all-zero log returns → GARCH optimizer warnings
        # (divide-by-zero, incompatibility constraints). Wrap to suppress
        # expected warnings for this pathological input.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = compute_garch_volatility(closes)
        # With constant prices, log returns are all zero; GARCH should still
        # produce some values (though small). At minimum it should not crash.
        assert len(result["ta_garch_vol"]) == 50

    def test_garch11_default(self):
        """Default p=1, q=1 should produce valid results."""
        closes = _make_sample(200)
        result = compute_garch_volatility(closes, p=1, q=1)
        valid_vol = [v for v in result["ta_garch_vol"] if v is not None]
        assert len(valid_vol) > 0

    def test_returns_match_log_returns_scale(self):
        """GARCH vol should be in a reasonable scale relative to returns."""
        closes = _make_sample(300)
        result = compute_garch_volatility(closes)
        valid_vol = [v for v in result["ta_garch_vol"] if v is not None]
        # With rescale=True in arch_model, conditional volatility is on the
        # original log-return scale; values should still be bounded.
        if valid_vol:
            assert max(valid_vol) < 3.0  # sanity check


# ---------------------------------------------------------------------------
# TestComputeHmmRegime
# ---------------------------------------------------------------------------


class TestComputeHmmRegime:
    def test_length(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        assert len(result["ta_hmm_regime"]) == 200
        assert len(result["ta_hmm_regime_prob_0"]) == 200
        assert len(result["ta_hmm_regime_prob_1"]) == 200
        assert len(result["ta_hmm_regime_prob_2"]) == 200

    def test_short_data_returns_none(self):
        closes = [100.0 + i for i in range(10)]
        result = compute_hmm_regime(closes, n_states=3)
        assert all(v is None for v in result["ta_hmm_regime"])

    def test_first_element_none(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        assert result["ta_hmm_regime"][0] is None
        assert result["ta_hmm_regime_prob_0"][0] is None

    def test_regime_values_are_valid(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        assert len(valid_regimes) > 0
        assert all(v in (0, 1, 2) for v in valid_regimes)

    def test_probabilities_sum_to_one(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        for i in range(1, len(closes)):  # skip first (None)
            p0 = result["ta_hmm_regime_prob_0"][i]
            p1 = result["ta_hmm_regime_prob_1"][i]
            p2 = result["ta_hmm_regime_prob_2"][i]
            if p0 is not None and p1 is not None and p2 is not None:
                total = p0 + p1 + p2
                assert total == pytest.approx(1.0, rel=1e-6)

    def test_probabilities_are_non_negative(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=3)
        for col in ["ta_hmm_regime_prob_0", "ta_hmm_regime_prob_1",
                     "ta_hmm_regime_prob_2"]:
            valid = [v for v in result[col] if v is not None]
            assert len(valid) > 0
            assert all(v >= 0.0 for v in valid)

    def test_multiple_regimes_detected(self):
        closes = _make_sample(500)
        result = compute_hmm_regime(closes, n_states=3)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        unique_regimes = set(valid_regimes)
        # Should detect at least 2 different regimes
        assert len(unique_regimes) >= 2

    def test_uptrend_has_bull_regime(self):
        closes = _make_uptrend(300)
        result = compute_hmm_regime(closes, n_states=3)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        assert 0 in valid_regimes  # Bull state should appear

    def test_volatile_regime_detected(self):
        closes = _make_volatile(300)
        result = compute_hmm_regime(closes, n_states=3)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        assert len(set(valid_regimes)) >= 2

    def test_two_state(self):
        closes = _make_sample(200)
        result = compute_hmm_regime(closes, n_states=2)
        valid_regimes = [v for v in result["ta_hmm_regime"] if v is not None]
        assert len(valid_regimes) > 0
        assert all(v in (0, 1) for v in valid_regimes)


# ---------------------------------------------------------------------------
# TestComputeRegimeColumns
# ---------------------------------------------------------------------------


class TestComputeRegimeColumns:
    def test_expected_keys(self):
        closes = _make_sample(200)
        cols = compute_regime_columns(closes, 200)
        expected = {
            "ta_garch_vol", "ta_garch_sq",
            "ta_hmm_regime",
            "ta_hmm_regime_prob_0", "ta_hmm_regime_prob_1", "ta_hmm_regime_prob_2",
        }
        assert set(cols.keys()) == expected

    def test_all_same_length(self):
        closes = _make_sample(200)
        cols = compute_regime_columns(closes, 200)
        for col in cols.values():
            assert len(col) == 200

    def test_short_data(self):
        closes = [100.0 + i for i in range(10)]
        cols = compute_regime_columns(closes, 10)
        assert all(v is None for v in cols["ta_garch_vol"])
        assert all(v is None for v in cols["ta_garch_sq"])
        assert all(v is None for v in cols["ta_hmm_regime"])

    def test_with_uptrend_data(self):
        closes = _make_uptrend(300)
        cols = compute_regime_columns(closes, 300)
        valid_vol = [v for v in cols["ta_garch_vol"] if v is not None]
        valid_regimes = [v for v in cols["ta_hmm_regime"] if v is not None]
        assert len(valid_vol) > 0
        assert len(valid_regimes) > 0

    def test_trim_to_n(self):
        """When n < len(closes), columns should be trimmed."""
        closes = _make_sample(200)
        cols = compute_regime_columns(closes, 100)
        for col in cols.values():
            assert len(col) == 100

    def test_padded_to_n(self):
        """When n > len(closes), columns should be padded with None."""
        closes = _make_sample(50)
        cols = compute_regime_columns(closes, 100)
        for col in cols.values():
            assert len(col) == 100


# ---------------------------------------------------------------------------
# TestProcessCSV
# ---------------------------------------------------------------------------


class TestProcessCSV:
    def _write_test_csv(self, directory, filename, rows):
        df = pd.DataFrame(rows)
        path = os.path.join(directory, filename)
        df.to_csv(path, index=False)
        return path

    def test_creates_output(self, tmp_path):
        from calculate_regime import process_csv

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
                for i in range(100)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        assert os.path.exists(output_path)

    def test_includes_regime_columns(self, tmp_path):
        from calculate_regime import process_csv

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
                for i in range(100)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_garch_vol" in df.columns
        assert "ta_garch_sq" in df.columns
        assert "ta_hmm_regime" in df.columns
        assert "ta_hmm_regime_prob_0" in df.columns
        assert "ta_hmm_regime_prob_1" in df.columns
        assert "ta_hmm_regime_prob_2" in df.columns

    def test_realistic_data(self, tmp_path):
        from calculate_regime import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(42)
        base = 150.0
        closes = [base]
        for _ in range(299):
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
                for i in range(300)
            ],
        )

        input_path = str(input_dir / "AAPL.csv")
        output_path = str(output_dir / "AAPL.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # GARCH vol should have valid values
        valid_garch = df["ta_garch_vol"].dropna()
        assert len(valid_garch) > 0
        # HMM regime should have valid values
        valid_regime = df["ta_hmm_regime"].dropna()
        assert len(valid_regime) > 0
        assert df["ta_hmm_regime"].dropna().isin([0, 1, 2]).all()

    def test_sort_order(self, tmp_path):
        from calculate_regime import process_csv

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
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        dates_out = pd.to_datetime(df["Date"])
        assert dates_out.is_monotonic_increasing

    def test_creates_own_columns_only(self, tmp_path):
        """process_csv writes only its own Date + regime columns, not merged with existing."""
        from calculate_regime import process_csv

        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        # Also write the input file
        self._write_test_csv(
            str(input_dir),
            "TEST.csv",
            [
                {"Date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                 "Open": 100.0, "High": 102.0, "Low": 99.0,
                 "Close": 100.0 + i * 0.5, "Volume": 1000000}
                for i in range(100)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # Should contain only Date + regime columns
        assert "Date" in df.columns
        assert "ta_garch_vol" in df.columns
        assert "ta_garch_sq" in df.columns
        assert "ta_hmm_regime" in df.columns
        # Should NOT contain columns from other modules (merge is done at orchestration level)
        assert "ta_rsi14" not in df.columns
        assert "ta_macd_line" not in df.columns
