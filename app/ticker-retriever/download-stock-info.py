"""Download stock info and calculate P/E ratio for all tickers in ticker_list.csv.

P/E = Closing Price / TTM EPS

Since EPS is reported quarterly/semi-annually and prices are daily,
we forward-fill the most recent TTM EPS for each date.

EPS is fetched from multiple sources (in priority order):
  1. quarterly_income_stmt  — quarterly Diluted EPS (US stocks, many international)
  2. earnings_dates         — Reported EPS from earnings calendar (more coverage)
  3. income_stmt            — annual Diluted EPS fallback

Output: data/pe-data/<ticker>_PE.csv  (columns: Date, Close, ta_eps_ttm, ta_pe)
"""

import os
import warnings

import yfinance as yf
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)


# --- Path resolution ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_csv = os.path.join(SCRIPT_DIR, "ticker_list.csv")
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


def calculate_pe_for_ticker(ticker: str, period: str = "15y") -> pd.DataFrame:
    """Calculate daily P/E using trailing EPS.

    Tries quarterly sources first, falls back to annual.

    Parameters
    ----------
    ticker : str
        Stock ticker (e.g. "NG.L").
    period : str
        How far back to get price data (passed to yfinance).

    Returns
    -------
    pd.DataFrame
        Columns: Date, Close, ta_eps_ttm, ta_pe
    """
    stock = yf.Ticker(ticker)

    # ── 1. Get historical daily closing prices ──────────────────────
    hist = stock.history(period=period)
    if hist.empty:
        raise ValueError(f"No price data for {ticker}")

    prices = hist[["Close"]].copy()
    prices.index.name = "Date"
    prices = prices.reset_index()
    prices["Date"] = pd.to_datetime(prices["Date"]).dt.tz_localize(None)

    # Normalize price to currency (GBp → GBP for UK stocks)
    currency = stock.info.get("currency", "")
    close_price = prices["Close"].values.copy()
    if currency == "GBp":
        close_price = close_price / 100

    prices["Close"] = close_price

    # ── 2. Get EPS (multi-source: quarterly → earnings_dates → annual) ──
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

    # ── 3. Compute TTM or use raw EPS ───────────────────────────────
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

    # ── 4. Map EPS to each price date (forward-fill) ────────────────
    # Sort valid EPS by date (merge_asof requires sorted input)
    valid_ttm = ttm_eps_series.dropna().sort_index()
    ttm_df = valid_ttm.reset_index()
    ttm_df.columns = ["EPS_Date", "ta_eps_ttm"]

    # Keep Close in price_df so it survives the merge
    price_df = prices[["Date", "Close"]].copy().sort_values("Date")

    merged = pd.merge_asof(
        price_df,
        ttm_df,
        left_on="Date",
        right_on="EPS_Date",
        direction="backward",
    )

    # ── 5. Calculate P/E ────────────────────────────────────────────
    merged["ta_pe"] = merged["Close"] / merged["ta_eps_ttm"]

    # ── 6. Clean up ─────────────────────────────────────────────────
    result = merged[["Date", "Close", "ta_eps_ttm", "ta_pe"]].copy()
    # Drop rows before we had any valid EPS
    result = result.dropna(subset=["ta_eps_ttm", "ta_pe"])

    return result


def bulk_download() -> None:
    """Read ticker_list.csv and calculate P/E for each ticker."""
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
    print(f"Downloading P/E data (quarterly EPS, TTM)...\n")

    for original_ticker, yf_ticker in ticker_map.items():
        safe_filename = original_ticker.replace("/", "_")
        filepath = os.path.join(output_dir, f"{safe_filename}_PE.csv")

        print(f"Processing [{yf_ticker}] -> {safe_filename} ...")
        try:
            result = calculate_pe_for_ticker(yf_ticker, period=PERIOD)
            if result.empty:
                print(f"  Skipped {yf_ticker}: No valid P/E data.\n")
                continue

            result = result.sort_values("Date").reset_index(drop=True)
            result.to_csv(filepath, index=False)
            print(f"  Saved {len(result)} rows to {filepath}")
            print(f"  Latest P/E: {result['ta_pe'].iloc[-1]:.2f}\n")

        except Exception as e:
            print(f"  Error processing {yf_ticker}: {e}\n")

    print(f"\nAll done. Output directory: {output_dir}")


if __name__ == "__main__":
    bulk_download()
