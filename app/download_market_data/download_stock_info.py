"""Download stock info and calculate P/E ratio, dividend yield, and fundamental metrics
for all tickers in ticker_list.csv.

P/E = Closing Price / TTM EPS
Dividend Yield = (TTM Dividend / Closing Price) × 100

Since EPS is reported quarterly/semi-annually and prices are daily,
we forward-fill the most recent TTM EPS for each date.

EPS is fetched from multiple sources (in priority order):
  1. quarterly_income_stmt  — quarterly Diluted EPS (US stocks, many international)
  2. earnings_dates         — Reported EPS from earnings calendar (more coverage)
  3. income_stmt            — annual Diluted EPS fallback

Dividends are fetched from historical price data (yfinance).

Additional fundamental metrics are extracted from stock.info (single API call per ticker).

Output files per ticker:
  - data/pe-data/<ticker>_PE.csv      — Daily: Date, Close, ta_eps_ttm, ta_pe, ta_div_ttm, ta_div_yield
  - data/pe-data/<ticker>_fundamentals.csv — REMOVED (static metrics no longer written)
"""

import os
import warnings

import yfinance as yf
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)


# --- Path resolution ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_csv = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "config", "ticker_list.csv"))
output_dir = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data", "pe-data"))
os.makedirs(output_dir, exist_ok=True)

PERIOD = "15y"


def _clean_eps_series(eps_series: pd.Series) -> pd.Series:
    """Normalize an EPS series: sort by date, tz-naive index, drop NaNs."""
    if eps_series.empty:
        return eps_series
    s = eps_series.copy()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s.sort_index().dropna()


def fetch_quarterly_eps_from_income_stmt(stock: yf.Ticker) -> pd.Series:
    """Get quarterly Diluted EPS from quarterly_income_stmt."""
    qs = stock.quarterly_income_stmt
    if qs is None or qs.empty:
        return pd.Series(dtype=float)

    try:
        eps_values = qs.loc["Diluted EPS"]
    except KeyError:
        try:
            eps_values = qs.loc["Basic EPS"]
        except KeyError:
            return pd.Series(dtype=float)

    if eps_values.empty or eps_values.dropna().empty:
        return pd.Series(dtype=float)

    return _clean_eps_series(eps_values)


def fetch_quarterly_eps_from_earnings_dates(stock: yf.Ticker) -> pd.Series:
    """Get quarterly EPS from earnings_dates (Reported EPS)."""
    try:
        ed = stock.earnings_dates
    except Exception:
        return pd.Series(dtype=float)

    if ed is None or ed.empty:
        return pd.Series(dtype=float)

    if "Reported EPS" not in ed.columns:
        return pd.Series(dtype=float)

    # Filter out rows where Reported EPS is NaN
    eps_series = ed["Reported EPS"].dropna()
    if eps_series.empty:
        return pd.Series(dtype=float)

    return _clean_eps_series(eps_series)


def fetch_annual_eps(stock: yf.Ticker) -> pd.Series:
    """Get annual Diluted EPS from income_stmt as a fallback."""
    try:
        is_ = stock.income_stmt
    except Exception:
        return pd.Series(dtype=float)

    if is_ is None or is_.empty:
        return pd.Series(dtype=float)

    try:
        eps_values = is_.loc["Diluted EPS"]
    except KeyError:
        try:
            eps_values = is_.loc["Basic EPS"]
        except KeyError:
            return pd.Series(dtype=float)

    if eps_values.empty or eps_values.dropna().empty:
        return pd.Series(dtype=float)

    return _clean_eps_series(eps_values)


def compute_ttm_eps(eps_series: pd.Series) -> pd.Series:
    """Return a Series with rolling 4-quarter (TTM) EPS.

    Where fewer than 4 quarters are available, return None (NaN).

    Parameters
    ----------
    eps_series : pd.Series
        Quarterly EPS indexed by report date, sorted ascending.

    Returns
    -------
    pd.Series
        TTM EPS indexed by the same dates. NaN where < 4 quarters available.
    """
    n = len(eps_series)
    ttm_values = [None] * n

    for i in range(3, n):
        ttm = sum(eps_series.iloc[i - 3 : i + 1].dropna())
        if ttm > 0:
            ttm_values[i] = ttm

    return pd.Series(ttm_values, index=eps_series.index)


