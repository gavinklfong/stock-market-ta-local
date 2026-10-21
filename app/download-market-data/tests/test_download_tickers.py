"""Unit tests for download_tickers.py — verifies incremental download logic."""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

import download_tickers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(dates, open_p=None, high=None, low=None, close=None, volume=None):
    """Create a sample OHLCV DataFrame with Date index."""
    if open_p is None:
        open_p = [100.0 + i for i in range(len(dates))]
    if close is None:
        close = [100.0 + i * 0.5 for i in range(len(dates))]
    if high is None:
        high = [o + 1.0 for o in open_p]
    if low is None:
        low = [o - 1.0 for o in open_p]
    if volume is None:
        volume = [1000] * len(dates)

    df = pd.DataFrame({
        "Open": open_p,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
    }, index=pd.DatetimeIndex(pd.to_datetime(dates)))
    df.index.name = "Date"
    return df


def _write_ohlcv_csv(filepath, df):
    """Write an OHLCV DataFrame to CSV in the yfinance format."""
    df_copy = df.reset_index()
    df_copy.to_csv(filepath, index=False)


def _make_ticker_csv(tmpdir, tickers, company_names=None, industries=None):
    """Create a ticker_list.csv in tmpdir with the given tickers."""
    ticker_csv = os.path.join(tmpdir, "ticker_list.csv")
    if company_names is None:
        company_names = [f"Company {i}" for i in range(len(tickers))]
    if industries is None:
        industries = ["Industry"] * len(tickers)
    pd.DataFrame({
        "Company": company_names,
        "Ticker": tickers,
        "Major Industry": industries
    }).to_csv(ticker_csv, index=False)
    return ticker_csv


# ---------------------------------------------------------------------------
# load_ticker_map tests
# ---------------------------------------------------------------------------

class TestLoadTickerMap:
    """Verify ticker list parsing and Yahoo Finance symbol mapping."""

    def test_missing_input_csv_raises(self, tmp_path):
        """Should raise FileNotFoundError for missing ticker_list.csv."""
        with pytest.raises(FileNotFoundError):
            download_tickers.load_ticker_map(str(tmp_path / "NONEXISTENT.csv"))

    def test_missing_ticker_column_raises(self, tmp_path):
        """Should raise KeyError if ticker_list.csv lacks 'Ticker' column."""
        csv = tmp_path / "ticker_list.csv"
        pd.DataFrame({"Company": ["Test"], "Name": ["Test Co"]}).to_csv(csv, index=False)
        with pytest.raises(KeyError):
            download_tickers.load_ticker_map(str(csv))

    def test_dot_to_hyphen_conversion(self, tmp_path):
        """BRK.B should map to BRK-B."""
        csv = tmp_path / "ticker_list.csv"
        pd.DataFrame({"Company": ["A", "B"], "Ticker": ["BRK.B", "GOOG"],
                      "Major Industry": ["", ""]}).to_csv(csv, index=False)
        ticker_map = download_tickers.load_ticker_map(str(csv))
        assert ticker_map["BRK.B"] == "BRK-B"
        assert ticker_map["GOOG"] == "GOOG"

    def test_london_suffix_preserved(self, tmp_path):
        """Ticker ending in .L should be preserved."""
        csv = tmp_path / "ticker_list.csv"
        pd.DataFrame({"Company": ["A", "B"], "Ticker": ["VOD.L", "BP.L"],
                      "Major Industry": ["", ""]}).to_csv(csv, index=False)
        ticker_map = download_tickers.load_ticker_map(str(csv))
        assert ticker_map["VOD.L"] == "VOD.L"
        assert ticker_map["BP.L"] == "BP.L"

    def test_whitespace_stripped(self, tmp_path):
        """Whitespace around tickers should be stripped."""
        csv = tmp_path / "ticker_list.csv"
        pd.DataFrame({"Company": ["A", "B", "C"],
                      "Ticker": [" AAPL ", "GOOG\t", "META\n"],
                      "Major Industry": ["", "", ""]}).to_csv(csv, index=False)
        ticker_map = download_tickers.load_ticker_map(str(csv))
        assert list(ticker_map.keys()) == ["AAPL", "GOOG", "META"]

    def test_empty_ticker_list(self, tmp_path):
        """Should return an empty dict for an empty ticker list."""
        csv = tmp_path / "ticker_list.csv"
        pd.DataFrame({"Company": [], "Ticker": [], "Major Industry": []}).to_csv(csv, index=False)
        ticker_map = download_tickers.load_ticker_map(str(csv))
        assert ticker_map == {}

    def test_dropna_removes_na_tickers(self, tmp_path):
        """Rows with missing ticker values should be skipped."""
        csv = tmp_path / "ticker_list.csv"
        pd.DataFrame({
            "Company": ["A", "B", "C"],
            "Ticker": ["AAPL", None, "GOOG"],
            "Major Industry": ["", "", ""]
        }).to_csv(csv, index=False)
        ticker_map = download_tickers.load_ticker_map(str(csv))
        assert "AAPL" in ticker_map
        assert "GOOG" in ticker_map
        assert None not in ticker_map


