"""Unit tests for download_stock_info.py — P/E ratio, dividend yield, and fundamental metrics.

Tests cover:
- EPS series cleaning and normalization
- TTM EPS calculation (4-quarter rolling sum)
- TTM dividend calculation (365-day sliding window)
- Currency normalization (GBp → GBP)
- Fundamental metrics extraction from stock.info
- Full pipeline via mocked yfinance
"""

from datetime import datetime

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

import download_stock_info as mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_eps_series(dates: list[str], values: list[float]) -> pd.Series:
    """Create an EPS Series indexed by date, sorted ascending."""
    idx = pd.DatetimeIndex(pd.to_datetime(dates)).sort_values()
    return pd.Series(values[:len(idx)], index=idx, name="EPS")


def _make_price_df(dates: list[str], close: list[float]) -> pd.DataFrame:
    """Create a DataFrame of price dates and close prices."""
    return pd.DataFrame({
        "Date": pd.to_datetime(dates),
        "Close": close,
    })


def _make_dividend_series(dates: list[str], values: list[float]) -> pd.Series:
    """Create a dividend Series indexed by date, sorted ascending."""
    idx = pd.DatetimeIndex(pd.to_datetime(dates)).sort_values()
    return pd.Series(values[:len(idx)], index=idx, name="Dividend")


# ---------------------------------------------------------------------------
# _clean_eps_series
# ---------------------------------------------------------------------------

class TestCleanEpSeries:
    """Tests for _clean_eps_series."""

    def test_empty_series(self):
        s = pd.Series(dtype=float)
        result = mod._clean_eps_series(s)
        assert result.empty

    def test_sorts_by_date(self):
        """_clean_eps_series should sort by date."""
        dates = ["2024-06-30", "2023-12-31", "2024-03-31", "2023-09-30"]
        values = [1.0, 2.0, 3.0, 4.0]
        raw = pd.Series(values, index=pd.to_datetime(dates), name="EPS")
        result = mod._clean_eps_series(raw)
        assert list(result.index) == sorted(pd.to_datetime(dates))

    def test_drops_nans(self):
        dates = ["2024-01-01", "2024-04-01", "2024-07-01"]
        values = [1.0, None, 3.0]
        s = pd.Series(values, index=pd.to_datetime(dates), name="EPS")
        result = mod._clean_eps_series(s)
        assert len(result) == 2
        assert pd.isna(result).sum() == 0

    def test_tz_naive_index(self):
        """Ensure timezone info is stripped."""
        dates = ["2024-01-01", "2024-04-01"]
        values = [1.0, 2.0]
        s = pd.Series(values, index=pd.to_datetime(dates, utc=True), name="EPS")
        result = mod._clean_eps_series(s)
        assert result.index.tz is None


# ---------------------------------------------------------------------------
# compute_ttm_eps
# ---------------------------------------------------------------------------

class TestComputeTtmEps:
    """Tests for compute_ttm_eps."""

    def test_exact_four_quarters(self):
        dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        values = [1.0, 1.5, 2.0, 2.5]
        s = _make_eps_series(dates, values)
        result = mod.compute_ttm_eps(s)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[2])
        assert result.iloc[3] == 7.0

    def test_more_than_four_quarters(self):
        dates = [
            "2022-03-31", "2022-06-30", "2022-09-30",
            "2022-12-31", "2023-03-31", "2023-06-30",
        ]
        values = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        s = _make_eps_series(dates, values)
        result = mod.compute_ttm_eps(s)
        # Index 3: sum of [1.0, 1.1, 1.2, 1.3] = 4.6
        assert result.iloc[3] == 4.6
        # Index 5: sum of [1.2, 1.3, 1.4, 1.5] = 5.4
        assert result.iloc[5] == 5.4

    def test_less_than_four_quarters(self):
        dates = ["2023-03-31", "2023-06-30", "2023-09-30"]
        values = [1.0, 1.5, 2.0]
        s = _make_eps_series(dates, values)
        result = mod.compute_ttm_eps(s)
        assert all(pd.isna(result))

    def test_with_nan_in_window(self):
        """NaN values in EPS window should be dropped from sum."""
        dates = [
            "2022-03-31", "2022-06-30", "2022-09-30",
            "2022-12-31", "2023-03-31",
        ]
        values = [1.0, 1.1, None, 1.3, 1.4]
        s = _make_eps_series(dates, values)
        result = mod.compute_ttm_eps(s)
        # Index 4: window is iloc[1:5] = [1.1, NaN, 1.3, 1.4]
        # Non-NaN sum = 1.1 + 1.3 + 1.4 = 3.8
        assert result.iloc[4] == 3.8

    def test_negative_eps(self):
        """Negative EPS should not be counted as valid TTM."""
        dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        values = [-1.0, -1.5, -2.0, -2.5]
        s = _make_eps_series(dates, values)
        result = mod.compute_ttm_eps(s)
        assert all(pd.isna(result))

    def test_mixed_positive_negative(self):
        """Window with mixed signs."""
        dates = [
            "2022-03-31", "2022-06-30", "2022-09-30",
            "2022-12-31", "2023-03-31",
        ]
        values = [-1.0, -1.1, 5.0, 6.0, 7.0]
        s = _make_eps_series(dates, values)
        result = mod.compute_ttm_eps(s)
        # Index 3: [-1.0, -1.1, 5.0, 6.0] = 8.9
        assert result.iloc[3] == 8.9
        # Index 4: [-1.1, 5.0, 6.0, 7.0] = 16.9
        assert result.iloc[4] == 16.9

    def test_empty_series(self):
        s = pd.Series(dtype=float)
        result = mod.compute_ttm_eps(s)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# compute_ttm_dividends
