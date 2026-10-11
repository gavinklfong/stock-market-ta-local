import math
import os
import pandas as pd

from common import main, read_yfinance_csv


def compute_atr(highs, lows, closes, period=14):
    """Compute Wilder's ATR. Returns list aligned with input."""
    if len(highs) < period + 1:
        return [None] * len(highs)

    true_ranges = [None] * len(highs)
    for i in range(len(highs)):
        if i == 0:
            true_ranges[i] = highs[i] - lows[i]
        else:
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges[i] = tr

    atr_values = [None] * len(highs)
    # Seed ATR at index `period` using first `period` true ranges (indices 0..period-1)
    initial_atr = sum(true_ranges[i] for i in range(period)) / period
    atr_values[period] = initial_atr

    k = 2.0 / (period + 1)
    for i in range(period + 1, len(highs)):
        if true_ranges[i] is not None:
            prev_atr = atr_values[i - 1]
            if prev_atr is not None:
                atr_values[i] = true_ranges[i] * k + prev_atr * (1 - k)

    return atr_values


def compute_bollinger_bands(closes, period=20, num_std=2.0):
    """Compute Bollinger Bands. Returns dict with upper, middle (SMA), lower."""
    n = len(closes)
    upper = [None] * n
    middle = [None] * n
    lower = [None] * n

    if n < period:
        return {"upper": upper, "middle": middle, "lower": lower}

    for i in range(period - 1, n):
        window = [float(closes[j]) for j in range(i - period + 1, i + 1)]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)
        middle[i] = mean
        upper[i] = mean + num_std * std
        lower[i] = mean - num_std * std

    return {"upper": upper, "middle": middle, "lower": lower}


def compute_volatility_columns(highs, lows, closes, n):
    """Compute all volatility indicator columns for a single ticker's data."""
    ta_atr = compute_atr(highs, lows, closes, 14) if n >= 15 else [None] * n
    ta_normalized_atr14 = [
        ta_atr[i] / closes[i] if ta_atr[i] is not None and closes[i] != 0 else None
        for i in range(n)
    ]
    bb = compute_bollinger_bands(closes) if n >= 20 else {"upper": [None] * n, "middle": [None] * n, "lower": [None] * n}

    return {
        "ta_atr14": ta_atr,
        "ta_normalized_atr14": ta_normalized_atr14,
        "ta_bband_upper": bb["upper"],
        "ta_bband_middle": bb["middle"],
        "ta_bband_lower": bb["lower"],
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    closes = raw_df["Close"].tolist()

    # Merge with existing TA data if available (preserves columns from prior modules)
    if os.path.exists(output_path):
        df = pd.read_csv(output_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        file_total = len(df)
        # Recompute volatility columns aligned to the sorted existing data
        raw_df = raw_df.sort_values("Date").reset_index(drop=True)
        highs = raw_df["High"].tolist()
        lows = raw_df["Low"].tolist()
        closes = raw_df["Close"].tolist()
    else:
        df = raw_df.copy()

    volatility_cols = compute_volatility_columns(highs, lows, closes, file_total)
    for col, values in volatility_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


main(
    module_name="calculate_volatility",
    description="volatility indicators: ATR(14), Bollinger Bands(20,2)",
    process_csv_fn=process_csv,
)