def compute_annual_eps_series(eps_series: pd.Series) -> pd.Series:
    """For annual EPS data, just return the EPS values as-is (no TTM needed).

    Annual EPS is already a full-year figure.
    """
    return eps_series.copy()


def fetch_historical_dividends(stock: yf.Ticker, period: str = "15y") -> pd.Series:
    """Get historical dividend data from yfinance.

    Dividends are extracted from the 'Dividends' column of the
    historical price data. Only non-zero payouts are returned.

    Parameters
    ----------
    stock : yf.Ticker
        A yfinance Ticker object.
    period : str
        How far back to get price data (passed to yfinance).

    Returns
    -------
    pd.Series
        Dividend amounts indexed by ex-dividend date, sorted ascending.
        Empty Series if no dividend data available.
    """
    hist = stock.history(period=period)
    if hist.empty:
        return pd.Series(dtype=float)

    dividends = hist["Dividends"].copy()
    if dividends.empty:
        return pd.Series(dtype=float)

    # Only keep actual dividend payouts (non-zero)
    dividends = dividends[dividends > 0]
    if dividends.empty:
        return pd.Series(dtype=float)

    # Normalize index: tz-naive, sorted ascending
    dividends.index = pd.to_datetime(dividends.index).tz_localize(None)
    return dividends.sort_index()


def compute_ttm_dividends(price_dates: pd.DatetimeIndex, dividends: pd.Series) -> pd.Series:
    """Calculate trailing twelve months (TTM) dividend sum for each price date.

    For each price date, sums all dividends paid within the preceding
    365 days (inclusive). Uses a two-pointer sliding window for efficiency.

    Parameters
    ----------
    price_dates : pd.DatetimeIndex
        Daily price dates (index), sorted ascending.
    dividends : pd.Series
        Dividend amounts indexed by ex-dividend date, sorted ascending.

    Returns
    -------
    pd.Series
        TTM dividend sum for each price date. NaN if no dividends in
        the last 365 days.
    """
    if dividends.empty:
        return pd.Series([None] * len(price_dates), index=price_dates)

    div_dates = dividends.index
    div_amounts = dividends.values.astype(float)

    n = len(price_dates)
    ttm_values = [None] * n

    # Sliding window: find all dividends within [date - 365d, date]
    window = pd.Timedelta(days=365)
    left = 0  # index into div_dates

    for i, price_date in enumerate(price_dates):
        cutoff = price_date - window

        # Advance left pointer to skip dividends older than 365 days
        while left < len(div_dates) and div_dates[left] < cutoff:
            left += 1

        # All dividends from `left` to current position (inclusive) that
        # are <= price_date contribute to TTM sum
        right = 0
        while right < len(div_dates) and div_dates[right] <= price_date:
            right += 1

        # Sum dividends in [left, right)
        if right > left:
            ttm_values[i] = float(div_amounts[left:right].sum())
        else:
            ttm_values[i] = None

    return pd.Series(ttm_values, index=price_dates)