# ---------------------------------------------------------------------------

class TestComputeTtmDividends:
    """Tests for compute_ttm_dividends."""

    def test_no_dividends(self):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        divs = pd.Series(dtype=float)
        result = mod.compute_ttm_dividends(dates, divs)
        assert all(pd.isna(result))

    def test_single_dividend_within_window(self):
        """One dividend payout within the price date range."""
        price_dates = pd.date_range("2024-01-01", periods=15, freq="D")
        dividends = _make_dividend_series(["2024-01-10"], [0.50])
        result = mod.compute_ttm_dividends(price_dates, dividends)
        # Before dividend (indices 0-8): None
        for i in range(9):
            assert pd.isna(result.iloc[i]), f"Expected NaN at index {i}, got {result.iloc[i]}"
        # On/after dividend (indices 9+): 0.50
        for i in range(9, 15):
            assert result.iloc[i] == 0.50, f"Expected 0.50 at index {i}, got {result.iloc[i]}"

    def test_multiple_dividends_accumulating(self):
        """Multiple dividends accumulate within window."""
        # Price dates: 2024-01-01, 02-01, 03-01, 04-01, 05-01
        price_dates = pd.date_range("2024-01-01", periods=5, freq="MS")
        # Dividends: 2024-01-15, 2024-04-15
        dividends = _make_dividend_series(
            ["2024-01-15", "2024-04-15"],
            [0.25, 0.25],
        )
        result = mod.compute_ttm_dividends(price_dates, dividends)
        # 2024-01-01: no div yet -> None
        assert pd.isna(result.iloc[0])
        # 2024-02-01: 2024-01-15 div happened -> 0.25
        assert result.iloc[1] == 0.25
        # 2024-03-01: same -> 0.25
        assert result.iloc[2] == 0.25
        # 2024-04-01: same -> 0.25
        assert result.iloc[3] == 0.25
        # 2024-05-01: both -> 0.50
        assert result.iloc[4] == 0.50

    def test_dividend_falls_off_window(self):
        """Dividend older than 365 days should be excluded."""
        price_dates = pd.date_range("2023-06-01", periods=800, freq="D")
        dividends = _make_dividend_series(
            ["2023-06-15", "2023-12-15"],
            [1.00, 0.50],
        )
        result = mod.compute_ttm_dividends(price_dates, dividends)

        # 2023-06-02 (idx 1): no div yet -> None
        assert pd.isna(result.iloc[1])
        # 2023-06-16 (idx 15): 2023-06-15 div -> 1.00
        assert result.iloc[15] == 1.00
        # 2023-12-16 (idx 199): both -> 1.50
        assert result.iloc[199] == 1.50

        # After 365 days from first div (~2024-06-15), first falls off -> 0.50
        around_idx = 380
        assert result.iloc[around_idx] == 0.50

        # After 365 days from second div (~2024-12-15), all None
        late_idx = 700
        assert pd.isna(result.iloc[late_idx])

    def test_empty_price_dates(self):
        divs = _make_dividend_series(["2024-01-15"], [0.50])
        result = mod.compute_ttm_dividends(pd.DatetimeIndex([]), divs)
        assert len(result) == 0

    def test_dividend_after_last_price_date(self):
        """Dividend after price dates should not affect result."""
        price_dates = pd.date_range("2024-01-01", periods=5, freq="D")
        dividends = _make_dividend_series(["2024-12-15"], [0.50])
        result = mod.compute_ttm_dividends(price_dates, dividends)
        assert all(pd.isna(result))

    def test_dividend_on_exact_price_date(self):
        """Dividend on the same day as a price date should count."""
        price_dates = pd.date_range("2024-01-01", periods=5, freq="D")
        dividends = _make_dividend_series(["2024-01-04"], [0.75])
        result = mod.compute_ttm_dividends(price_dates, dividends)
        assert pd.isna(result.iloc[0])  # Jan 1
        assert pd.isna(result.iloc[1])  # Jan 2
        assert pd.isna(result.iloc[2])  # Jan 3
        assert result.iloc[3] == 0.75   # Jan 4

    def test_two_year_window(self):
        """Verify sliding window over two years."""
        price_dates = pd.date_range("2023-01-01", periods=730, freq="D")
        dividends = _make_dividend_series(
            [
                "2023-03-15", "2023-06-15", "2023-09-15", "2023-12-15",
                "2024-03-15", "2024-06-15", "2024-09-15", "2024-12-15",
            ],
            [0.25, 0.25, 0.25, 0.25, 0.27, 0.27, 0.27, 0.27],
        )
        result = mod.compute_ttm_dividends(price_dates, dividends)
        end_idx = 729
        assert result.iloc[end_idx] == 1.08


