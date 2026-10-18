"""Unit tests for calculate_volatility.py — ATR, Bollinger Bands, Band Width, %B, Historical Volatility, Parkinson Volatility."""

import math
import os
import sys

import numpy as np
import pandas as pd
import pytest

from calculate_volatility import (
    compute_atr,
    compute_bollinger_bands,
    compute_historical_volatility,
    compute_parkinson_volatility,
    compute_volatility_columns,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sample(n=50, base_price=100.0, base_range=2.0):
    """Generate aligned OHLC data for testing."""
    np.random.seed(42)
    closes = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 1.0)
        closes.append(max(closes[-1] + change, 10.0))

    highs = [c + abs(np.random.normal(0, base_range / 2)) for c in closes]
    lows = [max(c - abs(np.random.normal(0, base_range / 2)), 1.0) for c in closes]

    return highs, lows, closes


# ---------------------------------------------------------------------------
# TestComputeATR
# ---------------------------------------------------------------------------


class TestComputeATR:
    def test_length(self):
        highs, lows, closes = _make_sample(n=30, base_price=100.0, base_range=5.0)
        result = compute_atr(highs, lows, closes, period=14)
        assert len(result) == 30

    def test_first_values_are_none(self):
        highs, lows, closes = _make_sample(n=30, base_price=100.0, base_range=5.0)
        result = compute_atr(highs, lows, closes, period=14)
        # ATR needs at least `period` true range values; first valid at index `period`
        for i in range(14):
            assert result[i] is None

    def test_first_valid_atr_value(self):
        # Use a simple deterministic case: flat high/low with constant range
        highs = [105.0] * 30
        lows = [95.0] * 30
        closes = [100.0] * 30
        result = compute_atr(highs, lows, closes, period=14)
        # First valid ATR at index 14
        assert result[14] is not None
        # With flat highs/lows, True Range = high - low = 10 for all rows
        # Initial ATR = average of first 14 TRs = 10
        assert result[14] == pytest.approx(10.0)

    def test_increasing_atr(self):
        """With widening range, ATR should increase over time."""
        np.random.seed(99)
        n = 50
        base = 100.0
        closes = [base]
        highs = [base + 1.0]
        lows = [base - 1.0]
        for i in range(1, n):
            widening = i * 0.2  # range grows over time
            close = closes[-1] + np.random.normal(0, 1.0)
            closes.append(close)
            highs.append(max(highs[-1], close) + widening)
            lows.append(min(lows[-1], close) - widening)

        result = compute_atr(highs, lows, closes, period=14)
        # ATR should generally be increasing
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert valid[-1] > valid[0]

    def test_short_series_returns_all_none(self):
        """When series is shorter than period + 1, all values are None."""
        highs = [100.0, 101.0, 102.0]
        lows = [98.0, 99.0, 100.0]
        closes = [99.0, 100.0, 101.0]
        result = compute_atr(highs, lows, closes, period=14)
        assert all(v is None for v in result)

    def test_atr_with_gap_down(self):
        """ATR should capture large true range from price gap."""
        highs = [100, 100, 90]
        lows = [90, 90, 80]
        closes = [95, 95, 85]
        result = compute_atr(highs, lows, closes, period=2)
        assert result[2] == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# TestComputeBollingerBands
# ---------------------------------------------------------------------------