# ---------------------------------------------------------------------------
# read_existing_data tests
# ---------------------------------------------------------------------------

class TestReadExistingData:
    """Verify read_existing_data helper."""

    def test_returns_none_for_missing_file(self, tmp_path):
        filepath = tmp_path / "NONEXISTENT.csv"
        assert download_tickers.read_existing_data(str(filepath)) is None

    def test_returns_none_for_csv_without_date_column(self, tmp_path):
        filepath = tmp_path / "bad.csv"
        pd.DataFrame({"a": [1], "b": [2]}).to_csv(filepath, index=False)
        assert download_tickers.read_existing_data(str(filepath)) is None

    def test_returns_dataframe_with_date_index(self, tmp_path):
        filepath = tmp_path / "data.csv"
        df = _make_ohlcv_df(["2024-01-01", "2024-01-02", "2024-01-03"])
        _write_ohlcv_csv(str(filepath), df)

        result = download_tickers.read_existing_data(str(filepath))
        assert result is not None
        assert isinstance(result.index, pd.DatetimeIndex)
        assert len(result) == 3

    def test_date_column_parsed_as_datetime(self, tmp_path):
        filepath = tmp_path / "data.csv"
        df = _make_ohlcv_df(["2024-01-01", "2024-06-15", "2024-12-31"])
        _write_ohlcv_csv(str(filepath), df)

        result = download_tickers.read_existing_data(str(filepath))
        assert result.index[0].day == 1
        assert result.index[0].month == 1
        assert result.index[2].day == 31

    def test_returns_all_ohlcv_columns(self, tmp_path):
        filepath = tmp_path / "data.csv"
        df = _make_ohlcv_df(["2024-01-01", "2024-01-02"])
        _write_ohlcv_csv(str(filepath), df)

        result = download_tickers.read_existing_data(str(filepath))
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns


# ---------------------------------------------------------------------------
# save_data tests
# ---------------------------------------------------------------------------

class TestSaveData:
    """Verify save_data helper."""

    def test_saves_csv_with_date_column(self, tmp_path):
        filepath = tmp_path / "output.csv"
        df = _make_ohlcv_df(["2024-01-01", "2024-01-02", "2024-01-03"])

        download_tickers.save_data(str(filepath), df)

        assert os.path.exists(filepath)
        result = pd.read_csv(filepath)
        assert "Date" in result.columns
        assert len(result) == 3

    def test_output_sorted_by_date(self, tmp_path):
        filepath = tmp_path / "output.csv"
        df = _make_ohlcv_df(["2024-01-03", "2024-01-01", "2024-01-02"])

        download_tickers.save_data(str(filepath), df)

        result = pd.read_csv(filepath)
        dates = pd.to_datetime(result["Date"])
        assert dates.is_monotonic_increasing

    def test_deduplicates_dates_keep_last(self, tmp_path):
        filepath = tmp_path / "output.csv"
        # Duplicate date: keep the later row
        dates = ["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03"]
        closes = [100, 101, 199, 103]  # 199 is the "last" for 2024-01-02
        df = _make_ohlcv_df(dates, close=closes)

        download_tickers.save_data(str(filepath), df)

        result = pd.read_csv(filepath)
        assert len(result) == 3  # duplicate removed
        jan2_row = result[result["Date"] == "2024-01-02"]
        assert len(jan2_row) == 1
        assert float(jan2_row["Close"].iloc[0]) == pytest.approx(199)

    def test_preserves_all_columns(self, tmp_path):
        filepath = tmp_path / "output.csv"
        df = _make_ohlcv_df(["2024-01-01", "2024-01-02"])

        download_tickers.save_data(str(filepath), df)

        result = pd.read_csv(filepath)
        for col in ["Date", "Open", "High", "Low", "Close", "Volume"]:
            assert col in result.columns