def _extract_info(stock: yf.Ticker) -> dict:
    """Extract all fundamental metrics from stock.info.

    Returns a dict mapping output column names to values.
    Missing/unavailable metrics are set to None (will become NaN in CSV).

    Parameters
    ----------
    stock : yf.Ticker
        A yfinance Ticker object.

    Returns
    -------
    dict
        Fundamental metrics keyed by output column name.
    """
    info = stock.info
    result = {}

    # --- Valuation multiples ---
    result["ta_pe_ttm_yf"] = info.get("trailingPE")
    result["ta_pe_forward"] = info.get("forwardPE")
    result["ta_pb"] = info.get("priceToBook") or info.get("pb_ratio")
    result["ta_ev_revenue"] = info.get("enterpriseToRevenue") or info.get("ev_to_revenue")
    result["ta_ev_ebitda"] = info.get("enterpriseToEbitda") or info.get("ev_to_ebitda")

    # --- Growth & margins (store as percentages) ---
    earnings_growth = info.get("earningsGrowth")
    result["ta_earnings_growth"] = float(earnings_growth * 100) if earnings_growth is not None else None

    revenue_growth = info.get("revenueGrowth")
    result["ta_revenue_growth"] = float(revenue_growth * 100) if revenue_growth is not None else None

    profit_margin = info.get("profitMargins")
    result["ta_profit_margin"] = float(profit_margin * 100) if profit_margin is not None else None

    operating_margin = info.get("operatingMargins")
    result["ta_operating_margin"] = float(operating_margin * 100) if operating_margin is not None else None

    # --- Dividend detail ---
    result["ta_div_rate"] = info.get("dividendRate")
    result["ta_div_yield_yf"] = info.get("dividendYield")
    result["ta_payout_ratio"] = info.get("payoutRatio")
    result["ta_div_yield_avg5y"] = info.get("fiveYearAvgDividendYield")

    ex_div = info.get("exDividendDate")
    if ex_div is not None:
        # yfinance returns exDividendDate as a Unix timestamp (seconds)
        result["ta_next_ex_div_date"] = pd.Timestamp(ex_div, unit="s", tz="UTC").tz_localize(None)
    else:
        result["ta_next_ex_div_date"] = pd.NaT

    result["ta_div_per_share"] = info.get("dividendsPerShare")

    # --- Balance sheet / capitalization ---
    result["ta_mkt_cap"] = info.get("marketCap")
    result["ta_shares_outstanding"] = info.get("sharesOutstanding")
    result["ta_book_value_ps"] = info.get("bookValue") or info.get("bookValuePerShare")
    result["ta_total_debt"] = info.get("totalDebt")
    result["ta_total_cash"] = info.get("totalCash")
    result["ta_debt_equity"] = info.get("debtToEquity")
    result["ta_current_ratio"] = info.get("currentRatio")
    result["ta_revenue_ttm"] = info.get("totalRevenue")
    result["ta_ebitda_ttm"] = info.get("ebitda")
    result["ta_net_income_ttm"] = info.get("netIncomeToCommon")

    return result


