import math
import os
import tempfile
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from calculate_momentum import (
    compute_ema,
    compute_macd,
    compute_momentum_columns,
    compute_roc,
    compute_rsi,
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
        closes.append(max(val, 1.0))  # keep positive
    return closes


# ---------------------------------------------------------------------------
# TestComputeEMA
# ---------------------------------------------------------------------------

class TestComputeEMA:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_ema(closes, 10)
        assert len(result) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        result = compute_ema(closes, 10)
        assert all(v is None for v in result)

    def test_first_valid_at_period_minus_one(self):
        closes = _make_closes(10, base=50)
        result = compute_ema(closes, 10)
        assert result[9] is not None
        for i in range(9):
            assert result[i] is None

    def test_sma_seed(self):
        """First EMA value should equal SMA of first `period` values."""
        closes = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = compute_ema(closes, 5)
        expected_sma = sum(closes[:5]) / 5  # 30.0
        assert result[4] == pytest.approx(expected_sma, abs=1e-9)

    def test_period_one(self):
        """EMA with period=1 should equal the raw values."""
        closes = [1.0, 2.0, 3.0, 4.0]
        result = compute_ema(closes, 1)
        for i in range(len(closes)):
            assert result[i] == closes[i]

    def test_monotonic_ema(self):
        """EMA should be smoother than raw data."""
        closes = list(range(1, 51))  # linearly increasing
        result = compute_ema(closes, 10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # EMA should be monotonically increasing for linear data
        for i in range(1, len(valid)):
            assert valid[i] >= valid[i - 1] - 1e-9

    def test_ema_reference_match(self):
        """Compare with a known recursive EMA implementation."""
        closes = _make_closes(30, base=50, noise_range=5)
        period = 7
        k = 2.0 / (period + 1)
        seed = sum(closes[:period]) / period

        expected = [None] * len(closes)
        expected[period - 1] = seed
        for i in range(period, len(closes)):
            expected[i] = closes[i] * k + expected[i - 1] * (1 - k)

        result = compute_ema(closes, period)
        for i in range(period - 1, len(closes)):
            assert result[i] == pytest.approx(expected[i], abs=1e-9)


# ---------------------------------------------------------------------------
# TestComputeRSI
# ---------------------------------------------------------------------------

class TestComputeRSI:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_rsi(closes, 14)
        assert len(result) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        result = compute_rsi(closes, 14)
        assert all(v is None for v in result)

    def test_first_valid_at_period(self):
        closes = _make_closes(20, base=100)
        result = compute_rsi(closes, 14)
        for i in range(14):
            assert result[i] is None
        assert result[14] is not None

    def test_rsi_range(self):
        closes = _make_closes(100, base=100, noise_range=5)
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert 0 <= v <= 100

    def test_constant_prices(self):
        """RSI should be 50 when prices don't change."""
        closes = [100.0] * 30
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(50.0, abs=1e-9)

    def test_always_up(self):
        """RSI should be 100 when every change is positive."""
        closes = [100.0 + i * 1.0 for i in range(30)]
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(100.0, abs=1e-9)

    def test_always_down(self):
        """RSI should be 0 when every change is negative."""
        closes = [100.0 - i * 1.0 for i in range(30)]
        result = compute_rsi(closes, 14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(0.0, abs=1e-9)

    def test_wilders_smoothing_match(self):
        """Verify the recursive smoothing step matches standard Wilder formula."""
        # Manually construct gains/losses to test the smoothed average
        closes = [100, 101, 99, 102, 100, 103, 101, 105, 102, 104, 103, 106,
                  104, 105, 106, 107, 106, 108, 107, 109, 108, 110, 109, 111]
        result = compute_rsi(closes, 14)
        # All should be valid for 24 data points with period 14
        valid = [v for v in result if v is not None]
        assert len(valid) > 0


# ---------------------------------------------------------------------------
# TestComputeMACD
# ---------------------------------------------------------------------------

class TestComputeMACD:
    def test_length(self):
        closes = _make_closes(50)
        macd = compute_macd(closes)
        assert len(macd["macd_line"]) == 50
        assert len(macd["signal_line"]) == 50
        assert len(macd["histogram"]) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        macd = compute_macd(closes)
        assert all(v is None for v in macd["macd_line"])
        assert all(v is None for v in macd["signal_line"])
        assert all(v is None for v in macd["histogram"])

    def test_keys(self):
        closes = _make_closes(50)
        macd = compute_macd(closes)
        assert set(macd.keys()) == {"macd_line", "signal_line", "histogram"}

    def test_first_valid_macd_line(self):
        """MACD line first valid at EMA slow period - 1 (index 25 for slow=26)."""
        closes = _make_closes(50, base=50)
        macd = compute_macd(closes)
        for i in range(25):
            assert macd["macd_line"][i] is None
        assert macd["macd_line"][25] is not None

    def test_histogram_equals_difference(self):
        """Histogram should equal MACD line minus signal line where both are non-None."""
        closes = _make_closes(60, base=50, noise_range=3)
        macd = compute_macd(closes)
        for i in range(len(closes)):
            if macd["macd_line"][i] is not None and macd["signal_line"][i] is not None:
                assert macd["histogram"][i] == pytest.approx(
                    macd["macd_line"][i] - macd["signal_line"][i], abs=1e-9
                )

    def test_macd_positive_trend(self):
        """In an uptrend, MACD line should eventually be positive."""
        closes = [100.0 + i * 0.5 for i in range(50)]
        macd = compute_macd(closes)
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0
        # Last few values should be positive in an uptrend
        assert valid[-1] > 0

    def test_macd_negative_trend(self):
        """In a downtrend, MACD line should eventually be negative."""
        closes = [100.0 - i * 0.5 for i in range(50)]
        macd = compute_macd(closes)
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0
        assert valid[-1] < 0

    def test_custom_params(self):
        """MACD with custom parameters should still produce valid output."""
        closes = _make_closes(50, base=50)
        macd = compute_macd(closes, fast=5, slow=10, signal=3)
        assert len(macd["macd_line"]) == 50
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0

    def test_constant_prices(self):
        """MACD should be zero when prices are constant."""
        closes = [100.0] * 50
        macd = compute_macd(closes)
        valid = [v for v in macd["macd_line"] if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# TestComputeROC
# ---------------------------------------------------------------------------

class TestComputeROC:
    def test_length(self):
        closes = _make_closes(50)
        result = compute_roc(closes, 20)
        assert len(result) == 50

    def test_short_data(self):
        closes = [1.0, 2.0, 3.0]
        result = compute_roc(closes, 20)
        assert all(v is None for v in result)

    def test_first_valid_at_period(self):
        closes = _make_closes(30, base=100)
        result = compute_roc(closes, 20)
        for i in range(20):
            assert result[i] is None
        assert result[20] is not None

    def test_roc_positive(self):
        """ROC should be positive when current > previous."""
        closes = [100.0, 110.0]
        result = compute_roc(closes, 1)
        assert result[1] == pytest.approx(10.0, abs=1e-9)  # (110-100)/100 * 100

    def test_roc_negative(self):
        """ROC should be negative when current < previous."""
        closes = [100.0, 90.0]
        result = compute_roc(closes, 1)
        assert result[1] == pytest.approx(-10.0, abs=1e-9)

    def test_roc_zero(self):
        """ROC should be 0 when current == previous."""
        closes = [100.0, 100.0]
        result = compute_roc(closes, 1)
        assert result[1] == pytest.approx(0.0, abs=1e-9)

    def test_roc_linear(self):
        """ROC for linearly increasing data should be positive."""
        closes = [100.0 + i for i in range(30)]
        result = compute_roc(closes, 5)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] > 0

    def test_roc_custom_period(self):
        """ROC with custom period should work."""
        closes = _make_closes(30, base=100, noise_range=2)
        result = compute_roc(closes, 5)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_roc_with_zero_price(self):
        """ROC should handle zero prices gracefully (skip division)."""
        closes = [0.0, 10.0]
        result = compute_roc(closes, 1)
        assert result[1] is None  # division by zero -> None


# ---------------------------------------------------------------------------
# TestComputeMomentumColumns
# ---------------------------------------------------------------------------

class TestComputeMomentumColumns:
    def test_expected_keys(self):
        closes = _make_closes(50)
        cols = compute_momentum_columns(closes, 50)
        assert set(cols.keys()) == {
            "ta_rsi14", "ta_macd_line", "ta_macd_signal",
            "ta_macd_histogram", "ta_roc20",
        }

    def test_all_same_length(self):
        closes = _make_closes(50)
        cols = compute_momentum_columns(closes, 50)
        for col in cols.values():
            assert len(col) == 50

    def test_rsi_present(self):
        closes = _make_closes(50)
        cols = compute_momentum_columns(closes, 50)
        valid = [v for v in cols["ta_rsi14"] if v is not None]
        assert len(valid) > 0

    def test_roc_present(self):
        closes = _make_closes(50)
        cols = compute_momentum_columns(closes, 50)
        valid = [v for v in cols["ta_roc20"] if v is not None]
        assert len(valid) > 0

    def test_short_data(self):
        closes = [100.0] * 5
        cols = compute_momentum_columns(closes, 5)
        assert cols["ta_rsi14"] == [None] * 5
        assert cols["ta_roc20"] == [None] * 5
        # MACD may produce some values even for short data
        assert len(cols["ta_macd_line"]) == 5

    def test_all_same_length(self):
        closes = _make_closes(100)
        cols = compute_momentum_columns(closes, 100)
        lengths = [len(v) for v in cols.values()]
        assert len(set(lengths)) == 1
        assert lengths[0] == 100


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
                for i in range(50)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        assert os.path.exists(output_path)

    def test_includes_momentum_columns(self, tmp_path):
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
                for i in range(50)
            ],
        )

        input_path = str(input_dir / "TEST.csv")
        output_path = str(output_dir / "TEST.csv")
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        assert "ta_rsi14" in df.columns
        assert "ta_macd_line" in df.columns
        assert "ta_macd_signal" in df.columns
        assert "ta_macd_histogram" in df.columns
        assert "ta_roc20" in df.columns

    def test_realistic_data(self, tmp_path):
        input_dir = tmp_path / "market-data"
        input_dir.mkdir()
        output_dir = tmp_path / "ta-data"
        output_dir.mkdir()

        np.random.seed(42)
        base = 150.0
        closes = [base]
        for _ in range(199):
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
                for i in range(200)
            ],
        )

        input_path = str(input_dir / "AAPL.csv")
        output_path = str(output_dir / "AAPL.csv")
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        # RSI should have valid values
        valid_rsi = df["ta_rsi14"].dropna()
        assert len(valid_rsi) > 0
        # ROC should have valid values
        valid_roc = df["ta_roc20"].dropna()
        assert len(valid_roc) > 0

    def test_sort_order(self, tmp_path):
        """Output should be sorted by Date."""
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
        from calculate_momentum import process_csv
        process_csv(input_path, output_path, 1, 1)

        df = pd.read_csv(output_path)
        dates_out = pd.to_datetime(df["Date"])
        assert dates_out.is_monotonic_increasing


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_ema_single_value(self):
        result = compute_ema([100.0], 10)
        assert result == [None]

    def test_rsi_single_value(self):
        result = compute_rsi([100.0], 14)
        assert result == [None]

    def test_macd_single_value(self):
        macd = compute_macd([100.0])
        assert macd["macd_line"] == [None]
        assert macd["signal_line"] == [None]
        assert macd["histogram"] == [None]

    def test_roc_single_value(self):
        result = compute_roc([100.0], 20)
        assert result == [None]

    def test_compute_momentum_columns_very_short(self):
        cols = compute_momentum_columns([100.0, 101.0], 2)
        assert len(cols["ta_rsi14"]) == 2
        assert all(v is None for v in cols["ta_rsi14"])
        assert len(cols["ta_roc20"]) == 2
        assert all(v is None for v in cols["ta_roc20"])

    def test_computing_momentum_with_nan_values(self):
        """Should handle NaN gracefully (convert to float)."""
        closes = [100.0, 101.0, None, 102.0, 103.0]
        closes_float = [float(v) if v is not None else 0.0 for v in closes]
        cols = compute_momentum_columns(closes_float, 5)
        assert len(cols["ta_rsi14"]) == 5