# ---------------------------------------------------------------------------
# download_catchup tests (mocked yfinance)
# ---------------------------------------------------------------------------

class TestDownloadCatchup:
    """Verify download_catchup uses correct date range."""

    def test_calls_yf_download_with_start_date(self):
        """Should download from day after last_date."""
        last_date = datetime(2024, 6, 15)
        expected_start = last_date + pd.Timedelta(days=1)

        mock_result = _make_ohlcv_df(["2024-06-16", "2024-06-17"])

        with patch.object(download_tickers.yf, "download") as mock_download:
            mock_download.return_value = mock_result

            result = download_tickers.download_catchup("AAPL", last_date)

            mock_download.assert_called_once()
            call_kwargs = mock_download.call_args.kwargs
            assert call_kwargs["start"] == expected_start
            assert "end" in call_kwargs
            assert call_kwargs["auto_adjust"] is False
            assert call_kwargs["threads"] is False
            assert len(result) == 2

    def test_returns_empty_when_no_new_data(self):
        """Should return empty DataFrame when there's no new data."""
        last_date = datetime(2026, 10, 17)  # today or future

        with patch.object(download_tickers.yf, "download") as mock_download:
            mock_download.return_value = pd.DataFrame()

            result = download_tickers.download_catchup("AAPL", last_date)

            assert result.empty

    def test_start_date_is_day_after_last(self):
        """Start date should be exactly last_date + 1 day."""
        last_date = datetime(2024, 12, 31)
        expected_start = datetime(2025, 1, 1)

        with patch.object(download_tickers.yf, "download") as mock_download:
            mock_download.return_value = pd.DataFrame()
            download_tickers.download_catchup("AAPL", last_date)

            call_args = mock_download.call_args
            assert call_args.kwargs["start"] == expected_start

    def test_end_date_limits_range(self):
        """Should respect end_date parameter to limit download range."""
        last_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)

        with patch.object(download_tickers.yf, "download") as mock_download:
            mock_download.return_value = pd.DataFrame()
            download_tickers.download_catchup("AAPL", last_date, end_date=end_date)

            call_args = mock_download.call_args
            assert call_args.kwargs["start"] == last_date + pd.Timedelta(days=1)
            assert call_args.kwargs["end"] == end_date

    def test_default_end_date_is_today(self):
        """When end_date is not provided, should default to today."""
        last_date = datetime(2024, 1, 1)

        with patch.object(download_tickers.yf, "download") as mock_download:
            mock_download.return_value = pd.DataFrame()
            download_tickers.download_catchup("AAPL", last_date)

            call_args = mock_download.call_args
            # Compare date only to avoid microsecond differences
            assert call_args.kwargs["end"].date() == pd.Timestamp.today().date()


# ---------------------------------------------------------------------------
# download_full tests (mocked yfinance)
# ---------------------------------------------------------------------------

class TestDownloadFull:
    """Verify download_full uses correct parameters."""

    def test_calls_yf_download_with_period(self):
        with patch.object(download_tickers.yf, "download") as mock_download:
            mock_download.return_value = _make_ohlcv_df(["2024-01-01"])

            download_tickers.download_full("AAPL")

            mock_download.assert_called_once_with(
                "AAPL",
                period=download_tickers.PERIOD,
                auto_adjust=False,
                threads=False,
            )

    def test_filters_na_rows(self):
        with patch.object(download_tickers.yf, "download") as mock_download:
            # Return data with some all-NA rows
            dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
            df = _make_ohlcv_df(dates)
            # Make the second row all NaN
            df.iloc[1] = float("nan")
            mock_download.return_value = df

            result = download_tickers.download_full("AAPL")

            # dropna(how="all") should remove the all-NA row
            assert len(result) == 2


# ---------------------------------------------------------------------------
# Main loop: full download path
# ---------------------------------------------------------------------------

class TestFullDownloadPath:
    """Verify the full download path when no existing data."""

    def test_full_download_when_no_existing_csv(self, tmp_path):
        """If no CSV exists, should do a full download."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        mock_df = _make_ohlcv_df(["2023-01-01", "2023-01-02", "2023-01-03"])

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = mock_df

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_file = os.path.join(str(tmp_path), "TEST.csv")
        assert os.path.exists(output_file)
        result = pd.read_csv(output_file)
        assert len(result) == 3

    def test_full_download_skips_when_no_data(self, tmp_path):
        """Should skip tickers where yfinance returns empty data."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["EMPTY"])

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = pd.DataFrame()

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_file = os.path.join(str(tmp_path), "EMPTY.csv")
        assert not os.path.exists(output_file)


