"""Calculate historical P/E ratio for a stock.

P/E = Closing Price / EPS

Since EPS is reported quarterly/annually and prices are daily,
we forward-fill the most recent EPS for each date.
"""

import warnings

import yfinance as yf
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)


def calculate_pe_ratio(
    ticker: str,
    period: str = "10y",
    eps_freq: str = "yearly",
) -> pd.DataFrame:
    """Return a DataFrame with daily dates, close price, trailing EPS, and P/E.

    Parameters
    ----------
    ticker : str
        Stock ticker (e.g. "NG.L").
    period : str
        How far back to get price data (passed to yfinance).
    eps_freq : str
        "yearly" or "quarterly" — which EPS granularity to use.

    Returns
    -------
    pd.DataFrame
        Columns: Date, Close, EPS, PE
    """
    stock = yf.Ticker(ticker)

    # ── 1. Get historical daily closing prices ──────────────────────
    hist = stock.history(period=period)
    if hist.empty:
        raise ValueError(f"No price data for {ticker}")

    prices = hist[["Close"]].copy()
    prices.index.name = "Date"
    prices = prices.reset_index()
    # Normalize dates to timezone-naive
    prices["Date"] = pd.to_datetime(prices["Date"]).dt.tz_localize(None)

    # ── 2. Get historical EPS ───────────────────────────────────────
    income_stmt = stock.income_stmt
    if income_stmt is None or income_stmt.empty:
        raise ValueError(f"No income statement data for {ticker}")

    eps_rows = ["Diluted EPS", "Basic EPS"]
    eps_df = income_stmt.loc[
        income_stmt.index.isin(eps_rows),
    ]
    if eps_df.empty:
        raise ValueError(f"No EPS data for {ticker}")

    # Pick Diluted EPS (or "Basic EPS" if you prefer)
    eps_values = eps_df.loc["Diluted EPS"].to_dict()

    # Build a DataFrame with EPS periods
    eps_dates = pd.to_datetime(list(eps_values.keys())).tz_localize(None)
    eps_data = pd.DataFrame(
        {"EPS": list(eps_values.values())},
        index=eps_dates,
    ).sort_index()

    print(f"EPS data ({eps_freq}):")
    print(eps_data.T.to_string())
    print()

    # ── 3. Map EPS to each price date ───────────────────────────────
    # For each date, find the most recent EPS report and forward-fill
    price_df = prices[["Date"]].copy()

    eps_reset = eps_data.reset_index().rename(columns={"index": "EPS_Date"})
    merged = pd.merge_asof(
        price_df,
        eps_reset,
        left_on="Date",
        right_on="EPS_Date",
        direction="backward",
    )

    # ── 4. Calculate P/E ────────────────────────────────────────────
    # Normalize price to EPS currency (GBp → GBP for UK stocks)
    close_price = prices["Close"].values.copy()
    currency = stock.info.get("currency", "")
    if currency == "GBp":
        close_price = close_price / 100  # pence → pounds

    merged["Close"] = close_price
    merged["PE"] = merged["Close"] / merged["EPS"]

    # Clean up
    result = merged[["Date", "Close", "EPS", "PE"]].copy()
    result = result.dropna(subset=["EPS"])  # drop dates before any EPS report

    return result


def print_pe_summary(df: pd.DataFrame, ticker: str) -> None:
    """Print a summary of the P/E data."""
    print(f"Historical P/E Ratio for {ticker}\n")
    print(
        df.tail(5).to_string(
            index=False,
            float_format="%.4f",
        )
    )
    print()
    print(f"Summary statistics:")
    print(f"  Min P/E:  {df['PE'].min():.2f}")
    print(f"  Max P/E:  {df['PE'].max():.2f}")
    print(f"  Mean P/E: {df['PE'].mean():.2f}")
    print(f"  Median P/E: {df['PE'].median():.2f}")
    print(f"  Latest P/E: {df['PE'].iloc[-1]:.2f}")


if __name__ == "__main__":
    result = calculate_pe_ratio("NG.L", period="10y", eps_freq="yearly")
    print_pe_summary(result, "NG.L")

    # Optionally save to CSV
    # output_dir = os.path.join(SCRIPT_DIR, "..", "..", "data", "pe-data")
    # os.makedirs(output_dir, exist_ok=True)
    # filepath = os.path.join(output_dir, "NG.L_PE.csv")
    # result.to_csv(filepath, index=False)
    # print(f"\nSaved to {filepath}")