def calculate_pe_for_ticker(
    ticker: str,
    period: str = "15y",
    existing_df: pd.DataFrame = None,
) -> tuple[pd.DataFrame, dict]:
    """Calculate daily P/E and dividend yield using trailing metrics.

    Tries quarterly EPS sources first, falls back to annual.
    Dividends are fetched from historical price data.
    Fundamental metrics from stock.info are no longer retrieved.

    When ``existing_df`` is provided, the function reconstructs the full
    price history (existing + new), recalculates all metrics, and returns
    only rows *after* the last date in ``existing_df`` — enabling
    incremental updates without re-downloading 15 years of data.

    Parameters
    ----------
    ticker : str
        Stock ticker (e.g. "NG.L").
    period : str
        How far back to get price data (passed to yfinance).  Only used
        when ``existing_df`` is None.
    existing_df : pd.DataFrame, optional
        Previously-saved PE DataFrame (columns: Date, Close, ta_eps_ttm,
        ta_pe, ta_div_ttm, ta_div_yield).  When provided the caller must
        ensure ``period`` is a short window covering only new data since
        ``existing_df``'s last date.

    Returns
    -------
    tuple[pd.DataFrame, dict]
        (daily_df, fundamentals)
        daily_df: Columns: Date, Close, ta_eps_ttm, ta_pe, ta_div_ttm, ta_div_yield
        fundamentals: empty dict (stock.info no longer queried)
    """
    stock = yf.Ticker(ticker)
    # fundamentals = _extract_info(stock)
    fundamentals = {}

    # ── 1. Get historical daily closing prices ──────────────────────
    hist = stock.history(period=period)
    if hist.empty:
        raise ValueError(f"No price data for {ticker}")

    new_prices = hist[["Close"]].copy()
    new_prices.index.name = "Date"
    new_prices = new_prices.reset_index()
    new_prices["Date"] = pd.to_datetime(new_prices["Date"]).dt.tz_localize(None).astype("datetime64[ns]")

    # ── 2. Merge with existing data (if provided) ───────────────────
    if existing_df is not None and not existing_df.empty and "Date" in existing_df.columns:
        old_dates = pd.to_datetime(existing_df["Date"]).astype("datetime64[ns]")
        old_closes = existing_df["Close"]

        old_prices = pd.DataFrame({"Date": old_dates, "Close": old_closes})

        # Combine old + new; new rows overwrite duplicates
        all_prices = pd.concat([old_prices, new_prices]).drop_duplicates(
            subset=["Date"], keep="last",
        ).sort_values("Date").reset_index(drop=True)
    else:
        all_prices = new_prices.copy()

    # Normalize price to currency (GBp → GBP for UK stocks)
    currency = stock.info.get("currency", "")
    close_price = all_prices["Close"].values.copy()
    if currency == "GBp":
        close_price = close_price / 100

    all_prices["Close"] = close_price

    # ── 3. Get EPS (multi-source: quarterly → earnings_dates → annual) ──
    eps_sources = [
        ("quarterly_income_stmt", fetch_quarterly_eps_from_income_stmt, True),
        ("earnings_dates", fetch_quarterly_eps_from_earnings_dates, True),
        ("income_stmt (annual)", fetch_annual_eps, False),
    ]

    eps_series = pd.Series(dtype=float)
    is_quarterly = False
    source_name = ""
    for label, fetch_fn, quarterly in eps_sources:
        eps_series = fetch_fn(stock)
        if not eps_series.empty:
            source_name = label
            is_quarterly = quarterly
            break

    if eps_series.empty:
        raise ValueError(f"No EPS data for {ticker}")

    # ── 4. Compute TTM or use raw EPS ───────────────────────────────
    # TTM only makes sense for quarterly data (sum of last 4 quarters).
    # For annual data, use the latest EPS directly.
    if is_quarterly and len(eps_series) >= 4:
        ttm_eps_series = compute_ttm_eps(eps_series)
        label = "TTM EPS (4q rolling)"
    else:
        # For annual/insufficient data: use latest EPS, forward-fill
        ttm_eps_series = eps_series.sort_index().copy()
        label = "Latest EPS (forward-filled)"

    # Print summary
    valid_ttm = ttm_eps_series.dropna()
    print(f"  EPS source: {source_name}")
    print(f"  EPS periods: {len(eps_series)}")
    print(f"  Method: {label} ({len(valid_ttm)} valid values)")
    if len(valid_ttm) > 0:
        print(f"  Latest {label.split()[0]}: {valid_ttm.iloc[-1]:.4f}")

    # ── 5. Map EPS to each price date (forward-fill) ────────────────
    # Sort valid EPS by date (merge_asof requires sorted input)
    valid_ttm = ttm_eps_series.dropna().sort_index()
    ttm_df = valid_ttm.reset_index()
    ttm_df.columns = ["EPS_Date", "ta_eps_ttm"]
    # Ensure datetime resolution matches price Date column (datetime64[ns])
    ttm_df["EPS_Date"] = pd.to_datetime(ttm_df["EPS_Date"]).dt.tz_localize(None).astype("datetime64[ns]")

    # Keep Close in price_df so it survives the merge
    price_df = all_prices[["Date", "Close"]].copy().sort_values("Date")

    merged = pd.merge_asof(
        price_df,
        ttm_df,
        left_on="Date",
        right_on="EPS_Date",
        direction="backward",
    )

    # ── 6. Calculate P/E ────────────────────────────────────────────
    merged["ta_pe"] = merged["Close"] / merged["ta_eps_ttm"]

    # ── 7. Calculate dividend yield (if data available) ─────────────
    div_series = fetch_historical_dividends(stock, period=period)
    if not div_series.empty:
        # Normalize dividend currency (GBp → GBP for UK stocks)
        if currency == "GBp":
            div_series = div_series / 100
        print(f"  Dividend payouts: {len(div_series)} in last {period}")

        # Compute TTM dividend sum for each price date
        ttm_div = compute_ttm_dividends(merged["Date"], div_series)

        # Merge TTM dividends into the result
        ttm_div_df = ttm_div.reset_index()
        ttm_div_df.columns = ["Date", "ta_div_ttm"]
        merged = pd.merge(merged, ttm_div_df, on="Date", how="left")

        # Calculate dividend yield: (TTM Div / Close) × 100
        merged["ta_div_yield"] = (merged["ta_div_ttm"] / merged["Close"]) * 100
    else:
        print(f"  No dividend data for {ticker}")
        merged["ta_div_ttm"] = float("nan")
        merged["ta_div_yield"] = float("nan")

    # ── 8. Clean up ─────────────────────────────────────────────────
    result = merged[["Date", "Close", "ta_eps_ttm", "ta_pe", "ta_div_ttm", "ta_div_yield"]].copy()
    # Drop rows before we had any valid EPS
    result = result.dropna(subset=["ta_eps_ttm", "ta_pe"])

    # ── 9. Filter to new rows only (when existing_df provided) ──────
    if existing_df is not None and not existing_df.empty and "Date" in existing_df.columns:
        old_last_date = pd.Timestamp(
            pd.to_datetime(existing_df["Date"]).max(),
        )
        new_dates = pd.to_datetime(result["Date"])
        result = result[new_dates > old_last_date].reset_index(drop=True)

    return result, fundamentals


