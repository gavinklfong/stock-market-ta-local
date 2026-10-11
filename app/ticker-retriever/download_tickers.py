import os
import pandas as pd
import yfinance as yf


PERIOD = "20y"  # Download 30 years of data to ensure we cover at least 20 years

# Resolve paths relative to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# File and directory configurations
input_csv = os.path.join(SCRIPT_DIR, "ticker_list.csv")
output_dir = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "data", "market-data"))

# Create output folder if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# 1. Read tickers from the CSV file
if not os.path.exists(input_csv):
    raise FileNotFoundError(f"Could not find '{input_csv}'. Make sure it exists in the same directory.")

df = pd.read_csv(input_csv)

if "Ticker" not in df.columns:
    raise KeyError("The input CSV must contain a 'Ticker' column.")

# Clean whitespace and create a map for Yahoo Finance formatting (e.g., BRK.B -> BRK-B)
raw_tickers = df["Ticker"].dropna().astype(str).str.strip().tolist()
ticker_map = {t: t if t.endswith(".L") else t.replace(".", "-") for t in raw_tickers}
yf_tickers = list(ticker_map.values())

print(f"Loaded {len(yf_tickers)} tickers from '{input_csv}'.")
print(f"Downloading {PERIOD} of daily market data...")

# 2. Bulk download 20 years of market data
data = yf.download(yf_tickers, period=PERIOD, group_by="ticker", threads=True)

print(f"Separating data into individual CSV files inside '{output_dir}/'...")

# 3. Export each ticker's dataset to [ticker].csv
for original_ticker, yf_ticker in ticker_map.items():
    try:
        # Handle single vs. multiple ticker DataFrame structure from yfinance
        if len(yf_tickers) == 1:
            ticker_df = data.dropna(how="all")
        else:
            ticker_df = data[yf_ticker].dropna(how="all") if yf_ticker in data else pd.DataFrame()

        if not ticker_df.empty:
            # Clean filename to ensure valid path characters
            safe_filename = original_ticker.replace("/", "_")
            filepath = os.path.join(output_dir, f"{safe_filename}.csv")
            ticker_df.to_csv(filepath)
            print(f"Saved: {filepath}")
        else:
            print(f"Skipped {original_ticker}: No data returned.")

    except Exception as e:
        print(f"Error saving {original_ticker}: {e}")

print("\nProcess completed successfully!")