# ---------------------------------------------------------------------------
# fetch_historical_dividends
# ---------------------------------------------------------------------------

class TestFetchHistoricalDividends:
    """Tests for fetch_historical_dividends."""

    def _make_hist_df(self, dates: list[str], divs: list[float]) -> pd.DataFrame:
        return pd.DataFrame({
            "Close": [100.0] * len(dates),
            "Dividends": divs,
        }, index=pd.to_datetime(dates))

    def test_empty_history(self):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        result = mod.fetch_historical_dividends(mock_ticker)
        assert result.empty

    def test_no_dividend_payouts(self):
        dates = ["2024-01-01", "2024-04-01", "2024-07-01"]
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = self._make_hist_df(dates, [0, 0, 0])
        result = mod.fetch_historical_dividends(mock_ticker)
        assert result.empty

    def test_with_dividend_payouts(self):
        dates = ["2024-01-15", "2024-04-15", "2024-07-15", "2024-10-15"]
        divs = [0.0, 0.25, 0.0, 0.30]
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = self._make_hist_df(dates, divs)
        result = mod.fetch_historical_dividends(mock_ticker)
        assert len(result) == 2
        assert result.iloc[0] == 0.25
        assert result.iloc[1] == 0.30

    def test_sorts_ascending(self):
        dates = ["2024-07-15", "2024-01-15", "2024-10-15", "2024-04-15"]
        divs = [0.0, 0.25, 0.30, 0.20]
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = self._make_hist_df(dates, divs)
        result = mod.fetch_historical_dividends(mock_ticker)
        # Non-zero: 2024-01-15 (0.25), 2024-04-15 (0.20), 2024-10-15 (0.30) = 3
        assert len(result) == 3
        assert result.index[0] < result.index[1] < result.index[2]


# ---------------------------------------------------------------------------
# calculate_pe_for_ticker (mocked)
# ---------------------------------------------------------------------------