def _compute_incremental_period(last_date_str: str) -> str:
    """Compute a short period string covering new data since *last_date_str*.

    Returns a yfinance-compatible period like ``"60d"`` based on how many
    days have passed since the last saved date.  Falls back to ``"30d"``
    for very recent data and caps at ``"2y"`` for older data.
    """
    last_date = pd.Timestamp(last_date_str)
    span_days = (pd.Timestamp.now() - last_date).days
    span_days = max(30, span_days)
    span_days = min(span_days, 365 * 2)  # cap at 2 years
    return f"{span_days}d"


def bulk_download() -> None:
    """Read ticker_list.csv and calculate P/E for each ticker.

    Increments: when a ``{ticker}_PE.csv`` already exists, only new price
    data since the last saved date is fetched; the full calculation is
    then performed on the combined data and only the delta rows are
    appended.
    """
    if not os.path.exists(input_csv):
        raise FileNotFoundError(
            f"Could not find '{input_csv}'. Make sure it exists in the same directory."
        )

    df = pd.read_csv(input_csv)
    if "Ticker" not in df.columns:
        raise KeyError("The input CSV must contain a 'Ticker' column.")

    # Clean whitespace and create a map for Yahoo Finance formatting
    raw_tickers = df["Ticker"].dropna().astype(str).str.strip().tolist()
    ticker_map = {t: t if t.endswith(".L") else t.replace(".", "-") for t in raw_tickers}
    tickers = list(ticker_map.values())

    print(f"Loaded {len(tickers)} tickers from '{input_csv}'.")
    print(f"Downloading P/E and dividend data...\n")

    for original_ticker, yf_ticker in ticker_map.items():
        safe_filename = original_ticker.replace("/", "_")
        daily_filepath = os.path.join(output_dir, f"{safe_filename}_PE.csv")
        fund_filepath = os.path.join(output_dir, f"{safe_filename}_fundamentals.csv")

        # Check for existing data (incremental update)
        existing_df = None
        if os.path.exists(daily_filepath):
            try:
                existing_df = pd.read_csv(daily_filepath)
                existing_df = existing_df.dropna(subset=["Date"])
                if not existing_df.empty and "Date" in existing_df.columns:
                    last_date = pd.to_datetime(existing_df["Date"]).max()
                    print(f"  Existing data up to {last_date.date()}")
                    period = _compute_incremental_period(last_date)
                else:
                    existing_df = None
                    period = PERIOD
            except Exception:
                existing_df = None
                period = PERIOD
        else:
            period = PERIOD

        print(f"Processing [{yf_ticker}] -> {safe_filename} ...")
        try:
            result, fundamentals = calculate_pe_for_ticker(
                yf_ticker, period=period, existing_df=existing_df,
            )
            if result.empty:
                print(f"  No new data for {yf_ticker}.")
                print()
                continue

            # Append new rows to existing file
            if existing_df is not None and not existing_df.empty:
                combined = pd.concat([existing_df, result])
                combined = combined.sort_values("Date").reset_index(drop=True)
                combined.to_csv(daily_filepath, index=False)
                print(f"  Appended {len(result)} new rows ({len(combined)} total)")
                print(f"  Latest P/E: {combined['ta_pe'].iloc[-1]:.2f}", end="")
                if "ta_div_yield" in combined.columns and pd.notna(combined["ta_div_yield"].iloc[-1]):
                    print(f"  | Div Yield: {combined['ta_div_yield'].iloc[-1]:.2f}%")
                else:
                    print()
            else:
                result = result.sort_values("Date").reset_index(drop=True)
                result.to_csv(daily_filepath, index=False)
                print(f"  Saved {len(result)} daily rows to {daily_filepath}")
                print(f"  Latest P/E: {result['ta_pe'].iloc[-1]:.2f}", end="")
                if "ta_div_yield" in result.columns and pd.notna(result["ta_div_yield"].iloc[-1]):
                    print(f"  | Div Yield: {result['ta_div_yield'].iloc[-1]:.2f}%")
                else:
                    print()

        except Exception as e:
            print(f"  Error processing {yf_ticker}: {e}\n")

    print(f"\nAll done. Output directory: {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download P/E and dividend data for tickers.")
    parser.add_argument("--ticker", nargs="*", help="Ticker(s) to process (default: all from ticker_list.csv)")
    args = parser.parse_args()

    if not os.path.exists(input_csv):
        raise FileNotFoundError(
            f"Could not find '{input_csv}'. Make sure it exists in the same directory."
        )

    df = pd.read_csv(input_csv)
    if "Ticker" not in df.columns:
        raise KeyError("The input CSV must contain a 'Ticker' column.")

    raw_tickers = df["Ticker"].dropna().astype(str).str.strip().tolist()
    ticker_map = {t: t if t.endswith(".L") else t.replace(".", "-") for t in raw_tickers}

    # Filter to requested ticker(s) if specified
    if args.ticker:
        ticker_map = {t: v for t, v in ticker_map.items() if t in args.ticker}
        missing = set(args.ticker) - set(ticker_map.keys())
        if missing:
            print(f"Warning: ticker(s) not found in ticker_list.csv: {', '.join(sorted(missing))}")

    tickers = list(ticker_map.values())

    print(f"Processing {len(tickers)} ticker(s)...")
    print(f"Downloading P/E and dividend data...\n")

    for original_ticker, yf_ticker in ticker_map.items():
        safe_filename = original_ticker.replace("/", "_")
        daily_filepath = os.path.join(output_dir, f"{safe_filename}_PE.csv")
        fund_filepath = os.path.join(output_dir, f"{safe_filename}_fundamentals.csv")

        existing_df = None
        if os.path.exists(daily_filepath):
            try:
                existing_df = pd.read_csv(daily_filepath)
                existing_df = existing_df.dropna(subset=["Date"])
                if not existing_df.empty and "Date" in existing_df.columns:
                    last_date = pd.to_datetime(existing_df["Date"]).max()
                    print(f"  Existing data up to {last_date.date()}")
                    period = _compute_incremental_period(last_date)
                else:
                    existing_df = None
                    period = PERIOD
            except Exception:
                existing_df = None
                period = PERIOD
        else:
            period = PERIOD

        print(f"Processing [{yf_ticker}] -> {safe_filename} ...")
        try:
            result, fundamentals = calculate_pe_for_ticker(
                yf_ticker, period=period, existing_df=existing_df,
            )
            if result.empty:
                print(f"  No new data for {yf_ticker}.")
                print()
                continue

            if existing_df is not None and not existing_df.empty:
                combined = pd.concat([existing_df, result])
                combined = combined.sort_values("Date").reset_index(drop=True)
                combined.to_csv(daily_filepath, index=False)
                print(f"  Appended {len(result)} new rows ({len(combined)} total)")
                print(f"  Latest P/E: {combined['ta_pe'].iloc[-1]:.2f}", end="")
                if "ta_div_yield" in combined.columns and pd.notna(combined["ta_div_yield"].iloc[-1]):
                    print(f"  | Div Yield: {combined['ta_div_yield'].iloc[-1]:.2f}%")
                else:
                    print()
            else:
                result = result.sort_values("Date").reset_index(drop=True)
                result.to_csv(daily_filepath, index=False)
                print(f"  Saved {len(result)} daily rows to {daily_filepath}")
                print(f"  Latest P/E: {result['ta_pe'].iloc[-1]:.2f}", end="")
                if "ta_div_yield" in result.columns and pd.notna(result["ta_div_yield"].iloc[-1]):
                    print(f"  | Div Yield: {result['ta_div_yield'].iloc[-1]:.2f}%")
                else:
                    print()

        except Exception as e:
            print(f"  Error processing {yf_ticker}: {e}\n")

    print(f"\nAll done. Output directory: {output_dir}")