# ---------------------------------------------------------------------------
# Main loop: incremental catch-up path
# ---------------------------------------------------------------------------

class TestIncrementalCatchupPath:
    """Verify the incremental catch-up path when data already exists."""

    def test_catchup_when_existing_csv(self, tmp_path):
        """Should only download new data and merge with existing."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        # Write existing data ending on 2024-01-03
        existing_df = _make_ohlcv_df(["2024-01-01", "2024-01-02", "2024-01-03"])
        existing_csv = tmp_path / "TEST.csv"
        _write_ohlcv_csv(str(existing_csv), existing_df)

        # New data from 2024-01-04 onwards
        new_df = _make_ohlcv_df(["2024-01-04", "2024-01-05"])

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = new_df

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_df = pd.read_csv(str(existing_csv))
        # Should have merged 3 + 2 = 5 rows
        assert len(output_df) == 5
        # Last date should be 2024-01-05
        assert output_df["Date"].iloc[-1] == "2024-01-05"

    def test_no_merge_when_no_new_data(self, tmp_path):
        """If catch-up returns empty, existing data should be unchanged."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        existing_df = _make_ohlcv_df(["2024-01-01", "2024-01-02", "2024-01-03"])
        existing_csv = tmp_path / "TEST.csv"
        _write_ohlcv_csv(str(existing_csv), existing_df)

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = pd.DataFrame()  # no new data

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_df = pd.read_csv(str(existing_csv))
        assert len(output_df) == 3  # unchanged

    def test_catchup_merges_without_duplicating(self, tmp_path):
        """Merged result should not have duplicate dates."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        # Existing data ending on 2024-01-03
        existing_df = _make_ohlcv_df(["2024-01-01", "2024-01-02", "2024-01-03"])
        existing_csv = tmp_path / "TEST.csv"
        _write_ohlcv_csv(str(existing_csv), existing_df)

        # New data starts on 2024-01-04
        new_df = _make_ohlcv_df(["2024-01-04", "2024-01-05", "2024-01-06"])

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = new_df

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_df = pd.read_csv(str(existing_csv))
        dates = pd.to_datetime(output_df["Date"])
        assert dates.is_monotonic_increasing
        assert len(dates) == len(dates.drop_duplicates())  # no duplicates

    def test_catchup_overwrites_existing_rows(self, tmp_path):
        """If new data overlaps existing dates (unlikely but possible),
        keep the last occurrence."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        # Existing data ending on 2024-01-03
        existing_df = _make_ohlcv_df(
            ["2024-01-01", "2024-01-02", "2024-01-03"],
            close=[100, 101, 102]
        )
        existing_csv = tmp_path / "TEST.csv"
        _write_ohlcv_csv(str(existing_csv), existing_df)

        # New data includes 2024-01-03 again (should overwrite)
        new_df = _make_ohlcv_df(
            ["2024-01-03", "2024-01-04"],
            close=[102.5, 103]  # 102.5 should overwrite 102 for 2024-01-03
        )

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = new_df

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_df = pd.read_csv(str(existing_csv))
        # 2024-01-03 should appear once with Close=102.5
        jan3 = output_df[output_df["Date"] == "2024-01-03"]
        assert len(jan3) == 1
        assert float(jan3["Close"].iloc[0]) == pytest.approx(102.5)
        # Total should be 4 unique dates (Jan 1-4), not 5
        assert len(output_df) == 4

    def test_catchup_updates_all_ohlcv_columns(self, tmp_path):
        """All OHLCV columns should be updated for overlapping dates."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        # Existing data for Jan 1-3
        existing_df = _make_ohlcv_df(
            ["2024-01-01", "2024-01-02", "2024-01-03"],
            open_p=[100, 101, 102],
            high=[105, 106, 107],
            low=[99, 100, 101],
            close=[100, 101, 102],
            volume=[1000, 1100, 1200]
        )
        existing_csv = tmp_path / "TEST.csv"
        _write_ohlcv_csv(str(existing_csv), existing_df)

        # New data with different values for Jan 3 (should overwrite)
        new_df = _make_ohlcv_df(
            ["2024-01-03", "2024-01-04"],
            open_p=[103, 104],
            high=[108, 109],
            low=[102, 103],
            close=[102.5, 103.5],
            volume=[2000, 2100]
        )

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = new_df

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_df = pd.read_csv(str(existing_csv))
        jan3 = output_df[output_df["Date"] == "2024-01-03"].iloc[0]
        assert float(jan3["Open"]) == pytest.approx(103)
        assert float(jan3["High"]) == pytest.approx(108)
        assert float(jan3["Low"]) == pytest.approx(102)
        assert float(jan3["Close"]) == pytest.approx(102.5)
        assert int(jan3["Volume"]) == 2000


class TestReDownloadToday:
    """Verify that when the last date in the CSV is today, today's data
    is re-downloaded and the existing entry is replaced with new data."""

    def test_re_download_when_last_date_is_today(self, tmp_path):
        """If existing data ends on today, re-download today's price."""
        from datetime import date as date_type

        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        # Existing data ending today — use a hardcoded date far in the past
        # to avoid flakiness from date comparisons during tests.
        # We'll mock pd.Timestamp.today() to return our test date.
        test_date = pd.Timestamp("2024-06-15")
        yesterday = test_date - pd.Timedelta(days=1)

        existing_df = _make_ohlcv_df(
            [str(yesterday.date()), str(test_date.date())],
            open_p=[99.0, 100.0],
            close=[99.0, 100.0]
        )
        existing_csv = tmp_path / "TEST.csv"
        _write_ohlcv_csv(str(existing_csv), existing_df)

        # New today's data with updated price
        new_today = _make_ohlcv_df(
            [str(test_date.date())],
            open_p=[100.5],
            close=[101.0]
        )

        with patch.object(download_tickers.yf, "download") as mock_yf, \
             patch.object(download_tickers.pd.Timestamp, "today", return_value=test_date):
            mock_yf.return_value = new_today

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_df = pd.read_csv(str(existing_csv))
        # Today's Close should be replaced with the new value
        today_row = output_df[output_df["Date"] == str(test_date.date())].iloc[0]
        assert float(today_row["Close"]) == pytest.approx(101.0)

    def test_re_download_preserves_older_entries(self, tmp_path):
        """Re-downloading today's data should not affect older entries."""
        test_date = pd.Timestamp("2024-06-15")
        yesterday = test_date - pd.Timedelta(days=1)
        day_before = test_date - pd.Timedelta(days=2)

        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        existing_df = _make_ohlcv_df(
            [str(day_before.date()), str(yesterday.date()), str(test_date.date())],
            close=[98.0, 99.0, 100.0]
        )
        existing_csv = tmp_path / "TEST.csv"
        _write_ohlcv_csv(str(existing_csv), existing_df)

        new_today = _make_ohlcv_df(
            [str(test_date.date())],
            close=[101.0]
        )

        with patch.object(download_tickers.yf, "download") as mock_yf, \
             patch.object(download_tickers.pd.Timestamp, "today", return_value=test_date):
            mock_yf.return_value = new_today

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_df = pd.read_csv(str(existing_csv))
        # Older entries should be unchanged
        day_before_row = output_df[output_df["Date"] == str(day_before.date())].iloc[0]
        assert float(day_before_row["Close"]) == pytest.approx(98.0)
        yesterday_row = output_df[output_df["Date"] == str(yesterday.date())].iloc[0]
        assert float(yesterday_row["Close"]) == pytest.approx(99.0)
        # Today's entry should be updated
        today_row = output_df[output_df["Date"] == str(test_date.date())].iloc[0]
        assert float(today_row["Close"]) == pytest.approx(101.0)

    def test_re_download_no_data_skips_save(self, tmp_path):
        """If re-download returns no data, existing file should be unchanged."""
        test_date = pd.Timestamp("2024-06-15")

        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        existing_df = _make_ohlcv_df(
            [str(test_date.date())],
            close=[100.0]
        )
        existing_csv = tmp_path / "TEST.csv"
        _write_ohlcv_csv(str(existing_csv), existing_df)
        original_modified = os.path.getmtime(str(existing_csv))

        import time
        time.sleep(0.1)  # Ensure mtime would differ if file is rewritten

        with patch.object(download_tickers.yf, "download") as mock_yf, \
             patch.object(download_tickers.pd.Timestamp, "today", return_value=test_date):
            mock_yf.return_value = pd.DataFrame()  # No data returned

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        # File should not have been rewritten (mtime should be essentially unchanged)
        new_modified = os.path.getmtime(str(existing_csv))
        assert new_modified == pytest.approx(original_modified, abs=0.5)
        # Data should be unchanged
        output_df = pd.read_csv(str(existing_csv))
        assert float(output_df["Close"].iloc[0]) == pytest.approx(100.0)

    def test_re_download_replaces_all_columns(self, tmp_path):
        """Re-download should replace all OHLCV columns for today's entry."""
        test_date = pd.Timestamp("2024-06-15")
        yesterday = test_date - pd.Timedelta(days=1)

        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])

        existing_df = _make_ohlcv_df(
            [str(yesterday.date()), str(test_date.date())],
            open_p=[99.0, 100.0],
            high=[100.0, 101.0],
            low=[98.0, 99.0],
            close=[99.0, 100.0],
            volume=[1000, 1100]
        )
        existing_csv = tmp_path / "TEST.csv"
        _write_ohlcv_csv(str(existing_csv), existing_df)

        new_today = _make_ohlcv_df(
            [str(test_date.date())],
            open_p=[100.5],
            high=[102.0],
            low=[99.5],
            close=[101.5],
            volume=[2000]
        )

        with patch.object(download_tickers.yf, "download") as mock_yf, \
             patch.object(download_tickers.pd.Timestamp, "today", return_value=test_date):
            mock_yf.return_value = new_today

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        output_df = pd.read_csv(str(existing_csv))
        today_row = output_df[output_df["Date"] == str(test_date.date())].iloc[0]
        assert float(today_row["Open"]) == pytest.approx(100.5)
        assert float(today_row["High"]) == pytest.approx(102.0)
        assert float(today_row["Low"]) == pytest.approx(99.5)
        assert float(today_row["Close"]) == pytest.approx(101.5)
        assert int(today_row["Volume"]) == 2000