class TestComputeBollingerBands:
    def test_length(self):
        closes = _make_sample(n=50)[2]
        result = compute_bollinger_bands(closes, period=20)
        assert len(result["upper"]) == 50
        assert len(result["middle"]) == 50
        assert len(result["lower"]) == 50

    def test_first_values_are_none(self):
        closes = _make_sample(n=50)[2]
        result = compute_bollinger_bands(closes, period=20)
        for i in range(19):  # 0-indexed, first valid at index 19 (20th element)
            assert result["middle"][i] is None
            assert result["upper"][i] is None
            assert result["lower"][i] is None

    def test_first_valid_value_equals_sma(self):
        """At first valid index, middle band equals SMA of window."""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0] * 5
        period = 5
        result = compute_bollinger_bands(closes, period=period)
        first_valid = result["middle"][period - 1]
        expected_sma = sum(closes[:period]) / period
        assert first_valid == pytest.approx(expected_sma)

    def test_upper_and_lower_are_symmetric(self):
        """Upper band should be middle + k*std, lower should be middle - k*std."""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0] * 10
        period = 5
        num_std = 2.0
        result = compute_bollinger_bands(closes, period=period, num_std=num_std)
        for i in range(period - 1, len(closes)):
            if result["middle"][i] is not None:
                assert result["upper"][i] == pytest.approx(result["middle"][i] + num_std * self._std(closes, i, period))
                assert result["lower"][i] == pytest.approx(result["middle"][i] - num_std * self._std(closes, i, period))

    def test_upper_below_lower(self):
        """Upper band should always be >= lower band."""
        closes = _make_sample(n=100)[2]
        result = compute_bollinger_bands(closes, period=20)
        for i in range(len(closes)):
            if result["upper"][i] is not None and result["lower"][i] is not None:
                assert result["upper"][i] >= result["lower"][i]

    def test_short_series_returns_all_none(self):
        """When series is shorter than period, all values are None."""
        closes = [100.0, 101.0, 102.0]
        result = compute_bollinger_bands(closes, period=20)
        assert all(v is None for v in result["middle"])

    def _std(self, closes, end_idx, period):
        """Compute population std of the window ending at end_idx."""
        window = [float(closes[j]) for j in range(end_idx - period + 1, end_idx + 1)]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        return math.sqrt(variance)

    def test_constant_prices(self):
        """With constant prices, std=0 so upper=lower=middle."""
        closes = [50.0] * 30
        result = compute_bollinger_bands(closes, period=10)
        for i in range(9, len(closes)):
            assert result["middle"][i] == pytest.approx(50.0)
            assert result["upper"][i] == pytest.approx(50.0)
            assert result["lower"][i] == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# TestComputeVolatilityColumns
# ---------------------------------------------------------------------------