class TestCalculatePeForTicker:
    """Tests for calculate_pe_for_ticker with mocked yfinance."""

    def _make_mock_history(self, dates: list[str], closes: list[float],
                           div_values: list[float] | None = None) -> MagicMock:
        """Create a mock history DataFrame."""
        hist = pd.DataFrame({"Close": closes}, index=pd.to_datetime(dates))
        mock_hist = MagicMock()
        if div_values:
            hist["Dividends"] = div_values
        else:
            hist["Dividends"] = [0.0] * len(dates)
        mock_hist.__getitem__ = lambda self, key: hist[key]
        mock_hist.empty = False
        mock_hist.__len__ = lambda self: len(hist)
        mock_hist["Close"] = hist["Close"]
        mock_hist["Dividends"] = hist["Dividends"]
        mock_hist.index.name = None
        mock_hist.columns = pd.Index(["Close", "Dividends"])
        return mock_hist

    def _make_mock_ticker(
        self,
        dates: list[str],
        closes: list[float],
        eps_dates: list[str] | None = None,
        eps_values: list[float] | None = None,
        div_dates: list[str] | None = None,
        div_values: list[float] | None = None,
        currency: str = "USD",
    ) -> MagicMock:
        """Build a fully mocked yf.Ticker with real pandas objects."""
        mock_stock = MagicMock()

        # Price history with Dividends column — use a real DataFrame
        hist_df = pd.DataFrame({
            "Close": closes,
        }, index=pd.to_datetime(dates))
        if div_dates and div_values:
            full_div = pd.Series(0.0, index=pd.to_datetime(dates), name="Dividends")
            for d, v in zip(div_dates, div_values):
                d_normalized = pd.to_datetime(d)
                if d_normalized in full_div.index:
                    full_div[d_normalized] = v
                else:
                    full_div[d_normalized] = v
            hist_df["Dividends"] = full_div
        else:
            hist_df["Dividends"] = pd.Series(0.0, index=pd.to_datetime(dates), name="Dividends")

        # hist_df already has a datetime index (mimics yfinance: history() returns DF with datetime index)
        mock_stock.history = MagicMock(return_value=hist_df)

        # Currency
        mock_stock.info = {"currency": currency}

        # EPS from quarterly_income_stmt — structured like yfinance
        if eps_dates and eps_values:
            # yfinance quarterly_income_stmt: index=row labels, columns=dates
            # Use datetime64[ns] to match price Date column resolution (date_range + strftime)
            eps_cols = pd.to_datetime(eps_dates).astype("datetime64[ns]")
            mock_stock.quarterly_income_stmt = pd.DataFrame(
                [eps_values],
                index=["Diluted EPS"],
                columns=eps_cols,
            )
        else:
            mock_stock.quarterly_income_stmt = pd.DataFrame()

        return mock_stock

    def _patch_yf_ticker(self, mock_ticker: MagicMock):
        patcher = patch("download_stock_info.yf.Ticker", return_value=mock_ticker)
        self._patcher = patcher
        patcher.start()

    def _unpatch_yf_ticker(self):
        if hasattr(self, "_patcher"):
            self._patcher.stop()

    def test_basic_usd(self):
        """Test basic USD stock with EPS and dividend."""
        # Extend to cover all EPS dates + some after for TTM validity
        price_dates = pd.date_range("2023-01-01", periods=400, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [50.0] * 400
        eps_dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        eps_values = [0.50, 0.60, 0.70, 0.80]
        div_dates = ["2023-02-15", "2023-03-15"]
        div_values = [0.25, 0.30]

        mock_ticker = self._make_mock_ticker(
            price_dates, closes,
            eps_dates, eps_values,
            div_dates, div_values,
            "USD",
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, fundamentals = mod.calculate_pe_for_ticker("AAPL")

            assert "Date" in result.columns
            assert "Close" in result.columns
            assert "ta_eps_ttm" in result.columns
            assert "ta_pe" in result.columns
            assert "ta_div_ttm" in result.columns
            assert "ta_div_yield" in result.columns

            assert len(result) > 0
            assert (result["Close"] == 50.0).all()
        finally:
            self._unpatch_yf_ticker()

    def test_gb_pence_currency(self):
        """Test GBp currency: both price and dividend divided by 100."""
        price_dates = pd.date_range("2023-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [5000] * 50  # 50.00 GBP in GBp
        eps_dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        eps_values = [100.0, 120.0, 130.0, 140.0]  # in GBp
        div_dates = ["2023-01-15", "2023-02-15"]
        div_values = [2.0, 2.5]  # in GBp

        mock_ticker = self._make_mock_ticker(
            price_dates, closes,
            eps_dates, eps_values,
            div_dates, div_values,
            "GBp",
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, fundamentals = mod.calculate_pe_for_ticker("NG.L")

            # Price should be converted to GBP
            assert (result["Close"] == 50.0).all()
            # EPS in GBp, Close in GBP, so P/E = 50 / (140/100) = 0.357
            assert (result["ta_pe"] > 0).all()
        finally:
            self._unpatch_yf_ticker()

    def test_no_dividend(self):
        """Stock with no dividend payouts."""
        price_dates = pd.date_range("2023-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [100.0] * 50
        eps_dates = ["2023-01-10", "2023-01-20", "2023-02-01", "2023-02-10"]
        eps_values = [1.0, 1.2, 1.3, 1.4]

        mock_ticker = self._make_mock_ticker(
            price_dates, closes,
            eps_dates, eps_values,
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, fundamentals = mod.calculate_pe_for_ticker("NO-DIV")

            assert len(result) > 0
            assert result["ta_div_ttm"].isna().all()
            assert result["ta_div_yield"].isna().all()
        finally:
            self._unpatch_yf_ticker()

    def test_fewer_than_4_eps_periods(self):
        """Fewer than 4 quarterly EPS → no TTM EPS."""
        price_dates = pd.date_range("2023-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [100.0] * 50
        eps_dates = ["2023-01-15", "2023-01-25", "2023-02-05"]
        eps_values = [1.0, 1.2, 1.3]

        mock_ticker = self._make_mock_ticker(
            price_dates, closes,
            eps_dates, eps_values,
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, fundamentals = mod.calculate_pe_for_ticker("FEW-EPS")
            assert len(result) > 0
        finally:
            self._unpatch_yf_ticker()

    def test_sorted_by_date(self):
        """Result should be sorted by Date."""
        price_dates = pd.date_range("2023-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [100.0] * 50
        eps_dates = ["2023-01-10", "2023-01-20", "2023-02-01", "2023-02-10"]
        eps_values = [1.0, 1.2, 1.3, 1.4]

        mock_ticker = self._make_mock_ticker(
            price_dates, closes,
            eps_dates, eps_values,
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, fundamentals = mod.calculate_pe_for_ticker("SORTED")
            dates = pd.to_datetime(result["Date"])
            assert dates.is_monotonic_increasing
        finally:
            self._unpatch_yf_ticker()

    def test_output_columns(self):
        """Result should have exactly the expected columns."""
        price_dates = pd.date_range("2023-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [100.0] * 50
        eps_dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        eps_values = [1.0, 1.2, 1.3, 1.4]
        div_dates = ["2023-01-15"]
        div_values = [0.25]

        mock_ticker = self._make_mock_ticker(
            price_dates, closes,
            eps_dates, eps_values,
            div_dates, div_values,
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, fundamentals = mod.calculate_pe_for_ticker("COLS")
            expected_cols = ["Date", "Close", "ta_eps_ttm", "ta_pe", "ta_div_ttm", "ta_div_yield"]
            assert list(result.columns) == expected_cols
        finally:
            self._unpatch_yf_ticker()

    def test_returns_fundamentals_dict(self):
        """calculate_pe_for_ticker returns an empty fundamentals dict (stock.info no longer queried)."""
        price_dates = pd.date_range("2023-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [100.0] * 50
        eps_dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        eps_values = [1.0, 1.2, 1.3, 1.4]

        mock_ticker = self._make_mock_ticker(
            price_dates, closes,
            eps_dates, eps_values,
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, fundamentals = mod.calculate_pe_for_ticker("FUND")
            assert isinstance(fundamentals, dict)
            # stock.info no longer queried — fundamentals dict is empty
            assert fundamentals == {}
        finally:
            self._unpatch_yf_ticker()

    def test_incremental_existing_df(self):
        """When existing_df is provided, only new rows should be returned."""
        # Old data: 50 trading days from 2023-01-01 → ~2023-03-10
        old_dates = pd.date_range("2023-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
        old_closes = [100.0] * 50
        old_df = pd.DataFrame({
            "Date": pd.to_datetime(old_dates),
            "Close": old_closes,
            "ta_eps_ttm": [1.4] * 50,
            "ta_pe": [100.0 / 1.4] * 50,
            "ta_div_ttm": [0.0] * 50,
            "ta_div_yield": [0.0] * 50,
        })

        # New mock data: 400 daily periods from 2023-01-01 → ~2024-01-25
        # EPS dates: 4 quarterly values ending 2023-12-31 → TTM valid from 2023-12-31
        new_price_dates = pd.date_range("2023-01-01", periods=400, freq="D").strftime("%Y-%m-%d").tolist()
        new_closes = [100.0] * 400
        eps_dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        eps_values = [1.0, 1.2, 1.3, 1.4]

        mock_ticker = self._make_mock_ticker(
            new_price_dates, new_closes,
            eps_dates, eps_values,
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, fundamentals = mod.calculate_pe_for_ticker(
                "INC", period="30d", existing_df=old_df,
            )
            assert isinstance(fundamentals, dict)
            assert fundamentals == {}
            # Should return rows after the last old date (~2023-03-10)
            old_last = pd.to_datetime(old_df["Date"]).max()
            result_last = pd.to_datetime(result["Date"]).max()
            assert result_last > old_last, \
                f"Expected new rows beyond {old_last.date()}, got {result_last}"
            assert len(result) > 0
        finally:
            self._unpatch_yf_ticker()

    def test_incremental_no_new_data(self):
        """When new data doesn't extend past existing data, result is empty."""
        old_dates = pd.date_range("2023-01-01", periods=400, freq="D").strftime("%Y-%m-%d").tolist()
        old_closes = [100.0] * 400
        old_df = pd.DataFrame({
            "Date": pd.to_datetime(old_dates),
            "Close": old_closes,
            "ta_eps_ttm": [1.4] * 400,
            "ta_pe": [100.0 / 1.4] * 400,
            "ta_div_ttm": [0.0] * 400,
            "ta_div_yield": [0.0] * 400,
        })

        # New data: same date range as old
        same_price_dates = pd.date_range("2023-01-01", periods=400, freq="D").strftime("%Y-%m-%d").tolist()
        same_closes = [100.0] * 400
        eps_dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        eps_values = [1.0, 1.2, 1.3, 1.4]

        mock_ticker = self._make_mock_ticker(
            same_price_dates, same_closes,
            eps_dates, eps_values,
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, fundamentals = mod.calculate_pe_for_ticker(
                "NO-NEW", period="30d", existing_df=old_df,
            )
            assert result.empty
        finally:
            self._unpatch_yf_ticker()

    def test_incremental_empty_existing_df(self):
        """When existing_df is empty, full calculation runs."""
        price_dates = pd.date_range("2023-01-01", periods=400, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [100.0] * 400
        eps_dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        eps_values = [1.0, 1.2, 1.3, 1.4]

        mock_ticker = self._make_mock_ticker(
            price_dates, closes,
            eps_dates, eps_values,
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            empty_df = pd.DataFrame()
            result, fundamentals = mod.calculate_pe_for_ticker(
                "EMPTY", period="15y", existing_df=empty_df,
            )
            assert len(result) > 0
        finally:
            self._unpatch_yf_ticker()

    def test_incremental_missing_date_column(self):
        """When existing_df has no Date column, full calculation runs."""
        price_dates = pd.date_range("2023-01-01", periods=400, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [100.0] * 400
        eps_dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        eps_values = [1.0, 1.2, 1.3, 1.4]

        mock_ticker = self._make_mock_ticker(
            price_dates, closes,
            eps_dates, eps_values,
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            no_date_df = pd.DataFrame({"Close": [100.0]})
            result, fundamentals = mod.calculate_pe_for_ticker(
                "NO-DT", period="15y", existing_df=no_date_df,
            )
            assert len(result) > 0
        finally:
            self._unpatch_yf_ticker()

    def test_incremental_gb_pence(self):
        """Incremental: GBp currency conversion should apply to merged data."""
        old_dates = pd.date_range("2023-01-01", periods=50, freq="D").strftime("%Y-%m-%d").tolist()
        old_closes = [5000] * 50  # GBp
        old_df = pd.DataFrame({
            "Date": pd.to_datetime(old_dates),
            "Close": old_closes,
            "ta_eps_ttm": [140.0] * 50,
            "ta_pe": [50.0 / 1.4] * 50,
            "ta_div_ttm": [0.0] * 50,
            "ta_div_yield": [0.0] * 50,
        })

        new_price_dates = pd.date_range("2023-01-01", periods=400, freq="D").strftime("%Y-%m-%d").tolist()
        new_closes = [5000] * 400  # GBp
        eps_dates = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31"]
        eps_values = [100.0, 120.0, 130.0, 140.0]

        mock_ticker = self._make_mock_ticker(
            new_price_dates, new_closes,
            eps_dates, eps_values,
            currency="GBp",
        )
        self._patch_yf_ticker(mock_ticker)

        try:
            result, _ = mod.calculate_pe_for_ticker(
                "NG.INC", period="30d", existing_df=old_df,
            )
            assert len(result) > 0
            # Close should be converted to GBP (5000 GBp -> 50.0 GBP)
            assert (result["Close"] == 50.0).all()
        finally:
            self._unpatch_yf_ticker()


# ---------------------------------------------------------------------------
# _compute_incremental_period
# ---------------------------------------------------------------------------

class TestComputeIncrementalPeriod:
    """Tests for _compute_incremental_period."""

    def test_recent_date(self):
        """A very recent date should yield a short period (30d minimum)."""
        from datetime import timedelta
        yesterday = (pd.Timestamp.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        result = mod._compute_incremental_period(yesterday)
        assert "30d" in result

    def test_60_days_ago(self):
        """60 days ago should yield ~60d."""
        from datetime import timedelta
        date_60 = (pd.Timestamp.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        result = mod._compute_incremental_period(date_60)
        assert "60d" in result

    def test_caps_at_2_years(self):
        """Dates older than ~730 days should cap at 730d."""
        old_date = "2020-01-01"
        result = mod._compute_incremental_period(old_date)
        # Should be 730d (2 years capped)
        assert "730d" in result or "2y" in result.lower()

class TestExtractInfo:
    """Tests for _extract_info."""

    def _make_mock_stock(self, info: dict) -> MagicMock:
        """Create a mock yf.Ticker with the given info dict."""
        mock_stock = MagicMock()
        mock_stock.info = info
        return mock_stock

    def test_all_fundamentals_extracted(self):
        """All 21 fundamental columns should be extracted."""
        info = {
            "trailingPE": 25.0, "forwardPE": 22.0, "priceToBook": 3.5,
            "enterpriseToEbitda": 15.0, "earningsGrowth": 0.12,
            "revenueGrowth": 0.08, "profitMargins": 0.15,
            "operatingMargins": 0.20, "dividendRate": 2.5,
            "dividendYield": 0.025, "payoutRatio": 0.45,
            "fiveYearAvgDividendYield": 2.8, "exDividendDate": 1735689600,
            "dividendsPerShare": 1.0, "marketCap": 2000000000000,
            "sharesOutstanding": 15000000000, "bookValue": 15.0,
            "totalDebt": 500000000000, "totalCash": 100000000000,
            "debtToEquity": 150.0, "currentRatio": 1.5,
            "totalRevenue": 300000000000, "ebitda": 60000000000,
            "netIncomeToCommon": 40000000000,
        }
        mock_stock = self._make_mock_stock(info)
        result = mod._extract_info(mock_stock)

        assert result["ta_pe_ttm_yf"] == 25.0
        assert result["ta_pe_forward"] == 22.0
        assert result["ta_pb"] == 3.5
        assert result["ta_ev_ebitda"] == 15.0
        assert result["ta_earnings_growth"] == 12.0  # 0.12 * 100
        assert result["ta_revenue_growth"] == 8.0
        assert result["ta_profit_margin"] == 15.0
        assert result["ta_operating_margin"] == 20.0
        assert result["ta_div_rate"] == 2.5
        assert result["ta_div_yield_yf"] == 0.025
        assert result["ta_payout_ratio"] == 0.45
        assert result["ta_div_yield_avg5y"] == 2.8
        assert isinstance(result["ta_next_ex_div_date"], pd.Timestamp)
        assert result["ta_next_ex_div_date"] == pd.Timestamp("2025-01-01")
        assert result["ta_div_per_share"] == 1.0
        assert result["ta_mkt_cap"] == 2000000000000
        assert result["ta_shares_outstanding"] == 15000000000
        assert result["ta_book_value_ps"] == 15.0
        assert result["ta_total_debt"] == 500000000000
        assert result["ta_total_cash"] == 100000000000
        assert result["ta_debt_equity"] == 150.0
        assert result["ta_current_ratio"] == 1.5
        assert result["ta_revenue_ttm"] == 300000000000
        assert result["ta_ebitda_ttm"] == 60000000000
        assert result["ta_net_income_ttm"] == 40000000000

    def test_all_expected_columns(self):
        """Verify all expected column names are present."""
        info = {k: 1.0 for k in [
            "trailingPE", "forwardPE", "priceToBook", "enterpriseToEbitda",
            "earningsGrowth", "revenueGrowth", "profitMargins", "operatingMargins",
            "dividendRate", "dividendYield", "payoutRatio", "fiveYearAvgDividendYield",
            "exDividendDate", "dividendsPerShare", "marketCap", "sharesOutstanding",
            "bookValue", "totalDebt", "totalCash", "debtToEquity", "currentRatio",
            "totalRevenue", "ebitda", "netIncomeToCommon",
        ]}
        mock_stock = self._make_mock_stock(info)
        result = mod._extract_info(mock_stock)

        expected = [
            "ta_pe_ttm_yf", "ta_pe_forward", "ta_pb", "ta_ev_revenue",
            "ta_ev_ebitda", "ta_earnings_growth", "ta_revenue_growth",
            "ta_profit_margin", "ta_operating_margin", "ta_div_rate",
            "ta_div_yield_yf", "ta_payout_ratio", "ta_div_yield_avg5y",
            "ta_next_ex_div_date", "ta_div_per_share", "ta_mkt_cap",
            "ta_shares_outstanding", "ta_book_value_ps", "ta_total_debt",
            "ta_total_cash", "ta_debt_equity", "ta_current_ratio",
            "ta_revenue_ttm", "ta_ebitda_ttm", "ta_net_income_ttm",
        ]
        for col in expected:
            assert col in result, f"Missing column: {col}"

    def test_missing_data_becomes_none(self):
        """Missing info keys should result in None values."""
        mock_stock = self._make_mock_stock({})
        result = mod._extract_info(mock_stock)
        for key, v in result.items():
            if key == "ta_next_ex_div_date":
                assert pd.isna(v), f"Expected NaT/NaN for {key}, got {v}"
            else:
                assert v is None, f"Expected None for {key}, got {v}"

    def test_percentage_conversion(self):
        """Growth and margin values should be converted from decimal to percentage."""
        info = {
            "earningsGrowth": 0.25,  # 25%
            "revenueGrowth": 0.10,   # 10%
            "profitMargins": 0.05,   # 5%
            "operatingMargins": 0.15, # 15%
        }
        mock_stock = self._make_mock_stock(info)
        result = mod._extract_info(mock_stock)
        assert result["ta_earnings_growth"] == 25.0
        assert result["ta_revenue_growth"] == 10.0
        assert result["ta_profit_margin"] == 5.0
        assert result["ta_operating_margin"] == 15.0

    def test_ex_dividend_date_unix_timestamp(self):
        """exDividendDate (Unix timestamp) should be converted to datetime."""
        # 2024-06-15 00:00:00 UTC
        ts = 1718409600
        info = {"exDividendDate": ts}
        mock_stock = self._make_mock_stock(info)
        result = mod._extract_info(mock_stock)
        assert isinstance(result["ta_next_ex_div_date"], pd.Timestamp)
        assert result["ta_next_ex_div_date"].year == 2024
        assert result["ta_next_ex_div_date"].month == 6
        assert result["ta_next_ex_div_date"].day == 15

    def test_no_ex_dividend_date(self):
        """Missing exDividendDate should produce NaT."""
        info = {}
        mock_stock = self._make_mock_stock(info)
        result = mod._extract_info(mock_stock)
        assert pd.isna(result["ta_next_ex_div_date"])

    def test_alternate_key_aliases(self):
        """Should fall back to alternate key names."""
        info = {
            "pb_ratio": 4.0,
            "ev_to_revenue": 8.0,
            "ev_to_ebitda": 12.0,
            "bookValuePerShare": 20.0,
        }
        mock_stock = self._make_mock_stock(info)
        result = mod._extract_info(mock_stock)
        assert result["ta_pb"] == 4.0
        assert result["ta_ev_revenue"] == 8.0
        assert result["ta_ev_ebitda"] == 12.0
        assert result["ta_book_value_ps"] == 20.0

    def test_large_numbers_preserved(self):
        """Large numbers like market cap should be preserved as-is."""
        info = {"marketCap": 3500000000000.0}  # 3.5T
        mock_stock = self._make_mock_stock(info)
        result = mod._extract_info(mock_stock)
        assert result["ta_mkt_cap"] == 3500000000000.0

    def test_integer_values_coerced_to_float(self):
        """Integer values from info should work (float conversion on percentages)."""
        info = {
            "earningsGrowth": 0,  # Zero is falsy but should still be converted
            "revenueGrowth": 1,   # 1 = 100%
        }
        mock_stock = self._make_mock_stock(info)
        result = mod._extract_info(mock_stock)
        assert result["ta_earnings_growth"] == 0.0
        assert result["ta_revenue_growth"] == 100.0

    def test_returns_dict(self):
        """Should return a plain dict, not wrapped."""
        info = {"marketCap": 1000}
        mock_stock = self._make_mock_stock(info)
        result = mod._extract_info(mock_stock)
        assert isinstance(result, dict)