# ---------------------------------------------------------------------------
# Ticker with slash in name
# ---------------------------------------------------------------------------

class TestTickerWithSlash:
    """Verify tickers with / in the name are sanitized for filenames."""

    def test_slash_replaced_with_underscore(self, tmp_path):
        """Ticker SPY/XX should be saved as SPY_XX.csv."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["SPY/XX"])

        mock_df = _make_ohlcv_df(["2024-01-01"])

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = mock_df

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        expected = tmp_path / "SPY_XX.csv"
        assert os.path.exists(expected)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_ticker_list(self, tmp_path):
        """Script should handle an empty ticker list gracefully."""
        ticker_csv = _make_ticker_csv(str(tmp_path), [], [], [])

        with patch.object(download_tickers.yf, "download") as mock_yf:
            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        # Should produce no CSV files (only the ticker_list.csv we created)
        csv_files = list((tmp_path).glob("*.csv"))
        # Filter out ticker_list.csv itself
        data_files = [f for f in csv_files if f.name != "ticker_list.csv"]
        assert len(data_files) == 0

    def test_multiple_tickers(self, tmp_path):
        """Should process all tickers in the list."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["AAPL", "GOOG", "MSFT"])

        mock_df = _make_ohlcv_df(["2024-01-01", "2024-01-02"])

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = mock_df

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        for ticker in ["AAPL", "GOOG", "MSFT"]:
            output_file = tmp_path / f"{ticker}.csv"
            assert os.path.exists(output_file), f"Missing file: {output_file}"

    def test_partial_failure_doesnt_stop_others(self, tmp_path):
        """If one ticker fails, others should still be processed."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["GOOD", "BAD", "ALSO_GOOD"])

        with patch.object(download_tickers.yf, "download") as mock_yf:
            # BAD ticker raises an exception
            call_count = [0]
            def side_effect(ticker, **kwargs):
                call_count[0] += 1
                if ticker == "BAD":
                    raise ValueError("Network error")
                return _make_ohlcv_df(["2024-01-01"])

            mock_yf.side_effect = side_effect

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(tmp_path),
            )

        # GOOD and ALSO_GOOD should exist
        assert (tmp_path / "GOOD.csv").exists()
        assert (tmp_path / "ALSO_GOOD.csv").exists()
        # BAD should not exist (failed during download)
        assert not (tmp_path / "BAD.csv").exists()

    def test_output_dir_created_if_missing(self, tmp_path):
        """Output directory should be created if it doesn't exist."""
        ticker_csv = _make_ticker_csv(str(tmp_path), ["TEST"])
        output_dir = tmp_path / "nonexistent"

        mock_df = _make_ohlcv_df(["2024-01-01"])

        with patch.object(download_tickers.yf, "download") as mock_yf:
            mock_yf.return_value = mock_df

            download_tickers.download_tickers(
                input_csv=str(ticker_csv),
                output_dir=str(output_dir),
            )

        assert output_dir.exists()
        assert (output_dir / "TEST.csv").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
