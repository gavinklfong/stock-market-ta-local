import os
import pandas as pd
import yfinance as yf


PERIOD = "20y"

# Resolve paths relative to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# File and directory configurations (defaults — can be overridden for testing)
DEFAULT_INPUT_CSV = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "config", "ticker_list.csv"))
DEFAULT_OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data", "market-data"))


def load_ticker_map(input_csv=None):
    """Read ticker_list.csv and return a mapping of original ticker → Yahoo ticker."""
    if input_csv is None:
        input_csv = DEFAULT_INPUT_CSV

    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Could not find '{input_csv}'. Make sure it exists in the same directory.")

    df = pd.read_csv(input_csv)

    if "Ticker" not in df.columns:
        raise KeyError("The input CSV must contain a 'Ticker' column.")

    raw_tickers = df["Ticker"].dropna().astype(str).str.strip().tolist()
    ticker_map = {t: t if t.endswith(".L") else t.replace(".", "-") for t in raw_tickers}
    return ticker_map


def read_existing_data(filepath):
    """Read existing CSV and return DataFrame with Date as datetime index, or None if not found."""
    if not os.path.exists(filepath):
        return None
    df_existing = pd.read_csv(filepath)
    if "Date" not in df_existing.columns:
        return None
    df_existing["Date"] = pd.to_datetime(df_existing["Date"])
    return df_existing.set_index("Date")


def download_full(yf_ticker):
    """Download full history for a ticker."""
    return yf.download(yf_ticker, period=PERIOD, auto_adjust=False, threads=False).dropna(how="all")


def download_catchup(yf_ticker, last_date, end_date=None):
    """Download data from the day after last_date up to today (or end_date).

    Args:
        yf_ticker: Yahoo Finance ticker symbol.
        last_date: The last date already in the local CSV. Download starts the next day.
        end_date: End date for the download range (default: today).

    Returns:
        DataFrame with new data, or empty DataFrame if no data in range.
    """
    start_date = last_date + pd.Timedelta(days=1)
    if end_date is None:
        end_date = pd.Timestamp.today()
    return yf.download(
        yf_ticker, start=start_date, end=end_date,
        auto_adjust=False, threads=False,
    ).dropna(how="all")


def save_data(filepath, ticker_df):
    """Save DataFrame to CSV with Date as a column, sorted by date.
    
    Adds a 'weekday' column (0=Monday, 1=Tuesday, …, 6=Sunday) derived from the DatetimeIndex.
    """
    ticker_df = ticker_df.copy()
    if isinstance(ticker_df.index, pd.DatetimeIndex):
        ticker_df.index.name = "Date"
        # Derive weekday from the DatetimeIndex (0=Mon … 6=Sun)
        ticker_df["weekday"] = ticker_df.index.dayofweek
    else:
        ticker_df["Date"] = pd.to_datetime(ticker_df["Date"])
        ticker_df = ticker_df.sort_values("Date")
        ticker_df = ticker_df.set_index("Date")
        ticker_df["weekday"] = ticker_df.index.dayofweek
    ticker_df = ticker_df[~ticker_df.index.duplicated(keep="last")]
    ticker_df = ticker_df.sort_index()
    ticker_df.to_csv(filepath)


def download_tickers(input_csv=None, output_dir=None):
    """Main entry point: download or update market data for all tickers.

    - If no CSV exists for a ticker, downloads full 20y history.
    - If a CSV already exists, downloads catch-up data from the day after
      the last date in the existing file.

    Args:
        input_csv: Path to ticker_list.csv (defaults to SCRIPT_DIR/ticker_list.csv).
        output_dir: Output directory for CSV files (defaults to data/market-data).
    """
    if input_csv is None:
        input_csv = DEFAULT_INPUT_CSV
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)
    ticker_map = load_ticker_map(input_csv)

    print(f"Loaded {len(ticker_map)} tickers from '{input_csv}'.")

    # Download data for each ticker
    for original_ticker, yf_ticker in ticker_map.items():
        try:
            safe_filename = original_ticker.replace("/", "_")
            filepath = os.path.join(output_dir, f"{safe_filename}.csv")

            existing = read_existing_data(filepath)

            if existing is not None:
                last_date = existing.index.max()
                today = pd.Timestamp.today().normalize()

                # If the last date is today, the catch-up range (tomorrow..today) is empty.
                # Re-download today's data to refresh the price.
                if last_date.date() == today.date():
                    print(f"Updating {original_ticker} (last date: {last_date.date()}, "
                          f"re-downloading today's price)...")
                    new_data = download_catchup(yf_ticker, last_date - pd.Timedelta(days=1),
                                               end_date=today)

                    if new_data.empty:
                        print(f"  No new data for {original_ticker}.")
                        continue

                    # Overwrite today's entry with the freshly downloaded data
                    merged = pd.concat([existing, new_data])
                    merged = merged[~merged.index.duplicated(keep="last")]
                    merged = merged.sort_index()
                    save_data(filepath, merged)
                    print(f"  Updated: {filepath} (replaced today's price)")
                    continue

                # Standard catch-up: download from the day after last_date through today
                print(f"Updating {original_ticker} (last date: {last_date.date()}, downloading catch-up)...")
                new_data = download_catchup(yf_ticker, last_date, end_date=today)

                if new_data.empty:
                    print(f"  No new data for {original_ticker}.")
                    continue

                # Merge: combine existing with new data; overlapping dates kept from new_data
                merged = pd.concat([existing, new_data])
                merged = merged[~merged.index.duplicated(keep="last")]
                merged = merged.sort_index()
                last_date = merged.index.max()

                save_data(filepath, merged)
                print(f"  Updated: {filepath} (last date: {last_date.date()}, "
                      f"added {len(new_data)} rows)")
            else:
                # Full download
                print(f"Downloading full history for {original_ticker} ({PERIOD})...")
                ticker_df = download_full(yf_ticker)

                if ticker_df.empty:
                    print(f"  Skipped {original_ticker}: No data returned.")
                    continue

                save_data(filepath, ticker_df)
                last_date = ticker_df.index.max()
                print(f"  Saved: {filepath} ({len(ticker_df)} rows, "
                      f"last date: {last_date.date()})")

        except Exception as e:
            print(f"Error processing {original_ticker}: {e}")

    print("\nProcess completed successfully!")


if __name__ == "__main__":
    download_tickers()