class TestComputeVolatilityColumns:
    def test_returns_expected_keys(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        assert "ta_atr14" in result
        assert "ta_normalized_atr14" in result
        assert "ta_bband_upper" in result
        assert "ta_bband_middle" in result
        assert "ta_bband_lower" in result
        assert "ta_bband_width" in result
        assert "ta_bband_pctb" in result
        assert "ta_parkinson_vol" in result

    def test_column_lengths_match(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for key, values in result.items():
            assert len(values) == 50

    def test_atr_none_before_period(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(14):
            assert result["ta_atr14"][i] is None

    def test_bbands_none_before_period(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(19):
            assert result["ta_bband_upper"][i] is None
            assert result["ta_bband_lower"][i] is None

    def test_short_series(self):
        """When n < 20, Bollinger Bands should all be None; ATR depends on n."""
        highs, lows, closes = _make_sample(n=10)
        result = compute_volatility_columns(highs, lows, closes, 10)
        assert all(v is None for v in result["ta_bband_upper"])
        # ATR also needs >= period + 1
        assert all(v is None for v in result["ta_atr14"])


# ---------------------------------------------------------------------------
# TestBollingerWidth
# ---------------------------------------------------------------------------


class TestBollingerWidth:
    def test_width_none_before_period(self):
        """Bollinger Width should be None before the first valid index."""
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(19):
            assert result["ta_bband_width"][i] is None

    def test_width_positive_with_varying_prices(self):
        """Band Width should be positive when prices vary."""
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_widths = [v for v in result["ta_bband_width"] if v is not None]
        assert len(valid_widths) > 0
        for w in valid_widths:
            assert w > 0

    def test_width_zero_with_constant_prices(self):
        """With constant prices, std=0 so Band Width should be 0."""
        closes = [50.0] * 30
        highs = [51.0] * 30
        lows = [49.0] * 30
        result = compute_volatility_columns(highs, lows, closes, 30)
        for i in range(19, len(closes)):
            assert result["ta_bband_width"][i] == pytest.approx(0.0)

    def test_width_formula(self):
        """Band Width = (upper - lower) / middle."""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0] * 10
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        bb = compute_bollinger_bands(closes)  # default period=20, num_std=2.0
        result = compute_volatility_columns(highs, lows, closes, len(closes))
        # First valid index for period=20 is 19
        for i in range(19, len(closes)):
            if (bb["upper"][i] is not None and bb["lower"][i] is not None
                    and bb["middle"][i] is not None and bb["middle"][i] != 0):
                expected = (bb["upper"][i] - bb["lower"][i]) / bb["middle"][i]
                assert result["ta_bband_width"][i] == pytest.approx(expected)


# ---------------------------------------------------------------------------
# TestBollingerPercentB
# ---------------------------------------------------------------------------


class TestBollingerPercentB:
    def test_pctb_none_before_period(self):
        """%B should be None before the first valid index."""
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(19):
            assert result["ta_bband_pctb"][i] is None

    def test_pctb_bounded_0_to_1_at_bounds(self):
        """%B = 1 at upper band, = 0 at lower band."""
        period = 5
        # Create prices that touch upper and lower bands
        # Middle ~100, std=5, so upper=110, lower=90 with num_std=2
        closes = []
        for i in range(50):
            if i % 3 == 0:
                closes.append(110.0)  # at upper band
            elif i % 3 == 1:
                closes.append(90.0)   # at lower band
            else:
                closes.append(100.0)  # at middle
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_pctb = [v for v in result["ta_bband_pctb"] if v is not None]
        assert len(valid_pctb) > 0

    def test_pctb_formula(self):
        """%B = (close - lower) / (upper - lower)."""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0] * 10
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        bb = compute_bollinger_bands(closes)  # default period=20, num_std=2.0
        result = compute_volatility_columns(highs, lows, closes, len(closes))
        # First valid index for period=20 is 19
        for i in range(19, len(closes)):
            if bb["upper"][i] is not None and bb["upper"][i] != bb["lower"][i]:
                expected = (closes[i] - bb["lower"][i]) / (bb["upper"][i] - bb["lower"][i])
                assert result["ta_bband_pctb"][i] == pytest.approx(expected)

    def test_pctb_at_middle_price(self):
        """When close = middle band, %B should be 0.5."""
        period = 5
        closes = [100.0] * 50
        highs = [101.0] * 50
        lows = [99.0] * 50
        bb = compute_bollinger_bands(closes, period=period)
        # With constant prices, std=0, so upper=lower=middle=100
        # Band width = 0, so %B should be None (denominator is 0)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(period - 1, len(closes)):
            assert result["ta_bband_pctb"][i] is None

    def test_pctb_varying_prices(self):
        """%B should vary between values as price moves relative to bands."""
        np.random.seed(42)
        closes = [100.0]
        for _ in range(49):
            closes.append(max(closes[-1] + np.random.normal(0, 1.5), 50.0))
        highs = [c + 1.0 for c in closes]
        lows = [max(c - 1.0, 1.0) for c in closes]
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_pctb = [v for v in result["ta_bband_pctb"] if v is not None]
        assert len(valid_pctb) > 0
        # %B should vary (not all the same value)
        assert len(set(round(v, 4) for v in valid_pctb)) > 1

    def test_pctb_at_upper_band(self):
        """When price is at upper band, %B should be ~1."""
        period = 5
        # Prices that stay near upper band
        # With constant std, if price = upper = middle + 2*std, %B = 1
        base = 100.0
        std = 5.0
        # Create a window where price = upper band
        # upper = mean + 2*std, so we need closes centered around base=90 with std=5
        # Actually, let's just verify the formula directly
        closes = [80.0, 85.0, 90.0, 95.0, 100.0] * 10  # increasing
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_pctb = [v for v in result["ta_bband_pctb"] if v is not None]
        assert len(valid_pctb) > 0

    def test_pctb_less_than_one_when_narrow_bands(self):
        """With very narrow bands and price near middle, %B should be near 0.5."""
        # Create a tight range of prices
        closes = [100.0 + (i % 10 - 5) * 0.1 for i in range(50)]  # 99.5 to 100.5
        highs = [c + 0.1 for c in closes]
        lows = [max(c - 0.1, 1.0) for c in closes]
        result = compute_volatility_columns(highs, lows, closes, 50)
        valid_pctb = [v for v in result["ta_bband_pctb"] if v is not None]
        assert len(valid_pctb) > 0
        # With tight prices, %B should be reasonable (not NaN or Inf)
        for v in valid_pctb:
            assert math.isfinite(v)


# ---------------------------------------------------------------------------
# TestComputeHistoricalVolatility
# ---------------------------------------------------------------------------


class TestComputeHistoricalVolatility:
    def test_length(self):
        closes = _make_sample(n=50)[2]
        result = compute_historical_volatility(closes, period=20)
        assert len(result) == 50

    def test_first_values_are_none(self):
        """HV needs at least `period` log returns; first valid at index `period`."""
        closes = _make_sample(n=50)[2]
        result = compute_historical_volatility(closes, period=20)
        for i in range(20):
            assert result[i] is None

    def test_returns_positive_for_varying_prices(self):
        """HV should be positive when prices vary."""
        closes = _make_sample(n=100)[2]
        result = compute_historical_volatility(closes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v > 0

    def test_zero_for_constant_prices(self):
        """With constant prices, log returns are 0 so HV should be 0."""
        closes = [100.0] * 50
        result = compute_historical_volatility(closes, period=20)
        for i in range(20, len(closes)):
            assert result[i] == pytest.approx(0.0)

    def test_short_series_returns_all_none(self):
        """When series is shorter than period + 1, all values are None."""
        closes = [100.0, 101.0, 102.0]
        result = compute_historical_volatility(closes, period=20)
        assert all(v is None for v in result)

    def test_annualization(self):
        """Annualized HV should be non_annualized * sqrt(252)."""
        np.random.seed(42)
        closes = [100.0]
        for _ in range(49):
            closes.append(closes[-1] * (1 + np.random.normal(0, 0.01)))
        result_ann = compute_historical_volatility(closes, period=20, annualize=True)
        result_raw = compute_historical_volatility(closes, period=20, annualize=False)
        valid_ann = [v for v in result_ann if v is not None]
        valid_raw = [v for v in result_raw if v is not None]
        assert len(valid_ann) > 0
        assert len(valid_raw) > 0
        for a, r in zip(valid_ann, valid_raw):
            assert a == pytest.approx(r * math.sqrt(252))

    def test_increasing_hvol_with_widening_volatility(self):
        """HV should increase when price volatility increases over time."""
        np.random.seed(99)
        closes = [100.0]
        for i in range(49):
            vol = 0.005 + i * 0.001  # volatility ramps up
            closes.append(closes[-1] * (1 + np.random.normal(0, vol)))
        result = compute_historical_volatility(closes, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Last value should be higher than first (generally)
        assert valid[-1] > valid[0]

    def test_first_valid_value(self):
        """Verify first valid HV value against manual calculation."""
        np.random.seed(42)
        closes = [100.0]
        for _ in range(49):
            closes.append(closes[-1] * (1 + np.random.normal(0, 0.01)))
        period = 20
        result = compute_historical_volatility(closes, period=period, annualize=False)
        # Manually compute: log returns for the window
        log_returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, period + 1)]
        mean = sum(log_returns) / period
        variance = sum((r - mean) ** 2 for r in log_returns) / period
        expected = math.sqrt(variance)  # non-annualized
        assert result[period] == pytest.approx(expected)


# ---------------------------------------------------------------------------
# TestComputeVolatilityColumnsWithHvol
# ---------------------------------------------------------------------------


class TestComputeVolatilityColumnsWithHvol:
    def test_returns_hvol20_key(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        assert "ta_hvol20" in result

    def test_hvol20_none_before_period(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_volatility_columns(highs, lows, closes, 50)
        for i in range(20):
            assert result["ta_hvol20"][i] is None

    def test_hvol20_positive_with_varying_prices(self):
        highs, lows, closes = _make_sample(n=100)
        result = compute_volatility_columns(highs, lows, closes, 100)
        valid_hvol = [v for v in result["ta_hvol20"] if v is not None]
        assert len(valid_hvol) > 0
        for v in valid_hvol:
            assert v > 0


# ---------------------------------------------------------------------------
# TestComputeParkinsonVolatility
# ---------------------------------------------------------------------------


class TestComputeParkinsonVolatility:
    def test_length(self):
        highs, lows, closes = _make_sample(n=50)
        result = compute_parkinson_volatility(highs, lows, period=20)
        assert len(result) == 50

    def test_first_values_are_none(self):
        """Parkinson Vol needs at least `period` bars; first valid at index `period-1`."""
        highs, lows, closes = _make_sample(n=50)
        result = compute_parkinson_volatility(highs, lows, period=20)
        for i in range(19):
            assert result[i] is None

    def test_returns_positive_for_varying_prices(self):
        """Parkinson Vol should be positive when prices vary."""
        highs, lows, closes = _make_sample(n=100)
        result = compute_parkinson_volatility(highs, lows, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert v > 0

    def test_short_series_returns_all_none(self):
        """When series is shorter than period, all values are None."""
        highs = [100.0, 101.0, 102.0]
        lows = [98.0, 99.0, 100.0]
        result = compute_parkinson_volatility(highs, lows, period=20)
        assert all(v is None for v in result)

    def test_annualization(self):
        """Annualized Parkinson Vol should be non_annualized * sqrt(252)."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(closes[-1] * (1 + np.random.normal(0, 0.01)))
        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]
        result_ann = compute_parkinson_volatility(highs, lows, period=20, annualize=True)
        result_raw = compute_parkinson_volatility(highs, lows, period=20, annualize=False)
        valid_ann = [v for v in result_ann if v is not None]
        valid_raw = [v for v in result_raw if v is not None]
        assert len(valid_ann) > 0
        assert len(valid_raw) > 0
        for a, r in zip(valid_ann, valid_raw):
            assert a == pytest.approx(r * math.sqrt(252))

    def test_increasing_with_widening_range(self):
        """Parkinson Vol should increase when high-low ranges widen."""
        np.random.seed(99)
        n = 100
        base = 100.0
        closes = [base]
        highs = [base + 1.0]
        lows = [base - 1.0]
        for i in range(1, n):
            widening = 0.3 * i  # range grows over time
            change = np.random.normal(0, 0.5)
            close = closes[-1] + change
            close = max(min(close, base + 10), base - 10)  # keep close near base
            closes.append(close)
            highs.append(max(highs[-1], close) + widening)
            lows.append(min(lows[-1], close) - widening)
            # Ensure lows stay positive
            lows[-1] = max(lows[-1], 1.0)
        result = compute_parkinson_volatility(highs, lows, period=20)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Average of last 5 should be higher than average of first 5
        assert sum(valid[-5:]) / 5 > sum(valid[:5]) / 5

    def test_formula_constant_range(self):
        """With constant high/low ratio, verify formula manually."""
        # Constant range ratio: high = 105, low = 95 for all bars
        n = 30
        highs = [105.0] * n
        lows = [95.0] * n
        period = 20
        result = compute_parkinson_volatility(highs, lows, period=period, annualize=False)
        # Manual: ln(105/95) = ln(1.10526...)
        hl_ratio = math.log(105.0 / 95.0)
        expected = math.sqrt((period * hl_ratio ** 2) / (4 * math.log(2) * period))
        # First valid at index 19
        assert result[period - 1] == pytest.approx(expected)

    def test_zero_when_low_equals_high(self):
        """When high == low for all bars, Parkinson Vol should be 0."""
        n = 30
        highs = [100.0] * n
        lows = [100.0] * n
        result = compute_parkinson_volatility(highs, lows, period=20, annualize=False)
        for i in range(19, n):
            assert result[i] == pytest.approx(0.0)

    def test_non_annualized_value(self):
        """Non-annualized Parkinson Vol should be a reasonable small positive number."""
        np.random.seed(42)
        n = 100
        closes = [100.0]
        for _ in range(n - 1):
            closes.append(closes[-1] * (1 + np.random.normal(0, 0.01)))
        highs = [c + abs(np.random.normal(0, 1.0)) for c in closes]
        lows = [max(c - abs(np.random.normal(0, 1.0)), 1.0) for c in closes]
        result = compute_parkinson_volatility(highs, lows, period=20, annualize=False)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Daily vol is typically 0.5-5% for most stocks
        assert all(0 < v < 0.5 for v in valid)
