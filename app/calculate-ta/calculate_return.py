import os
import sys
import pandas as pd

from common import (
    file_progress_bar,
    main,
    read_yfinance_csv,
)


def compute_future_returns(closes, horizons=(5, 10, 20)):
    """Compute forward-looking percentage returns for each horizon.

    For each horizon H, future_return_H = (close[t+H] - close[t]) / close[t].
    Returns None for the last H rows where future data is unavailable.

    Args:
        closes: list/array of close prices.
        horizons: tuple of integer horizons in trading days.

    Returns:
        dict mapping horizon (int) to list of float returns aligned with input.
    """
    n = len(closes)
    result = {}
    for h in horizons:
        returns = [None] * n
        for i in range(n - h):
            prev_close = closes[i]
            future_close = closes[i + h]
            if prev_close != 0:
                returns[i] = (future_close - prev_close) / prev_close
        result[h] = returns
    return result


def compute_return_columns(highs, lows, closes, volumes, n, horizons=(5, 10, 20)):
    """Compute all future-return indicator columns for a single ticker's data."""
    future = compute_future_returns(closes, horizons)
    cols = {}
    for h in horizons:
        cols[f"ta_return_{h}d"] = future[h]
    return cols


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    closes = raw_df["Close"].tolist()
    volumes = raw_df["Volume"].tolist()

    # Merge with existing TA data if available (preserves columns from prior modules)
    if os.path.exists(output_path):
        df = pd.read_csv(output_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        file_total = len(df)
        # Realign closes to the sorted existing data
        raw_df = raw_df.sort_values("Date").reset_index(drop=True)
        closes = raw_df["Close"].tolist()
    else:
        df = raw_df.copy()

    return_cols = compute_return_columns(highs, lows, closes, volumes, file_total)
    for col, values in return_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


if __name__ == "__main__":
    main(
        module_name="calculate_return",
        description="future returns: 5d/10d/20d",
        process_csv_fn=process_csv,
    )
